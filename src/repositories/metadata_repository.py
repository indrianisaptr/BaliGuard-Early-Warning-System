"""
metadata_repository.py — BaliGuard Metadata Storage
=========================================================
Tanggung jawab tunggal: baca/tulis satu baris ringkasan metadata pipeline
(versi model, tanggal training, bulan data terakhir, dll) ke Supabase tabel
`public.metadata`, via upsert (on conflict id).

Tidak menyentuh feature engineering / training / crisis score / dashboard /
automation / scheduler — repository ini murni storage layer, mengikuti pola
arsitektur yang sama dengan PredictionRepository (src/repositories/
prediction_repository.py), hanya beda tabel & tanpa batching (metadata
selalu satu baris).

Env var yang dibutuhkan (service_role key — sama seperti PredictionRepository):
    SUPABASE_URL
    SUPABASE_SERVICE_KEY

Kalau kredensial tidak tersedia atau supabase-py tidak terinstall, repository
ini TIDAK melempar exception ke caller secara default (lihat upsert_metadata
param `raise_on_error`) — supaya pipeline lokal tetap bisa jalan walau belum
dikonfigurasi Supabase-nya. Caller cukup cek summary dict yang dikembalikan.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

try:
    from supabase import create_client, Client
    _SUPABASE_SDK_AVAILABLE = True
except ImportError:
    _SUPABASE_SDK_AVAILABLE = False


# Kolom public.metadata yang dikenal repository ini. Daftar ini dipakai
# untuk menyaring dict sebelum dikirim (jaga-jaga kalau caller menyertakan
# key ekstra yang belum ada di skema tabel).
METADATA_TABLE = "pipeline_metadata"

METADATA_COLUMNS = [
    "model_version", "training_date", "latest_prediction_month",
    "latest_data_month", "prediction_rows", "pipeline_version",
    "dashboard_version", "updated_at", "notes",
]

# BaliGuard hanya memiliki SATU metadata aktif — bukan histori per waktu,
# melainkan current snapshot (ringkasan kondisi pipeline paling mutakhir).
# Seluruh dashboard/caller selalu membaca & menulis id=1 yang sama.
METADATA_ROW_ID = 1


class MetadataRepository:
    """Upsert & baca satu baris ringkasan metadata pipeline di Supabase."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_KEY")
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

    # ── Konversi dict caller -> record siap upsert ──────────────────
    @staticmethod
    def _dict_to_record(data: dict) -> dict:
        """
        Saring `data` supaya hanya berisi key yang dikenal METADATA_COLUMNS,
        lalu tambahkan primary key tetap (METADATA_ROW_ID) karena metadata
        selalu satu baris.

        Kalau caller tidak mengirim `updated_at`, isi otomatis dengan waktu
        saat ini (UTC, ISO 8601) — supaya kolom ini tidak pernah kosong
        walau pipeline lupa mengisinya. Kalau caller sudah mengirim
        `updated_at` sendiri, nilai itu tetap dipakai (tidak ditimpa).
        """
        record = {k: v for k, v in data.items() if k in METADATA_COLUMNS}
        record.setdefault("updated_at", datetime.utcnow().isoformat())
        record["id"] = METADATA_ROW_ID
        return record

    # ── Upsert (satu baris, tanpa batching) ─────────────────────────
    def upsert_metadata(
        self,
        data: dict,
        raise_on_error: bool = False,
    ) -> dict:
        """
        Upsert satu baris ringkasan metadata ke public.metadata, on
        conflict(id) do update. Karena metadata hanya satu baris, tidak
        ada batching di sini (beda dengan PredictionRepository.upsert_predictions
        yang mem-batch banyak baris).

        Param:
            data: dict berisi sebagian/seluruh METADATA_COLUMNS, contoh
                {"model_version": "...", "training_date": "...", ...}.
                Key di luar METADATA_COLUMNS diabaikan (tidak error).
            raise_on_error: kalau True, lempar exception alih-alih
                mengembalikan summary dengan ok=False.

        Return summary dict: {"ok": bool, "error": str|None}
        """
        summary = {"ok": False, "error": None}

        if not self.is_configured():
            msg = (
                "MetadataRepository belum dikonfigurasi (SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY/paket supabase belum tersedia) — upsert dilewati."
            )
            summary["error"] = msg
            if raise_on_error:
                raise RuntimeError(msg)
            return summary

        try:
            record = self._dict_to_record(data)
            (
                self.client.table(METADATA_TABLE)
                .upsert(record, on_conflict="id")
                .execute()
            )
            summary["ok"] = True
        except Exception as e:
            summary["error"] = str(e)
            if raise_on_error:
                raise

        return summary

    # ── Fetch: Supabase -> dict ──────────────────────────────────────
    def get_metadata(self) -> dict:
        """
        Ambil baris metadata (id=METADATA_ROW_ID) dari public.metadata.

        Tidak mengubah write path (upsert_metadata, _dict_to_record,
        constructor, is_configured) — method ini murni tambahan read-only
        di sisi yang sama dengan client Supabase yang sudah ada.

        Return:
            dict berisi kolom METADATA_COLUMNS kalau baris ditemukan.
            Kalau tabel kosong / repository belum dikonfigurasi / terjadi
            error, kembalikan {} — BUKAN exception, supaya pipeline tidak
            crash hanya karena metadata belum ada.
        """
        if not self.is_configured():
            return {}

        try:
            response = (
                self.client.table(METADATA_TABLE)
                .select(",".join(METADATA_COLUMNS))
                .eq("id", METADATA_ROW_ID)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if not rows:
                return {}
            return rows[0]
        except Exception:
            return {}
