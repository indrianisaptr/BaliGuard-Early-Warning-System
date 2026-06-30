# BaliGuard Automation — Cara Menjalankan fetch_usd

## 1. Penempatan
Letakkan folder `automation/` ini SEJAJAR dengan `src/` di root project Anda
(bukan di dalam `src/`):

```
project_root/
├── src/            <- dashboard & services existing, TIDAK disentuh
├── automation/      <- folder baru dari paket ini
└── requirements.txt <- gabungkan isinya dengan requirements.txt project Anda
```

## 2. Install dependency
```
pip install -r requirements.txt
```
Hanya `requests` dan `PyYAML` — dependency minimal khusus automation hari ini,
tidak termasuk dependency dashboard/pipeline ML.

## 3. Jalankan job USD/IDR
Dari root project (PENTING: dijalankan sebagai module, bukan `python automation/fetch/usd_idr.py`
langsung, supaya relative import `automation.config...` jalan benar):

```
python -m automation.scheduler.run_job usd_idr
```

Atau untuk bulan tertentu (default: bulan berjalan):
```
python -m automation.scheduler.run_job usd_idr --month 2025-06
```

## 4. Cek hasil
- Staging   : `automation/data/staging/usd_idr/<month>.json`
- Log       : `automation/logs/automation.log`
- Cache fallback (hanya terisi setelah fetch live sukses minimal sekali):
  `automation/data/cache/usd_idr_last_success.json`

## 5. Exit code
- `0` = sukses, data masuk staging
- `1` = gagal (fetch gagal total ATAU validasi menolak data) — TIDAK ada yang
  masuk staging dalam kondisi gagal, sesuai prinsip "validasi sebelum masuk staging"

## 6. Catatan penting
- Script ini BERHENTI di staging. Tidak menyentuh Supabase, tidak menyentuh
  dashboard, tidak menyentuh pipeline ML — sesuai scope hari ini.
- Re-run untuk bulan yang sama akan MENIMPA file staging bulan itu saja
  (upsert-by-key), bukan menambah duplikat — sudah diuji idempotent.
- Jaringan ke `api.exchangerate-api.com` dan `api.frankfurter.app` perlu
  terbuka dari environment tempat job ini dijalankan (cron/laptop Anda).
  Saya sudah uji jalur validate→clean→staging dengan fetch yang di-stub
  (karena sandbox saya tidak punya akses ke domain tsb), dan jalur
  retry+fallback+exit-code terbukti benar saat API memang tidak terjangkau.
