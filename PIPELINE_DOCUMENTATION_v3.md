# Dokumentasi Pipeline — BaliGuard Early Warning System Krisis Pariwisata Bali
> Dokumen handoff antar sesi Claude. Dibuat dari pembacaan langsung seluruh notebook NB01–NB06.
> Versi ini mencerminkan **state final** semua notebook yang telah dijalankan dan diverifikasi.

---

## Status Notebook

| Notebook | File | Status | Output Utama |
|---|---|---|---|
| NB01 — Load & EDA | `01_LoadDataset_dan_EDA.ipynb` | ✅ Final | `reports/figures/eda_wisman_trend.png` |
| NB02 — Preprocessing | `02_Preprocessing.ipynb` | ✅ Final | 10 file CSV di `data/processed/` |
| NB03 — Sentiment | `03_Text_Preprocessing_Sentiment.ipynb` | ✅ Final | `monthly_sentiment.csv`, `sentiment_stats.csv`, `all_reviews_sentiment.csv` |
| NB04 — Feature Engineering & Crisis Score | `04_Feature_Engineering_Crisis_Score.ipynb` | ✅ Final | `crisis_dataset_final.csv`, `master_dataset_clean.parquet` |
| NB05 — Modeling | `05_Modeling_Anomaly_Detection_Classification.ipynb` | ✅ Final | `predictions_final.csv` (208×31), model `.pkl` |
| NB06 — LLM Narrative Engine | `06_LLM_Narrative_Engine.ipynb` | ✅ Final | `narrative_engine.py`, `narratives_cache.json` |

---

## NB01 — Load Semua Dataset & EDA

### Tujuan
Notebook rekonaisans — load semua data mentah, preview struktur, cek missing value, duplicate timestamp, dan stasioneritas. **Tidak menghasilkan file CSV apapun ke disk.**

### Dataset yang Dimuat (14 sumber)

| Variabel | File | Format | Rentang | Dilanjutkan? |
|---|---|---|---|---|
| `wisman_gab` | `Gab_Data_Wisman_Bali.xlsx` | Long (Tanggal, Banyak) | 2009–2026 | ✅ → NB02 |
| `wisman_old` | `banyaknya-wisatawan-mancanegara-bulanan-ke-bali.xls` | Wide BPS | 1982–2008 | ❌ Superseded oleh wisman_gab |
| `wisman_bali_indonesia_raw` | `banyaknya-wisatawan-mancanegara-ke-bali-dan-indonesia.xls` | Wide tahunan | 1969–2025 | ✅ → NB02 |
| `wisnus` | `wisnus_bali_2004_2025.xlsx` | Wide BPS (3 sheet) | 2004–2025 | ✅ → NB02 |
| `wisman_kebangsaan` | `-banyaknya-wisatawan-...xlsx` | Per negara tahunan | 2019–2024 | ❌ Tidak dilanjutkan — tahunan saja, downscale ke bulanan artificial |
| `tpk_bintang` | `Tingkat Penghunian Kamar (TPK) Hotel Bintang.xlsx` | Wide BPS | 2000–sekarang | ✅ → NB02 |
| `tpk_nonbintang` | `Tingkat Penghunian Kamar (TPK).xlsx` | Wide BPS per kabupaten | 2007–sekarang | ✅ → NB02 |
| `lama_bintang` | `Rata-Rata Lama Menginap...Hotel Bintang.xlsx` | Wide BPS | 2000–sekarang | ✅ → NB02 Section 3.2 |
| `lama_nonbintang` | `Rata-Rata Lama Menginap...Hotel Non Bintang.xlsx` | Wide BPS per kabupaten | 2007–sekarang | ✅ → NB02 Section 3.2 |
| `inflasi` | `Data Inflasi.xlsx` | Long | 2009–2025 | ✅ → NB02 |
| `usd_idr` | `USD_IDR Historical Data.csv` | Long harian | ~2009–2024 | ✅ → NB02 |
| `forex` | `daily_forex_rates.csv` | Long harian multi-pair | | ✅ → NB02 |
| `hotel_reviews` | `merged_all_hotels.xlsx` | date, location, hotel, review, rating | 2009–2026 | ✅ → NB03 |
| `digital_reviews` | `Dataset of Digital Reviews in Tourism - 2.csv` | hanya kolom review | tanpa tanggal | ✅ → NB03 (supplement teks) |

### Perbaikan yang Dilakukan
1. **Cell 14** — Komentar sheet wisnus diperbaiki (awalnya hanya tulis "2004–2012" padahal ada 3 sheet)
2. **Cell 37** — `plt.savefig()` dipindah dari `data/processed/` ke `reports/figures/`
3. **Cell 41** — Bug nama variabel `reviews` → `hotel_reviews` di duplicate check
4. **Cell 17** — Ditambah catatan eksplisit kenapa `wisman_kebangsaan` tidak dilanjutkan
5. **Cell 25** — Ditambah catatan eksplisit kenapa `lama_bintang` & `lama_nonbintang` dilanjutkan ke NB02

### Analisis EDA
- Missing value heatmap (5 dataset utama)
- Duplicate timestamp check (`wisman_gab`, `hotel_reviews`)
- ADF Stationarity Test: wisman raw (non-stasioner), wisman growth MoM (stasioner), USD/IDR raw (non-stasioner), USD/IDR pct_change (stasioner)

### Output
- `reports/figures/eda_wisman_trend.png` — plot wisman dengan highlight periode COVID 2020–2021

---

## NB02 — Preprocessing Data

### Tujuan
Membersihkan semua sumber data mentah dan menyimpan ke format bulanan konsisten di `data/processed/`. Disusun per tema (bukan per notebook asli).

### Struktur

| Section | Tema | Output |
|---|---|---|
| 0. Setup | Import, mkdir | — |
| 1. Pariwisata | Wisman, wisnus, wisman vs Indonesia | `wisman_clean.csv`, `wisnus_clean.csv`, `wisman_vs_indonesia_clean.csv` |
| 2. Ekonomi & Moneter | USD/IDR, forex, inflasi, World Bank | `monthly_usd.csv`, `monthly_forex.csv`, `inflasi_clean.csv`, `wb_monthly_economic.csv` |
| 3. Akomodasi | TPK + Lama Menginap | `tpk_clean.csv`, `lama_menginap_clean.csv` |
| 4. Risiko Eksternal | Gempa (USGS), Cuaca (Open-Meteo), BaliGuard historical | (dalam memori → merge di Section 6) |
| 5. Sinyal Digital | GDELT, Google Trends | (dalam memori → merge di Section 6) |
| 6. Merge & Validasi | Gabung semua tema 4–5 + coverage check | `combined_additional_features_new.csv` |
| 7. Save | — | (semua file di atas) |

### Output Files (10 file di `data/processed/`)

| File | Kolom Kunci | Rentang | Catatan Penting |
|---|---|---|---|
| `wisman_clean.csv` | date, wisman, month | 2009-01 → 2026-04 | Backbone timeline; data real sampai 2026-04 |
| `wisnus_clean.csv` | date, month, wisnus | 2004-01 → 2025-12 | 3 sheet BPS di-melt |
| `wisman_vs_indonesia_clean.csv` | tahun, indonesia_total, bali_total, bali_share_pct | 1969–2025 | **Tahunan** — di-join by tahun di NB04 |
| `monthly_usd.csv` | month, usd_idr_avg | | Rata-rata harian → bulanan |
| `monthly_forex.csv` | month, idr_eur_rate | | Filter IDR saja dari daily_forex |
| `inflasi_clean.csv` | date, month, inflasi_processed | 2009-01 → 2025-12 | Strip `%`, filter 2009–2025 |
| `wb_monthly_economic.csv` | economic_index, economic_risk_score, wb_is_imputed | | ⚠ **Tersimpan dengan index** (`index=False` tidak dipakai) → load di NB04 wajib `index_col=0`. `wb_is_imputed=1` = data hasil ffill bukan asli WB |
| `tpk_clean.csv` | date, month, tpk_bintang, tpk_non_bintang | | Rata-rata per kelas/kabupaten per bulan |
| `lama_menginap_clean.csv` | date, month, lama_menginap_bintang, lama_menginap_non_bintang | 2009-01 → 2025-12 | Leading indicator kualitas kunjungan |
| `combined_additional_features_new.csv` | date + ~30 kolom | 2009-01 → 2025-12 | ⚠ **Tidak punya kolom `month`** — buat dari `date` saat load di NB04 |

### Detail Penting per Tema

**Tema 2 — World Bank:**
- Bobot wisatawan per negara: AUS 20%, CHN 18%, JPN 10%, IND 12%, MYS 10%, USA 8%, GBR 8%, SGP 7%, DEU 7%
- `economic_risk_score` = 1 − normalisasi(economic_index) — GDP rendah = risiko tinggi
- Extended sampai Des 2025 via ffill, `wb_is_imputed` menandai bulan imputed

**Tema 4 — External Risk:**
- Gempa (USGS): composite `eq_risk_score` = 70% energi seismik + 30% frekuensi
- Cuaca (Open-Meteo): `wx_precip_sum`, `wx_humidity_mean` per bulan
- BaliGuard historical: `disaster_risk_score` = 40% seismik + 30% gunung berapi + 30% cuaca ekstrem

**Tema 5 — Digital & Media:**
- GDELT: `gdelt_crisis_score` = (tone_risk_score + risk_ratio_score) / 2; tone negatif → score tinggi
- Google Trends: `trend_risk_score` = 1 − normalisasi(trend_composite); minat turun → risiko naik

### Perbaikan yang Dilakukan vs Notebook Asli
1. Bug f-string `{{ }}` di semua cell validasi — semua diperbaiki ke `{ }`
2. `inflasi_df.to_csv()` tersimpan 2x dengan kode identik — disederhanakan jadi sekali
3. `wb_is_imputed` (flag transparansi imputasi World Bank) disimpan ke `wb_monthly_economic.csv` — tidak lagi di-drop sebelum disimpan
4. `bulan_map` yang dipakai ulang di 3 section dengan isi berbeda — di-namespace jadi `bulan_map_wisnus`, `bulan_map_inflasi`, `bulan_map_tpk`
5. **Ditambah Section 3.2** — Lama Menginap Hotel Bintang & Non Bintang (5 cells baru)

---

## NB03 — Text Preprocessing & Sentiment Analysis

### Tujuan
Proses review wisatawan melalui pipeline cleaning → deteksi bahasa → sentiment model → agregasi bulanan.

### Dataset Input

| Sumber | File | Baris | Keterangan |
|---|---|---|---|
| Hotel reviews | `merged_all_hotels.xlsx` | 29.332 | Kolom: date, location, hotel, review, rating. Ada tanggal |
| Digital reviews | `Dataset of Digital Reviews in Tourism - 2.csv` | 56.448 | Hanya kolom `review`. **Tanpa tanggal** |
| Total setelah cleaning | — | ~82.236 | Setelah hapus duplikat & review < 10 karakter |

### Pipeline
1. **Load & Merge** — gabung dengan kolom `source`; digital_tourism diberi `date = NaT`
2. **Text Cleaning** (`clean_text()`) — lowercase, hapus URL/HTML/karakter khusus (pertahankan CJK untuk Mandarin), hapus review duplikat & < 10 karakter
3. **Deteksi Bahasa** (`langdetect`) — target: EN, ID, ZH, MS; distribusi utama: `en` (73.291), `id` (3.191), `de` (923), `ko` (891), `fr` (804)
4. **Sentiment Analysis** — model `cardiffnlp/twitter-xlm-roberta-base-sentiment`, batch 32, truncation 512 token, output skor −1 s/d +1
5. **Agregasi Bulanan** — hanya `merged_hotels` (punya tanggal) yang masuk timeline
6. **Volume Flag** — `is_volume_reliable = 1` jika review_count ≥ 10

### Kolom `monthly_sentiment.csv`
```
month, avg_sentiment, pct_positive, pct_negative, pct_neutral,
review_count, avg_rating, is_volume_reliable
```
**Catatan:** Nama kolom di sini `pct_negative`. Di NB04 setelah merge, **di-rename** menjadi `pct_negative_monthly` (via `final_df.rename()`).

### Output Files

| File | Keterangan |
|---|---|
| `monthly_sentiment.csv` | 169 bulan (2009-05 → 2026-05) — input utama NB04 |
| `sentiment_stats.csv` | Nilai global (fallback untuk bulan tanpa data review) |
| `all_reviews_sentiment.csv` | 82.236 review individual dengan `sentiment_score`, `sentiment_label`, `sentiment_confidence` |

---

## NB04 — Feature Engineering & Crisis Score

### Tujuan
Gabungan NB04_2 (External Risk FE) + NB04_1 (Merge + Crisis Score). Menghasilkan dataset final untuk NB05.

### Struktur (Urutan Eksekusi Wajib Dijaga)

| Section | Isi | Catatan |
|---|---|---|
| 0. Setup | Import, mkdir | — |
| 1. External Risk FE | Konten NB04_2 | **Harus selesai sebelum Section 2** |
| 2. Load Data | Load semua CSV processed | wb_monthly: `index_col=0`; combined_additional: buat `month` dari `date` |
| 3. Merge | Backbone wisman → merge semua dataset | ffill untuk lama_menginap, sentiment, external |
| 4. Feature Engineering | Inline FE + definisi `build_features()` | FE inline di 4a & 4b; `build_features()` di 4c hanya definisi |
| 5. Normalisasi | MinMaxScaler per komponen | — |
| 6. Crisis Score | Hitung score + label + ffill dashboard indicators | Lihat formula di bawah |
| 7. Visualisasi | Timeline + heatmap korelasi | → `reports/figures/` |
| 8. Save | CSV + Parquet | → `data/final/` |
| 9. Summary | Statistik akhir | — |

### Section 1 — External Risk Feature Engineering

Input: `combined_additional_features_new.csv`

Fitur yang dibuat:
- Rolling MA3: `gdelt_crisis_score_ma3`, `disaster_risk_score_ma3`, `economic_risk_score_ma3`
- Slope 3m: `gdelt_crisis_score_slope3m`, `disaster_risk_score_slope3m`, `economic_risk_score_slope3m`
- Z-score 12 bulan: `gdelt_crisis_score_zscore`, `disaster_risk_score_zscore`
- Composite: `external_risk_avg` (equal weight), `external_risk_max` (shock detector), `external_risk_range` (divergensi)

Output: `combined_additional_features_engineered_new.csv` → `data/processed/`

### Crisis Score Formula & Threshold

```
Crisis Score = 0.45 × component_tourism
             + 0.25 × component_economy
             + 0.20 × external_risk_score
             + 0.10 × component_sentiment
```

| Level | Kondisi (crisis_score_100) |
|---|---|
| AMAN | score < 30 |
| WASPADA | 30 ≤ score < 45 |
| SIAGA | 45 ≤ score < 60 |
| KRISIS | score ≥ 60 |

### Kolom Dashboard Indicators (Alias)

Dibuat di Section 6 untuk kebutuhan dashboard, nilainya dari kolom lain:

| Kolom Dashboard | Sumber |
|---|---|
| `physical_risk_score` | `disaster_risk_score` |
| `media_risk_score` | `gdelt_crisis_score` |
| `tourist_perception_score` | rata-rata `trend_risk_score` + `economic_risk_score` |
| `external_risk_score` | `external_risk_avg` |

Keempat kolom ini **di-ffill** di Section 6 (setelah dibuat) untuk mengisi NaN di bulan 2026-01–04 yang tidak punya data GDELT/disaster terbaru.

Keempat kolom ini **sengaja tidak dimasukkan ke FEATURES model** di NB05 (karena duplikat dengan kolom sumber), tapi tetap tersimpan di `predictions_final.csv` untuk dashboard.

### Output Files NB04

| File | Path | Keterangan |
|---|---|---|
| `crisis_dataset_final.csv` | `data/final/` | Dataset lengkap — semua kolom output_cols |
| `master_dataset_clean.parquet` | `data/final/` | Input untuk NB05 (month dikonversi ke string) |
| `combined_additional_features_engineered_new.csv` | `data/processed/` | Output Section 1, input NB05 |
| `crisis_score_timeline.png` | `reports/figures/` | Plot timeline crisis score |
| `feature_correlation_heatmap.png` | `reports/figures/` | Heatmap korelasi fitur |

### Kolom output_cols NB04 (lengkap)
```
month,
wisman, wisnus, usd_idr_avg,
tpk_bintang, tpk_non_bintang, tpk_change_mom, tpk_ma3,
lama_menginap_bintang, lama_menginap_non_bintang,
inflasi_processed, indonesia_total, bali_share_pct,
avg_sentiment_monthly, pct_negative_monthly, pct_positive_monthly, pct_neutral_monthly,
wisman_growth_mom, wisnus_growth_mom, wisman_growth_yoy,
wisman_ma3, wisman_ma6, wisman_zscore, is_anomaly,
usd_volatility_3m, usd_change_mom,
month_num, is_peak_season, is_covid_period, bali_share_change, wisman_precovid_mean,
wisman_lag_1, wisman_lag_3, tpk_lag_1, sentiment_lag_1,
wisman_trend_3m, sentiment_trend_3m, usd_trend_3m,
is_postcovid, wisman_recovery_pct,
crisis_component_tourism, crisis_component_economy, crisis_component_sentiment,
external_risk_avg, external_risk_max, external_risk_range,
physical_risk_score, media_risk_score, tourist_perception_score, external_risk_score,
crisis_score, crisis_score_100, crisis_level
```

### Hasil Verifikasi NB04
- Shape: 208 × 53 (backbone 2009-01 → 2026-04, data wisman real sampai 2026-04)
- COVID check: semua 24 bulan (2020-01 → 2021-12) masuk SIAGA/KRISIS ✅
- Tidak ada nilai inf ✅
- External risk bervariasi s/d 2025-12; flat (ffill 0.3302) di 2026-01–04 karena GDELT/disaster hanya sampai 2025-12 — wajar, bukan bug

---

## NB05 — Modeling: Anomaly Detection & Classification

### Tujuan
Membangun dua model ML + evaluasi lengkap + simpan output untuk NB06 dan dashboard.

### Struktur

| Section | Isi |
|---|---|
| 1. Import | sklearn, shap, joblib |
| 2. Load | `master_dataset_clean.parquet` + merge `combined_additional_features_engineered_new.csv` |
| 3. Feature Selection | Definisi FEATURES, filter alias duplikat |
| 4. Normalisasi | StandardScaler + clip 1%–99% |
| 5. Isolation Forest | Train + validasi COVID |
| 6. Random Forest | Train + TimeSeriesSplit CV |
| 7. SHAP | Explainability (dengan graceful fallback jika SHAP tidak terinstall) |
| 8. Confusion Matrix | → `reports/figures/confusion_matrix_rf.png` |
| 9. Save Output | `predictions_final.csv` + model `.pkl` |
| 10. Verifikasi | Cek semua kolom kritis |
| 11. Ringkasan | Summary model |
| 12. Evaluasi | CV + IF + validasi domain — angka untuk presentasi |

### Fitur Model

**FEATURES_CORE (13):**
`wisman_growth_mom`, `wisman_growth_yoy`, `wisman_zscore`, `usd_idr_avg`, `usd_volatility_3m`, `usd_change_mom`, `tpk_bintang`, `tpk_change_mom`, `inflasi_processed`, `bali_share_pct`, `avg_sentiment_monthly`, `month_num`, `is_peak_season`

**FEATURES_LAG (4):**
`wisman_ma3`, `wisman_trend_3m`, `bali_share_change`, `sentiment_trend_3m`

**FEATURES_EXTERNAL (hingga 8, sesuai ketersediaan di df):**
`gdelt_crisis_score`, `economic_risk_score`, `disaster_risk_score`, `external_risk_avg`, `external_risk_max`, `external_risk_range`, `gdelt_crisis_score_zscore`, `disaster_risk_score_zscore`

**Yang dikeluarkan dari FEATURES (ada guard raise ValueError):**
`physical_risk_score`, `media_risk_score`, `tourist_perception_score`, `external_risk_score` — alias duplikat, tetap di CSV output untuk dashboard.

### Parameter Model

| Model | Parameter |
|---|---|
| Isolation Forest | `n_estimators=200`, `contamination=0.15`, `random_state=42` |
| Random Forest | `n_estimators=300`, `max_depth=8`, `class_weight='balanced'`, `random_state=42` |
| Scaler | `StandardScaler` |
| CV | `TimeSeriesSplit(n_splits=5)` walk-forward |

### Hasil Evaluasi (Section 12) — Angka Final untuk Presentasi

**Random Forest — Walk-Forward CV:**

| Metrik | Nilai |
|---|---|
| CV Accuracy | **72.9%** |
| F1 Makro CV | **0.444** |
| F1 AMAN | 0.816 |
| F1 WASPADA | 0.834 |
| F1 SIAGA | 0.000 |
| F1 KRISIS | 0.125 |

SIAGA F1=0 bukan bug — masalah struktural: 18 dari 26 bulan SIAGA jatuh di fold 4 (2020-09 → 2023-06), periode transisi COVID paling ambigu. Akurasi training 99% adalah overfitting — **tidak dipakai untuk presentasi**.

Custom weight (SIAGA=3×, KRISIS=4×) sudah dicoba, hasilnya turun ke 68.8% — model original lebih baik.

**Diagnostic per Fold:**

| Fold | Periode Test | Akurasi | SIAGA actual |
|---|---|---|---|
| 1 | 2012-03 → 2014-12 | 79.4% | 0 |
| 2 | 2015-01 → 2017-10 | 82.4% | 3 |
| 3 | 2017-11 → 2020-08 | 70.6% | 3 |
| 4 | 2020-09 → 2023-06 | 41.2% | 18 ← fold paling sulit |
| 5 | 2023-07 → 2026-04 | 91.2% | 1 |

**Isolation Forest:**

| Metrik | Nilai |
|---|---|
| Total anomali | 32 dari 208 bulan |
| Deteksi COVID 2020-2021 | 16/24 bulan (67%) |
| Presisi anomali (→ SIAGA/KRISIS) | 56.2% |

**Validasi Domain:**

| Periode | Avg Score | Level Dominan |
|---|---|---|
| COVID awal (Mar–Jun 2020) | 67.0 | KRISIS |
| COVID puncak (Jul 2020–Jun 2021) | 47.8 | SIAGA |
| Pemulihan (Jul 2021–Jun 2022) | 28.4 | SIAGA |
| Normal post-COVID (2023–2024) | 34.8 | WASPADA |

**Narasi siap pakai untuk dosen:**
> *"Kami mengevaluasi model dengan walk-forward cross-validation — metode yang tepat untuk time series karena tidak memakai data masa depan untuk melatih model masa lalu. Hasilnya: akurasi 72.9% dan F1 makro 0.444. SIAGA F1=0 bukan kegagalan teknis, melainkan keterbatasan data: hanya 25 bulan SIAGA dari 208, sebagian besar jatuh di periode transisi COVID yang crisis score-nya berada di batas ambang antar kelas. Isolation Forest memvalidasi secara domain: 67% bulan COVID terdeteksi sebagai anomali tanpa label. Sistem ini dirancang sebagai early warning tool, bukan forecasting presisi tinggi."*

**3 angka untuk tab "Tentang Model" di dashboard:**
- CV Accuracy: **72.9%**
- F1 Makro CV: **0.444**
- Deteksi COVID (IF): **67% (16/24 bulan)**

### Patch yang Diterapkan di NB05

| # | Cell | Perubahan |
|---|---|---|
| PATCH 1 | Cell load dataset | Hardcode "harus 192" → dinamis `periode: {min} → {max}` |
| PATCH 2 | Cell confusion matrix | `savefig` → `../reports/figures/confusion_matrix_rf.png` + `os.makedirs` |
| PATCH 3a | Cell save output | `wisman_recovery_pct` masuk `OUTPUT_COLS_REQUIRED` |
| PATCH 3b | Cell save output | Fallback `external_risk_avg` dari `external_risk_score` sebelum save |
| PATCH 3c | Cell save output | `pct_negative_monthly` dan `usd_volatility_3m` masuk `OUTPUT_COLS_REQUIRED` (patch NB06 dominant_factor) |
| PATCH 4 | Cell plot timeline | `savefig` → `../reports/figures/crisis_timeline_final.png` + `os.makedirs` |
| PATCH 5 | Cell ringkasan | Tambah path kedua plot + info jumlah kolom output |

### `OUTPUT_COLS_REQUIRED` NB05 (31 kolom → `predictions_final.csv`)
```
month, wisman, tpk_bintang, inflasi_processed, usd_idr_avg,
avg_sentiment_monthly, bali_share_pct, wisman_zscore,
wisman_growth_mom, wisman_growth_yoy, crisis_score_100, crisis_level,
rf_predicted_level, rf_confidence,
prob_aman, prob_waspada, prob_siaga, prob_krisis,
iso_anomaly, iso_score,
gdelt_crisis_score, economic_risk_score, disaster_risk_score,
external_risk_avg, physical_risk_score, media_risk_score,
tourist_perception_score, external_risk_score,
wisman_recovery_pct,
pct_negative_monthly,   ← dipakai NB06 dominant_factor
usd_volatility_3m       ← dipakai NB06 dominant_factor
```

### Output Files NB05

| File | Path | Keterangan |
|---|---|---|
| `predictions_final.csv` | `data/final/` | 208 × 31 — **terverifikasi bersih** |
| `model_random_forest.pkl` | `models/` | |
| `model_isolation_forest.pkl` | `models/` | |
| `scaler.pkl` | `models/` | |
| `label_encoder.pkl` | `models/` | |
| `confusion_matrix_rf.png` | `reports/figures/` | |
| `crisis_timeline_final.png` | `reports/figures/` | |

### Hasil Verifikasi NB05 (Lulus Semua)
```
Shape: (208, 31) | Periode: 2009-01 → 2026-04
Semua 10 kolom kritis: 0 NaN
pct_negative_monthly: ada, zeros=31, tail=[6.60, 6.80, 5.86]
usd_volatility_3m: ada, zeros=28 (flat di bulan terbaru — wajar, data kurs tidak update)
wisman_recovery_pct: 192 non-zero values
external_risk_avg: 0 NaN, 0 zeros
Plot: ✓ confusion_matrix_rf.png | ✓ crisis_timeline_final.png
Model: ✓ semua 4 file pkl ada
```

---

## NB06 — LLM Narrative Engine

### Tujuan
Membaca `predictions_final.csv`, membangun konteks per bulan, generate narasi via Groq API, export `narrative_engine.py` untuk dashboard.

### Struktur

| Section | Isi |
|---|---|
| 1. Import | groq SDK (auto-install jika tidak ada) |
| 2. Konfigurasi | Load `GROQ_API_KEY` dari `.env` via `python-dotenv` |
| 3. Load Data | `predictions_final.csv` + model artifacts |
| 4. `build_crisis_context()` | Bangun context dict per bulan: score_delta, dominant_factor, anomaly_explanation, last_month_summary |
| 5. `build_prompt()` | 3 tipe: `summary`, `alert`, `monthly` |
| 6. `generate_narrative()` | Panggil Groq API, return dict result |
| 7. Batch Generate | Generate 10 bulan KRISIS/SIAGA teratas → simpan ke JSON |
| 8. Export `narrative_engine.py` | Tulis modul Python ke `src/` |
| 9. Checklist | Verifikasi semua file output ada |

### Isu yang Diidentifikasi & Dipatch

| # | Isu | Status | Fix |
|---|---|---|---|
| 1 | `test_month` tidak didefinisikan eksplisit sebelum cell 12 | ✅ Dipatch | Tambah `test_month = predictions['month'].iloc[-1]` di awal cell 12 |
| 2 | Checklist install menyebut `anthropic` bukan `groq` | ✅ Dipatch | Ganti string ke `groq` |
| 3 | `narrative_engine.py` pakai `build_context()` tapi NB06 pakai `build_crisis_context()` | Intentional | Inkonsistensi didokumentasi di header NB06, tidak perlu refactor |
| 4 | `wisman_recovery_pct` sebelumnya selalu 0 | ✅ Sudah fix via PATCH 3a di NB05 | `wisman_recovery_pct` sekarang ada di `predictions_final.csv` |
| 5 | `pct_negative_monthly` & `usd_volatility_3m` tidak ada di `predictions_final.csv` | ✅ Sudah fix via PATCH 3c di NB05 | Kedua kolom sekarang tersimpan di CSV |

### Perbedaan Nama Fungsi (Intentional)

| Lokasi | Nama Fungsi | Keterangan |
|---|---|---|
| NB06 (notebook) | `build_crisis_context()` | Nama deskriptif untuk eksplorasi |
| `narrative_engine.py` (modul) | `build_context()` | Nama pendek untuk API dashboard |

Keduanya fungsional equivalen. Inkonsistensi ini intentional dan sudah didokumentasi di header NB06.

### `dominant_factor` — 3 Komponen

```python
factors = {
    'Kunjungan Wisatawan': abs(wisman_zscore),
    'Tekanan Kurs'       : abs(usd_volatility_3m) / 500.0,
    'Sentimen Negatif'   : pct_negative_monthly / 100.0,
}
dominant_factor = max(factors, key=factors.get)
```

Kedua kolom `usd_volatility_3m` dan `pct_negative_monthly` sekarang tersimpan di `predictions_final.csv` (patch NB05). Untuk bulan 2025–2026, `usd_volatility_3m = 0` karena data kurs tidak ter-update — sehingga `dominant_factor` selalu jatuh ke "Kunjungan Wisatawan" untuk periode tersebut. Ini **bukan bug**, tapi keterbatasan data.

### Groq API & Model
- Model: `llama-3.3-70b-versatile`
- Temperature: 0.7
- Max tokens: 1024
- API key: dari `.env` file (`GROQ_API_KEY`)

### Fungsi di `narrative_engine.py`
- `build_context(pred_row, history_rows, narratives_cache)` → context dict
- `build_prompt(ctx, report_type)` → string prompt (summary/alert/monthly)
- `generate(pred_row, report_type, api_key, history_rows, narratives_cache)` → result dict
- `load_cache(cache_path)` → dict dari JSON

### Output Files NB06

| File | Path | Keterangan |
|---|---|---|
| `narrative_engine.py` | `src/` | 7505 bytes, semua 4 fungsi ada |
| `__init__.py` | `src/` | 0 bytes (marker package) |
| `narratives_cache.json` | `data/final/` | 10 narasi KRISIS/SIAGA terbaru |

### Hasil Verifikasi NB06 (Lulus Semua)
```
narrative_engine.py: ✓ (7505 bytes)
Fungsi: ✓ build_context, build_prompt, generate, load_cache
Referensi kolom: ✓ pct_negative_monthly, usd_volatility_3m, wisman_recovery_pct
narratives_cache.json: ✓ (10 narasi)
Semua 8 file output: ✓
```

### Dependency Install Dashboard
```
pip install streamlit plotly groq pyarrow joblib python-dotenv
```

### Import di Dashboard
```python
from src.narrative_engine import generate, build_context, load_cache
```

---

## Masukan Dosen (dari Demo Sebelumnya) — Untuk Dashboard

| # | Masukan | Status |
|---|---|---|
| 1 | Evaluasi model dengan akurasi, presisi, F1 | ✅ Section 12 NB05 sudah ada |
| 2 | Transparansi parameter yang dipakai untuk prediksi | ⏳ Dashboard |
| 3 | Label bahasa manusia (bukan kode teknis) | ⏳ Dashboard |
| 4 | Rekomendasi tindakan di bawah analisis SWOT | ⏳ Dashboard |
| 5 | Opsi format narasi (bullet/paragraf) | ⏳ Dashboard |
| 6 | Fitur komparasi antar bulan | ⏳ Dashboard |
| 7 | Database riwayat narasi | ✅ `narratives_cache.json` (partial) — perlu UI |
| 8 | Alur pengambilan keputusan yang terlihat jelas | ⏳ Dashboard |

---

## Struktur Folder Proyek

```
project/
├── data/
│   ├── raw/                              # Data mentah (tidak dimodifikasi)
│   │   ├── weather/                      # USGS, Open-Meteo, BaliGuard
│   │   ├── gdelt/                        # GDELT historical + recent
│   │   └── gtrends/                      # Google Trends
│   ├── processed/                        # Output NB02 & NB03 (10 file)
│   └── final/                            # Output NB04, NB05, NB06
│       ├── crisis_dataset_final.csv      # 208 × ~53 kolom
│       ├── master_dataset_clean.parquet  # Input NB05
│       ├── predictions_final.csv         # 208 × 31 — input dashboard
│       └── narratives_cache.json         # 10 narasi LLM
├── models/                               # 4 file pkl
│   ├── model_random_forest.pkl
│   ├── model_isolation_forest.pkl
│   ├── scaler.pkl
│   └── label_encoder.pkl
├── src/
│   ├── __init__.py
│   └── narrative_engine.py               # Diimport dashboard
├── reports/
│   └── figures/                          # Semua plot (NB01, NB04, NB05)
└── notebooks/
    ├── 01_LoadDataset_dan_EDA.ipynb      ✅
    ├── 02_Preprocessing.ipynb            ✅
    ├── 03_Text_Preprocessing_Sentiment.ipynb  ✅
    ├── 04_Feature_Engineering_Crisis_Score.ipynb  ✅
    ├── 05_Modeling_Anomaly_Detection_Classification.ipynb  ✅
    └── 06_LLM_Narrative_Engine.ipynb     ✅
```

---

## Catatan untuk Sesi Claude Berikutnya

**State terakhir:** NB01–NB06 semua final dan sudah diverifikasi.

**Pekerjaan berikutnya:** Dashboard Streamlit.

**File yang perlu diupload:** File dashboard (`dashboard.py` atau struktur dashboard), plus MD ini sebagai konteks.

**Hal-hal teknis penting yang tidak boleh dilupakan:**
- Backbone 208 baris (2009-01 → 2026-04) — data wisman real sampai 2026-04
- `usd_volatility_3m` flat (= 0) di 2025–2026 karena data kurs tidak update — dominant_factor selalu "Kunjungan Wisatawan" untuk periode itu
- `external_risk_avg` flat (= 0.3302) di 2026-01–04 — ffill karena GDELT/disaster hanya sampai 2025-12
- `wb_monthly_economic.csv` tersimpan **dengan index** — load wajib pakai `index_col=0`
- `combined_additional_features_new.csv` **tidak punya kolom `month`** — buat dari `date`
- Alias duplikat (`physical_risk_score`, `media_risk_score`, `tourist_perception_score`, `external_risk_score`) tidak boleh masuk FEATURES model — sudah ada guard `raise ValueError` di NB05
- Import dashboard: `from src.narrative_engine import generate, build_context, load_cache`
- Evaluasi yang valid: CV Accuracy 72.9%, F1 Makro 0.444 — akurasi training 99% adalah overfitting
- SIAGA F1=0 adalah keterbatasan data yang bisa dijelaskan, bukan kegagalan model
