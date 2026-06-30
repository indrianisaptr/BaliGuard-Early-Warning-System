"""
automation/scheduler/run_job.py — BaliGuard Automation: Job Runner (CLI)

Entrypoint untuk menjalankan SATU job secara independen — bisa dipanggil
manual, cron, atau scheduler lain nanti. Hari ini hanya job 'usd_idr'
yang terdaftar.

Cara pakai:
    python -m automation.scheduler.run_job usd_idr
    python -m automation.scheduler.run_job usd_idr --month 2025-06
"""
from __future__ import annotations

import argparse
import logging
import sys

from automation.config.settings import LOG_FILE, LOG_LEVEL, ensure_dirs
from automation.fetch.usd_idr import FetchError, fetch_usd_idr_latest
from automation.process.validate_usd_idr import clean_usd_record, validate_usd_record
from automation.storage.staging_writer import write_staging

logger = logging.getLogger("automation.scheduler.run_job")


def _setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_usd_idr(target_month: str = None) -> int:
    """
    Jalankan satu siklus job usd_idr: fetch -> validate -> clean -> staging.
    Return: exit code (0 = sukses, 1 = gagal)
    """
    logger.info("[1/4] Fetch USD/IDR mulai (target_month=%s)", target_month or "current")
    try:
        raw_record = fetch_usd_idr_latest(target_month)
    except FetchError as e:
        logger.error("[1/4] Fetch GAGAL TOTAL: %s", e)
        return 1
    logger.info("[1/4] Fetch selesai: %s", raw_record)

    logger.info("[2/4] Validasi mulai")
    result = validate_usd_record(raw_record)
    if not result.is_valid:
        logger.error("[2/4] Validasi GAGAL: %s", result.errors)
        logger.error("[2/4] Record DITOLAK, TIDAK disimpan ke staging.")
        return 1
    logger.info("[2/4] Validasi lolos")

    logger.info("[3/4] Cleaning ringan mulai")
    cleaned_record = clean_usd_record(raw_record)
    logger.info("[3/4] Cleaning selesai: %s", cleaned_record)

    logger.info("[4/4] Simpan ke staging mulai")
    path = write_staging(source="usd_idr", key=cleaned_record["month"], record=cleaned_record)
    logger.info("[4/4] Tersimpan di: %s", path)

    logger.info("Job usd_idr SELESAI sukses untuk month=%s", cleaned_record["month"])
    return 0


JOBS = {
    "usd_idr": run_usd_idr,
}


def main() -> None:
    _setup_logging()

    parser = argparse.ArgumentParser(description="BaliGuard Automation — Job Runner")
    parser.add_argument("job", choices=sorted(JOBS.keys()), help="Nama job yang dijalankan")
    parser.add_argument("--month", default=None, help="Target bulan YYYY-MM (default: bulan berjalan)")
    args = parser.parse_args()

    job_fn = JOBS[args.job]
    exit_code = job_fn(target_month=args.month)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
