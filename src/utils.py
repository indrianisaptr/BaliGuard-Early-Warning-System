"""
src/utils.py — BaliGuard: Core Constants & Base Helpers
========================================================
Perubahan dari versi sebelumnya (untuk memenuhi masukan dosen):

[BARU] LABEL_MANUSIAWI — dict mapping nama kolom teknis → bahasa awam.
       Dipakai oleh analisis.py (feature importance), dashboard.py (tabel),
       dan halaman lain yang menampilkan nama kolom.

[BARU] REKOMENDASI_LEVEL — rekomendasi tindakan rule-based per crisis level.
       Dipanggil oleh analisis.py dan narasi.py sebagai fallback / pelengkap
       output LLM untuk section "Rekomendasi Tindakan".

[BARU] interpretasi_indikator() — konversi nilai numerik ke kalimat singkat
       bahasa awam. Dipakai di analisis.py untuk section "Mengapa status ini?"

[BARU] is_current_month() — helper untuk cek apakah bulan yang dipilih
       adalah bulan berjalan. Dipakai overview.py untuk memutuskan
       apakah kurs yang ditampilkan adalah live atau historis.

[BARU] format_usd_source_label() — helper untuk sub-label KPI kurs:
       tampilkan "data historis bulan ini" vs "LIVE saat ini" secara konsisten.

Semua fungsi dan konstanta lama dipertahankan tanpa perubahan signature
agar tidak ada breaking change di file lain.
"""

import streamlit as st
from src.config import (
    LABEL_ORDER, FEATURES_CORE, FEATURES_LAG,
    THRESHOLD, DATA_DIR, MODEL_DIR,
)
import pandas as pd
import numpy as np
import requests, json, os
from src.config import LEVEL_COLORS
from pathlib import Path
from datetime import datetime

from src.components.cards import (
    kpi_card,
    alert_card,
)

from src.components.badges import (
    status_dot,
)

import time

_t_start = time.perf_counter()
_t = {}

def _tick(label):
    _t[label] = time.perf_counter() - _t_start

# Compatibility aliases
kpi_html = kpi_card
alert_html = alert_card

# ── Path config ───────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / 'data' / 'final'
MODEL_DIR = BASE_DIR / 'models'


# ══════════════════════════════════════════════════════════════════════
# LABEL_MANUSIAWI — mapping nama kolom teknis → bahasa awam
# ══════════════════════════════════════════════════════════════════════
# Cara pakai:
#   from src.utils import LABEL_MANUSIAWI
#   label_tampil = LABEL_MANUSIAWI.get(nama_kolom, nama_kolom)
#
# Fallback ke nama_kolom asli kalau tidak ada di dict
# (aman untuk kolom baru yang belum terdaftar).
# ─────────────────────────────────────────────────────────────────────
LABEL_MANUSIAWI: dict[str, str] = {
    # ── Indikator pariwisata ──────────────────────────────────────────
    "wisman":                    "Jumlah Wisatawan Mancanegara",
    "wisnus":                    "Jumlah Wisatawan Nusantara",
    "wisman_growth_mom":         "Pertumbuhan Wisatawan vs Bulan Lalu (%)",
    "wisman_growth_yoy":         "Pertumbuhan Wisatawan vs Tahun Lalu (%)",
    "wisman_zscore":             "Penyimpangan Wisatawan dari Rata-rata Historis (Z-score)",
    "wisman_ma3":                "Rata-rata Kunjungan 3 Bulan Terakhir",
    "wisman_recovery_pct":       "Tingkat Pemulihan vs Baseline 2017–2019 (%)",
    "wisman_lag_1":              "Jumlah Wisatawan Bulan Lalu",
    "wisman_lag_3":              "Jumlah Wisatawan 3 Bulan Lalu",
    "wisman_trend_3m":           "Arah Tren Kunjungan 3 Bulan",
    "bali_share_pct":            "Pangsa Wisatawan Bali dari Total Nasional (%)",
    "bali_share_change":         "Perubahan Pangsa Wisatawan Bali",

    # ── Akomodasi ─────────────────────────────────────────────────────
    "tpk_bintang":               "Tingkat Hunian Hotel Berbintang (%)",
    "tpk_non_bintang":           "Tingkat Hunian Hotel Non-Berbintang (%)",
    "tpk_change_mom":            "Perubahan Tingkat Hunian vs Bulan Lalu",
    "tpk_ma3":                   "Rata-rata Tingkat Hunian 3 Bulan Terakhir",
    "tpk_lag_1":                 "Tingkat Hunian Bulan Lalu",
    "lama_menginap_bintang":     "Rata-rata Lama Menginap Hotel Berbintang (malam)",
    "lama_menginap_non_bintang": "Rata-rata Lama Menginap Hotel Non-Berbintang (malam)",

    # ── Ekonomi & moneter ─────────────────────────────────────────────
    "usd_idr_avg":               "Kurs USD/IDR Rata-rata Bulan Ini (Rp)",
    "usd_change_mom":            "Perubahan Kurs USD/IDR vs Bulan Lalu (%)",
    "usd_volatility_3m":         "Volatilitas Kurs USD/IDR (3 Bulan)",
    "inflasi_processed":         "Tingkat Inflasi Bali (%)",
    "economic_risk_score":       "Indeks Risiko Ekonomi Global",

    # ── Sentimen ──────────────────────────────────────────────────────
    "avg_sentiment_monthly":     "Sentimen Rata-rata Ulasan Wisatawan (-1 s/d +1)",
    "pct_positive_monthly":      "Persentase Ulasan Positif (%)",
    "pct_negative_monthly":      "Persentase Ulasan Negatif (%)",
    "pct_neutral_monthly":       "Persentase Ulasan Netral (%)",
    "sentiment_lag_1":           "Sentimen Ulasan Bulan Lalu",
    "sentiment_trend_3m":        "Arah Tren Sentimen 3 Bulan",

    # ── Risiko eksternal ─────────────────────────────────────────────
    "gdelt_crisis_score":        "Indeks Risiko Pemberitaan Internasional (GDELT)",
    "disaster_risk_score":       "Indeks Risiko Bencana Alam",
    "external_risk_avg":         "Indeks Risiko Eksternal Gabungan",
    "external_risk_max":         "Risiko Eksternal Tertinggi (Shock Detector)",
    "external_risk_range":       "Divergensi Risiko Eksternal",
    "physical_risk_score":       "Risiko Fisik (Gempa & Bencana)",
    "media_risk_score":          "Risiko Pemberitaan Negatif di Media",
    "tourist_perception_score":  "Indeks Persepsi Wisatawan",
    "external_risk_score":       "Indeks Risiko Eksternal (Komposit)",
    "eq_risk_score":             "Indeks Risiko Gempa Bumi",

    # ── Crisis score & level ──────────────────────────────────────────
    "crisis_score":              "Skor Krisis Pariwisata",
    "crisis_score_100":          "Skor Krisis (0–100)",
    "crisis_level":              "Level Status Pariwisata",
    "crisis_component_tourism":  "Komponen Kunjungan Wisatawan (dalam Skor Krisis)",
    "crisis_component_economy":  "Komponen Kondisi Ekonomi (dalam Skor Krisis)",
    "crisis_component_sentiment":"Komponen Sentimen Ulasan (dalam Skor Krisis)",

    # ── Output model ML ───────────────────────────────────────────────
    "rf_predicted_level":        "Prediksi Level Krisis (Random Forest)",
    "rf_confidence":             "Tingkat Keyakinan Prediksi Model (%)",
    "iso_anomaly":               "Terdeteksi sebagai Anomali (Ya=1 / Tidak=0)",
    "iso_score":                 "Skor Anomali Isolation Forest",
    "prob_aman":                 "Probabilitas Status AMAN (%)",
    "prob_waspada":              "Probabilitas Status WASPADA (%)",
    "prob_siaga":                "Probabilitas Status SIAGA (%)",
    "prob_krisis":               "Probabilitas Status KRISIS (%)",

    # ── Fitur waktu & kontekstual ─────────────────────────────────────
    "month":                     "Bulan",
    "month_num":                 "Nomor Bulan dalam Setahun",
    "is_peak_season":            "Musim Puncak Pariwisata (Ya/Tidak)",
    "is_covid_period":           "Periode COVID-19 (Ya/Tidak)",
    "is_postcovid":              "Periode Pasca-COVID (Ya/Tidak)",
    "is_anomaly":                "Teridentifikasi Anomali Historis",
}


# ══════════════════════════════════════════════════════════════════════
# REKOMENDASI_LEVEL — tindakan rule-based per crisis level
# ══════════════════════════════════════════════════════════════════════
# Dipakai sebagai:
#   (a) Fallback jika LLM tidak tersedia
#   (b) Anchor di bawah output SWOT LLM (selalu tampil, tidak bergantung LLM)
#
# Format: dict[level] → list[dict] dengan key 'prioritas', 'aksi', 'aktor'
# ─────────────────────────────────────────────────────────────────────
REKOMENDASI_LEVEL: dict[str, list[dict]] = {
    "AMAN": [
        {
            "prioritas": "Jangka Pendek",
            "aksi": "Pertahankan kualitas layanan dan promosi pariwisata yang sedang berjalan",
            "aktor": "Dinas Pariwisata Bali",
        },
        {
            "prioritas": "Jangka Menengah",
            "aksi": "Manfaatkan kondisi stabil untuk diversifikasi pasar wisatawan baru",
            "aktor": "Kemenparekraf + Pemerintah Provinsi",
        },
        {
            "prioritas": "Monitoring",
            "aksi": "Pantau indikator eksternal (kurs, GDELT) untuk deteksi dini perubahan",
            "aktor": "Tim BaliGuard",
        },
    ],
    "WASPADA": [
        {
            "prioritas": "Segera",
            "aksi": (
                "Tingkatkan frekuensi monitoring mingguan terhadap indikator "
                "yang menunjukkan tekanan (wisman, kurs, sentimen)"
            ),
            "aktor": "Tim BaliGuard + Dinas Pariwisata",
        },
        {
            "prioritas": "Jangka Pendek",
            "aksi": "Siapkan paket stimulus promosi wisata sebagai respons antisipatif",
            "aktor": "Kemenparekraf",
        },
        {
            "prioritas": "Koordinasi",
            "aksi": "Koordinasikan dengan asosiasi hotel dan agen perjalanan untuk pemantauan lapangan",
            "aktor": "PHRI + ASITA Bali",
        },
    ],
    "SIAGA": [
        {
            "prioritas": "🔴 Mendesak",
            "aksi": (
                "Aktifkan rapat koordinasi lintas-sektor pariwisata dalam 48 jam "
                "untuk menilai situasi dan menetapkan langkah respons"
            ),
            "aktor": "Gubernur Bali + Kepala Dinas Pariwisata",
        },
        {
            "prioritas": "🔴 Segera",
            "aksi": (
                "Luncurkan kampanye promosi darurat di pasar utama "
                "(Australia, Tiongkok, India) untuk menahan penurunan kunjungan"
            ),
            "aktor": "Kemenparekraf + Indonesia Tourism",
        },
        {
            "prioritas": "Jangka Pendek",
            "aksi": "Evaluasi dan tunda kebijakan yang berpotensi menambah beban biaya wisatawan",
            "aktor": "Pemerintah Provinsi Bali",
        },
        {
            "prioritas": "Monitoring",
            "aksi": "Naikkan frekuensi laporan BaliGuard menjadi mingguan dan distribusikan ke pemangku kepentingan",
            "aktor": "Tim BaliGuard",
        },
    ],
    "KRISIS": [
        {
            "prioritas": "🚨 Darurat",
            "aksi": (
                "Aktifkan Protokol Penanganan Krisis Pariwisata — bentuk task force "
                "dengan kewenangan lintas kementerian dalam 24 jam"
            ),
            "aktor": "Kemenparekraf + Gubernur Bali + Kemenkeu",
        },
        {
            "prioritas": "🚨 Darurat",
            "aksi": (
                "Siapkan paket insentif fiskal darurat untuk pelaku usaha pariwisata "
                "(keringanan pajak, subsidi promosi, pinjaman lunak)"
            ),
            "aktor": "Kemenkeu + Bank Indonesia",
        },
        {
            "prioritas": "🔴 Segera",
            "aksi": (
                "Rilis pernyataan resmi pemerintah untuk manajemen persepsi dan "
                "mencegah eskalasi pemberitaan negatif internasional"
            ),
            "aktor": "Kemenparekraf + Kemenlu",
        },
        {
            "prioritas": "🔴 Segera",
            "aksi": "Koordinasikan dengan maskapai dan platform OTA untuk menjaga konektivitas dan harga kompetitif",
            "aktor": "Kemenhub + Kemenparekraf",
        },
        {
            "prioritas": "Monitoring",
            "aksi": "Laporan harian BaliGuard wajib dikirim ke seluruh pemangku kepentingan",
            "aktor": "Tim BaliGuard",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════
# interpretasi_indikator() — nilai numerik → kalimat bahasa awam
# ══════════════════════════════════════════════════════════════════════
# Dipakai di analisis.py untuk section "Mengapa Status Ini Muncul?"
#
# Cara pakai:
#   kalimat = interpretasi_indikator("wisman_growth_mom", -0.15)
#   # → "turun 15.0% dibanding bulan lalu — mengindikasikan tekanan kunjungan"
# ─────────────────────────────────────────────────────────────────────
def interpretasi_indikator(kolom: str, nilai: float) -> str:
    """
    Konversi nilai numerik indikator ke kalimat interpretatif singkat.
    Return string kosong kalau kolom tidak dikenali atau nilai NaN.
    """
    if nilai is None or (isinstance(nilai, float) and np.isnan(nilai)):
        return "data tidak tersedia"

    v = float(nilai)

    if kolom == "wisman_growth_mom":
        if v > 0.15:
            return f"naik {v:.1%} dibanding bulan lalu — pertumbuhan kunjungan kuat"
        if v > 0.03:
            return f"naik {v:.1%} dibanding bulan lalu — pertumbuhan moderat"
        if v >= -0.03:
            return f"relatif stabil ({v:+.1%}) dibanding bulan lalu"
        if v >= -0.15:
            return f"turun {abs(v):.1%} dibanding bulan lalu — perlu perhatian"
        return f"turun {abs(v):.1%} dibanding bulan lalu — tekanan kunjungan signifikan"

    if kolom == "wisman_growth_yoy":
        if v > 0.2:
            return f"naik {v:.1%} dibanding tahun lalu — tren pemulihan kuat"
        if v > 0:
            return f"naik {v:.1%} dibanding tahun lalu — tren positif"
        if v >= -0.1:
            return f"sedikit turun {abs(v):.1%} dibanding tahun lalu"
        return f"turun {abs(v):.1%} dibanding tahun lalu — perlu intervensi"

    if kolom == "wisman_zscore":
        if v > 2:
            return f"sangat di atas normal (z={v:.2f}) — lonjakan kunjungan tidak biasa"
        if v > 1:
            return f"di atas rata-rata historis (z={v:.2f})"
        if v >= -1:
            return f"dalam kisaran normal (z={v:.2f})"
        if v >= -2:
            return f"di bawah rata-rata historis (z={v:.2f}) — kunjungan melemah"
        return f"sangat di bawah normal (z={v:.2f}) — kunjungan anjlok signifikan"

    if kolom in ("tpk_bintang", "tpk_non_bintang"):
        label = "berbintang" if kolom == "tpk_bintang" else "non-berbintang"
        if v >= 70:
            return f"{v:.1f}% — hunian hotel {label} tinggi, kapasitas hampir penuh"
        if v >= 50:
            return f"{v:.1f}% — hunian hotel {label} normal"
        if v >= 30:
            return f"{v:.1f}% — hunian hotel {label} rendah, kapasitas banyak kosong"
        return f"{v:.1f}% — hunian hotel {label} sangat rendah, tekanan serius pada industri akomodasi"

    if kolom == "usd_idr_avg":
        if v > 16500:
            return f"Rp {v:,.0f}/USD — kurs sangat tinggi, biaya perjalanan ke Bali meningkat bagi wisatawan asing"
        if v > 15500:
            return f"Rp {v:,.0f}/USD — kurs tinggi, sedikit memberatkan wisatawan asing"
        if v >= 14500:
            return f"Rp {v:,.0f}/USD — kurs dalam kisaran normal"
        return f"Rp {v:,.0f}/USD — kurs rendah, menguntungkan bagi wisatawan asing ke Bali"

    if kolom == "usd_change_mom":
        if v > 0.03:
            return f"rupiah melemah {abs(v):.1%} terhadap USD bulan ini — meningkatkan risiko ekonomi"
        if v < -0.03:
            return f"rupiah menguat {abs(v):.1%} terhadap USD bulan ini — kondisi positif"
        return f"kurs relatif stabil ({v:+.1%} bulan ini)"

    if kolom == "inflasi_processed":
        if v > 5:
            return f"{v:.2f}% — inflasi tinggi, berpotensi menaikkan biaya perjalanan domestik"
        if v > 3:
            return f"{v:.2f}% — inflasi moderat"
        if v >= 0:
            return f"{v:.2f}% — inflasi terkendali"
        return f"{v:.2f}% — deflasi, harga-harga turun"

    if kolom == "avg_sentiment_monthly":
        if v >= 0.5:
            return f"skor {v:+.3f} — wisatawan sangat puas dengan pengalaman di Bali"
        if v >= 0.3:
            return f"skor {v:+.3f} — sentimen positif, ulasan wisatawan umumnya baik"
        if v >= -0.3:
            return f"skor {v:+.3f} — sentimen netral atau campuran"
        if v >= -0.5:
            return f"skor {v:+.3f} — sentimen negatif, banyak keluhan dari wisatawan"
        return f"skor {v:+.3f} — sentimen sangat negatif, perlu perhatian serius"

    if kolom == "gdelt_crisis_score":
        if v > 0.7:
            return f"skor {v:.3f} — pemberitaan internasional sangat negatif tentang Bali"
        if v > 0.5:
            return f"skor {v:.3f} — pemberitaan internasional cenderung negatif"
        if v > 0.3:
            return f"skor {v:.3f} — pemberitaan internasional netral hingga sedikit negatif"
        return f"skor {v:.3f} — pemberitaan internasional relatif positif atau netral"

    if kolom == "disaster_risk_score":
        if v > 0.7:
            return f"skor {v:.3f} — risiko bencana alam sangat tinggi pada periode ini"
        if v > 0.5:
            return f"skor {v:.3f} — risiko bencana alam cukup tinggi"
        if v > 0.3:
            return f"skor {v:.3f} — risiko bencana alam moderat"
        return f"skor {v:.3f} — risiko bencana alam rendah"

    if kolom == "economic_risk_score":
        if v > 0.7:
            return f"skor {v:.3f} — kondisi ekonomi global sangat tidak menguntungkan"
        if v > 0.5:
            return f"skor {v:.3f} — tekanan ekonomi global cukup tinggi"
        if v > 0.3:
            return f"skor {v:.3f} — kondisi ekonomi global moderat"
        return f"skor {v:.3f} — kondisi ekonomi global relatif stabil"

    if kolom == "bali_share_pct":
        if v > 40:
            return f"{v:.1f}% — Bali mendominasi kunjungan wisatawan nasional"
        if v > 30:
            return f"{v:.1f}% — pangsa Bali di atas rata-rata"
        if v > 20:
            return f"{v:.1f}% — pangsa Bali dalam kisaran normal"
        return f"{v:.1f}% — pangsa Bali rendah, wisatawan beralih ke destinasi lain"

    if kolom == "wisman_recovery_pct":
        if v >= 100:
            return f"{v:.1f}% — kunjungan telah pulih melebihi level sebelum pandemi (2017–2019)"
        if v >= 80:
            return f"{v:.1f}% — pemulihan hampir sempurna"
        if v >= 50:
            return f"{v:.1f}% — pemulihan sudah separuh jalan"
        if v > 0:
            return f"{v:.1f}% — pemulihan masih terbatas"
        return "data pemulihan belum tersedia"

    # Kolom tidak dikenali → kembalikan nilai mentah
    return f"{v:.3f}"


# ══════════════════════════════════════════════════════════════════════
# is_current_month() — cek apakah bulan yang dipilih adalah bulan ini
# ══════════════════════════════════════════════════════════════════════
# Dipakai di overview.py dan dashboard.py untuk menentukan apakah
# kurs yang ditampilkan harus live atau historis.
#
# Cara pakai:
#   if is_current_month(sel):
#       label_usd = "LIVE saat ini"
#   else:
#       label_usd = f"rata-rata historis {sel}"
# ─────────────────────────────────────────────────────────────────────
def is_current_month(month_str: str) -> bool:
    """
    Return True kalau month_str (format 'YYYY-MM') sama dengan bulan ini.
    Aman terhadap format input yang tidak sesuai (return False).
    """
    try:
        return month_str[:7] == datetime.now().strftime('%Y-%m')
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
# format_usd_source_label() — sub-label KPI kurs yang konsisten
# ══════════════════════════════════════════════════════════════════════
# Memastikan label sumber data kurs selalu jelas dan relevan
# dengan bulan yang sedang dianalisis.
#
# Cara pakai (di overview.py atau dashboard.py):
#   sub_label, badge_html = format_usd_source_label(sel, is_live)
# ─────────────────────────────────────────────────────────────────────
def format_usd_source_label(month_str: str, is_live: bool) -> tuple[str, str]:
    """
    Return (sub_label_text, badge_html).

    - Bulan historis  → sub_label = "rata-rata historis {bulan}", badge = ""
    - Bulan berjalan + live berhasil → sub_label = "kurs saat ini", badge = HTML "LIVE"
    - Bulan berjalan + live gagal    → sub_label = "rata-rata historis tersedia", badge = ""
    """
    _LIVE_BADGE = (
        "<span style='display:inline-flex;align-items:center;gap:5px;font-size:10px;"
        "font-weight:700;background:rgba(239,68,68,0.15);color:#ef4444;padding:3px 8px;"
        "border-radius:20px;border:1px solid rgba(239,68,68,0.3);letter-spacing:.04em'>"
        "<span style='width:6px;height:6px;border-radius:50%;background:#ef4444;"
        "animation:pulse 1.5s infinite;flex-shrink:0;display:inline-block'></span>LIVE</span>"
    )

    if is_live and is_current_month(month_str):
        return "kurs saat ini (real-time)", _LIVE_BADGE
    else:
        try:
            # Format bulan ke nama manusiawi, misal "2024-03" → "Maret 2024"
            dt = datetime.strptime(month_str[:7], '%Y-%m')
            bulan_label = dt.strftime('%B %Y')
        except Exception:
            bulan_label = month_str
        return f"rata-rata historis {bulan_label}", ""


# ══════════════════════════════════════════════════════════════════════
# Semua fungsi lama — tidak ada perubahan, dipertahankan agar tidak
# ada breaking change di file lain yang sudah import dari utils.py
# ══════════════════════════════════════════════════════════════════════

def sf(val, default: float = 0.0) -> float:
    """Safe float — return default jika None/NaN/error."""
    try:
        v = float(val)
        return default if (v != v) else v
    except Exception:
        return default


def level_from_score(s: float) -> str:
    if s >= THRESHOLD["KRISIS"]:  return 'KRISIS'
    if s >= THRESHOLD["SIAGA"]:   return 'SIAGA'
    if s >= THRESHOLD["WASPADA"]: return 'WASPADA'
    return 'AMAN'


@st.cache_data(show_spinner=False)
def load_data() -> tuple:
    master = pd.read_parquet(DATA_DIR / 'master_dataset_clean.parquet')
    pred   = pd.read_csv(DATA_DIR / 'predictions_final.csv')
    cache  = {}
    p = DATA_DIR / 'narratives_cache.json'
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    return master, pred, cache


@st.cache_resource(show_spinner=False)
def load_models() -> tuple:
    import joblib
    rf     = joblib.load(MODEL_DIR / 'model_random_forest.pkl')
    iso_f  = joblib.load(MODEL_DIR / 'model_isolation_forest.pkl')
    scaler = joblib.load(MODEL_DIR / 'scaler.pkl')
    le     = joblib.load(MODEL_DIR / 'label_encoder.pkl')
    return rf, iso_f, scaler, le


@st.cache_resource(show_spinner=False)
def load_nav_icons() -> dict:
    """Base64 icon dari icons/ — dibuat sekali, tidak dibuat ulang setiap rerun."""
    import base64
    mapping = {
        'Gambaran Umum & Garis Waktu': BASE_DIR / 'assets' / 'icons' / 'overview&timeline.png',
        'Analisis Detail':             BASE_DIR / 'assets' / 'icons' / 'analisis_detail.png',
        'Sentimen':                    BASE_DIR / 'assets' / 'icons' / 'sentimen.png',
        'Prediksi & Proyeksi':         BASE_DIR / 'assets' / 'icons' / 'prediksi&proyeksi.png',
        'Narasi AI':                   BASE_DIR / 'assets' / 'icons' / 'narasi_ai.png',
    }
    result = {}
    for label, path in mapping.items():
        if path.exists():
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            result[label] = f'data:image/png;base64,{b64}'
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_usd_idr() -> float | None:
    for url in [
        'https://api.exchangerate-api.com/v4/latest/USD',
        'https://open.er-api.com/v6/latest/USD',
    ]:
        try:
            r = requests.get(url, timeout=5)
            return float(r.json()['rates']['IDR'])
        except Exception:
            continue
    return None


def get_current_usd_idr(predictions: pd.DataFrame,
                          month: str) -> tuple[float | None, bool]:
    """
    Return (rate, is_live).

    Logika yang diperbaiki sesuai masukan dosen:
    - Bulan historis (lebih lama dari data terakhir): SELALU pakai data historis,
      TIDAK pernah fetch live. Kurs live tidak relevan untuk bulan lalu.
    - Bulan berjalan (== bulan ini secara kalender): coba fetch live dulu.
      Kalau gagal, fallback ke data historis CSV.
    - Bulan proyeksi (lebih baru dari data terakhir): coba fetch live sebagai
      estimasi terbaik yang tersedia.
    """
    last_m     = predictions['month'].max()
    curr_cal_m = datetime.now().strftime('%Y-%m')

    # Ambil nilai historis dari CSV (selalu tersedia sebagai fallback)
    hist_val = None
    rows = predictions[predictions['month'] == month]
    if len(rows) and 'usd_idr_avg' in rows.columns:
        hist_val = float(rows.iloc[0]['usd_idr_avg'])

    # Bulan historis yang sudah berlalu — tampilkan historis, BUKAN live
    if month < curr_cal_m and month <= last_m:
        if hist_val is not None:
            return hist_val, False
        return None, False

    # Bulan berjalan atau proyeksi — coba live dulu
    live = fetch_live_usd_idr()
    if live:
        return live, True

    # Fallback ke historis kalau live gagal
    if hist_val is not None:
        return hist_val, False

    return None, False


@st.cache_data(show_spinner=False)
def compute_delta_context(row_data_dict: dict,
                           pred_df: pd.DataFrame,
                           sel_month: str) -> dict:
    """Hitung delta MoM untuk semua KPI utama."""
    months = list(pred_df['month'].values)
    if sel_month not in months:
        return {}
    idx = months.index(sel_month)
    if idx <= 0:
        return {}
    prev = pred_df.iloc[idx - 1].to_dict()
    result = {}
    for key in ['wisman', 'tpk_bintang', 'inflasi_processed', 'usd_idr_avg',
                'avg_sentiment_monthly', 'crisis_score_100', 'bali_share_pct']:
        c, p = sf(row_data_dict.get(key)), sf(prev.get(key))
        result[key] = {
            'curr': c, 'prev': p,
            'delta': c - p,
            'delta_pct': (c - p) / p * 100 if p != 0 else 0,
        }
    return result