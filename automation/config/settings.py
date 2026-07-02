"""
automation/config/settings.py — BaliGuard Automation: Central Settings

HANYA path & konfigurasi teknis. TIDAK ADA logic bisnis di sini.
"""
import os
from pathlib import Path

# ── Path dasar ───────────────────────────────────────────────
AUTOMATION_ROOT = Path(__file__).resolve().parent.parent  # .../automation
STAGING_ROOT     = AUTOMATION_ROOT / "data" / "staging"
LOGS_ROOT         = AUTOMATION_ROOT / "logs"
CACHE_ROOT         = AUTOMATION_ROOT / "data" / "cache"     # fallback offline terakhir

# ── Retry policy (dipakai semua fetch/*, bukan hardcode per source) ──
RETRY_MAX_ATTEMPTS         = int(os.getenv("AUTOMATION_RETRY_MAX_ATTEMPTS", 3))
RETRY_BACKOFF_BASE_SECONDS = float(os.getenv("AUTOMATION_RETRY_BACKOFF_BASE_SECONDS", 1.5))
HTTP_TIMEOUT_SECONDS       = float(os.getenv("AUTOMATION_HTTP_TIMEOUT_SECONDS", 10.0))

# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL = os.getenv("AUTOMATION_LOG_LEVEL", "INFO")
LOG_FILE  = LOGS_ROOT / "automation.log"


def ensure_dirs() -> None:
    """Pastikan folder data/staging, data/cache, logs ada sebelum job jalan."""
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
