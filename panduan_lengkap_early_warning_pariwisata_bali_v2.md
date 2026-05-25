# 🏝️ Panduan Lengkap Proyek Akhir
## Multimodal Early Warning System Krisis Pariwisata Bali
### Berbasis Analisis Sentimen Multibahasa, LLM Narrative Engine & ML Modeling

> **Versi:** 2.0 — diperbarui setelah NB01–NB04 selesai, NB05 dalam pengerjaan  
> **Status pipeline:** NB01 ✅ · NB02 ✅ · NB03 ✅ · NB04 ✅ · NB05 🔧

---

## 📋 Daftar Isi
1. [Gambaran Besar Proyek](#1-gambaran-besar-proyek)
2. [Arsitektur Sistem — 5 Layer](#2-arsitektur-sistem--5-layer)
3. [Dataset Lengkap (14 File)](#3-dataset-lengkap-14-file)
4. [Pipeline Notebook End-to-End](#4-pipeline-notebook-end-to-end)
5. [Feature Engineering](#5-feature-engineering)
6. [Crisis Score — Formula & Bobot](#6-crisis-score--formula--bobot)
7. [NB05 — ML Modeling & Explainability](#7-nb05--ml-modeling--explainability)
8. [Peran LLM & Transformer](#8-peran-llm--transformer)
9. [Tech Stack & Tools](#9-tech-stack--tools)
10. [Timeline Pengerjaan](#10-timeline-pengerjaan)
11. [Tips Asistensi ke Dosen](#11-tips-asistensi-ke-dosen)

---

## 1. 🎯 Gambaran Besar Proyek

### Definisi Singkat
Sistem dashboard cerdas yang **secara otomatis mendeteksi potensi krisis pariwisata Bali** dengan menggabungkan empat sumber data sekaligus — ulasan wisatawan multibahasa, data ekonomi, statistik hotel, dan posisi Bali di pasar nasional — kemudian menghasilkan **sinyal early warning**, **laporan naratif otomatis**, dan **prediksi level krisis** menggunakan ML.

### Checklist Penilaian Dosen
| Kriteria | Pemenuhan |
|---|---|
| Ada analisis sains, bukan sekadar grafik | ✅ Anomaly detection + Sentiment scoring + Decision engine + SHAP explainability |
| Multi-metode | ✅ Transformer (XLM-RoBERTa) + Isolation Forest + Random Forest + Weighted scoring |
| Ada LLM / Transformer | ✅ XLM-RoBERTa sebagai sentimen, LLM sebagai Narrative Engine |
| Feature engineering jelas | ✅ 24 fitur terstruktur: growth rate, z-score, rolling window, embedding, share market |
| Dashboard powerful | ✅ Early warning signal + laporan naratif + prediksi RF + SHAP feature importance |

### Kontribusi Unik
> *"Sistem kami tidak hanya memprediksi krisis — tapi juga **menjelaskan dalam narasi** mengapa potensi krisis pariwisata sedang terjadi, menggunakan LLM yang membaca data dari tiga bahasa sekaligus, diperkuat dengan visualisasi SHAP yang menunjukkan fitur mana yang paling berkontribusi terhadap level krisis."*

---

## 2. 🏗️ Arsitektur Sistem — 5 Layer

```
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — SUMBER DATA (4 Modalitas, 14 Dataset)                    │
│  [Hotel Reviews / merged_all_hotels]  [BPS Wisman & Wisnus]         │
│  [Kurs USD/IDR]  [TPK & Lama Menginap Hotel]  [Inflasi Bali]        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  LAYER 2 — INGESTION PIPELINE                                        │
│  [Web scraper / read_excel / read_csv]                               │
│  → Normalisasi format wide→long, timestamp alignment, Excel fix      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  LAYER 3 — PROCESSING LAYER (Inti Analisis)                         │
│  [XLM-RoBERTa Sentiment]  [Z-score Anomaly]  [Feature Engineering]  │
│  → 24 fitur terstruktur, monthly aggregation, crisis components      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  LAYER 4 — DECISION ENGINE                                           │
│  [Weighted Crisis Score]  [Isolation Forest]  [Random Forest]       │
│  [SHAP Explainability]   [LLM Narrative Engine]                     │
│  → Crisis Score 0–100, label 4 kelas, laporan naratif otomatis      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  LAYER 5 — DASHBOARD OUTPUT (Streamlit)                             │
│  [Gauge: Crisis Score]  [Timeline + Anomali]  [SHAP Chart]          │
│  [Laporan Naratif LLM]  [Rekomendasi Kebijakan]                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. 📦 Dataset Lengkap (14 File)

### Kelompok A — Data Kunjungan Wisatawan (BPS Bali)

| # | File | Isi | Rentang | Dipakai di |
|---|---|---|---|---|
| 1 | `Gab_Data_Wisman_Bali.xlsx` | Wisman bulanan gabungan Bali | 2009–2025 | NB01, NB02, NB04 |
| 2 | `banyaknya-wisatawan-mancanegara-bulanan-ke-bali.xls` | Wisman bulanan historis (format wide BPS) | 1982–2008 | NB01 |
| 3 | `banyaknya-wisatawan-mancanegara-ke-bali-dan-indonesia.xls` | Wisman Bali vs Indonesia tahunan + growth% | 1969–2025 | NB01, NB02, NB04 |
| 4 | `-banyaknya-wisatawan-mancanegara-yang-datang-langsung-ke-bali-menurut-kebangsaan-2019-2024.xlsx` | Wisman per kebangsaan | 2019–2024 | NB01 |
| 5 | `banyaknya-wisatawan-domestik-bulanan-ke-bali.xls` | Wisnus (domestik) bulanan (format wide BPS) | 2004–2025 | NB01, NB02, NB04 |

### Kelompok B — Data Hotel & Akomodasi (BPS Bali)

| # | File | Isi | Dipakai di |
|---|---|---|---|
| 6 | `Tingkat_Penghunian_Kamar__TPK__Hotel_Bintang.xlsx` | TPK hotel bintang per kelas | NB01, NB02, NB04 |
| 7 | `Tingkat_Penghunian_Kamar__TPK_.xlsx` | TPK hotel non-bintang | NB01, NB02, NB04 |
| 8 | `Rata-Rata_Lama_Menginap_Tamu_Asing_dan_Domestik_pada_Hotel_Bintang.xlsx` | Lama menginap (hotel bintang) | NB01, NB02 |
| 9 | `Rata-Rata_Lama_Menginap_Tamu_Asing_dan_Domestik_pada_Hotel_Non_Bintang.xlsx` | Lama menginap (hotel non-bintang) | NB01, NB02 |

### Kelompok C — Data Ekonomi

| # | File | Isi | Rentang | Dipakai di |
|---|---|---|---|---|
| 10 | `Inflasi_Bulanan.xlsx` | Inflasi bulanan kota-kota Bali | 2024 | NB01, NB02, NB04 |
| 11 | `USD_IDR_Historical_Data.csv` | Kurs USD/IDR harian | 2010–2024 | NB01, NB02, NB04 |
| 12 | `daily_forex_rates.csv` | Kurs multi-mata uang harian (filter IDR) | 2004–2024 | NB01 |

### Kelompok D — Data Sentimen (NLP)

| # | File | Isi | Baris | Dipakai di |
|---|---|---|---|---|
| 13 | `merged_all_hotels.xlsx` | Review hotel Bali dengan tanggal, lokasi, rating | 29.332 | NB01, NB03 |
| 14 | `Dataset_of_Digital_Reviews_in_Tourism_-_2.csv` | Review digital wisata (tanpa tanggal) | ~2.000 | NB01, NB03 |

> **Catatan NB03:** `merged_all_hotels.xlsx` menggantikan `Bali_Hotel_Review.csv`. Dataset ini memiliki kolom `date` (`datetime64`) yang memungkinkan agregasi sentimen per bulan — menyelesaikan masalah *static sentiment* di versi sebelumnya.

---

## 4. 🔄 Pipeline Notebook End-to-End

### Alur Data Antar Notebook

```
NB01 (EDA)
  └─ data/raw/* (14 dataset)
       │
NB02 (Preprocessing Time Series)
  └─ data/processed/
       ├── wisman_clean.csv
       ├── wisnus_clean.csv
       ├── monthly_usd.csv
       ├── tpk_clean.csv           ← tpk_bintang + tpk_non_bintang
       ├── inflasi_clean.csv
       └── wisman_vs_indonesia_clean.csv   ← 14th dataset
       │
NB03 (Text Preprocessing & Sentiment)
  └─ data/processed/
       ├── monthly_sentiment.csv   ← sentimen per bulan (bervariasi!)
       ├── sentiment_stats.csv     ← fallback global
       └── all_reviews_sentiment.csv
       │
NB04 (Merge, Feature Engineering & Crisis Score)
  └─ data/final/
       ├── crisis_dataset_final.csv    ← 192 baris, 31 kolom
       └── master_dataset_clean.parquet  ← input NB05
       │
NB05 (ML Modeling & Explainability)  ← SEDANG DIKERJAKAN
  └─ models/
       ├── isolation_forest_model.pkl
       ├── random_forest_model.pkl
       └── predictions_with_shap.csv
```

---

### NB01 — Load & EDA
**Tujuan:** Setup project, load 14 dataset, eksplorasi awal.

**Yang dilakukan:**
- Setup folder `data/raw`, `data/processed`, `data/final`, `models/`
- Load 14 dataset dengan parameter yang tepat (`xlrd` untuk `.xls`, `parse_dates` untuk Excel dengan datetime)
- EDA: shape, kolom, tipe data, preview
- Visualisasi tren wisman gabungan 2009–2025 dengan highlight COVID

**Output:** Insight awal, plot `eda_wisman_trend.png`

---

### NB02 — Preprocessing Time Series
**Tujuan:** Konversi semua data numerik ke format bulanan yang bersih.

**Yang dilakukan:**
- **Wisman gabungan** → rename, convert datetime, simpan `wisman_clean.csv`
- **Wisnus BPS** → melt format wide→long, mapping nama bulan, simpan `wisnus_clean.csv`
- **Kurs USD/IDR** → hapus koma (format `16,090.00`), agregasi harian→bulanan, simpan `monthly_usd.csv`
- **TPK hotel** → ekstrak bintang & non-bintang, rata-ratakan per bulan, simpan `tpk_clean.csv`
- **Inflasi** → rata-ratakan semua kota Bali per bulan, simpan `inflasi_clean.csv`
- **Wisman Bali vs Indonesia** → ekstrak tabel tahunan, hitung `bali_share_pct`, simpan `wisman_vs_indonesia_clean.csv`

**Output:** 6 file CSV bersih di `data/processed/`

---

### NB03 — Text Preprocessing & Sentiment
**Tujuan:** Analisis sentimen multibahasa dari ulasan wisatawan.

**Yang dilakukan:**
- Load `merged_all_hotels.xlsx` (29.332 baris, kolom `date` sudah `datetime64`)
- Load `Dataset_of_Digital_Reviews_in_Tourism_-_2.csv` (tanpa tanggal → `date = NaT`)
- Gabung kedua sumber, tambahkan kolom `source`
- **Text cleaning** yang aman untuk multibahasa: pertahankan karakter Unicode Mandarin (`\u4e00–\u9fff`), hapus URL, HTML, spasi berlebih
- **Deteksi bahasa** otomatis dengan `langdetect`
- **Sentiment analysis** dengan `cardiffnlp/twitter-xlm-roberta-base-sentiment` (batch processing, support EN/ID/ZH)
- **Defensive date parse** — konversi otomatis jika tanggal terbaca sebagai Excel serial number
- **Agregasi bulanan** → `monthly_sentiment.csv` dengan kolom: `avg_sentiment`, `pct_positive`, `pct_negative`, `pct_neutral`, `review_count`, `avg_rating`

**Output:** `monthly_sentiment.csv`, `sentiment_stats.csv`, `all_reviews_sentiment.csv`

> ⚠️ **Perubahan penting dari versi lama:** Sentimen sekarang **bervariasi per bulan** (bukan nilai konstan), sehingga `crisis_component_sentiment` di NB04 menjadi fitur yang bermakna secara temporal.

---

### NB04 — Merge, Feature Engineering & Crisis Score
**Tujuan:** Gabungkan semua data processed, bangun fitur, hitung Crisis Score.

**Backbone timeline:** `wisman_clean.csv` — 192 bulan (Januari 2009 – Desember 2024)

**Merge yang dilakukan:**
| Dataset | Join key | Coverage |
|---|---|---|
| wisnus | month | 192/192 |
| monthly_usd | month | 192/192 |
| tpk (bintang + non-bintang) | month | 192/192 |
| inflasi | month | 192/192 |
| wisman_vs_indonesia | tahun | 192/192 |
| monthly_sentiment | month | ~170 (sisanya fallback global) |

**Handle missing:** `ffill().bfill()` untuk kurs & TPK, `interpolate(linear)` untuk wisnus.

**Output:** `crisis_dataset_final.csv` + `master_dataset_clean.parquet` — 192 baris, 31 kolom

---

## 5. ⚙️ Feature Engineering

Master dataset (`master_dataset_clean.parquet`) memiliki **24 fitur input** yang terbagi dalam 5 kelompok:

### Kelompok 1 — Kunjungan Wisatawan (Raw)
| Fitur | Deskripsi |
|---|---|
| `wisman` | Jumlah wisatawan mancanegara per bulan |
| `wisnus` | Jumlah wisatawan domestik per bulan |
| `indonesia_total` | Total wisman nasional (data tahunan, di-join per bulan) |
| `bali_share_pct` | Persentase Bali dari total wisman nasional |

### Kelompok 2 — Fitur Temporal Kunjungan (Engineered)
| Fitur | Formula | Interpretasi |
|---|---|---|
| `wisman_growth_mom` | `wisman.pct_change()` | Pertumbuhan bulan ke bulan |
| `wisman_growth_yoy` | `wisman.pct_change(periods=12)` | Pertumbuhan year-over-year |
| `wisman_ma3` | `wisman.rolling(3).mean()` | Rata-rata bergerak 3 bulan |
| `wisman_ma6` | `wisman.rolling(6).mean()` | Rata-rata bergerak 6 bulan |
| `wisman_zscore` | `(x - μ₁₂) / σ₁₂` | Anomali dalam satuan standar deviasi |
| `is_anomaly` | `zscore < -2.0` → 1 | Flag anomali penurunan ekstrem |
| `bali_share_change` | `bali_share_pct.pct_change()` | Perubahan posisi Bali di pasar nasional |

### Kelompok 3 — Kondisi Hotel (Engineered)
| Fitur | Deskripsi |
|---|---|
| `tpk_bintang` | Tingkat hunian hotel bintang (%) |
| `tpk_non_bintang` | Tingkat hunian hotel non-bintang (%) |
| `tpk_change_mom` | Perubahan TPK bulan ke bulan |
| `tpk_ma3` | Rolling average 3 bulan untuk TPK |

### Kelompok 4 — Kondisi Ekonomi (Engineered)
| Fitur | Deskripsi |
|---|---|
| `usd_idr_avg` | Rata-rata kurs USD/IDR per bulan |
| `usd_volatility_3m` | Rolling std 3 bulan kurs USD/IDR |
| `usd_change_mom` | Perubahan kurs bulan ke bulan |
| `inflasi_processed` | Rata-rata inflasi kota-kota Bali |

### Kelompok 5 — Sentimen & Konteks (Engineered)
| Fitur | Deskripsi |
|---|---|
| `avg_sentiment_monthly` | Rata-rata skor sentimen ulasan per bulan (-1 s.d. 1) |
| `pct_negative_monthly` | Persentase ulasan negatif per bulan (%) |
| `month_num` | Nomor bulan (1–12) — komponen musiman |
| `is_peak_season` | 1 jika Juli/Agustus/Desember |
| `is_covid_period` | 1 jika Maret 2020 – Desember 2021 |

---

### Cara Menjelaskan Feature Engineering ke Dosen
> *"Pak, kami membangun tiga jenis fitur:*
> 1. ***Embedding fitur** dari teks ulasan menggunakan XLM-RoBERTa (diagregasi menjadi skor bulanan)*
> 2. ***Temporal fitur** dari time series kunjungan: rolling window, growth rate MoM/YoY, dan Z-score anomali*
> 3. ***Cross-modal fitur**: Bali share index (posisi Bali di pasar nasional), korelasi sentimen–kunjungan, dan volatilitas kurs"*

---

## 6. 📊 Crisis Score — Formula & Bobot

```
Crisis Score = (0.45 × S_kunjungan) + (0.30 × S_ekonomi) + (0.25 × S_sentimen)
```

### Komponen Detail

**S_kunjungan (bobot 45%)** — dari data wisman
```python
# 60% dari growth MoM yang diinversi (growth turun = krisis naik)
# 40% dari Z-score anomali (makin negatif = makin krisis)
S_kunjungan = (1 - growth_mom_norm) * 0.6 + zscore_component * 0.4
```

**S_ekonomi (bobot 30%)** — dari kurs USD/IDR
```python
# 50% volatilitas kurs 3 bulan + 50% perubahan kurs MoM
S_ekonomi = usd_volatility_3m_norm * 0.5 + usd_change_mom_norm * 0.5
```

**S_sentimen (bobot 25%)** — dari ulasan wisatawan
```python
# Langsung dari pct_negative_monthly (bervariasi per bulan)
S_sentimen = pct_negative_monthly / 100
```

### Level Krisis

| Level | Threshold | Emoji | Jumlah Bulan (2009–2024) |
|---|---|---|---|
| AMAN | CS < 30 | 🟢 | 7 bulan (3.6%) |
| WASPADA | 30 ≤ CS < 50 | 🟡 | 147 bulan (76.6%) |
| SIAGA | 50 ≤ CS < 70 | 🟠 | 33 bulan (17.2%) |
| KRISIS | CS ≥ 70 | 🔴 | 5 bulan (2.6%) |

> **Validasi:** 22 bulan periode COVID-19 (Mar 2020–Des 2021) → 18 bulan SIAGA + 4 bulan KRISIS ✅ — membuktikan crisis score sensitif terhadap gangguan nyata.

---

## 7. 🤖 NB05 — ML Modeling & Explainability

### Input
`master_dataset_clean.parquet` — 192 baris × 31 kolom (sudah bersih, siap pakai)

### Alur NB05

```
STEP 1 — Load & Preprocessing
├── Load parquet
├── Pilih 10–12 fitur utama (drop: crisis_component_*, crisis_score, is_covid_period)
├── Dropna
└── TimeSeriesSplit(n_splits=5) — bukan random split!

STEP 2 — Isolation Forest (Unsupervised)
├── Fit pada seluruh data (unsupervised, tidak perlu label)
├── Output: anomaly_score per bulan
└── Validasi: cocokkan anomali dengan periode COVID → visualisasi

STEP 3 — Random Forest Classifier (Supervised)
├── Target: crisis_level (4 kelas: AMAN/WASPADA/SIAGA/KRISIS)
├── Handle imbalance: class_weight='balanced'
├── Evaluasi: classification_report + confusion matrix
└── Simpan model: random_forest_model.pkl

STEP 4 — SHAP Explainability
├── Hitung SHAP values untuk RF model
├── Beeswarm plot — global feature importance
├── Waterfall plot — penjelasan per prediksi
└── Simpan SHAP values ke CSV

STEP 5 — Simpan Output
├── random_forest_model.pkl     ← dimuat dashboard Streamlit
├── isolation_forest_model.pkl  ← dimuat dashboard Streamlit
└── predictions_with_shap.csv   ← data prediksi + SHAP untuk dashboard
```

### Fitur yang Direkomendasikan untuk NB05 (10–12 fitur)

```python
SELECTED_FEATURES = [
    # Kunjungan (paling penting)
    'wisman_growth_mom',
    'wisman_growth_yoy',
    'wisman_zscore',
    # Hotel
    'tpk_bintang',
    'tpk_change_mom',
    # Ekonomi
    'usd_idr_avg',
    'usd_volatility_3m',
    # Sentimen
    'avg_sentiment_monthly',
    'pct_negative_monthly',
    # Konteks
    'bali_share_pct',
    'month_num',
    'is_peak_season',
]
```

### Catatan Penting NB05

**Class imbalance** — distribusi crisis_level tidak seimbang:
```
WASPADA : 147  (76.6%)  ← mayoritas
SIAGA   :  33  (17.2%)
AMAN    :   7   (3.6%)
KRISIS  :   5   (2.6%)  ← sangat sedikit
```
→ Gunakan `class_weight='balanced'` pada Random Forest  
→ Evaluasi dengan **macro F1-score**, bukan accuracy (accuracy bisa misleading)

**TimeSeriesSplit** — wajib digunakan, bukan `train_test_split(random_state=42)`, karena data bersifat time series dan memiliki temporal dependency.

---

## 8. 🤖 Peran LLM & Transformer

### Transformer — XLM-RoBERTa (Layer Pemrosesan)
- **Model:** `cardiffnlp/twitter-xlm-roberta-base-sentiment`
- **Peran:** Mengkonversi teks ulasan wisatawan (EN/ID/ZH) menjadi skor sentimen bulanan
- **Cara kerja:** Batch inference → skor -1 s.d. 1 per ulasan → agregasi ke `monthly_sentiment.csv`
- **Hasil:** `avg_sentiment_monthly` dan `pct_negative_monthly` yang bervariasi per bulan

### LLM — Narrative Engine (Layer Decision)
- **Model:** Claude API / Groq (Llama 3) / Ollama (lokal)
- **Peran:** Menerima semua output model dan menghasilkan laporan naratif analisis krisis
- **Output:** Paragraf laporan + daftar rekomendasi kebijakan dalam Bahasa Indonesia

```python
SYSTEM_PROMPT = """
Kamu adalah analis sistem pariwisata Bali. Berdasarkan data yang diberikan,
tulis laporan naratif singkat (3–4 paragraf) yang menjelaskan kondisi pariwisata
Bali saat ini, faktor-faktor yang mempengaruhinya, dan rekomendasi kebijakan.
Gunakan bahasa formal yang mudah dipahami pemangku kebijakan.
"""

USER_PROMPT = f"""
Data terkini (periode: {periode}):
- Crisis Score   : {crisis_score}/100 (Level: {crisis_level})
- Sentimen ulasan: avg={avg_sentiment:.2f}, negatif={pct_negative:.1f}%
- Tren kunjungan : growth MoM={wisman_growth_mom:.1%}, YoY={wisman_growth_yoy:.1%}
- Z-score anomali: {wisman_zscore:.2f} {'⚠️ ANOMALI' if is_anomaly else ''}
- Kurs USD/IDR  : {usd_idr_avg:.0f} (volatilitas {usd_volatility_3m:.0f})
- SHAP top fitur: {top_shap_features}

Hasilkan laporan naratif analisis krisis pariwisata.
"""
```

### Diagram Peran Keduanya
```
Teks Ulasan ──→ [XLM-RoBERTa]  ──→ Skor Sentimen Bulanan
                                             │
Time Series  ──→ [Z-score / rolling] ──→ Fitur Temporal
                                             │
Data Kurs    ──→ [Volatility calc]   ──→ Indeks Tekanan
                                             │
                                  [Random Forest + SHAP]
                                             │
                              Crisis Score + Feature Importance
                                             │
                                  [LLM Narrative Engine]
                                             │
                                    Laporan Naratif 📄
```

---

## 9. 🛠️ Tech Stack & Tools

### Core ML / NLP
| Library | Versi | Kegunaan |
|---|---|---|
| `transformers` | ≥4.35 | XLM-RoBERTa sentiment |
| `torch` | ≥2.0 | PyTorch backend |
| `scikit-learn` | ≥1.3 | Isolation Forest, Random Forest, TimeSeriesSplit |
| `shap` | ≥0.44 | Feature importance + explainability |
| `langdetect` | latest | Deteksi bahasa otomatis |

### Data Processing
| Library | Kegunaan |
|---|---|
| `pandas` | Manipulasi tabular, melt, merge |
| `numpy` | Operasi numerik |
| `openpyxl` | Baca `.xlsx` |
| `xlrd` | Baca `.xls` (format lama BPS) |
| `pyarrow` | Baca/tulis `.parquet` |

### Visualisasi & Dashboard
| Tool | Kegunaan |
|---|---|
| `matplotlib` / `seaborn` | Plot statis (EDA, heatmap) |
| `plotly` | Chart interaktif di Streamlit |
| **Streamlit** | ⭐ Framework dashboard utama |

### LLM API (pilih salah satu)
| Opsi | Keterangan |
|---|---|
| **Groq API** | ⭐ Gratis, cepat (Llama 3 70B) — `console.groq.com` |
| Anthropic Claude | Kualitas tinggi, perlu kredit — `api.anthropic.com` |
| Ollama (lokal) | Gratis tapi berat — `ollama.ai` |

### Install Sekaligus
```bash
pip install pandas numpy matplotlib seaborn plotly openpyxl xlrd pyarrow
pip install transformers torch sentencepiece langdetect
pip install scikit-learn shap streamlit
```

---

## 10. 📅 Timeline Pengerjaan

| Tahap | Notebook | Status | Output |
|---|---|---|---|
| Load & EDA | NB01 | ✅ Selesai | 14 dataset ter-load, EDA awal |
| Preprocessing Time Series | NB02 | ✅ Selesai | 6 CSV bersih di `data/processed/` |
| Text & Sentiment | NB03 | ✅ Selesai | `monthly_sentiment.csv` |
| Merge & Feature Engineering | NB04 | ✅ Selesai | `master_dataset_clean.parquet` (192 baris, 31 kolom) |
| ML Modeling & Explainability | NB05 | 🔧 Dalam pengerjaan | Model `.pkl` + SHAP output |
| Dashboard Streamlit | - | ⏳ Berikutnya | Dashboard interaktif |
| LLM Integration | - | ⏳ Berikutnya | Narrative engine |
| Demo & Polish | - | ⏳ Berikutnya | Siap presentasi |

---

## 11. 💡 Tips Asistensi ke Dosen

### Kalimat Pembuka yang Kuat
> *"Pak/Bu, proyek kami adalah sistem **Early Warning Krisis Pariwisata Bali** berbasis data multimodal. Yang kami jadikan highlight adalah tiga hal: pertama, **XLM-RoBERTa** untuk analisis sentimen ulasan wisatawan dalam tiga bahasa secara bulanan; kedua, **Random Forest + SHAP** yang tidak hanya memprediksi level krisis tapi juga menjelaskan fitur mana yang paling berpengaruh; dan ketiga, **LLM sebagai Narrative Engine** yang mengubah semua output model menjadi laporan naratif otomatis dalam Bahasa Indonesia."*

### Jelaskan Feature Engineering
> *"Feature engineering kami terdiri dari empat lapisan:*
> 1. *Embedding teks dari XLM-RoBERTa, diagregasi menjadi skor sentimen bulanan*
> 2. *Temporal fitur dari time series kunjungan: growth MoM/YoY, rolling window, dan Z-score anomali*
> 3. *Fitur posisi pasar: Bali share index (Bali vs total wisman nasional)*
> 4. *Crisis Score komposit berbobot yang menggabungkan tiga dimensi: kunjungan (45%), ekonomi (30%), sentimen (25%)"*

### Antisipasi Pertanyaan Dosen
| Pertanyaan | Jawaban Siap |
|---|---|
| "Di mana peran LLM-nya?" | "LLM berperan di layer akhir sebagai Narrative Engine. Ia menerima Crisis Score, SHAP feature importance, dan statistik sentimen, lalu menghasilkan laporan analisis dalam Bahasa Indonesia yang bisa dibaca pemangku kebijakan langsung." |
| "Apa bedanya dengan dashboard biasa?" | "Dashboard biasa hanya menampilkan data. Sistem kami menambahkan empat layer analisis sains: sentiment transformer, anomaly detection, supervised classification, dan generative AI untuk narasi." |
| "Kenapa pilih Bali?" | "Bali memiliki data pariwisata terpublikasi lengkap dari BPS, komunitas wisatawan multibahasa yang aktif menulis ulasan (EN/ZH/ID), dan konteks yang sangat relevan dengan isu nyata — terbukti dari validasi sistem kami dengan data COVID 2020–2021." |
| "Kenapa TimeSeriesSplit, bukan random split?" | "Karena data kami bersifat temporal. Random split akan membocorkan informasi masa depan ke data training (data leakage), sehingga evaluasi menjadi tidak valid. TimeSeriesSplit memastikan model selalu diuji pada data yang lebih baru dari data training." |
| "Kenapa class_weight='balanced'?" | "Distribusi crisis_level sangat tidak seimbang: 76% WASPADA, hanya 2.6% KRISIS. Tanpa bobot, model akan bias memprediksi semua WASPADA dan mendapat accuracy 76% tapi gagal mendeteksi krisis yang justru paling penting." |
| "Apakah bisa real-time?" | "Untuk proyek ini kami gunakan data historis sebagai simulasi. Arsitekturnya sudah dirancang modular — tinggal mengganti loader CSV dengan API scraper untuk upgrade ke real-time." |
