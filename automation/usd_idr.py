"""
automation/fetch/usd_idr.py — BaliGuard Automation: Fetch USD/IDR

Bertugas HANYA bicara ke API eksternal dan mengembalikan data mentah
terstruktur. TIDAK ADA validasi atau cleaning di sini (itu di
process/validate_usd_idr.py) — sesuai pemisahan tanggung jawab
fetch/ vs process/ di Automation Architecture.

Fallback chain (dipertahankan dari pola handout lama):
  1. ExchangeRate-API (live/current rate)
  2. Frankfurter API (rate historis, jika API #1 gagal)
  3. Cache lokal hasil fetch sukses terakhir (jika kedua API gagal)
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from automation.config.settings import (
    CACHE_ROOT,
    HTTP_TIMEOUT_SECONDS,
    RETRY_BACKOFF_BASE_SECONDS,
    RETRY_MAX_ATTEMPTS,
)

logger = logging.getLogger("automation.fetch.usd_idr")

EXCHANGERATE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
FRANKFURTER_API_URL  = "https://api.frankfurter.app/latest"
CACHE_FILE            = CACHE_ROOT / "usd_idr_last_success.json"


class FetchError(Exception):
    """Dilempar saat SELURUH fallback chain gagal."""
    pass


def _http_get_with_retry(url: str, params: Optional[dict] = None) -> dict:
    """Retry dengan exponential backoff untuk satu endpoint, hanya untuk
    error transient (timeout/koneksi/5xx). Error 4xx tidak di-retry."""
    last_exc = None
    for attempt in range(1, RETRY_MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            if resp.status_code >= 500:
                raise requests.HTTPError(f"{url} -> HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            last_exc = e
            is_5xx_or_transient = True
            if isinstance(e, requests.HTTPError) and "HTTP" in str(e):
                pass  # sudah dianggap transient di atas (status >= 500)
            if attempt < RETRY_MAX_ATTEMPTS and is_5xx_or_transient:
                backoff = RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "fetch_retry url=%s attempt=%d error=%s backoff=%.1fs",
                    url, attempt, e, backoff,
                )
                time.sleep(backoff)
                continue
            raise
    raise last_exc  # pragma: no cover (selalu raise di loop terakhir)


def _try_exchangerate_api() -> Optional[float]:
    try:
        data = _http_get_with_retry(EXCHANGERATE_API_URL)
        rate = data.get("rates", {}).get("IDR")
        if rate is None:
            raise FetchError("ExchangeRate-API: key 'IDR' tidak ditemukan di response")
        return float(rate)
    except Exception as e:
        logger.warning("source=exchangerate-api status=failed error=%s", e)
        return None


def _try_frankfurter() -> Optional[float]:
    try:
        data = _http_get_with_retry(FRANKFURTER_API_URL, params={"from": "USD", "to": "IDR"})
        rate = data.get("rates", {}).get("IDR")
        if rate is None:
            raise FetchError("Frankfurter: key 'IDR' tidak ditemukan di response")
        return float(rate)
    except Exception as e:
        logger.warning("source=frankfurter status=failed error=%s", e)
        return None


def _try_cache() -> Optional[float]:
    if not CACHE_FILE.exists():
        logger.warning("source=cache status=failed error=no_cache_file")
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        rate = cached.get("usd_idr_avg")
        if rate is None:
            return None
        logger.warning(
            "source=cache status=used cached_at=%s (DATA BUKAN LIVE, ini fallback terakhir)",
            cached.get("fetched_at"),
        )
        return float(rate)
    except Exception as e:
        logger.warning("source=cache status=failed error=%s", e)
        return None


def _save_cache(rate: float, source: str, fetched_at: str) -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"usd_idr_avg": rate, "usd_idr_source": source, "fetched_at": fetched_at},
            f, ensure_ascii=False, indent=2,
        )


def fetch_usd_idr_latest(target_month: Optional[str] = None) -> dict:
    """
    Ambil rate USD/IDR terbaru lewat fallback chain.

    Input:
        target_month: 'YYYY-MM', default bulan berjalan (UTC) jika None.
                       Fungsi ini TIDAK mengambil histori penuh — hanya
                       titik data "terbaru" untuk bulan target, sesuai
                       pola incremental update di handout lama.

    Output: dict mentah (BELUM divalidasi/dibersihkan):
        {
            'month': 'YYYY-MM',
            'usd_idr_avg': float,
            'usd_idr_source': 'exchangerate-api' | 'frankfurter' | 'cache',
            'fetched_at': ISO8601 timestamp UTC,
        }

    Raises:
        FetchError jika SELURUH fallback chain (API #1, API #2, cache) gagal.
    """
    now = datetime.now(timezone.utc)
    month = target_month or now.strftime("%Y-%m")
    fetched_at = now.isoformat()

    rate = _try_exchangerate_api()
    source = "exchangerate-api"

    if rate is None:
        rate = _try_frankfurter()
        source = "frankfurter"

    if rate is None:
        rate = _try_cache()
        source = "cache"

    if rate is None:
        raise FetchError(
            "Seluruh fallback chain USD/IDR gagal: ExchangeRate-API, "
            "Frankfurter, dan cache lokal semuanya tidak tersedia."
        )

    if source != "cache":
        _save_cache(rate, source, fetched_at)

    record = {
        "month": month,
        "usd_idr_avg": rate,
        "usd_idr_source": source,
        "fetched_at": fetched_at,
    }
    logger.info("fetch_usd_idr_latest result=%s", record)
    return record
