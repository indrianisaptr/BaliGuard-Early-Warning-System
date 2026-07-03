# Dokumentasi Teknis — BaliGuard Dashboard (`src/`)
> Dokumentasi handoff developer. Dibuat dari pembacaan langsung source code di `src/`.
> File `dashboard.py` (entry point utama) tidak ada dalam paket yang diupload — dokumentasi ini fokus pada isi `src/` saja.
> **v2** — update setelah perubahan pada `narasi.py` dan `llm_service.py` (lihat changelog di akhir dokumen).

---

## Gambaran Umum Project

BaliGuard adalah dashboard Streamlit untuk memantau kondisi pariwisata Bali (early warning system). Dashboard membaca output pipeline (NB01–NB06): CSV/Parquet hasil olahan, model ML (`.pkl`), cache narasi LLM (`.json`).

Alur singkat:
1. Data & model di-load sekali, di-cache (`st.cache_data`/`st.cache_resource`).
2. Pengguna pilih bulan/tahun di sidebar (historis atau proyeksi s/d 24 bulan ke depan).
3. `src/shared.py` membangun satu dict `ctx` berisi semua KPI, delta MoM, forecast untuk bulan terpilih.
4. 5 halaman (`pages/*.py`) menerima `ctx` dan merender chart Plotly + HTML.
5. Halaman **Narasi AI**: generate laporan otomatis (summary/alert/monthly/predict/SWOT) via Groq LLM, dengan pilihan format paragraf/poin, plus mode komparasi dua periode.
6. Halaman **Prediksi & Proyeksi**: simulator skenario risiko (what-if) tanpa panggil model ulang.

Konstanta global (path, threshold, warna, bobot) terpusat di `src/config.py`.

---

## Struktur Folder

```
src/
├── __init__.py                # Kosong
├── config.py                  # Konstanta global
├── shared.py                  # Pembangun ctx dict
├── sidebar.py                 # Navigasi & pemilih periode
├── utils.py                   # Helper umum, load data/model, label awam
├── narrative_engine.py        # Modul LLM lama — TIDAK DIPAKAI (lihat catatan)
├── components/
│   ├── cards.py                # KPI card, alert card, dll.
│   └── badges.py                # Status dot, level badge, trend badge
├── services/
│   ├── forecast.py              # Proyeksi & forecast n-bulan
│   ├── simulation.py            # Simulator skenario risiko
│   └── llm_service.py           # Prompt builder LLM (tanpa Streamlit)
└── pages/
    ├── overview.py               # "Gambaran Umum & Garis Waktu"
    ├── analisis.py                # "Analisis Detail"
    ├── sentimen.py                 # "Sentimen"
    ├── prediksi.py                 # "Prediksi & Proyeksi"
    └── narasi.py                   # "Narasi AI"
```

Diasumsikan ada di root project (tidak termasuk paket ini): `data/final/`, `models/`, `assets/icons/`.

---

## Alur Eksekusi Project

1. Entry point (asumsi `dashboard.py`) memanggil `utils.load_data()` + `utils.load_models()`.
2. `sidebar.render_sidebar(ctx)` → user pilih bulan, navigasi → return `(selected_nav, sel)`.
3. `shared.build_context(...)` → bangun `ctx` untuk bulan `sel`.
4. Routing ke `pages/{selected_nav}.render(ctx)`.
5. Di halaman Prediksi: slider simulasi → `services.simulation.simulate_score()` (lokal, real-time, tanpa API/model call).
6. Di halaman Narasi AI: tombol Generate → `llm_service.build_ctx()` + `build_prompt()` → panggil Groq API langsung → bersihkan output → simpan ke `narratives_cache.json`.
7. Mode komparasi (Narasi AI): **tidak lagi memanggil API** — membaca cache narasi yang sudah ada untuk dua bulan terpilih (lihat changelog).

---

## Hubungan Antar File

- `config.py` → sumber konstanta untuk hampir semua file lain.
- `utils.py` → impor `config.py` + `components/cards.py` + `components/badges.py`. Dipakai semua halaman.
- `shared.py` → jembatan utama: pakai `utils.py` + `services/forecast.py`, hasilnya (`ctx`) dikonsumsi semua `pages/*.py`.
- `sidebar.py` → pakai `config.COLOR_MAP`, return `sel` yang jadi input `shared.build_context()`.
- `services/forecast.py` → dipakai `shared.py`, `pages/prediksi.py`, `pages/narasi.py`.
- `services/simulation.py` → hanya dipakai `pages/prediksi.py`.
- `services/llm_service.py` → satu-satunya tempat logika prompt. Dipakai `pages/narasi.py`.
- `components/cards.py` → impor `components/badges.py`.
- `narrative_engine.py` (root `src/`) → **tidak diimpor file manapun** (terkonfirmasi via grep). Tumpang tindih fungsi dengan `services/llm_service.py`.

**Aliran data**: `data/final/*` + `models/*.pkl` → `utils.load_data()`/`load_models()` → `shared.build_context()` → `ctx` → `pages/*.render(ctx)` → output visual. Untuk Narasi AI: `ctx`/`row_data` → `llm_service.build_ctx()` → `build_prompt()` → Groq API → `narasi.py` bersihkan & tampilkan → tulis ke `narratives_cache.json`.

---

## Dokumentasi Per File

### `src/config.py`

**Tujuan**: Satu-satunya sumber konfigurasi statis: path, threshold level krisis, warna per level, daftar fitur model, bobot crisis score, parameter hyperparameter ML, config LLM, styling chart. Tidak ada logika/import Streamlit.

**Fungsi**: Konstanta global yang diimpor hampir semua modul.

**Proses**: Mendefinisikan `THRESHOLD`, `COLOR_MAP`/`BG_MAP`/`LEVEL_DESC`, `FEATURES_CORE`/`FEATURES_LAG`, `WEIGHT_TOURISM/ECONOMY/SENTIMENT`, `RF_PARAMS`/`ISO_PARAMS`, `GROQ_MODEL`/`GROQ_ENDPOINT`, styling Plotly default.

**Dependensi**: `pathlib` saja.

**Catatan**:
- `WEIGHT_TOURISM=0.75/ECONOMY=0.20/SENTIMENT=0.05` di file ini **berbeda** dari formula resmi pipeline (tourism 0.45/economy 0.25/external 0.20/sentiment 0.10) dan dari yang dipakai aktual di `services/simulation.py` & `pages/analisis.py`. Konstanta ini **tidak dipakai file manapun** di paket ini — kemungkinan sisa skrip retrain yang tidak diikutkan.
- `ISO_PARAMS['contamination']=0.05` berbeda dari nilai pipeline (0.15) — tidak berdampak karena model sudah pre-trained, dipanggil dari `.pkl`.
- Komentar di `COLOR_MAP` menyebut harus sinkron manual dengan CSS dashboard utama (di luar paket ini) — tidak ada validasi otomatis.

**Ringkasan**: Pusat konfigurasi, tapi ada konstanta bobot/parameter yang tidak konsisten dengan formula resmi & tidak dipakai di kode dashboard manapun.

---

### `src/shared.py`

**Tujuan**: Membangun satu dict `ctx` (sekali per rerun) yang jadi sumber data tunggal untuk semua halaman — menghindari duplikasi logika KPI/delta/forecast di tiap halaman.

**Input**: `predictions`, `master`, `narratives_cache`, model (`rf_model`, `iso_model`, `scaler`, `le`), `sel`, `logo_html`, `nav_icons`.

**Proses**:
- Tentukan `last_data_month`, `is_projection`.
- Ambil `row_data` (proyeksi via `forecast.project_future_row()`, historis langsung dari `predictions`).
- Isi KPI utama + 4 indikator risiko eksternal (via `sf()`).
- Kurs via `utils.get_current_usd_idr()`.
- Delta MoM via `utils.compute_delta_context()` (try/except).
- Forecast 6 bulan via `forecast.forecast_months()` (try/except).
- Hitung `recovery_pct`, `score_delta`/`score_trend`, `dominant_factor`, `precovid_mean`, `anomaly_exp`.

**Output**: Dict `ctx` (~30 key), tidak menulis file.

**Dependensi**: `numpy`, `pandas`; internal `src.utils`, `src.services.forecast`, `src.config`.

**Catatan**:
- `dominant_factor` di sini menduplikasi logika serupa di `narrative_engine.py` (tidak terpakai) — bukan masalah aktif karena `llm_service.py` punya pendekatan sendiri.
- `level_from_score` diimpor tapi tidak terpakai di body (dead import) — level diambil langsung dari kolom `crisis_level`.

**Ringkasan**: Inti logika dashboard — satu fungsi yang menyatukan data, model, dan kalkulasi turunan untuk dikonsumsi 5 halaman.

---

### `src/sidebar.py`

**Tujuan**: Render sidebar — logo, pemilih Tahun/Bulan (termasuk proyeksi), 5 tombol navigasi, panel status bulan terpilih, info statis sumber data/model.

**Fungsi**: `render_sidebar(ctx) -> (selected_nav, sel)`.

**Proses**:
1. Bangun daftar bulan (historis + 24 bulan proyeksi).
2. Render logo, dropdown Tahun/Bulan (label Indonesia, tanda `[PROYEKSI]`).
3. Render 5 tombol nav (ikon PNG base64 atau fallback SVG); klik → ubah `session_state.selected_nav` + rerun.
4. Render panel status (level, score, anomali) untuk bulan terpilih.
5. Render info statis (sumber data, model, AI/analytics).

**Dependensi**: `streamlit`, `pandas`; internal `src.config.COLOR_MAP`.

**Catatan**:
- File punya **dua blok `NAV_OPTIONS`** (blok pertama label panjang "Gambaran Umum & Garis Waktu" dst, ditimpa blok kedua dengan label pendek "Overview & Timeline" dst). Yang dipakai aktual = definisi terakhir. Tidak bug, tapi sisa refactor yang belum dibersihkan.
- Ikon nav dimuat dua kali (sekali via `ctx['nav_icons']` yang sudah di-cache, sekali lagi via cache lokal tidak ter-cache di `render_sidebar()`) — `nav_icons` diprioritaskan, jadi inefisiensi minor saja.

**Ringkasan**: Kontrol navigasi & pemilihan periode. Fungsional, tapi ada kode duplikat (`NAV_OPTIONS` ganda) yang sebaiknya dibersihkan.

---

### `src/utils.py`

**Tujuan**: Toolbox inti dashboard — loading data/model dengan cache, `sf()`, klasifikasi level, kurs live/historis, delta MoM, plus 3 komponen "humanisasi" data: `LABEL_MANUSIAWI` (label kolom teknis → bahasa awam), `REKOMENDASI_LEVEL` (rekomendasi tindakan per level), `interpretasi_indikator()` (nilai → kalimat interpretasi).

**Proses**:
- `LABEL_MANUSIAWI`: dict ~50 kolom → label awam, dipakai dengan fallback `.get(col, col)`.
- `REKOMENDASI_LEVEL`: dict 4 level → list rekomendasi tindakan.
- `interpretasi_indikator(kolom, nilai)`: rangkaian `if/elif` per kolom → kalimat interpretatif berbasis threshold.
- `is_current_month()`, `format_usd_source_label()`: helper label sumber kurs.
- `sf()`, `level_from_score()`: helper numerik dasar.
- `load_data()`, `load_models()`, `load_nav_icons()`: loader ter-cache.
- `fetch_live_usd_idr()`: fetch 2 API kurs eksternal (cache 1 jam).
- `get_current_usd_idr()`: keputusan live vs historis berdasarkan posisi bulan terhadap kalender sekarang.
- `compute_delta_context()`: delta & delta% 7 KPI vs bulan sebelumnya (cache).

**Dependensi**: `streamlit`, `pandas`, `numpy`, `requests`; internal `src.config`, `src.components.cards`, `src.components.badges`.

**Catatan**:
- `get_current_usd_idr()`: bulan lebih lama dari kalender sekarang → selalu historis, tidak pernah live. Bulan berjalan/proyeksi → coba live dulu, fallback historis.
- `_t_start`/`_t`/`_tick()`: utilitas profiling yang dipanggil di tiap halaman (`_tick("nav_start_xxx")`), tapi **tidak ada kode yang membaca isi `_t`** di paket ini — kemungkinan debug manual yang belum terhubung ke UI.
- `BASE_DIR`/`DATA_DIR`/`MODEL_DIR` didefinisikan ulang di file ini meski sudah diimpor dari `config.py` — hasil sama (formula identik), tapi duplikasi kode yang tidak perlu.
- `fetch_live_usd_idr()` menelan semua exception per provider tanpa log — kalau API down, `get_current_usd_idr()` fallback ke historis (UI aman), tapi tidak ada diagnostik.

**Ringkasan**: Modul paling sentral — loading data/model + lapisan "humanisasi" data teknis (label awam, interpretasi kalimat, rekomendasi tindakan).

---

### `src/components/cards.py`

**Tujuan**: Komponen HTML reusable — KPI card, alert card, header seksi, dll.

**Proses**: `kpi_card()`, `alert_card()`, `status_summary_card()` → return string HTML. `section_header()`, `metric_row()`, `info_box()`, `divider_line()` → render langsung ke `st`.

**Dependensi**: `streamlit`; internal `src.components.badges`.

**Catatan**:
- Inkonsistensi pola return: sebagian return string, sebagian render langsung — pemanggil harus ingat mana yang mana.
- `status_summary_card()` dan `metric_row()` tidak dipanggil di halaman manapun dalam paket ini.

**Ringkasan**: Pustaka komponen KPI/alert; beberapa fungsi tampak tidak terpakai aktif.

---

### `src/components/badges.py`

**Tujuan**: Komponen badge kecil — status dot, level pill, trend badge, confidence bar, anomaly badge.

**Proses**: 5 fungsi, semua return string HTML, warna berbasis `config.COLOR_MAP`/`BG_MAP`.

**Dependensi**: Internal saja (`src.config`). Tidak ada dependensi Streamlit.

**Catatan**:
- `TREND_ICONS` didefinisikan tapi tidak dipakai (`trend_badge()` hardcode ikon sendiri) — sisa refactor.
- `level_badge()`, `confidence_bar()`, `anomaly_badge()` tidak dipanggil langsung di halaman manapun dalam paket ini.

**Ringkasan**: Lapisan komponen paling dasar, murni presentasional, fondasi untuk `cards.py`.

---

### `src/services/forecast.py`

**Tujuan**: Logika proyeksi/forecast — satu baris (`project_future_row`) atau n-bulan ke depan (`forecast_months`), plus helper arah tren.

**Proses**:
- `project_future_row()`: fit linear (`np.polyfit`) per kolom numerik dari 6 baris terakhir, ekstrapolasi 1 titik ke depan. `crisis_level` dihitung ulang via `level_from_score()` lokal.
- `forecast_months()`: tren linear dari 12 bulan terakhir, proyeksi n-bulan dari `from_month`. Bulan yang sudah ada di data historis → pakai data asli, bukan hasil ekstrapolasi. Confidence menurun linear seiring jarak (`85 - (i-1)*10`, min 35).
- `compute_trend_direction()`: tidak dipanggil di halaman manapun pada paket ini.

**Dependensi**: `streamlit` (cache), `pandas`, `numpy`, `dateutil.relativedelta` (impor tidak terpakai); internal `src.config`, `src.utils.sf`.

**Catatan**:
- `level_from_score()` didefinisikan ulang lokal (bukan impor dari `utils.py` — baris impornya di-comment-out). Identik logikanya, jadi ada 3 salinan fungsi yang sama tersebar di codebase (`utils.py`, `forecast.py`, `simulation.py`).
- `forecast_months()`: untuk bulan yang sudah ada di data historis, hasilnya adalah **data aktual**, bukan forecast — penting dipahami karena nama fungsinya bisa menyesatkan.
- Interval confidence band `±8` di `prediksi.py` adalah angka hardcoded di halaman, tidak terkait perhitungan `forecast.py`.

**Ringkasan**: Service forecasting murni ekstrapolasi linear (tanpa model ML), dasar semua tampilan proyeksi.

---

### `src/services/simulation.py`

**Tujuan**: Simulator "what-if" — hitung ulang crisis score instan dari 3 variabel (wisman/kurs/sentimen) tanpa panggil model ML, murni formula berbobot.

**Proses**:
1. `simulate_score()`: ambil 4 komponen dari `row`, terapkan penyesuaian linear sesuai delta slider, clip ke [0,1], hitung skor akhir dengan bobot resmi (0.45/0.25/0.20/0.10) × 100.
2. `level_from_score()`: duplikasi dari `utils.py`.
3. `compute_scenario_summary()`: tidak dipanggil di `prediksi.py` (yang justru memanggil `simulate_score()` + `level_from_score()` terpisah).

**Dependensi**: `numpy`; internal `src.config.THRESHOLD`.

**Catatan**:
- Bobot 0.45/0.25/0.20/0.10 di-hardcode di sini, **tidak diimpor** dari `config.py` (yang nilainya beda — lihat catatan `config.py`).
- `sf()` didefinisikan ulang lokal sebagai nested function.

**Ringkasan**: Mesin kalkulasi instan simulator skenario risiko, formula resmi di-hardcode independen dari `config.py`.

---

### `src/services/llm_service.py`

**Tujuan**: Layer murni prompt-engineering LLM — context block, prompt builder per tipe laporan, prompt komparasi, pembersih output. Tanpa `st.*`.

**Fungsi**: Backend prompt untuk `pages/narasi.py`.

**Proses**:
- `build_data_block(ctx)`: blok teks angka penting + deteksi "kontradiksi" antar indikator.
- `build_prompt_summary/alert/monthly/predict()`: prompt per tipe laporan, semua diakhiri `NARASI_RULE` (instruksi anti-karakter-non-Latin + pola penjelasan skor risiko).
- `build_prompt_swot(ctx, format_style='paragraf')`: prompt SWOT + kuadran "REKOMENDASI STRATEGIS".
- `build_prompt_comparison(ctx_a, ctx_b, report_type, format_style='paragraf')`: prompt komparasi dua periode, semua tipe laporan.
- `build_prompt(ctx, report_type, format_style='paragraf')`: router tipe laporan, menambahkan `FORMAT_STYLE_RULE` di akhir.
- `build_ctx(row_data, history)`: row prediksi + histori → dict context (delta MoM, tren wisman, histori level).
- `clean_output(text)`: hapus karakter non-Latin yang bocor.

**Dependensi**: `os`, `json`, `re`, `requests` (sebagian tidak dipakai — sisa versi lama); `pathlib`.

**Catatan (v2 — update dari versi sebelumnya)**:
- **[BARU] `FORMAT_STYLE_RULE`**: dict 2 entri (`paragraf`, `poin`) — blok instruksi format output yang ditambahkan di akhir setiap prompt via `build_prompt()`. `paragraf` melarang bullet/numbering; `poin` mewajibkan bullet list maks 2 kalimat/poin.
- **[BARU] Parameter `format_style`** ditambahkan ke `build_prompt_swot()`, `build_prompt_comparison()`, `build_prompt()` — default `'paragraf'`.
- **[UBAH] SWOT dirombak agar lebih padat & tidak mengulang**: tiap kuadran (Kekuatan/Kelemahan/Peluang) diberi batas eksplisit "maksimal 3 kalimat", Ancaman "maksimal 4 kalimat". Kuadran "Rekomendasi Strategis" diganti dari 6 bullet point eksplisit jadi instruksi 6 substansi (a–f) yang **wajib dijelaskan berbeda, dilarang tumpang-tindih ide**, dan dilarang menulis label (a)-(f) secara harfiah — cara penyajian (paragraf/poin) sepenuhnya diserahkan ke `FORMAT_STYLE_RULE`, bukan format implisit dari instruksi SWOT.
- **[REFACTOR]** `build_prompt_comparison()` (publik) sekarang adalah wrapper tipis yang memanggil `_build_prompt_comparison_inner()` (isi lama, di-rename) + menambahkan `FORMAT_STYLE_RULE`.
- **[REFACTOR]** `build_prompt(ctx, report_type, format_style)`: SWOT ditangani jalur khusus (pass `format_style`), tipe lain tetap lewat dict `builders`, lalu hasil akhir digabung dengan `FORMAT_STYLE_RULE` di satu tempat (bukan diulang per builder) — lebih konsisten dibanding sebelumnya.
- **[TIDAK BERUBAH]** `NARASI_RULE`, `build_data_block()`, `build_ctx()`, `clean_output()`, `build_prompt_summary/alert/monthly/predict()` — isinya identik dengan versi sebelumnya.
- `CACHE_PATH`/`GROQ_ENDPOINT` masih didefinisikan tapi tetap tidak dipakai (pemanggilan API & penulisan cache tetap di `pages/narasi.py` via SDK `groq` resmi).

**Ringkasan**: Otak prompt engineering BaliGuard. Update kali ini menambah kontrol format output (paragraf/poin) di semua prompt, dan merampingkan instruksi SWOT agar tidak repetitif/bertele-tele.

---

### `src/narrative_engine.py`

**Tujuan**: Modul LLM mandiri versi lama (`build_context`, `build_prompt`, `generate`, `load_cache`) — tumpang tindih fungsi dengan `services/llm_service.py` + logika di `pages/narasi.py`, tapi implementasi independen.

**Catatan**:
- **Tidak diimpor file manapun** di paket ini (dikonfirmasi via grep). `pages/narasi.py` memanggil Groq API langsung + pakai `services/llm_service.py`, bukan modul ini.
- Model tidak lagi di-hardcode — dibaca dari environment variable `GROQ_MODEL` (default `openai/gpt-oss-120b`, model `llama-3.3-70b-versatile` sebelumnya sudah deprecated). Modul ini tetap tidak mendukung pilihan 4 model seperti di UI `narasi.py`, hanya satu model dari `GROQ_MODEL`.
- Tidak punya `NARASI_RULE` atau kontrol format paragraf/poin — kalau modul ini pernah dipanggil ulang tanpa sadar menggantikan `llm_service.py`, hasil narasi akan beda signifikan format & kualitasnya.

**Ringkasan**: Dead code — tidak dipakai di alur eksekusi dashboard saat ini.

---

### `src/pages/overview.py`

**Tujuan**: Halaman pertama — 3 chart time-series (Wisman, Kurs, Crisis Score & Level dengan anotasi event historis), panel "External Risk Monitor" (4 kartu), expander metodologi, strip statistik ringkasan.

**Proses**: 3 fungsi `_build_overview_fig1/2/3()` (cache) bangun chart Plotly. `render()` tampilkan chart berurutan, panel risiko eksternal (4 kartu, warna berjenjang), expander metodologi (tabel komponen + formula), strip 4 statistik bawah (% AMAN, % KRISIS, avg score, peak wisman).

**Dependensi**: `streamlit`, `plotly`, `pandas`, `numpy`; internal `src.utils`, `src.components.*`, `src.config.COLOR_MAP`.

**Catatan**:
- Bobot di expander metodologi (35% Physical/35% Media/30% Tourist Perception) **berbeda** dari bobot resmi pipeline (equal-weight 3 komponen berbeda: gdelt/disaster/economic risk). Teks ini tampak ditulis manual untuk dashboard, terpisah dari implementasi aktual `external_risk_avg`.
- Fitur kurs live/historis yang sudah dibangun di `utils.py` (`get_current_usd_idr`, `format_usd_source_label`) **tidak dipakai** di halaman ini — tidak ada KPI card kurs sama sekali, hanya chart tren tanpa label live/historis.
- Statistik ringkasan bawah dihitung ulang dari `predictions` langsung, padahal nilai sama sudah tersedia di `ctx['pct_aman']` dkk — duplikasi komputasi minor.

**Ringkasan**: Chart historis lengkap + ringkasan statistik. Bobot metodologi yang ditampilkan tidak sinkron dengan formula pipeline resmi; fitur kurs live/historis belum dimanfaatkan di sini.

---

### `src/pages/analisis.py`

> **Tidak ada perubahan** dari versi sebelumnya (diverifikasi diff byte-identik dengan file yang diupload kali ini).

**Tujuan**: Halaman "Analisis Detail" — breakdown kontribusi komponen crisis score, section "Mengapa Status Ini Muncul?" (bahasa awam), daftar indikator detail, probabilitas prediksi RF, feature importance.

**Proses**:
1. Panel Komponen Crisis Score: kontribusi 4 komponen (Wisatawan ×0.45, Ekonomi ×0.25, Sentimen ×0.10, External Risk ×0.20) sebagai bar chart.
2. "Mengapa Status Ini Muncul?": 5 indikator utama, label dari `LABEL_MANUSIAWI`, kalimat dari `interpretasi_indikator()`.
3. Panel Indikator Detail: 14 baris key-value (sebagian label hardcoded Indonesia, sebagian via `LABEL_MANUSIAWI`).
4. Panel Probabilitas Prediksi: bar chart 4 level.
5. Panel Feature Importance: 8 fitur teratas dari `rf_model.feature_importances_`, label via `LABEL_MANUSIAWI`.

**Dependensi**: `streamlit`, `plotly`, `pandas`, `numpy`; internal `src.utils`.

**Catatan**:
- **Bug feature-alignment masih ada**: `fi_available[:len(rf_model.feature_importances_)]` memasangkan fitur ↔ importance secara **posisional**, bukan via `rf_model.feature_names_in_` (atribut resmi scikit-learn). Risiko: pemasangan nama fitur salah jika urutan fitur saat training berbeda dari urutan `FEATURES_CORE + FEATURES_LAG` di `config.py` saat ini. Perbaikan ini sebelumnya sudah direkomendasikan tapi **belum diterapkan**.
- Class CSS (`sec-blue`, `risk-row`, dll.) dipakai tapi tidak didefinisikan di file ini — bergantung pada CSS global di entry point dashboard (di luar paket).

**Ringkasan**: Halaman transparansi model. Masih membawa bug feature-alignment posisional yang belum diperbaiki.

---

### `src/pages/sentimen.py`

**Tujuan**: Hero metrik sentimen, distribusi review (positif/negatif/netral), gauge sentimen, tren historis, bar chart 6 bulan terakhir.

**Proses**: Cabang proyeksi (placeholder "—" untuk distribusi, tampilkan sentimen riil terakhir) vs historis (ambil dari `master`). Label sentimen dari skor, fallback ke distribusi persen jika skor di zona netral. Hero 5 kolom + 2 kolom bawah (tren historis & 6 bulan terakhir | gauge & distribusi).

**Dependensi**: `streamlit`, `plotly`, `pandas`, `numpy`; internal `src.utils` (sebagian impor tidak dipakai).

**Catatan**:
- Komentar dangling `# TAB 4: PREDIKSI & PROYEKSI` di baris terakhir tanpa kode lanjutan — sisa refactor pemisahan tab jadi file terpisah.
- Banyak import tidak terpakai (`LEVEL_COLORS`, `LABEL_ORDER`, `FEATURES_CORE/LAG`, `plotly.express`, dll.) — pola sama di semua halaman.
- `_netral_estimated` diinisialisasi `False` tapi tidak pernah diset `True` — logika "netral diestimasi" belum aktif.

**Ringkasan**: Analisis sentimen visual lengkap dengan penanganan kasus proyeksi yang baik. Ada sisa kode tidak terpakai dari refactor sebelumnya.

---

### `src/pages/prediksi.py`

**Tujuan**: Kontrol proyeksi (tahun/bulan/jumlah bulan), grid kartu forecast, simulator skenario risiko, breakdown risiko + rekomendasi, 3 mode chart (Tren+Proyeksi, Recovery Rate, Peta Risiko Historis).

**Proses**:
1. Selector proyeksi → `forecast_months()`.
2. Grid forecast 12 slot (skor, level, confidence dengan bar warna berjenjang).
3. Simulator: 3 slider → `simulate_score()` real-time.
4. Panel External Risk Score: 4 kartu kategori (Rendah/Sedang/Tinggi, threshold 0.33/0.66).
5. Breakdown Risiko + Rekomendasi: pakai `ADVICE_MAP` (dict lokal, beda dari `REKOMENDASI_LEVEL` di `utils.py`).
6. 3 tab chart (kontrol manual via tombol + session_state, bukan `st.tabs`).

**Dependensi**: `streamlit`, `plotly`, `pandas`, `numpy`; internal `src.utils.level_from_score`, `src.services.simulation.simulate_score`, `src.services.forecast`, `src.config.COLOR_MAP`.

**Catatan**:
- `level_from_score` diimpor dua kali dari sumber berbeda (`utils.py` lalu ditimpa `services.forecast`) — tidak bug (logika identik), tapi membingungkan.
- File berakhir dengan komentar dangling `# TAB 5: NARASI AI` tanpa kode lanjutan.
- `ADVICE_MAP` vs `REKOMENDASI_LEVEL`: dua sumber rekomendasi tindakan berbeda konten, tidak saling terhubung. `REKOMENDASI_LEVEL` didokumentasikan untuk dipakai `analisis.py`/`narasi.py` tapi tidak ditemukan benar-benar dipanggil di keduanya.
- Interval `±8` poin di chart Tren+Proyeksi hardcoded, tidak berasal dari kalkulasi statistik.

**Ringkasan**: Halaman paling interaktif — forecast otomatis + simulasi manual + rekomendasi kontekstual. Ada duplikasi impor dan dua sistem rekomendasi tindakan yang tidak terkonsolidasi.

---

### `src/pages/narasi.py`

**Tujuan**: UI lengkap fitur Narasi AI — pilih tipe laporan (5 jenis), model Groq (4 model), format output (paragraf/poin), bulan target, generate via Groq API, tampilkan hasil + copy/download, cache lokal, komparasi antar periode.

**Proses**:
1. Load & migrasi cache ke `session_state['narratives_cache']`.
2. Hero banner + kartu kegunaan (statis).
3. Pilih tipe laporan (5 kartu) → `session_state['report_type_sel']`.
4. Pilih model AI (4 kartu, warna mengikuti posisi kolom tipe laporan).
5. Pilih bulan/tahun target (s/d 18 bulan proyeksi).
6. Generate: ambil row data → `build_ctx()` + `build_prompt()` → panggil Groq API sekali → bersihkan output → tampilkan → simpan ke `narratives_cache.json`.
7. Tampilkan cache tersimpan jika ada & belum digenerate ulang.
8. Komparasi antar periode: pilih 2 bulan + format → tampilkan **dari cache yang sudah ada** untuk kombinasi bulan+tipe+model+format tersebut (lihat changelog — bukan generate baru lagi).

**Dependensi**: `streamlit`, `streamlit.components.v1`, `plotly`, `pandas`, `numpy`; internal `src.services.llm_service` (`build_ctx`, `build_prompt`, `build_prompt_comparison` — kini tidak dipakai, lihat catatan, `clean_output`), `src.services.forecast.forecast_months`, `src.utils`, `src.config.COLOR_MAP`. Eksternal: SDK `groq` (impor lokal di dalam blok generate).

**Catatan (v2 — update dari versi sebelumnya)**:
- **[FIXED] Bug pemanggilan API duplikat sudah diperbaiki.** Versi sebelumnya memanggil Groq API dua kali berturut-turut dengan prompt identik (boros 2× kuota per klik Generate). Sekarang hanya **satu** panggilan API per generate.
- **[BARU] Format output (paragraf/poin)**: selectbox baru di antara Bulan dan Status (`_c_format`, kolom layout berubah dari 4 jadi 5: Tahun|Bulan|Format|Status|Cache). Tersimpan di `session_state['format_style_sel']`, diteruskan ke `build_prompt(..., format_style)`.
- **[BARU] Cache key menyertakan format**: `{month}_{report_type}_{model}_{format}` (sebelumnya tanpa suffix format). Migrasi cache lama otomatis: key tanpa `report_type` → ditambah `report_type`; key tanpa suffix format → ditambah format dari field `format` di data lama (default `paragraf`).
- **[BARU] `_MAX_TOKENS_BY_TYPE`**: max_tokens kini dinamis per tipe laporan (summary/alert 700, monthly/predict 900, swot 1800, comparison 1500) — sebelumnya flat 1024 untuk semua tipe.
- **[BARU] `narasi_shown_keys`** (session_state set): menandai kombinasi cache key yang sudah pernah ditampilkan di sesi browser ini. Narasi cache hanya auto-tampil kalau **sudah pernah ditampilkan sebelumnya** (`_already_shown`) — pertama kali masuk halaman, narasi cache tidak langsung muncul otomatis sebelum user klik Generate (beda dari versi sebelumnya yang langsung auto-tampil kalau cache ada).
- **[HAPUS] Mode komparasi tidak lagi memanggil Groq API.** Toggle tombol "Aktifkan Komparasi" dihapus — section komparasi sekarang selalu tampil (`compare_mode = True` konstan). Saat klik "Generate Komparasi", sistem **mencari cache yang sudah ada** untuk bulan A & B (dengan kombinasi tipe+model+format yang sama) — kalau salah satu belum pernah digenerate, muncul warning minta user generate dulu di bagian atas. Kalau keduanya ada, ditampilkan **berdampingan 2 kolom** (bukan satu narasi gabungan hasil LLM seperti sebelumnya).
- **Akibat dari perubahan komparasi**: `build_prompt_comparison()` (di `llm_service.py`) dan helper lokal `_get_ctx_for_month()` **masih diimpor/didefinisikan tapi sudah tidak pernah dipanggil** — dead code baru yang muncul akibat refactor ini.
- **[HAPUS]** Blok kode UI input API key yang sebelumnya di-comment-out (instruksi + link "Dapatkan Key Gratis") sudah dihapus total dari file (bukan di-comment lagi). Perilaku tetap sama: `_get_groq_key()` hanya baca `st.secrets`/env var, tombol Generate otomatis disabled kalau key kosong, tanpa penjelasan ke user baru kenapa tombol disabled.
- `narratives_cache.json` masih ditulis ulang penuh ke path relatif `'data/final/narratives_cache.json'` (bukan `DATA_DIR` dari `config.py`) — bergantung pada working directory proses saat dashboard dijalankan.
- Pola import tidak terpakai (`plotly.graph_objects`, `plotly.express`, `make_subplots`, `sys`) masih konsisten dengan halaman lain.

**Ringkasan**: Halaman paling kompleks di dashboard. Update kali ini memperbaiki bug API duplikat, menambah kontrol format output, dan mengubah total mekanisme komparasi dari "generate narasi gabungan via LLM" menjadi "tampilkan dua narasi cache berdampingan" — implikasinya, komparasi sekarang **mensyaratkan** kedua periode sudah pernah digenerate lebih dulu lewat alur generate biasa.

---

## Output Project (Dashboard)

**Dibaca** dashboard (dihasilkan oleh pipeline NB01–NB06, di luar paket ini):

| File | Dibaca Oleh | Kegunaan |
|---|---|---|
| `data/final/predictions_final.csv` | `utils.load_data()` → semua halaman | KPI, chart historis, forecast |
| `data/final/master_dataset_clean.parquet` | `utils.load_data()` → `analisis.py`, `sentimen.py`, `prediksi.py` | Komponen crisis score mentah, fitur lengkap |
| `models/model_random_forest.pkl` | `utils.load_models()` | Prediksi level krisis & confidence |
| `models/model_isolation_forest.pkl` | `utils.load_models()` | Deteksi anomali |
| `models/scaler.pkl`, `models/label_encoder.pkl` | `utils.load_models()` | Preprocessing (tidak terlihat dipakai aktif di paket ini) |
| `assets/icons/*.png` | `utils.load_nav_icons()`, `sidebar.py` | Ikon navigasi & logo |

**Dihasilkan** dashboard:

| File | Dihasilkan Oleh | Kegunaan |
|---|---|---|
| `data/final/narratives_cache.json` | `pages/narasi.py` (overwrite penuh tiap generate) | Cache narasi per kombinasi bulan + tipe + model + **format** (baru) |

File `.txt` narasi di-download langsung oleh browser (tidak disimpan ke server).

---

## Temuan Lintas File yang Perlu Perhatian

1. **Bug feature-importance di `analisis.py`** — masih belum diperbaiki (lihat catatan file tersebut).
2. **`narrative_engine.py` masih ada di `src/`** meski tidak dipakai file manapun — dead code.
3. ~~Bug pemanggilan API duplikat di `narasi.py`~~ — **sudah diperbaiki** di versi ini.
4. **Tiga implementasi `level_from_score()` independen** (`utils.py`, `services/forecast.py`, `services/simulation.py`) — identik logikanya, sebaiknya dikonsolidasi.
5. **Dua sistem rekomendasi tindakan tidak terhubung**: `ADVICE_MAP` (`prediksi.py`) vs `REKOMENDASI_LEVEL` (`utils.py`, tidak dipanggil di mana pun).
6. **Bobot/formula yang ditampilkan ke user vs formula resmi pipeline tidak sinkron**: expander metodologi `overview.py` (35/35/30%), `WEIGHT_*` di `config.py`.
7. **Fitur kurs live/historis di `utils.py` belum dipakai** di `overview.py`.
8. **Pola boilerplate**: tiap halaman impor modul yang tidak dipakai (`plotly.express`, `make_subplots`, `json`/`os`/`time`/`requests`/`sys`).
9. **Komentar "TAB" dangling** tanpa kode di akhir `sentimen.py` dan `prediksi.py`.
10. **[BARU] Dead code baru di `narasi.py`**: `build_prompt_comparison()` dan `_get_ctx_for_month()` masih ada tapi tidak pernah dipanggil lagi setelah mode komparasi diubah ke pendekatan cache-lookup.

---

## Changelog (v1 → v2)

| File | Perubahan |
|---|---|
| `analisis.py` | Tidak ada perubahan (diff byte-identik). |
| `llm_service.py` | + `FORMAT_STYLE_RULE` (paragraf/poin); param `format_style` di `build_prompt_swot`, `build_prompt_comparison`, `build_prompt`; prompt SWOT dirombak lebih padat (batas kalimat per kuadran, instruksi 6 substansi non-repetitif untuk Rekomendasi Strategis); `build_prompt_comparison` di-refactor jadi wrapper + `_build_prompt_comparison_inner`. |
| `narasi.py` | Bug panggilan API duplikat **diperbaiki**; + selectbox Format (paragraf/poin); cache key + suffix format; migrasi cache 2-tahap; `_MAX_TOKENS_BY_TYPE` (dinamis per tipe, sebelumnya flat 1024); + `narasi_shown_keys` (cache tidak auto-tampil sebelum pernah ditampilkan/digenerate); mode komparasi diubah total — tidak lagi panggil API, hanya menampilkan cache existing dua periode berdampingan (mensyaratkan kedua periode sudah digenerate lebih dulu); blok comment-out UI API key dihapus total; `build_prompt_comparison`/`_get_ctx_for_month` jadi dead code. |
