# BaliGuard — Migrasi narratives_cache.json → Supabase `narratives`

Implementasi bertahap. Scope: HANYA tabel `narratives`. Tidak ada tabel lain,
tidak ada perubahan UI, tidak ada perubahan prompt builder.

## Isi paket ini

```
src/infra/supabase_client.py              -> koneksi Supabase (dipakai repository saja)
src/repositories/narrative_repository.py  -> NarrativeRepository (insert, get_latest, get_history, get_by_id, get_all, exists)
scripts/migrate_narratives_cache_to_supabase.py -> backfill satu-kali dari JSON lama
patches/narasi.py                         -> narasi.py yang SUDAH dipatch (3 titik storage saja)
```

`llm_service.py` TIDAK disertakan sebagai file terpisah karena audit awal
menemukan ia tidak pernah membaca/menulis JSON sama sekali — tidak ada yang
perlu diubah di file itu untuk migrasi storage ini.

## Tahapan implementasi (jalankan berurutan)

### Tahap 1 — Provisioning Supabase (manual, di luar scope kode ini)
- Buat tabel `narratives` sesuai Data Contract + 2 kolom tambahan minor:
  - `format_style` (text, nullable, default 'paragraf')
  - enum `report_type` diperluas: tambah nilai `predict`, `swot`
- Set environment variable: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  (lihat Supabase Implementation Spec Bagian 5).

### Tahap 2 — Pasang dependency & file repository
1. `pip install supabase`
2. Copy `src/infra/supabase_client.py` ke project Anda di path yang sama.
3. Copy `src/repositories/narrative_repository.py` ke project Anda di path yang sama.
4. Pastikan `src/infra/__init__.py` dan `src/repositories/__init__.py` ada
   (boleh kosong) agar import `from src.repositories.narrative_repository import ...` jalan.

### Tahap 3 — Backfill data lama (one-time, dry-run dulu)
```
python scripts/migrate_narratives_cache_to_supabase.py --dry-run
```
Periksa output — pastikan jumlah entry & isi sudah sesuai ekspektasi.
Jika sudah yakin, jalankan sungguhan:
```
python scripts/migrate_narratives_cache_to_supabase.py
```
JANGAN hapus `data/final/narratives_cache.json` dulu — simpan sebagai arsip
sampai Tahap 5 dikonfirmasi stabil.

### Tahap 4 — Terapkan patch ke narasi.py
File `patches/narasi.py` adalah versi narasi.py Anda yang SUDAH dipatch di
3 titik (import, load cache, save setelah generate). Bandingkan dengan
narasi.py Anda saat ini menggunakan diff tool, lalu terapkan — JANGAN
langsung overwrite file Anda kalau ada perubahan lain di antara waktu audit
dan sekarang (selalu diff dulu).

Tiga titik yang berubah:
1. Tambah `from src.repositories.narrative_repository import NarrativeRepository`
2. Blok load awal `render()`: baca dari `NarrativeRepository.get_all()`,
   bukan `json.load()` — bentuk dict `narratives_cache` di session_state
   TETAP SAMA PERSIS, jadi seluruh kode UI di bawahnya tidak perlu disentuh.
3. Blok setelah generate sukses: `NarrativeRepository.insert(...)`,
   bukan `json.dump()` ke file.

Tidak ada baris lain di narasi.py yang berubah.

### Tahap 5 — Uji paralel
- Jalankan dashboard, generate narasi baru → cek muncul di tabel Supabase.
- Refresh halaman → cek narasi lama (hasil backfill) tetap muncul dengan benar.
- Uji fitur Komparasi Antar Periode → pastikan kedua sisi (A & B) tetap
  terbaca benar dari cache yang sudah dimuat dari Supabase.

### Tahap 6 — Cutover
Setelah stabil beberapa hari pemakaian normal, `data/final/narratives_cache.json`
bisa dipindah ke folder arsip (bukan dihapus) sebagai jaring pengaman audit.

## Hal yang SENGAJA tidak diubah
- Seluruh prompt builder di llm_service.py — tidak disentuh.
- Seluruh tampilan HTML/CSS narasi di narasi.py — tidak disentuh.
- Logika tombol Copy/Download, Komparasi Antar Periode — tidak disentuh.
- Tabel master_dataset, predictions, recommendations, metadata — tidak disentuh sama sekali.
