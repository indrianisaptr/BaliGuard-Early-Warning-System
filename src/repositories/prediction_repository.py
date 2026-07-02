"""
prediction_repository.py — BaliGuard Prediction Storage
=========================================================
Tanggung jawab tunggal: kirim hasil predictions_final.csv (DataFrame) ke
Supabase tabel `public.predictions`, via batch upsert (on conflict month).

Tidak menyentuh feature engineering / training / crisis score / dashboard /
automation — repository ini murni storage layer baru, dipanggil dari
update_pipeline.py SETELAH predictions_final.csv berhasil ditulis ke disk.

Env var yang dibutuhkan (service_role key — write access via RLS policy
"predictions_write_service_role", lihat 002_create_predictions.sql):
    SUPABASE_URL
    SUPABASE_SERVICE_KEY

Kalau kredensial tidak tersedia atau supabase-py tidak terinstall, repository
ini TIDAK melempar exception ke caller secara default (lihat upsert_predictions
param `raise_on_error`) — supaya pipeline lokal tetap bisa jalan generate CSV
walau belum dikonfigurasi Supabase-nya. Caller (update_pipeline.py) hanya
mencetak warning kalau upsert gagal/skip.
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd

try:
    from supabase import create_client, Client
    _SUPABASE_SDK_AVAILABLE = True
except ImportError:
    _SUPABASE_SDK_AVAILABLE = False


# Kolom predictions_final.csv yang dipetakan ke tabel public.predictions.
# Urutan tidak penting (upsert pakai dict per baris), tapi daftar ini dipakai
# untuk memvalidasi & menyaring kolom sebelum dikirim (jaga-jaga kalau CSV
# punya kolom ekstra di masa depan yang belum ada di skema tabel).
PREDICTIONS_TABLE = "predictions"

PREDICTIONS_COLUMNS = [
    "month", "wisman", "tpk_bintang", "inflasi_processed", "usd_idr_avg",
    "avg_sentiment_monthly", "bali_share_pct", "wisman_zscore",
    "wisman_growth_mom", "wisman_growth_yoy", "crisis_score_100",
    "crisis_level", "rf_predicted_level", "rf_confidence",
    "prob_aman", "prob_waspada", "prob_siaga", "prob_krisis",
    "iso_anomaly", "iso_score", "gdelt_crisis_score", "economic_risk_score",
    "disaster_risk_score", "external_risk_avg", "physical_risk_score",
    "media_risk_score", "tourist_perception_score", "external_risk_score",
    "wisman_recovery_pct", "pct_negative_monthly", "usd_volatility_3m",
]

# Kolom wajib non-null di skema tabel (constraint `not null`).
REQUIRED_COLUMNS = PREDICTIONS_COLUMNS  # semua kolom di atas NOT NULL di 002

DEFAULT_BATCH_SIZE = 50


class PredictionRepository:
    """Batch upsert predictions_final.csv ke Supabase."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_KEY")
        self.batch_size = batch_size
        self._client: Optional["Client"] = None

    # ── Client lazy-init ─────────────────────────────────────────────
    @property
    def client(self) -> "Client":
        if self._client is not None:
            return self._client

        if not _SUPABASE_SDK_AVAILABLE:
            raise RuntimeError(
                "Package 'supabase' belum terinstall. Jalankan: pip install supabase"
            )
        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY belum diset di environment."
            )

        self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client

    def is_configured(self) -> bool:
        """True kalau SDK terinstall dan kredensial tersedia."""
        return _SUPABASE_SDK_AVAILABLE and bool(self.supabase_url) and bool(self.supabase_key)

    # ── Konversi DataFrame -> list[dict] siap upsert ────────────────
    @staticmethod
    def _dataframe_to_records(df: pd.DataFrame) -> list[dict]:
        missing = [c for c in PREDICTIONS_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame predictions kekurangan kolom yang dibutuhkan tabel: {missing}"
            )

        subset = df[PREDICTIONS_COLUMNS].copy()

        # month harus YYYY-MM string (samakan dengan constraint chk_predictions_month_format)
        subset["month"] = subset["month"].astype(str).str[:7]

        # iso_anomaly harus int (0/1), bukan numpy.int64 (supaya JSON-serializable)
        subset["iso_anomaly"] = subset["iso_anomaly"].astype(int)
        subset["wisman"] = subset["wisman"].astype(int)

        records = subset.to_dict(orient="records")

        # Pastikan semua nilai numpy -> tipe Python native (json-serializable)
        for row in records:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif hasattr(v, "item"):
                    row[k] = v.item()

        return records

    # ── Batch upsert ─────────────────────────────────────────────────
    def upsert_predictions(
        self,
        df: pd.DataFrame,
        raise_on_error: bool = False,
    ) -> dict:
        """
        Upsert seluruh baris df ke public.predictions, on conflict(month)
        do update (default behaviour Supabase upsert dengan PK month).

        Return summary dict: {"sent": int, "batches": int, "ok": bool, "error": str|None}
        """
        summary = {"sent": 0, "batches": 0, "ok": False, "error": None}

        if not self.is_configured():
            msg = (
                "PredictionRepository belum dikonfigurasi (SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY/paket supabase belum tersedia) — upsert dilewati."
            )
            summary["error"] = msg
            if raise_on_error:
                raise RuntimeError(msg)
            return summary

        try:
            records = self._dataframe_to_records(df)
        except ValueError as e:
            summary["error"] = str(e)
            if raise_on_error:
                raise
            return summary

        try:
            for i in range(0, len(records), self.batch_size):
                batch = records[i : i + self.batch_size]
                (
                    self.client.table(PREDICTIONS_TABLE)
                    .upsert(batch, on_conflict="month")
                    .execute()
                )
                summary["sent"] += len(batch)
                summary["batches"] += 1
            summary["ok"] = True
        except Exception as e:
            summary["error"] = str(e)
            if raise_on_error:
                raise

        return summary

    # ── Fetch: Supabase -> pandas.DataFrame ─────────────────────────
    def get_predictions_dataframe(self) -> pd.DataFrame:
        """
        Ambil seluruh baris dari public.predictions, diurutkan month ASC,
        dan kembalikan sebagai pandas.DataFrame yang skema & dtype-nya
        kompatibel dengan hasil pd.read_csv("predictions_final.csv").

        Tidak mengubah write path (upsert_predictions, _dataframe_to_records,
        constructor, validasi, batching, logging) — method ini murni
        tambahan read-only di sisi yang sama dengan client Supabase yang
        sudah ada.

        Kolom yang diambil & urutannya mengikuti PREDICTIONS_COLUMNS
        (bukan SELECT * dan bukan daftar kolom baru), karena sudah
        diverifikasi identik 1:1 dengan kolom data di 002_create_predictions.sql.

        PostgREST membatasi jumlah baris per response (default umumnya
        1000). Pagination ditangani via `.range()` supaya data tidak
        terpotong diam-diam kalau tabel predictions tumbuh melewati
        batas tersebut di masa depan.

        Return:
            pandas.DataFrame dengan kolom PREDICTIONS_COLUMNS, terurut
            month ASC, RangeIndex 0..n-1. Kalau tabel kosong, kembalikan
            DataFrame kosong (0 baris) dengan kolom PREDICTIONS_COLUMNS
            tetap ada — bukan exception.

        Raises:
            RuntimeError: kalau repository belum dikonfigurasi (SDK/
                kredensial belum tersedia) — caller perlu cek
                is_configured() dulu kalau ingin menghindari exception ini,
                sama seperti pola `client` property di atas.
        """
        if not self.is_configured():
            raise RuntimeError(
                "PredictionRepository belum dikonfigurasi (SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY/paket supabase belum tersedia) — "
                "tidak bisa fetch predictions."
            )

        select_cols = ",".join(PREDICTIONS_COLUMNS)
        page_size = 1000
        offset = 0
        rows: list[dict] = []

        while True:
            response = (
                self.client.table(PREDICTIONS_TABLE)
                .select(select_cols)
                .order("month", desc=False)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            page = response.data or []
            rows.extend(page)
            if len(page) < page_size:
                break
            offset += page_size

        if not rows:
            return pd.DataFrame(columns=PREDICTIONS_COLUMNS)

        df = pd.DataFrame(rows, columns=PREDICTIONS_COLUMNS)
        df = df.reset_index(drop=True)

        # month: pastikan string, pertahankan format YYYY-MM (defensive,
        # karena kolom sudah text di skema, tapi tetap dijaga independen
        # dari detail tipe sisi DB — konsisten dengan kontrak di write path).
        df["month"] = df["month"].astype(str).str[:7]

        # Seluruh kolom numerik: konversi aman supaya dtype mendekati
        # hasil pd.read_csv() (int64/float64), bukan tetap object dtype
        # akibat hasil JSON dari Supabase API.
        numeric_cols = [
            c for c in PREDICTIONS_COLUMNS
            if c not in ("month", "crisis_level", "rf_predicted_level")
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df
