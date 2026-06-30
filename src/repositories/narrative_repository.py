"""
src/repositories/narrative_repository.py — BaliGuard: Narrative Repository

Satu-satunya jalur baca/tulis ke tabel Supabase `narratives`.
Sesuai Data Contract: dataset ini APPEND-ONLY — tidak ada method
update/overwrite pada baris existing, hanya insert baris baru dan baca.

SCOPE KETAT: file ini HANYA menangani tabel `narratives`.
Tidak ada predictions/master_dataset/recommendations/metadata di sini.

Tidak ada logika prompt, tidak ada panggilan Groq, tidak ada logika UI.
Murni akses data — sesuai Repository Layer Design Bagian 7.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from src.infra.supabase_client import get_service_client

logger = logging.getLogger("baliguard.repository.narrative")

TABLE_NAME = "narratives"

# Enum report_type — DIPERLUAS dari Data Contract asal (summary/alert/monthly)
# untuk mencakup tipe yang sudah nyata dipakai narasi.py: predict, swot.
# Ini Minor Change sesuai Data Contract Bagian 9 (menambah nilai enum baru
# yang tidak mengubah makna nilai existing).
VALID_REPORT_TYPES = {"summary", "alert", "monthly", "predict", "swot"}
VALID_GENERATED_BY = {"user", "scheduler"}
VALID_CRISIS_LEVELS = {"AMAN", "WASPADA", "SIAGA", "KRISIS"}

_RETRY_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_BASE_SECONDS = 1.0


@dataclass
class Result:
    """
    Return value terstruktur, selaras Repository Layer Design Bagian 6.2.
    status=True berarti operasi berhasil DIEKSEKUSI (data boleh None/kosong).
    status=False berarti operasi itu sendiri gagal (mis. koneksi putus).
    """
    status: bool
    data: Any = None
    error: Optional[str] = None


class NarrativeValidationError(Exception):
    """
    Fail-fast untuk pelanggaran kontrak data oleh PEMANGGIL
    (format salah, field wajib kosong) — bukan kegagalan operasional.
    Selaras Repository Layer Design Bagian 6.3.
    """
    pass


def _is_transient(exc: Exception) -> bool:
    """Heuristik sederhana: error jaringan/timeout/5xx dianggap transient."""
    msg = str(exc).lower()
    transient_markers = ("timeout", "connection", "503", "502", "504", "rate limit", "429")
    return any(m in msg for m in transient_markers)


def _with_retry(operation_name: str, fn, *args, **kwargs) -> Result:
    """
    Retry dengan exponential backoff HANYA untuk error transient.
    Error validasi (NarrativeValidationError) tidak pernah diulang — fail-fast.
    """
    attempt = 0
    while True:
        attempt += 1
        start = time.monotonic()
        try:
            data = fn(*args, **kwargs)
            duration = time.monotonic() - start
            logger.info(
                "narrative_repo op=%s status=success attempt=%d duration=%.3fs",
                operation_name, attempt, duration,
            )
            return Result(status=True, data=data)
        except NarrativeValidationError:
            raise  # fail-fast, tidak di-retry
        except Exception as e:
            duration = time.monotonic() - start
            if _is_transient(e) and attempt < _RETRY_MAX_ATTEMPTS:
                backoff = _RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "narrative_repo op=%s status=retry attempt=%d duration=%.3fs error=%s backoff=%.1fs",
                    operation_name, attempt, duration, e, backoff,
                )
                time.sleep(backoff)
                continue
            logger.error(
                "narrative_repo op=%s status=failed attempt=%d duration=%.3fs error=%s",
                operation_name, attempt, duration, e,
            )
            return Result(status=False, error=str(e))


class NarrativeRepository:
    """
    Repository untuk tabel `narratives`.

    Lifecycle: stateless terhadap data — instance dibuat per pemanggilan
    (per request generate di narasi.py), hanya memegang client Supabase
    yang sudah terinisialisasi (lihat src/infra/supabase_client.py).
    """

    def __init__(self, client=None):
        self._client = client or get_service_client()

    # ──────────────────────────────────────────────────────────
    # WRITE
    # ──────────────────────────────────────────────────────────
    def insert(self, month: str, report_type: str, data: dict) -> Result:
        """
        Insert satu baris narasi baru. SELALU insert, tidak pernah update
        (append-only sesuai Data Contract Bagian 3.4).

        Input:
            month: 'YYYY-MM'
            report_type: salah satu dari VALID_REPORT_TYPES
            data: dict berisi field sesuai skema narratives, minimal:
                narrative_text, crisis_level_snapshot, tokens_used,
                model_used, format_style, success, error_message,
                generated_by

        Output:
            Result[data=str]  -> id baris baru jika sukses
        """
        self._validate_month(month)
        if report_type not in VALID_REPORT_TYPES:
            raise NarrativeValidationError(
                f"report_type '{report_type}' tidak valid. "
                f"Harus salah satu dari: {sorted(VALID_REPORT_TYPES)}"
            )

        generated_by = data.get("generated_by", "user")
        if generated_by not in VALID_GENERATED_BY:
            raise NarrativeValidationError(
                f"generated_by '{generated_by}' tidak valid."
            )

        success = bool(data.get("success", True))
        narrative_text = data.get("narrative_text") or ""
        error_message = data.get("error_message")

        if success and not narrative_text.strip():
            raise NarrativeValidationError(
                "narrative_text tidak boleh kosong jika success=true."
            )
        if not success and not error_message:
            raise NarrativeValidationError(
                "error_message wajib diisi jika success=false."
            )
        if success:
            error_message = None

        crisis_level = data.get("crisis_level_snapshot")
        if crisis_level is not None and crisis_level not in VALID_CRISIS_LEVELS:
            raise NarrativeValidationError(
                f"crisis_level_snapshot '{crisis_level}' tidak valid."
            )

        payload = {
            "month": month,
            "report_type": report_type,
            "narrative_text": narrative_text,
            "crisis_level_snapshot": crisis_level,
            "tokens_used": data.get("tokens_used"),
            "model_used": data.get("model_used"),
            "format_style": data.get("format_style", "paragraf"),
            "success": success,
            "error_message": error_message,
            "generated_by": generated_by,
        }

        def _do_insert():
            res = self._client.table(TABLE_NAME).insert(payload).execute()
            rows = res.data or []
            if not rows:
                raise RuntimeError("Insert ke narratives tidak mengembalikan baris.")
            return rows[0]["id"]

        return _with_retry("insert", _do_insert)

    # ──────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────
    def get_latest(
        self,
        month: str,
        report_type: str,
        model_used: Optional[str] = None,
        format_style: Optional[str] = None,
    ) -> Result:
        """
        Ambil versi terbaru berdasarkan generated_at, untuk kombinasi
        (month, report_type) — DIPERLUAS dengan filter opsional
        model_used dan format_style untuk menjaga semantik cache_key
        existing di narasi.py (`{month}_{report_type}_{model}_{format}`),
        yang membedakan narasi per kombinasi model & format output.

        Tanpa filter ini, dua narasi format berbeda untuk bulan & tipe
        laporan yang sama akan tertukar saat ditampilkan — perilaku ini
        TIDAK boleh berubah dari JSON cache lama.

        Output: Result[data=dict|None]
        """
        self._validate_month(month)
        if report_type not in VALID_REPORT_TYPES:
            raise NarrativeValidationError(f"report_type '{report_type}' tidak valid.")

        def _do_query():
            q = (
                self._client.table(TABLE_NAME)
                .select("*")
                .eq("month", month)
                .eq("report_type", report_type)
            )
            if model_used:
                q = q.eq("model_used", model_used)
            if format_style:
                q = q.eq("format_style", format_style)
            res = q.order("generated_at", desc=True).limit(1).execute()
            rows = res.data or []
            return rows[0] if rows else None

        return _with_retry("get_latest", _do_query)

    def get_history(self, month: str, report_type: str) -> Result:
        """
        Ambil seluruh versi historis untuk satu (month, report_type),
        terurut generated_at descending.

        Output: Result[data=list[dict]]
        """
        self._validate_month(month)
        if report_type not in VALID_REPORT_TYPES:
            raise NarrativeValidationError(f"report_type '{report_type}' tidak valid.")

        def _do_query():
            res = (
                self._client.table(TABLE_NAME)
                .select("*")
                .eq("month", month)
                .eq("report_type", report_type)
                .order("generated_at", desc=True)
                .execute()
            )
            return res.data or []

        return _with_retry("get_history", _do_query)

    def get_by_id(self, narrative_id: str) -> Result:
        """Ambil satu baris spesifik by id (audit/link langsung)."""
        def _do_query():
            res = (
                self._client.table(TABLE_NAME)
                .select("*")
                .eq("id", narrative_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            return rows[0] if rows else None

        return _with_retry("get_by_id", _do_query)

    def get_all(self) -> Result:
        """
        Ambil SELURUH baris narratives. Dipakai khusus untuk migrasi
        satu-kali (backfill) dari JSON lama, BUKAN untuk dipanggil
        rutin dari Dashboard (gunakan get_latest/get_history untuk itu).

        Output: Result[data=list[dict]]
        """
        def _do_query():
            res = self._client.table(TABLE_NAME).select("*").execute()
            return res.data or []

        return _with_retry("get_all", _do_query)

    def exists(self, month: str, report_type: str, model_used: str, format_style: str) -> Result:
        """
        Cek apakah sudah ada minimal satu narasi untuk kombinasi
        (month, report_type, model_used, format_style). Dipakai pemanggil
        untuk menampilkan status 'Cache Tersedia' tanpa narik seluruh data.

        Output: Result[data=bool]
        """
        r = self.get_latest(month, report_type, model_used, format_style)
        if not r.status:
            return r
        return Result(status=True, data=r.data is not None)

    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _validate_month(month: str) -> None:
        import re
        if not re.match(r"^\d{4}-\d{2}$", month or ""):
            raise NarrativeValidationError(
                f"month '{month}' harus berformat YYYY-MM."
            )
