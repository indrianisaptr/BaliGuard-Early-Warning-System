"""
pipeline_log_repository.py — BaliGuard Pipeline Log Storage
=========================================================
Tanggung jawab tunggal: catat histori setiap eksekusi update_pipeline.py
(waktu mulai/selesai, status, ringkasan hasil run) ke Supabase tabel
`public.pipeline_logs`, via insert (satu baris baru per run — BUKAN
upsert, karena setiap eksekusi pipeline adalah histori terpisah, tidak
seperti MetadataRepository yang selalu menimpa satu baris current
snapshot).

Tidak menyentuh feature engineering / training / crisis score / dashboard /
automation / scheduler — repository ini murni storage layer, mengikuti pola
arsitektur yang sama dengan MetadataRepository (src/repositories/
metadata_repository.py) dan PredictionRepository (src/repositories/
prediction_repository.py).

Env var yang dibutuhkan (service_role key — sama seperti MetadataRepository
dan PredictionRepository):
    SUPABASE_URL
    SUPABASE_SERVICE_KEY

Kalau kredensial tidak tersedia atau supabase-py tidak terinstall, repository
ini TIDAK melempar exception ke caller secara default (lihat insert_log
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


# Kolom public.pipeline_logs yang dikenal repository ini. Daftar ini dipakai
# untuk menyaring dict sebelum dikirim (jaga-jaga kalau caller menyertakan
# key ekstra yang belum ada di skema tabel). `id` tidak masuk daftar ini
# karena primary key di-generate otomatis oleh database saat insert.
PIPELINE_LOGS_TABLE = "pipeline_logs"

PIPELINE_LOG_COLUMNS = [
    "run_id", "started_at", "finished_at", "duration_seconds",
    "status", "latest_month", "prediction_rows", "prediction_uploaded",
    "metadata_uploaded", "pipeline_version", "error_message", "created_at",
]

# Kolom yang diambil saat fetch (whitelist select, termasuk `id` karena
# untuk read-path primary key berguna untuk caller, beda dengan write-path
# yang tidak butuh caller mengirim id).
PIPELINE_LOG_SELECT_COLUMNS = ["id"] + PIPELINE_LOG_COLUMNS


class PipelineLogRepository:
    """Insert & baca histori eksekusi pipeline di Supabase."""

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

    # ── Konversi dict caller -> record siap insert ──────────────────
    @staticmethod
    def _dict_to_record(data: dict) -> dict:
        """
        Saring `data` supaya hanya berisi key yang dikenal
        PIPELINE_LOG_COLUMNS (id tidak disertakan — auto-generated DB).

        Kalau caller tidak mengirim `created_at`, isi otomatis dengan
        waktu saat ini (UTC, ISO 8601) — supaya kolom ini tidak pernah
        kosong walau caller lupa mengisinya. Kalau caller sudah mengirim
        `created_at` sendiri, nilai itu tetap dipakai (tidak ditimpa).
        """
        record = {k: v for k, v in data.items() if k in PIPELINE_LOG_COLUMNS}
        record.setdefault("created_at", datetime.utcnow().isoformat())
        return record

    # ── Insert (satu baris baru per run, tanpa upsert) ───────────────
    def insert_log(
        self,
        data: dict,
        raise_on_error: bool = False,
    ) -> dict:
        """
        Insert satu baris histori eksekusi pipeline ke public.pipeline_logs.
        Setiap panggilan menghasilkan baris baru (bukan upsert), karena
        tiap eksekusi pipeline adalah histori terpisah.

        Param:
            data: dict berisi sebagian/seluruh PIPELINE_LOG_COLUMNS, contoh
                {"run_id": "...", "status": "success", ...}.
                Key di luar PIPELINE_LOG_COLUMNS diabaikan (tidak error).
            raise_on_error: kalau True, lempar exception alih-alih
                mengembalikan summary dengan ok=False.

        Return summary dict: {"ok": bool, "error": str|None}
        """
        summary = {"ok": False, "error": None}

        if not self.is_configured():
            msg = (
                "PipelineLogRepository belum dikonfigurasi (SUPABASE_URL/"
                "SUPABASE_SERVICE_KEY/paket supabase belum tersedia) — insert dilewati."
            )
            summary["error"] = msg
            if raise_on_error:
                raise RuntimeError(msg)
            return summary

        try:
            record = self._dict_to_record(data)
            self.client.table(PIPELINE_LOGS_TABLE).insert(record).execute()
            summary["ok"] = True
        except Exception as e:
            summary["error"] = str(e)
            if raise_on_error:
                raise

        return summary

    # ── Fetch: Supabase -> dict ──────────────────────────────────────
    def get_latest_log(self) -> dict:
        """
        Ambil baris histori pipeline paling baru dari public.pipeline_logs,
        diurutkan `started_at` DESC.

        Tidak mengubah write path (insert_log, _dict_to_record, constructor,
        is_configured) — method ini murni tambahan read-only di sisi yang
        sama dengan client Supabase yang sudah ada.

        Return:
            dict berisi kolom PIPELINE_LOG_SELECT_COLUMNS kalau baris
            ditemukan. Kalau tabel kosong / repository belum dikonfigurasi /
            terjadi error, kembalikan {} — BUKAN exception, supaya pipeline
            tidak crash hanya karena log belum ada.
        """
        if not self.is_configured():
            return {}

        try:
            response = (
                self.client.table(PIPELINE_LOGS_TABLE)
                .select(",".join(PIPELINE_LOG_SELECT_COLUMNS))
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if not rows:
                return {}
            return rows[0]
        except Exception:
            return {}
