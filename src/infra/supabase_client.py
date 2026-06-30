"""
src/infra/supabase_client.py — BaliGuard: Supabase Connection

Satu-satunya tempat yang membuat client Supabase untuk Repository Layer.
Tidak ada komponen lain (Dashboard page, llm_service, dsb.) yang boleh
membuat koneksi Supabase secara langsung — sesuai Repository Layer Design
Bagian 1: "Repository Layer adalah satu-satunya komponen yang boleh
berbicara langsung ke Supabase."

TIDAK ada logika bisnis di sini. Hanya inisialisasi client.
"""
import os
from functools import lru_cache

try:
    from supabase import create_client, Client
except ImportError as e:
    raise ImportError(
        "Package 'supabase' belum terpasang. Jalankan: pip install supabase"
    ) from e


class SupabaseConfigError(Exception):
    """Dilempar saat environment variable wajib tidak tersedia."""
    pass


@lru_cache(maxsize=2)
def _build_client(url: str, key: str) -> "Client":
    return create_client(url, key)


def get_service_client() -> "Client":
    """
    Client dengan SERVICE_ROLE_KEY (bypass RLS).
    HANYA dipakai oleh Repository Layer di sisi server (Narrative Service,
    ML Pipeline). TIDAK PERNAH dipakai dari proses client-side/browser.

    Untuk migrasi tahap ini, NarrativeRepository memakai client ini karena
    operasi insert/read dilakukan dari proses server-side Streamlit
    (narasi.py dijalankan di server Streamlit, bukan di browser).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY wajib diset di "
            "environment variable / st.secrets sebelum repository dipakai."
        )
    return _build_client(url, key)


def get_anon_client() -> "Client":
    """
    Client dengan ANON_KEY (tunduk RLS, read-only sesuai policy).
    Disediakan untuk konsistensi dengan SAD/Repository Design, meski pada
    migrasi tahap ini NarrativeRepository memakai service client (lihat
    docstring get_service_client). Dipertahankan agar Dashboard di masa
    depan bisa pindah ke anon key tanpa mengubah modul ini.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL dan SUPABASE_ANON_KEY wajib diset di "
            "environment variable / st.secrets."
        )
    return _build_client(url, key)
