"""
automation/storage/staging_writer.py — BaliGuard Automation: Staging Writer

Interface TUNGGAL untuk menulis ke staging. Fase 1: file-backed (JSON per key).
Fase nanti (Supabase): hanya isi fungsi ini yang berubah — caller (fetch/process)
TIDAK PERNAH berubah, sesuai prinsip Automation Architecture Bagian 9 Fase 3.

Pola: satu file per (source, key) — bukan satu file besar yang ditimpa.
Ini meniru semantik "upsert by key" walau backend-nya masih file biasa.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from automation.config.settings import STAGING_ROOT

logger = logging.getLogger("automation.storage.staging_writer")


def _staging_path(source: str, key: str) -> Path:
    source_dir = STAGING_ROOT / source
    source_dir.mkdir(parents=True, exist_ok=True)
    safe_key = key.replace("/", "_")
    return source_dir / f"{safe_key}.json"


def write_staging(source: str, key: str, record: dict) -> Path:
    """
    Tulis satu record ke staging dengan semantik upsert-by-key:
    file dengan nama `key` akan DITIMPA (bukan di-append) jika sudah ada
    — re-run fetch untuk key yang sama tidak menggandakan data (idempotent),
    sesuai checklist Automation Architecture Bagian 10.

    Input:
        source: nama source, mis. 'usd_idr'
        key:    key logis record, mis. month 'YYYY-MM'
        record: dict yang sudah lolos validasi & cleaning
    Output:
        Path file staging yang ditulis
    """
    path = _staging_path(source, key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    logger.info("staging_write source=%s key=%s path=%s", source, key, path)
    return path


def read_staging(source: str, key: str) -> Optional[dict]:
    """Baca satu record staging by key. Return None jika belum ada."""
    path = _staging_path(source, key)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_staging_keys(source: str) -> list:
    """Daftar seluruh key yang sudah tersimpan di staging untuk satu source."""
    source_dir = STAGING_ROOT / source
    if not source_dir.exists():
        return []
    return sorted(p.stem for p in source_dir.glob("*.json"))
