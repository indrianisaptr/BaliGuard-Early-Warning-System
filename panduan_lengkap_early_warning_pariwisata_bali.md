# 🏝️ Panduan Lengkap Proyek Akhir
## Multimodal Early Warning System Krisis Pariwisata Bali
### Berbasis Analisis Sentimen Multibahasa & LLM Narrative Engine

---

## 📋 Daftar Isi
1. Gambaran Besar Proyek
2. Arsitektur Sistem (5 Layer)
3. Penjelasan Setiap Komponen
4. Pipeline Data End-to-End
5. Tech Stack & Tools
6. Cara Mengerjakan (Step-by-Step)
7. Feature Engineering
8. Peran LLM / Transformer
9. Dataset Lengkap + Link
10. Timeline Pengerjaan
11. Tips Asistensi ke Dosen

---

## 1. 🎯 Gambaran Besar Proyek

### Definisi Singkat
Sistem dashboard cerdas yang **secara otomatis mendeteksi potensi krisis pariwisata Bali** dengan menggabungkan empat sumber data sekaligus (ulasan wisatawan multibahasa, data ekonomi, cuaca, dan media sosial), kemudian menghasilkan **sinyal early warning** dan **laporan naratif otomatis berbahasa Indonesia** menggunakan LLM.

### Mengapa Ini Kuat Secara Akademik?
| Kriteria Dosen | Pemenuhan Proyek Ini |
|---|---|
| Ada analisis sains, bukan sekadar grafik | ✅ Anomaly detection + Sentiment scoring + Decision engine |
| Multi-metode | ✅ Transformer (BERT multilingual) + LSTM time series + Scoring multifaktor |
| Ada LLM/Transformer | ✅ LLM sebagai Narrative Engine, mBERT sebagai sentimen |
| Feature engineering jelas | ✅ Embedding, rolling window, z-score anomaly, weighted scoring |
| Dashboard powerfull | ✅ Sinyal krisis + laporan naratif + rekomendasi kebijakan |

### Kontribusi Unik
> "Sistem kami tidak hanya memprediksi krisis — tapi juga **menjelaskan dalam narasi** mengapa potensi krisis pariwisata sedang terjadi, menggunakan LLM yang membaca data dari tiga bahasa sekaligus."

---

## 2. 🏗️ Arsitektur Sistem (5 Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1 — SUMBER DATA (4 Modalitas)                           │
│  [TripAdvisor/Reviews]  [Media Sosial]  [BPS/BI/Kurs]  [BMKG] │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  LAYER 2 — INGESTION PIPELINE                                   │
│  [Web Scraper]  [API Collector]  [CSV/Excel Loader]            │
│  → Normalisasi format, deteksi bahasa, timestamp alignment     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  LAYER 3 — PROCESSING LAYER (Inti Analisis)                    │
│  [mBERT Sentiment]  [LSTM Anomaly]  [Normalizer & Scorer]      │
│  → Setiap input diproses jadi skor 0–100 per dimensi           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  LAYER 4 — DECISION ENGINE                                      │
│  [Weighted Multifactor Aggregator]  [LLM Narrative Engine]     │
│  → Crisis Score + Narasi otomatis + Rekomendasi kebijakan      │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  LAYER 5 — DASHBOARD OUTPUT (Streamlit)                        │
│  [Early Warning Signal]  [Laporan Naratif]  [Rekomendasi]      │
│  → Visualisasi interaktif untuk pemangku kebijakan pariwisata  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 🔍 Penjelasan Setiap Komponen

### Layer 1 — Sumber Data

#### 📝 Sumber 1: Ulasan Wisatawan (TripAdvisor & Google Reviews)
- **Bahasa:** English (EN), Mandarin (ZH), Indonesia (ID)
- **Yang diambil:** Rating bintang, teks ulasan, tanggal ulasan, nama hotel/destinasi
- **Kenapa penting:** Sentimen wisatawan adalah indikator leading — ia turun *sebelum* jumlah kunjungan turun
- **Cara mendapat data:** Dataset Mendeley (Bali Hotel Reviews) + dataset Kaggle

#### 📱 Sumber 2: Media Sosial (Twitter/X & Instagram)
- **Yang diambil:** Tweet/caption tentang Bali, hashtag terkait, jumlah engagement
- **Kenapa penting:** Reaksi real-time terhadap kejadian (bencana, kontroversi, dll)
- **Cara mendapat data:** Dataset Twitter/sentimen dari Kaggle

#### 📊 Sumber 3: Data Ekonomi (BPS Bali, Bank Indonesia)
- **Yang diambil:** Jumlah kunjungan wisatawan bulanan, TPK hotel, kurs IDR/USD, inflasi
- **Kenapa penting:** Ground truth untuk label krisis; menangkap tekanan ekonomi struktural
- **Cara mendapat data:** BPS Bali (bali.bps.go.id) + Kaggle kurs historis

#### 🌦️ Sumber 4: Data Cuaca & Bencana (BMKG)
- **Yang diambil:** Curah hujan, suhu, kejadian ekstrem (gunung berapi, banjir)
- **Kenapa penting:** Cuaca buruk + bencana = penurunan kunjungan mendadak
- **Cara mendapat data:** Dataset cuaca Indonesia dari Kaggle + BMKG API

---

### Layer 3 — Processing Layer (Paling Krusial)

#### 🤖 Modul A: Analisis Sentimen Multibahasa (mBERT/XLM-RoBERTa)
```
Input : "This place is terrible, too crowded" (EN)
        "这里太吵了，服务很差" (ZH)
        "Pantainya kotor banget, kecewa" (ID)
        
Proses: Tokenisasi → mBERT Embedding → Classification Head
        
Output: {
  "sentiment_score": 0.23,   // 0=sangat negatif, 1=sangat positif
  "label": "NEGATIVE",
  "aspects": {
    "cleanliness": 0.1,
    "service": 0.2,
    "price_value": 0.4
  }
}
```

#### 📈 Modul B: Anomali Detection Time Series (LSTM / Isolation Forest)
```
Input : Data time series kunjungan wisatawan bulanan (2015–2024)
        Data kurs IDR/USD harian

Proses: Rolling window (3 bulan) → Normalisasi Z-score → 
        LSTM Autoencoder (reconstruction error = anomaly score)
        
Output: {
  "anomaly_flag": True,
  "reconstruction_error": 2.8,   // > 2.0 = anomali
  "trend": "DECLINING",
  "months_to_crisis": 2
}
```

#### ⚖️ Modul C: Multifactor Scoring & Aggregator
```
Bobot setiap dimensi (total = 100%):
  - Sentimen ulasan wisatawan  : 35%
  - Tren kunjungan wisatawan   : 30%
  - Kondisi ekonomi (kurs dll) : 20%
  - Cuaca & bencana            : 15%

Rumus Crisis Score:
  CS = (0.35 × S_sentimen) + (0.30 × S_kunjungan) + 
       (0.20 × S_ekonomi) + (0.15 × S_cuaca)

Interpretasi:
  CS 0–30  : 🟢 AMAN
  CS 31–60 : 🟡 WASPADA
  CS 61–80 : 🟠 SIAGA
  CS 81–100: 🔴 KRISIS
```

---

### Layer 4 — LLM Narrative Engine

Inilah komponen paling unik yang membedakan proyek ini dari yang lain.

#### Cara Kerjanya:
```
1. Semua output dari Layer 3 dikumpulkan menjadi "context JSON"
2. Context dikirim ke LLM (Claude API / GPT / Llama) via prompt engineering
3. LLM menghasilkan laporan naratif dalam Bahasa Indonesia
4. Laporan mencakup: analisis situasi, faktor penyebab, proyeksi, rekomendasi
```

#### Contoh Prompt ke LLM:
```python
SYSTEM_PROMPT = """
Kamu adalah analis sistem pariwisata Bali. Berdasarkan data yang diberikan,
tulis laporan naratif singkat (3–4 paragraf) yang menjelaskan kondisi pariwisata
Bali saat ini, faktor-faktor yang mempengaruhinya, dan rekomendasi kebijakan.
Gunakan bahasa formal yang mudah dipahami pemangku kebijakan.
"""

USER_PROMPT = f"""
Data terkini (periode: {periode}):
- Crisis Score: {crisis_score}/100 (Level: {crisis_level})
- Sentimen ulasan EN/ZH/ID: {sentiment_data}
- Tren kunjungan: {trend_data}
- Anomali ekonomi: {economy_data}
- Kondisi cuaca: {weather_data}
- Faktor dominan: {top_factors}

Hasilkan laporan naratif analisis krisis pariwisata.
"""
```

#### Contoh Output LLM:
```
📄 LAPORAN ANALISIS PARIWISATA BALI — Juli 2024

Kondisi pariwisata Bali saat ini berada pada level WASPADA dengan Crisis Score 
sebesar 48/100. Indikasi ini diperkuat oleh tren penurunan sentimen wisatawan 
mancanegara selama tiga bulan terakhir, khususnya pada segmen wisatawan asal 
Tiongkok yang menunjukkan keluhan dominan terkait kualitas layanan dan kepadatan 
destinasi.

Data ekonomi menunjukkan tekanan nilai tukar rupiah terhadap dolar AS yang 
meningkat sebesar 4.2% dalam 60 hari terakhir, berpotensi mengurangi daya 
saing harga destinasi Bali dibanding negara pesaing seperti Thailand dan Vietnam.

[Rekomendasi Kebijakan]:
1. Tingkatkan program pelatihan SDM pariwisata, khususnya kemampuan berbahasa Mandarin
2. Lakukan diversifikasi pasar ke wisatawan Australia dan India yang menunjukkan tren positif
3. Pantau perkembangan cuaca musim hujan yang diprakirakan dimulai Oktober
```

---

## 4. 🔄 Pipeline Data End-to-End

```
FASE 1 — DATA COLLECTION
│
├── Ulasan Hotel (CSV dari Kaggle/Mendeley)
│   └── load_reviews.py → pandas DataFrame
│
├── Data Kunjungan BPS (Excel dari bali.bps.go.id)
│   └── load_bps.py → time series DataFrame
│
├── Kurs IDR/USD (Kaggle dataset)
│   └── load_forex.py → time series DataFrame
│
└── Data Cuaca (Kaggle dataset)
    └── load_weather.py → DataFrame

FASE 2 — PREPROCESSING
│
├── Deteksi bahasa (langdetect library)
├── Cleaning teks (remove emoji, HTML, stopwords)
├── Tokenisasi dengan mBERT tokenizer
└── Normalisasi time series (min-max / z-score)

FASE 3 — FEATURE ENGINEERING
│
├── Sentiment embeddings (768-dim dari mBERT)
├── Aspect-based sentiment per kategori
├── Rolling average sentimen (7, 30, 90 hari)
├── Z-score anomali kunjungan wisatawan
├── Persentase perubahan kurs (delta)
└── Crisis Score komposit (weighted sum)

FASE 4 — LLM NARRATIVE GENERATION
│
├── Agregasi semua fitur → context JSON
├── Prompt engineering ke LLM API
└── Parsing & display laporan naratif

FASE 5 — DASHBOARD STREAMLIT
│
├── Gauge chart → Crisis Score
├── Line chart → Tren kunjungan + anomali
├── Heatmap → Sentimen per bahasa per bulan
├── Bar chart → Faktor kontributor krisis
└── Text panel → Laporan naratif + rekomendasi
```

---

## 5. 🛠️ Tech Stack & Tools

### Core ML/NLP
| Library | Kegunaan | Install |
|---|---|---|
| `transformers` (HuggingFace) | mBERT / XLM-RoBERTa sentiment | `pip install transformers` |
| `torch` | PyTorch backend | `pip install torch` |
| `scikit-learn` | Isolation Forest, normalisasi | `pip install scikit-learn` |
| `keras/tensorflow` | LSTM time series | `pip install tensorflow` |
| `langdetect` | Deteksi bahasa otomatis | `pip install langdetect` |
| `sentence-transformers` | Embedding kalimat | `pip install sentence-transformers` |

### LLM API
| Opsi | Keterangan | Link |
|---|---|---|
| **Anthropic Claude API** | ⭐ Rekomendasi utama, gratis trial | api.anthropic.com |
| OpenAI GPT-4o | Alternatif, perlu API key | platform.openai.com |
| Ollama (lokal) | Gratis, berat, butuh GPU | ollama.ai |
| Groq API | Gratis, cepat (Llama 3) | console.groq.com |

### Data Processing
| Library | Kegunaan |
|---|---|
| `pandas` | Manipulasi data tabular |
| `numpy` | Komputasi numerik |
| `plotly` | Visualisasi interaktif |
| `scipy` | Deteksi anomali statistik |

### Dashboard
| Tool | Kegunaan |
|---|---|
| **Streamlit** | ⭐ Framework dashboard Python (paling mudah) |
| Plotly Dash | Alternatif lebih fleksibel |
| Vue.js + FastAPI | Alternatif full-stack |

### Model NLP yang Direkomendasikan
```python
# Opsi 1: mBERT (support EN + ZH + ID)
from transformers import pipeline
sentiment = pipeline("sentiment-analysis", 
                     model="nlptown/bert-base-multilingual-uncased-sentiment")

# Opsi 2: XLM-RoBERTa (lebih akurat)
sentiment = pipeline("sentiment-analysis",
                     model="cardiffnlp/twitter-xlm-roberta-base-sentiment")

# Opsi 3: IndoBERT (khusus Indonesian)
sentiment = pipeline("sentiment-analysis",
                     model="indobenchmark/indobert-base-p1")
```

---

## 6. 📅 Cara Mengerjakan (Step-by-Step)

### Minggu 1 — Setup & Data
```
Hari 1-2: Setup environment, install semua library
Hari 3-4: Download semua dataset, eksplorasi EDA awal
Hari 5-7: Preprocessing ulasan hotel (cleaning, deteksi bahasa)
```

### Minggu 2 — Model Core
```
Hari 8-10: Implementasi sentiment analysis dengan mBERT
           → Test dengan sampel ulasan EN, ZH, ID
Hari 11-12: Implementasi anomaly detection time series
            → Test dengan data kunjungan BPS 2015-2024
Hari 13-14: Bangun Multifactor Scoring Engine
            → Tentukan bobot setiap dimensi
```

### Minggu 3 — LLM & Integration
```
Hari 15-16: Setup LLM API (Claude/Groq)
Hari 17-18: Desain sistem prompt Narrative Engine
            → Test prompt engineering, iterasi hingga output bagus
Hari 19-21: Integrasi semua modul jadi 1 pipeline
```

### Minggu 4 — Dashboard & Finishing
```
Hari 22-24: Bangun dashboard Streamlit
            → Gauge, line chart, heatmap, teks narasi
Hari 25-26: Styling & UI/UX (benchmarking dari referensi bagus)
Hari 27-28: Testing, bug fixing, persiapan demo
```

---

## 7. ⚙️ Feature Engineering (Wajib Dijelaskan ke Dosen)

### Fitur dari Ulasan (NLP Features)
```python
# 1. Sentiment Score per Review
sentiment_score = mbert_model.predict(review_text)  # float 0–1

# 2. Aspect-Based Score (6 aspek)
aspects = {
    "cleanliness": extract_aspect(text, "kebersihan"),
    "service": extract_aspect(text, "pelayanan"),
    "price_value": extract_aspect(text, "harga"),
    "accessibility": extract_aspect(text, "akses"),
    "accommodation": extract_aspect(text, "penginapan"),
    "overall_experience": extract_aspect(text, "pengalaman")
}

# 3. Rolling Sentiment (agregasi per bulan)
monthly_sentiment = df.resample('M')['sentiment_score'].mean()

# 4. Sentiment Velocity (laju perubahan)
sentiment_velocity = monthly_sentiment.diff()  # delta per bulan

# 5. Multilingual Sentiment Gap
gap = sentiment_en.mean() - sentiment_zh.mean()  # deteksi disparitas persepsi
```

### Fitur dari Time Series (Numerical Features)
```python
# 1. Z-Score Anomali Kunjungan
z_score = (x - rolling_mean) / rolling_std
anomaly_flag = z_score < -2.0  # 2 std di bawah rata-rata = anomali

# 2. Kurs Shock Index
kurs_change_30d = (kurs_now - kurs_30d_ago) / kurs_30d_ago * 100

# 3. Seasonality Residual (setelah decompose)
from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(kunjungan_series, model='multiplicative', period=12)
residual = result.resid  # komponen yang "tidak normal"
```

### Cara Menjelaskan Feature Engineering ke Dosen
> "Pak, kami membangun tiga jenis fitur:
> 1. **Embedding fitur** dari teks ulasan menggunakan mBERT (768 dimensi per ulasan, lalu diagregasi per bulan)
> 2. **Temporal fitur** dari time series kunjungan menggunakan rolling window dan Z-score
> 3. **Cross-modal fitur** berupa gap sentimen antarbahasa dan korelasi sentimen-kunjungan dengan lag 2 bulan"

---

## 8. 🤖 Peran LLM & Transformer

### Transformer (mBERT) — Layer Pemrosesan
- **Model:** `bert-base-multilingual-uncased` atau `xlm-roberta-base`
- **Peran:** Mengkonversi teks ulasan multibahasa menjadi representasi numerik (embedding) dan klasifikasi sentimen
- **Cara kerja:** Fine-tuning pada dataset sentimen hotel (atau zero-shot dengan pre-trained model)
- **Output:** Skor sentimen 0–1 per ulasan, per aspek, per bahasa

### LLM (Claude/GPT/Llama) — Narrative Engine
- **Model:** Claude claude-sonnet-4-20250514 atau GPT-4o-mini (hemat cost)
- **Peran:** Menerima semua data terstruktur dan menghasilkan laporan naratif yang dapat dibaca manusia
- **Perbedaan fundamental:** Transformer = **memahami teks**, LLM = **menghasilkan penjelasan**
- **Output:** Paragraf laporan analisis + daftar rekomendasi kebijakan

### Diagram Peran Keduanya
```
Teks Ulasan ──→ [mBERT Transformer] ──→ Skor Numerik
                                              │
Time Series ──→ [LSTM/IsolForest]   ──→ Flag Anomali
                                              │
Data Kurs   ──→ [Statistical Test]  ──→ Indeks Tekanan
                                              │
                                    [Aggregator Engine]
                                              │
                                       Crisis Score JSON
                                              │
                                    [LLM Narrative Engine]
                                              │
                                      Laporan Naratif 📄
```

---

## 9. 📦 Dataset Lengkap + Link

### Dataset 1 — Ulasan Hotel Bali ⭐⭐⭐ (UTAMA)
```
Nama  : Bali Hotel Reviews Dataset
Sumber: Mendeley Data
Link  : https://data.mendeley.com/datasets/s62ycm698z/2
Isi   : Ulasan hotel Bali dengan label aspek (Value, Service, Room,
        Cleanliness, Accessibility, Sleep Quality)
Format: CSV
Catatan: SUDAH berlabel aspek → ideal untuk ABSA (Aspect-Based Sentiment)
```

### Dataset 2 — Data Kunjungan Wisatawan BPS ⭐⭐⭐ (UTAMA)
```
Nama  : Statistik Pariwisata Bali
Sumber: BPS Provinsi Bali
Link  : https://bali.bps.go.id/en/statistics-table?subject=561
Isi   : Jumlah wisman bulanan, TPK hotel, lama tinggal (2004–2024)
Format: Excel/CSV (unduh dari tabel statistik)
Catatan: Data resmi pemerintah → bisa jadi ground truth label krisis
```

### Dataset 3 — Kurs IDR/USD Historis ⭐⭐
```
Nama  : USD IDR Historical Data 2010-2024
Sumber: Kaggle
Link  : https://www.kaggle.com/datasets/ferdinandvn/usd-idr-historical-data-2010-2024
Isi   : Kurs harian IDR/USD dari 2010 hingga 2024
Format: CSV
```

### Dataset 4 — Kurs Multi-Mata Uang ⭐⭐
```
Nama  : Forex Exchange Rates Since 2004
Sumber: Kaggle
Link  : https://www.kaggle.com/datasets/asaniczka/forex-exchange-rate-since-2004-updated-daily
Isi   : Kurs harian berbagai mata uang termasuk IDR
Format: CSV (update harian)
```

### Dataset 5 — Hotel Reviews Multi-Aspek ⭐⭐
```
Nama  : Hotel Reviews: Aspects, Sentiments and Topics
Sumber: Kaggle
Link  : https://www.kaggle.com/datasets/costastziouvas/hotel-reviews-aspects-sentiments-and-topics
Isi   : Reviews dengan label aspek dan sentimen untuk benchmark
Format: CSV
```

### Dataset 6 — Hotel Reviews Multikriteria ⭐⭐
```
Nama  : Multi-Criteria Hotel Reviews
Sumber: Kaggle
Link  : https://www.kaggle.com/datasets/harrachimustapha/hotel-reviews-dataset
Isi   : Reviews dengan rating per kriteria (cocok untuk multi-aspek)
Format: CSV
```

### Dataset 7 — Cuaca Indonesia ⭐
```
Nama  : Indonesia Weather Historical
Sumber: Kaggle (cari "indonesia weather BMKG")
Link  : https://www.kaggle.com/search?q=indonesia+weather+bmkg
Isi   : Data cuaca historis stasiun Bali/Denpasar
Format: CSV
Alternatif: BMKG Open Data → https://dataonline.bmkg.go.id
```

### Dataset 8 — Twitter Sentiment Indonesia ⭐
```
Nama  : Indonesian Twitter Sentiment Dataset
Sumber: Kaggle
Link  : https://www.kaggle.com/search?q=twitter+sentiment+indonesia+bali+tourism
Isi   : Tweet bahasa Indonesia bertema pariwisata + label sentimen
Format: CSV
```

### Strategi Dataset yang Disarankan
```
Untuk kelompok kecil / waktu terbatas:
→ Gunakan Dataset 1 (Bali Hotel Reviews, Mendeley) sebagai UTAMA untuk NLP
→ Gunakan Dataset 2 (BPS) untuk time series kunjungan
→ Gunakan Dataset 3 (Kaggle kurs) untuk faktor ekonomi
→ Cukup 3 dataset ini → sudah multimodal dan layak presentasi!

Untuk kelompok ambisius:
→ Tambahkan Dataset 7 (cuaca) dan scrape sedikit tweet
→ Buat simulasi periode krisis: COVID 2020–2021 vs recovery 2022–2024
```

---

## 10. 📆 Timeline Pengerjaan (4 Minggu)

| Minggu | Target | Deliverable untuk Demo |
|---|---|---|
| 1 | Data collection + EDA + preprocessing | Notebook eksplorasi data |
| 2 | Model sentimen + anomali detection | Demo output skor per review |
| 3 | Multifactor engine + LLM integration | Demo narasi otomatis |
| 4 | Dashboard Streamlit + polish | Demo dashboard lengkap |

---

## 11. 💡 Tips Asistensi ke Dosen

### Cara Membuka Asistensi
> "Pak/Bu, proyek kami adalah sistem **Early Warning Krisis Pariwisata Bali** yang menggunakan data multimodal. Yang kami jadikan highlight adalah penggunaan **mBERT** untuk analisis sentimen ulasan wisatawan dalam tiga bahasa (Indonesia, Inggris, Mandarin), dan **LLM sebagai Narrative Engine** yang mengubah output model menjadi laporan naratif otomatis. Ini bukan sekadar prediksi angka, tapi sistem decision support yang bisa dibaca langsung oleh pemangku kebijakan."

### Jelaskan Feature Engineering Ini
> "Feature engineering kami terdiri dari tiga lapisan:
> 1. Embedding fitur teks dari mBERT (multi-bahasa)
> 2. Temporal anomaly fitur dari LSTM/Z-score pada time series BPS
> 3. Crisis Score komposit berbobot yang menggabungkan keempat dimensi"

### Antisipasi Pertanyaan Dosen
| Pertanyaan Dosen | Jawaban Siap |
|---|---|
| "Di mana peran LLM-nya?" | "LLM berperan di layer akhir sebagai Narrative Engine, ia menerima semua output model dan menghasilkan laporan analisis dalam bahasa Indonesia" |
| "Apa bedanya dengan dashboard biasa?" | "Dashboard biasa hanya menampilkan data. Sistem kami menambahkan tiga layer analisis sains: sentiment transformer, anomaly detection, dan generative AI untuk narasi" |
| "Kenapa pilih Bali?" | "Bali memiliki data pariwisata terpublish lengkap dari BPS, komunitas wisatawan multibahasa yang aktif menulis ulasan, dan konteks yang relevan dengan isu nyata" |
| "Apakah bisa real-time?" | "Untuk proyek ini kami menggunakan data historis sebagai simulasi. Arsitektur sudah dirancang untuk dapat diupgrade ke real-time scraping" |
```
