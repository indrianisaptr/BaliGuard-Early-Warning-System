"""
scripts/migrate_narratives_cache_to_supabase.py — BaliGuard

Script SATU KALI (one-time) untuk backfill isi
data/final/narratives_cache.json ke tabel Supabase `narratives`.

TIDAK menyentuh tabel lain. TIDAK mengubah narasi.py / llm_service.py.
Jalankan manual, di luar proses Streamlit:

    python scripts/migrate_narratives_cache_to_supabase.py [--dry-run]

Perilaku:
- Membaca narratives_cache.json apa adanya, TERMASUK menjalankan logika
  migrasi key lama yang sebelumnya hidup di narasi.py (baris 224-239),
  supaya key lama (tanpa report_type/format) tetap bisa dipetakan benar.
- Setiap entry di-insert sebagai SATU baris baru ke tabel narratives
  (insert-only, sesuai semantik append-only — bukan upsert).
- --dry-run: print apa yang AKAN di-insert tanpa benar-benar menulis ke
  Supabase. Disarankan dijalankan dry-run dulu sebelum run sungguhan.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.getcwd())  # agar `src.*` bisa diimport saat dijalankan dari root project

from src.repositories.narrative_repository import NarrativeRepository, VALID_REPORT_TYPES

CACHE_PATH = "data/final/narratives_cache.json"
_FORMAT_KEYS = ("paragraf", "poin")


def _load_and_normalize_cache(path: str) -> dict:
    """
    Replika PERSIS dari logika migrasi key lama yang ada di narasi.py
    (baris 224-239), supaya backfill konsisten dengan apa yang selama ini
    ditampilkan dashboard dari file JSON.
    """
    if not os.path.exists(path):
        print(f"[WARN] File cache tidak ditemukan: {path}. Tidak ada yang dimigrasikan.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    normalized = {}
    for k, v in raw.items():
        key_final = k
        if "_" not in k[4:]:
            rt = v.get("report_type", "alert")
            key_final = f"{k}_{rt}"
        if not key_final.endswith(_FORMAT_KEYS):
            fmt = v.get("format", "paragraf")
            v["format"] = fmt
            key_final = f"{key_final}_{fmt}"
        else:
            v.setdefault("format", key_final.rsplit("_", 1)[-1])
        normalized[key_final] = v

    return normalized


def _parse_cache_key(key: str, entry: dict) -> dict:
    """
    Cache key existing: '{month}_{report_type}_{model}_{format}'
    Karena bagian month/model bisa mengandung underscore, sumber paling
    aman untuk report_type/format/model adalah field DI DALAM entry itu
    sendiri (entry['month'], entry['report_type'], entry['format']),
    bukan parsing string key — entry JSON sudah menyimpan field ini.
    """
    month = entry.get("month")
    report_type = entry.get("report_type")
    format_style = entry.get("format", "paragraf")

    if not month or not report_type:
        raise ValueError(
            f"Entry untuk key '{key}' tidak punya field 'month'/'report_type' "
            f"yang valid — entry ini di-skip, perlu dicek manual."
        )
    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(
            f"Entry '{key}' punya report_type '{report_type}' di luar "
            f"VALID_REPORT_TYPES — entry ini di-skip, perlu dicek manual."
        )

    # model_used tidak tersimpan eksplisit di entry lama (hanya ada di cache
    # key, bukan di value) pada beberapa versi cache. Ambil dari field
    # 'model' jika ada; jika tidak ada, set None — kolom model_used nullable.
    model_used = entry.get("model")

    return {
        "month": month,
        "report_type": report_type,
        "data": {
            "narrative_text": entry.get("narrative", ""),
            "crisis_level_snapshot": entry.get("crisis_level"),
            "tokens_used": entry.get("tokens"),
            "model_used": model_used,
            "format_style": format_style,
            "success": True,
            "error_message": None,
            "generated_by": "user",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Tampilkan rencana insert tanpa menulis ke Supabase")
    args = parser.parse_args()

    cache = _load_and_normalize_cache(CACHE_PATH)
    print(f"[INFO] Total entry ditemukan di cache: {len(cache)}")

    if not cache:
        print("[INFO] Tidak ada yang perlu dimigrasikan.")
        return

    repo = None if args.dry_run else NarrativeRepository()

    success_count = 0
    skipped = []

    for key, entry in cache.items():
        try:
            parsed = _parse_cache_key(key, entry)
        except ValueError as e:
            print(f"[SKIP] {e}")
            skipped.append(key)
            continue

        if args.dry_run:
            print(f"[DRY-RUN] Akan insert: month={parsed['month']} "
                  f"report_type={parsed['report_type']} "
                  f"model={parsed['data']['model_used']} "
                  f"format={parsed['data']['format_style']} "
                  f"tokens={parsed['data']['tokens_used']}")
            success_count += 1
            continue

        result = repo.insert(parsed["month"], parsed["report_type"], parsed["data"])
        if result.status:
            print(f"[OK] key='{key}' -> narrative id={result.data}")
            success_count += 1
        else:
            print(f"[FAIL] key='{key}' error={result.error}")
            skipped.append(key)

    print("\n=== RINGKASAN ===")
    print(f"Berhasil  : {success_count}")
    print(f"Gagal/skip: {len(skipped)}")
    if skipped:
        print("Key yang gagal/skip:")
        for k in skipped:
            print(f"  - {k}")


if __name__ == "__main__":
    main()
