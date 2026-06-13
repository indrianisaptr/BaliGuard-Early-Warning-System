"""
src/config.py — BaliGuard: Global Configuration
================================================
Satu-satunya tempat untuk mengubah konstanta sistem.

Aturan:
  - Threshold berubah? → ubah di sini saja
  - Warna level berubah? → ubah di sini saja
  - Path file berubah? → ubah di sini saja

Tidak ada logika atau import streamlit di file ini.
"""
from pathlib import Path

# ── Path ──────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / 'data' / 'final'
MODEL_DIR = BASE_DIR / 'models'
ASSET_DIR = BASE_DIR / 'assets'
IMAGE_DIR = BASE_DIR / 'assets' / 'icons'

# ── Crisis Level Thresholds ───────────────────────────────────────────
# crisis_score_100 >= nilai → masuk level tersebut
THRESHOLD = {
    'WASPADA': 30,   # score >= 30
    'SIAGA':   45,   # score >= 45
    'KRISIS':  60,   # score >= 60
    # score < 30 → AMAN
}

# ── Level Metadata ────────────────────────────────────────────────────
LABEL_ORDER = ['AMAN', 'WASPADA', 'SIAGA', 'KRISIS']   # severity ascending

# Warna level — HARUS SAMA dengan dashboard_indri.py CSS variables
COLOR_MAP = {
    'AMAN':    '#236A26',   # --c-aman
    'WASPADA': '#F9F871',   # --c-waspada
    'SIAGA':   '#ff6c43',   # --c-siaga
    'KRISIS':  '#d90000',   # --c-krisis
}

LEVEL_COLORS = COLOR_MAP   # alias untuk kompatibilitas

BG_MAP = {
    'AMAN':    'rgba(35,106,38,.15)',
    'WASPADA': 'rgba(249,248,113,.12)',
    'SIAGA':   'rgba(255,108,67,.15)',
    'KRISIS':  'rgba(217,0,0,.15)',
}

LEVEL_DESC = {
    'AMAN':    'Kondisi pariwisata normal dan stabil',
    'WASPADA': 'Tanda perlambatan terdeteksi, perlu pemantauan',
    'SIAGA':   'Tekanan signifikan, diperlukan respons aktif',
    'KRISIS':  'Krisis aktif, diperlukan intervensi segera',
}

# ── Model Features ────────────────────────────────────────────────────
FEATURES_CORE = [
    'wisman_growth_mom', 'wisman_growth_yoy', 'wisman_zscore',
    'usd_idr_avg', 'usd_volatility_3m', 'usd_change_mom',
    'tpk_bintang', 'tpk_change_mom',
    'inflasi_processed', 'bali_share_pct',
    'avg_sentiment_monthly', 'month_num', 'is_peak_season',
]
FEATURES_LAG = [
    'wisman_lag_1', 'wisman_lag_3',
    'wisman_trend_3m', 'wisman_recovery_pct',
]

# ── Crisis Score Weights ──────────────────────────────────────────────
# Dipakai di: update_pipeline.py, retrain_model.py, services/simulation.py
WEIGHT_TOURISM   = 0.75
WEIGHT_ECONOMY   = 0.20
WEIGHT_SENTIMENT = 0.05

# ── Model Config ──────────────────────────────────────────────────────
RF_PARAMS = dict(
    n_estimators=200,
    max_depth=None,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1,
)
ISO_PARAMS = dict(
    n_estimators=200,
    contamination=0.05,
    max_features=1.0,
    bootstrap=False,
    random_state=42,
    n_jobs=-1,
)

# ── LLM Config ────────────────────────────────────────────────────────
GROQ_MODEL      = 'llama3-8b-8192'
GROQ_ENDPOINT   = 'https://api.groq.com/openai/v1/chat/completions'
ANTHROPIC_MODEL = 'claude-sonnet-4-5'

# ── Chart Styling ─────────────────────────────────────────────────────
CHART_FONT     = dict(family='Inter, sans-serif', size=12, color='#94a3b8')
CHART_PAPER_BG = 'rgba(0,0,0,0)'
CHART_PLOT_BG  = 'rgba(255,255,255,0.02)'
CHART_GRID     = 'rgba(255,255,255,0.06)'
