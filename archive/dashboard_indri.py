import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib, json, os, sys, urllib.request, time
from datetime import datetime
from PIL import Image
import base64

# ── PERFORMANCE TIMER — mulai saat rerun dimulai ──────────
_t_start = time.perf_counter()
_t = {}   # dict untuk catat waktu tiap section
def _tick(label):
    _t[label] = time.perf_counter() - _t_start

# ── Cache logo agar tidak dibaca ulang setiap rerun ──
@st.cache_resource
def _load_logo():
    with open("images/FIX.png", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"

_logo_html = _load_logo()

st.set_page_config(
    page_title="BaliGuard — Early Warning Pariwisata",
    page_icon="images/FIX.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════
# CSS — LUXURY DARK THEME
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --c-bg:        #060d1c;
  --c-surface:   #0d1b33;
  --c-border:    rgba(255,255,255,0.07);
  --c-text:      #e2e8f0;
  --c-muted:     #64748b;
  --c-dimmer:    #334155;
  --c-aman:      #22c55e;
  --c-waspada:   #f59e0b;
  --c-siaga:     #f97316;
  --c-krisis:    #ef4444;
  --c-accent:    #3b82f6;
  --c-accent-lt: #93c5fd;
  --radius-lg:   18px;
  --radius-md:   12px;
  --radius-sm:   8px;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: var(--c-bg);
  color: var(--c-text);
  font-size: 14px;
}
.main { background: var(--c-bg); }
.block-container { padding: 3.5rem 2rem 3rem; max-width: 1680px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--c-surface) !important;
  border-right: 1px solid var(--c-border);
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label { font-size: 13px !important; line-height: 1.8 !important; }
[data-testid="stSidebar"] b { color: #e2e8f0 !important; }

/* ── KPI Cards — redesigned ── */
.kpi-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 16px 18px 14px;
  border-top: 2px solid var(--c-accent);
  position: relative;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}
.kpi-card::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 80px; height: 80px;
  background: radial-gradient(circle at top right, rgba(255,255,255,0.04), transparent 70%);
  pointer-events: none;
}
.kpi-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--c-muted);
  text-transform: uppercase;
  letter-spacing: .12em;
  margin-bottom: 10px;
  font-family: 'DM Sans';
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.15;
  font-family: 'DM Serif Display';
  word-break: break-word;
}
.kpi-sub {
  font-size: 10px;
  color: var(--c-dimmer);
  margin-top: 6px;
  line-height: 1.5;
}
.kpi-delta {
  margin-top: 7px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono';
  line-height: 1.4;
}

/* ── KPI level accent colors ── */
.kpi-AMAN    { border-top-color: var(--c-aman);    }
.kpi-WASPADA { border-top-color: var(--c-waspada); }
.kpi-SIAGA   { border-top-color: var(--c-siaga);   }
.kpi-KRISIS  { border-top-color: var(--c-krisis);  }

/* ── Alert Boxes ── */
.alert-aman    { background:rgba(34,197,94,0.07);  border-left:3px solid var(--c-aman);    padding:14px 20px; border-radius:var(--radius-sm); margin-top:14px; }
.alert-waspada { background:rgba(245,158,11,0.07); border-left:3px solid var(--c-waspada); padding:14px 20px; border-radius:var(--radius-sm); margin-top:14px; }
.alert-siaga   { background:rgba(249,115,22,0.07); border-left:3px solid var(--c-siaga);   padding:14px 20px; border-radius:var(--radius-sm); margin-top:14px; }
.alert-krisis  { background:rgba(239,68,68,0.09);  border-left:3px solid var(--c-krisis);  padding:14px 20px; border-radius:var(--radius-sm); margin-top:14px; }
.alert-title   { font-family:'DM Sans'; font-size:16px; font-weight:700; color:#f1f5f9; margin-bottom:6px; }
.alert-body    { font-size:14px; color:#cbd5e1; line-height:1.75; }

/* ── Section Titles ── */
.section-title {
  font-family: 'DM Sans';
  font-size: 15px;
  font-weight: 700;
  padding: 0 0 14px;
  letter-spacing: .04em;
  text-transform: uppercase;
  display: block;
  margin-top: 0;
}
.sec-blue   { color: #60a5fa !important; border-left: 3px solid var(--c-accent);  padding-left: 10px !important; }
.sec-orange { color: #fb923c !important; border-left: 3px solid var(--c-siaga);   padding-left: 10px !important; }
.sec-green  { color: #4ade80 !important; border-left: 3px solid var(--c-aman);    padding-left: 10px !important; }
.sec-purple { color: #c084fc !important; border-left: 3px solid #a855f7;          padding-left: 10px !important; }
.sec-amber  { color: #fcd34d !important; border-left: 3px solid var(--c-waspada); padding-left: 10px !important; }
.sec-red    { color: #f87171 !important; border-left: 3px solid var(--c-krisis);  padding-left: 10px !important; }
.sec-teal   { color: #2dd4bf !important; border-left: 3px solid #14b8a6;          padding-left: 10px !important; }
.sec-sky    { color: #38bdf8 !important; border-left: 3px solid #0ea5e9;          padding-left: 10px !important; }
.sec-gap-sm { margin-top: 16px; }
.sec-gap-md { margin-top: 24px; }
.sec-gap-lg { margin-top: 32px; }

/* ── Narrative Box ── */
.narrative-box {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 22px 26px;
  line-height: 1.9;
  font-size: 14px;
  color: #cbd5e1;
  white-space: pre-wrap;
  font-family: 'DM Sans';
}

/* ── Forecast Card ── */
.fc-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 10px;
  transition: border-color .2s, background .2s;
}
.fc-card:hover { border-color: rgba(255,255,255,0.14); background: rgba(255,255,255,0.05); }

/* ── Risk Row ── */
.risk-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 13px;
}
.risk-name { color: #94a3b8; }
.risk-val  { color: #e2e8f0; font-weight: 700; font-family: 'JetBrains Mono'; font-size: 12px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px 12px 0 0;
  padding: 6px 6px 0;
  display: flex;
  width: 100%;
}
.stTabs [data-baseweb="tab"] {
  flex: 1;
  border-radius: 8px 8px 0 0;
  padding: 12px 16px;
  font-weight: 700 !important;
  font-size: 14px !important;
  color: #cbd5e1 !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
  letter-spacing: .03em;
  text-align: center;
  justify-content: center;
  transition: color .18s, background .18s;
}
.stTabs [data-baseweb="tab"]:hover {
  color: #f1f5f9 !important;
  background: rgba(255,255,255,0.07) !important;
}
.stTabs [aria-selected="true"] {
  color: #ffffff !important;
  background: rgba(59,130,246,0.18) !important;
  border-bottom: 2px solid #60a5fa !important;
  text-shadow: 0 0 20px rgba(147,197,253,0.4);
}

/* ── Badge ── */
.badge { display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: .03em; }
.badge-green  { background: rgba(34,197,94,0.15);  color: #4ade80; }
.badge-yellow { background: rgba(245,158,11,0.15); color: #fbbf24; }
.badge-orange { background: rgba(249,115,22,0.15); color: #fb923c; }
.badge-red    { background: rgba(239,68,68,0.15);  color: #f87171; }

/* ── Sidebar Nav Buttons ── */
[data-testid="stSidebar"] [data-testid="stButton"] button {
  width: 100%;
  padding: 8px 12px !important;
  border-radius: 8px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: #94a3b8 !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  cursor: pointer;
  transition: background .15s, color .15s, border-color .15s;
  font-family: 'DM Sans', sans-serif !important;
  letter-spacing: .01em;
  justify-content: flex-start !important;
  text-align: left !important;
  box-shadow: none !important;
  display: flex !important;
  align-items: center !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button > div,
[data-testid="stSidebar"] [data-testid="stButton"] button p,
[data-testid="stSidebar"] [data-testid="stButton"] button span {
  text-align: left !important;
  justify-content: flex-start !important;
  width: 100% !important;
  margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #e2e8f0 !important;
  border-color: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:focus {
  outline: none !important;
  box-shadow: none !important;
}
/* Active (primary) nav button */
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
  background: rgba(59,130,246,0.18) !important;
  color: #93c5fd !important;
  border-color: rgba(59,130,246,0.35) !important;
  font-weight: 700 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {
  background: rgba(59,130,246,0.25) !important;
}
/* Reduce gap between nav buttons */
[data-testid="stSidebar"] [data-testid="stButton"] {
  margin-bottom: -10px !important;
}

/* Fix emoji alignment in nav buttons */
[data-testid="stSidebar"] [data-testid="stButton"] button p {
  display: flex !important;
  align-items: center !important;
}

/* ── Collapse iframe margin (components.html) ── */

[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-family: 'DM Serif Display' !important; font-size: 22px !important; }
[data-testid="stMetricLabel"] { color: var(--c-muted) !important; font-size: 11px !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid var(--c-border) !important;
  border-radius: var(--radius-sm) !important;
}

/* ── Groq expander: tighten gap below text_input ── */
[data-testid="stExpander"] [data-testid="stTextInput"] {
  margin-bottom: -10px !important;
  margin-top: -10px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { background: transparent !important; }
.dvn-scroller { background: rgba(255,255,255,0.02) !important; }

/* ── Selectbox / slider ── */
[data-baseweb="select"] { background: rgba(255,255,255,0.05) !important; }
.stSlider [data-baseweb="slider"] { background: rgba(255,255,255,0.08) !important; }
.stSlider label p { font-size:14px !important; font-weight:700 !important; color:#e2e8f0 !important; letter-spacing:.01em !important; }
[data-testid='stButton-pct_trend'] button p,[data-testid='stButton-pct_rec'] button p,[data-testid='stButton-pct_scatter'] button p { font-weight:800 !important; letter-spacing:.02em !important; }
[data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { display: none !important; visibility: hidden !important; }

/* ── Status dot (SVG-based, replaces emoji circles) ── */
.status-dot {
  display: inline-block;
  width: 16px !important;
  height: 16px !important;
  border-radius: 50%;
  margin-right: 7px;
  vertical-align: middle;
  flex-shrink: 0;
}
.dot-AMAN    { background: var(--c-aman);    box-shadow: 0 0 6px var(--c-aman);    }
.dot-WASPADA { background: var(--c-waspada); box-shadow: 0 0 6px var(--c-waspada); }
.dot-SIAGA   { background: var(--c-siaga);   box-shadow: 0 0 6px var(--c-siaga);   }
.dot-KRISIS  { background: var(--c-krisis);  box-shadow: 0 0 6px var(--c-krisis);  }

/* ── Projection Banner stats ── */
.proj-stat { text-align: center; min-width: 80px; }
.proj-stat-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--c-muted);
  margin-bottom: 4px;
}
.proj-stat-value {
  font-family: 'JetBrains Mono';
  font-size: 17px;
  font-weight: 700;
  color: var(--c-accent-lt);
}

/* ── Live badge ── */
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  background: rgba(74,222,128,0.12);
  color: #4ade80;
  padding: 3px 8px;
  border-radius: 20px;
  border: 1px solid rgba(74,222,128,0.25);
  letter-spacing: .04em;
}
.live-pulse {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #4ade80;
  animation: pulse 1.5s infinite;
  flex-shrink: 0;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .4; transform: scale(.7); }
}

/*── Navigasi: button transparan di atas visual div (click area fix) ──*/
[data-testid="stSidebar"] .stButton button {
  opacity: 0 !important;
  height: 38px !important;
  min-height: 38px !important;
  padding: 0 !important;
  margin: -41px 0 3px 0 !important;
  border: none !important;
  background: transparent !important;
  pointer-events: all !important;
  position: relative !important;
  z-index: 10 !important;
  width: 100% !important;
  cursor: pointer !important;
}
[data-testid="stSidebar"] .stButton {
  margin-bottom: 0 !important;
}

/* ── Accent top-border (global — berlaku di semua tab) ── */
.accent-blue   { display:block; border-top: 3px solid #3b82f6; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
.accent-orange { display:block; border-top: 3px solid #f97316; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
.accent-purple { display:block; border-top: 3px solid #a855f7; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
.accent-green  { display:block; border-top: 3px solid #22c55e; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
.accent-teal   { display:block; border-top: 3px solid #14b8a6; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════
COLOR_MAP  = {'AMAN':'#22c55e','WASPADA':'#f59e0b','SIAGA':'#f97316','KRISIS':'#ef4444'}
EMOJI_MAP  = {'AMAN':'','WASPADA':'','SIAGA':'','KRISIS':''}
def status_dot(level):
    return f"<span class='status-dot dot-{level}'></span>"
BADGE_MAP  = {'AMAN':'badge-green','WASPADA':'badge-yellow','SIAGA':'badge-orange','KRISIS':'badge-red'}
ALERT_MAP  = {'AMAN':'alert-aman','WASPADA':'alert-waspada','SIAGA':'alert-siaga','KRISIS':'alert-krisis'}
GROQ_MODEL = 'llama-3.3-70b-versatile'


FEATURES = [
    'wisman_growth_mom','wisman_growth_yoy','wisman_zscore',
    'usd_idr_avg','usd_volatility_3m','usd_change_mom',
    'tpk_bintang','tpk_change_mom','inflasi_processed',
    'bali_share_pct','avg_sentiment_monthly','month_num','is_peak_season'
]

ADVICE_MAP = {
    'AMAN':    ["Manfaatkan momentum positif untuk ekspansi promosi ke segmen pasar baru.",
                "Pertahankan kualitas layanan dan pantau indikator secara berkala.",
                "Siapkan protokol respons untuk mengantisipasi perubahan mendadak."],
    'WASPADA': ["Tingkatkan frekuensi pemantauan data wisman dan sentimen secara mingguan.",
                "Koordinasikan dengan dinas terkait untuk identifikasi faktor risiko.",
                "Pertimbangkan kampanye promosi untuk menstabilkan arus wisatawan."],
    'SIAGA':   ["Aktifkan satgas pariwisata dan lakukan rapat koordinasi darurat.",
                "Evaluasi penyebab: volatilitas kurs, sentimen negatif, atau faktor eksternal.",
                "Siapkan paket insentif wisatawan dan stimulus industri perhotelan."],
    'KRISIS':  ["Deklarasikan status darurat pariwisata dan aktifkan protokol krisis penuh.",
                "Intervensi langsung: subsidi, relaksasi regulasi, stimulus fiskal sektoral.",
                "Bentuk posko lintas kementerian dan koordinasi penanganan krisis segera."]
}

# ══════════════════════════════════════════════════════
# LOAD DATA & MODELS
# ══════════════════════════════════════════════════════
@st.cache_resource
def load_data():
    master = pd.read_parquet('data/final/master_dataset_clean.parquet')
    pred   = pd.read_csv('data/final/predictions_final.csv')
    cache  = {}
    p = 'data/final/narratives_cache.json'
    if os.path.exists(p):
        with open(p,'r',encoding='utf-8') as f: cache = json.load(f)
    return master, pred, cache

@st.cache_resource                                          # ✅ Icons di-cache — tidak dibuat ulang setiap rerun
def _build_nav_icons() -> dict:
    """Base64 nav icons — dibuat sekali, disimpan di memory selama app hidup."""
    return {
        "Overview & Timeline": "data:image/png;base64,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",
        "Analisis Detail":     "data:image/png;base64,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",
        "Sentimen":            "data:image/png;base64,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",
        "Prediksi & Proyeksi": "data:image/png;base64,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",
        "Narasi AI":           "data:image/png;base64,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",
    }

@st.cache_resource
def load_models():
    rf     = joblib.load('models/model_random_forest.pkl')   # ✅ FIX: was label_encoder.pkl
    iso_f  = joblib.load('models/model_isolation_forest.pkl')
    scaler = joblib.load('models/scaler.pkl')
    le     = joblib.load('models/label_encoder.pkl')
    return rf, iso_f, scaler, le

try:
    master, predictions, narratives_cache = load_data()
    rf_model, iso_model, scaler, le = load_models()
    DATA_OK = True
    _tick("load_data_models")
except Exception as e:
    DATA_OK = False; DATA_ERR = str(e)

if not DATA_OK:
    st.error(f"❌ Gagal memuat data/model: {DATA_ERR}")
    st.info("Pastikan semua file ada di `data/final/` dan `data/models/`.")
    st.stop()

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════
def _get_groq_key() -> str:
    try:
        k = st.secrets.get("GROQ_API", "")
        if k: return k
    except Exception:
        pass
    return os.environ.get("GROQ_API", "")

def sf(val, d=0.0):
    try: return float(val)
    except: return d

_last_data_month = predictions['month'].iloc[-1]

@st.cache_data(show_spinner=False)
def get_row(m):
    r = predictions[predictions['month'] == m]
    if len(r):
        return r.iloc[0]
    # Bulan di luar dataset → proyeksi
    if str(m) > _last_data_month:
        return pd.Series(project_future_row(predictions, str(m)))
    return predictions.iloc[-1]


def kpi_html(label, value, sub="", level=None):
    cls = f"kpi-card kpi-{level}" if level else "kpi-card"
    return (f'<div class="{cls}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')

def alert_html(level, title, body):
    return (f'<div class="{ALERT_MAP.get(level,"alert-aman")}">'
            f'<div class="alert-title">{title}</div>'
            f'<div class="alert-body">{body}</div></div>')

def level_from_score(s):
    # Threshold disesuaikan distribusi aktual data (range 11.5–48.1)
    # 42 = tepat menangkap Mar-Apr 2020 COVID sebagai KRISIS (validasi empiris)
    if s >= 60: return 'KRISIS'
    if s >= 45: return 'SIAGA'
    if s >= 30: return 'WASPADA'
    return 'AMAN'

# ── Live USD/IDR ──────────────────────────────────────────────
@st.cache_resource
def fetch_live_usd_idr() -> float | None:
    """Ambil kurs USD/IDR live dari Frankfurter → Open ER. Cache 1 jam."""
    sources = [
        ("https://api.frankfurter.app/latest?from=USD&to=IDR",
         lambda d: float(d["rates"]["IDR"])),
        ("https://open.er-api.com/v6/latest/USD",
         lambda d: float(d["rates"]["IDR"])),
    ]
    for url, parser in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BaliGuard/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            rate = parser(data)
            if rate and rate > 5000:
                return round(rate, 0)
        except Exception:
            continue
    return None

def get_current_usd_idr(predictions: pd.DataFrame, month: str) -> tuple[float, bool]:
    """
    Return (usd_rate, is_live).
    Untuk bulan sekarang/masa depan → coba live rate.
    Untuk bulan historis → dari dataset.
    """
    now_month = datetime.now().strftime('%Y-%m')
    last_data = predictions['month'].iloc[-1]

    if month >= last_data:
        live = fetch_live_usd_idr()
        if live:
            return live, True
    val = float(predictions[predictions['month'] == month]['usd_idr_avg'].iloc[0]) \
          if month in predictions['month'].values else 0.0
    return val, False

def project_future_row(predictions: pd.DataFrame, target_month: str) -> dict:
    """Proyeksi data untuk bulan di luar dataset."""
    last   = dict(predictions.iloc[-1])
    lm     = predictions['month'].iloc[-1]
    n      = int((pd.Period(target_month, freq='M') - pd.Period(lm, freq='M')).n)
    tail12 = predictions.tail(12)

    # Crisis score trend
    score_trend = float(np.polyfit(range(len(tail12)), tail12['crisis_score_100'].values, 1)[0])
    proj_score  = float(np.clip(float(last['crisis_score_100']) + score_trend * n, 0, 100))

    # Wisman: tren + seasonal
    if len(predictions) >= 24:
        month_key   = target_month[5:7]
        monthly_avg = predictions.groupby(predictions['month'].str[5:7])['wisman'].mean()
        seasonal    = float(monthly_avg.get(month_key, monthly_avg.mean())) / max(monthly_avg.mean(), 1)
        w_trend     = float(np.polyfit(range(len(tail12)), tail12['wisman'].values, 1)[0])
        proj_wisman = max(0, int((float(last['wisman']) + w_trend * n) * seasonal))
    else:
        proj_wisman = int(last.get('wisman', 0))

    # TPK trend
    tpk_trend = float(np.polyfit(range(len(tail12)), tail12['tpk_bintang'].values, 1)[0])
    proj_tpk  = float(np.clip(float(last['tpk_bintang']) + tpk_trend * n, 0, 100))

    # Sentimen mean-revert
    proj_sent = float(last.get('avg_sentiment_monthly', 0.5)) * (0.95 ** n) + 0.5 * (1 - 0.95 ** n)

    # USD/IDR: coba live, fallback trend
    live_rate = fetch_live_usd_idr()
    if live_rate:
        usd_trend = float(np.polyfit(range(len(tail12)), tail12['usd_idr_avg'].values, 1)[0])
        proj_usd  = live_rate + usd_trend * max(0, n - 1)
    else:
        usd_trend = float(np.polyfit(range(len(tail12)), tail12['usd_idr_avg'].values, 1)[0])
        proj_usd  = float(last.get('usd_idr_avg', 15500)) + usd_trend * n

    proj = dict(last)
    proj.update({
        'month'                 : target_month,
        'crisis_score_100'      : proj_score,
        'crisis_level'          : level_from_score(proj_score),
        'rf_predicted_level'    : level_from_score(proj_score),
        'rf_confidence'         : max(0.35, float(last.get('rf_confidence', 0.70)) - 0.05 * n),
        'iso_anomaly'           : 0,
        'wisman'                : proj_wisman,
        'tpk_bintang'           : proj_tpk,
        'avg_sentiment_monthly' : proj_sent,
        'usd_idr_avg'           : proj_usd,
        'inflasi_processed'     : float(last.get('inflasi_processed', 3.0)),
        'bali_share_pct'        : float(last.get('bali_share_pct', 40.0)),
        'wisman_zscore'         : 0.0,
        'prob_krisis'           : proj_score / 200,
        'prob_siaga'            : 0.3,
        '_is_projected'         : True,
        '_proj_confidence'      : max(35, 85 - (n - 1) * 8),
    })
    return proj

@st.cache_data(show_spinner=False)
def forecast_months(pred_df, n=6, from_month=None):
    """Proyeksi n bulan ke depan dari titik yang dipilih (default: data terakhir)."""
    last_n     = pred_df.tail(12)
    last_val   = float(last_n['crisis_score_100'].values[-1])
    trend      = float(np.polyfit(range(len(last_n)), last_n['crisis_score_100'].values, 1)[0])
    data_last_p = pd.Period(pred_df['month'].iloc[-1], freq='M')

    if from_month is None:
        start_p = data_last_p
        base    = last_val
    else:
        start_p = pd.Period(from_month, freq='M')
        offset  = int((start_p - data_last_p).n)
        base    = float(np.clip(last_val + trend * offset, 0, 100))

    results = []
    for i in range(1, n+1):
        p    = start_p + i
        sc   = float(np.clip(base + trend * i, 0, 100))
        conf = max(35.0, 85.0 - (i - 1) * 10.0)
        results.append({'month': str(p), 'score': round(sc, 1),
                        'level': level_from_score(sc), 'confidence': conf})
    return results, round(trend, 2)

def simulate_score(row, wisman_delta, usd_delta, sent_delta):
    ct = sf(row.get('crisis_component_tourism', 0.4))
    ce = sf(row.get('crisis_component_economy', 0.3))
    cs = sf(row.get('crisis_component_sentiment', 0.25))
    ct2 = float(np.clip(ct - (wisman_delta/100)*0.5, 0, 1))
    ce2 = float(np.clip(ce + (usd_delta/100)*0.3, 0, 1))
    cs2 = float(np.clip(cs - sent_delta*0.2, 0, 1))
    return round((0.45*ct2 + 0.30*ce2 + 0.25*cs2)*100, 1)

@st.cache_data(show_spinner=False)
def compute_delta_context(row_data_dict, pred_df, sel_month):
    """Hitung score_delta, dominant_factor, anomaly_explanation, recovery_pct."""
    row_data = row_data_dict
    score  = sf(row_data.get('crisis_score_100', 0))
    zscore = sf(row_data.get('wisman_zscore', 0))
    wisman_val = int(sf(row_data.get('wisman', 0)))

    # Score delta vs bulan lalu
    sorted_months = sorted(pred_df['month'].unique())
    idx_list = [i for i, m in enumerate(sorted_months) if m == sel_month]
    delta, trend = 0.0, 'STABIL'
    if idx_list and idx_list[0] > 0:
        prev_m     = sorted_months[idx_list[0] - 1]
        prev_score = sf(pred_df[pred_df['month'] == prev_m]['crisis_score_100'].values[0]
                        if len(pred_df[pred_df['month'] == prev_m]) > 0 else score)
        delta = round(score - prev_score, 1)
        trend = 'MENINGKAT' if delta > 2 else ('MENURUN' if delta < -2 else 'STABIL')

    # Dominant factor (heuristic dari nilai komponen)
    factors = {
        'Kunjungan Wisatawan': abs(zscore),
        'Sentimen Negatif':    sf(row_data.get('pct_negative_monthly', 0)) / 100.0,
        'Tekanan Kurs':        sf(row_data.get('usd_volatility_3m', 0)) / 1000.0,
    }
    dominant = max(factors, key=factors.get)

    # Anomaly explanation berdasarkan z-score
    if zscore <= -3:
        anom_exp = f'Z-score {zscore:.2f} — kunjungan {abs(zscore):.1f}× std di bawah rata-rata 12 bln. Kejadian sangat ekstrem (<0.1%).'
    elif zscore <= -2:
        anom_exp = f'Z-score {zscore:.2f} — anomali signifikan, jauh di bawah baseline historis.'
    elif zscore >= 2:
        anom_exp = f'Z-score {zscore:.2f} — kunjungan di atas normal, potensi peak season atau event besar.'
    else:
        anom_exp = f'Z-score {zscore:.2f} — kunjungan dalam rentang normal (±2 std).'

    # Recovery % vs baseline pre-COVID 2017-2019
    pre_covid = pred_df[
        pd.to_datetime(pred_df['month'].astype(str)).dt.year.isin([2017, 2018, 2019])
    ]['wisman'] if 'wisman' in pred_df.columns else pd.Series(dtype=float)
    precovid_mean = float(pre_covid.mean()) if len(pre_covid) > 0 else 0.0
    recovery_pct  = round(wisman_val / precovid_mean * 100, 1) if precovid_mean > 0 else 0.0

    return {
        'score_delta':   delta,
        'score_trend':   trend,
        'dominant':      dominant,
        'anomaly_exp':   anom_exp,
        'recovery_pct':  recovery_pct,
        'precovid_mean': round(precovid_mean, 0),
    }

# ══════════════════════════════════════════════════════
# PRE-COMPUTE FORECAST  (dari bulan nyata saat ini)
# ══════════════════════════════════════════════════════
current_real    = pd.Period(datetime.now().strftime('%Y-%m'), freq='M')
prev_real       = current_real - 1          # mulai dari bulan lalu agar bulan pertama = bulan ini
fc_list, fc_trend = forecast_months(predictions, n=6, from_month=str(prev_real))
current_fc      = fc_list[0]                # entri pertama = bulan sekarang

# ── Cache chart Overview agar tidak rebuild setiap navigasi ──
@st.cache_data(show_spinner=False)
def _build_overview_fig(sel_month_str: str):
    """Build Overview subplot figure. Di-cache per bulan yang dipilih."""
    _months_dt = pd.to_datetime(predictions['month'].astype(str))
    _sel_dt    = pd.to_datetime(sel_month_str)

    _fig = make_subplots(rows=3, cols=1,
        subplot_titles=(
            'Crisis Score & Level Krisis',
            'Kunjungan Wisatawan Mancanegara',
            'Kurs USD/IDR'
        ),
        vertical_spacing=0.18, row_heights=[0.44, 0.30, 0.26])

    _fig.add_trace(go.Scatter(x=_months_dt, y=predictions['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#cbd5e1', width=2),
        fill='tozeroy', fillcolor='rgba(148,163,184,0.06)'), row=1, col=1)
    for lv, col in COLOR_MAP.items():
        mask = predictions['crisis_level'] == lv
        if mask.sum() > 0:
            _fig.add_trace(go.Scatter(
                x=_months_dt[mask], y=predictions.loc[mask, 'crisis_score_100'],
                mode='markers', name=lv,
                marker=dict(color=col, size=7, line=dict(width=1.2, color='#050d1a')),
                hovertemplate=f'<b>{lv}</b><br>%{{x|%b %Y}}<br>Score: %{{y:.1f}}<extra></extra>'
            ), row=1, col=1)
    for thr, lbl, col in [(60, 'KRISIS', '#ef4444'), (45, 'SIAGA', '#f97316'), (30, 'WASPADA', '#f59e0b')]:
        _fig.add_hline(y=thr, line_dash='dot', line_color=col, line_width=1, opacity=0.7,
                       annotation_text=lbl, annotation_position='right',
                       annotation_font_size=9, annotation_font_color=col,
                       annotation_xanchor='left', annotation_xshift=-52,
                       row=1, col=1)

    _fig.add_trace(go.Scatter(x=_months_dt, y=predictions['wisman'],
        mode='lines', name='Wisman', showlegend=False,
        line=dict(color='#7dd3fc', width=2),
        fill='tozeroy', fillcolor='rgba(96,165,250,0.09)'), row=2, col=1)

    if 'usd_idr_avg' in predictions.columns:
        _fig.add_trace(go.Scatter(x=_months_dt, y=predictions['usd_idr_avg'],
            mode='lines', name='USD/IDR', showlegend=False,
            line=dict(color='#fbbf24', width=2)), row=3, col=1)

    for r in [1, 2, 3]:
        _fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
            fillcolor='rgba(239,68,68,0.06)', line_width=0,
            annotation_text='COVID-19' if r == 1 else '',
            annotation_font_color='#ef4444',
            annotation_font_size=10, row=r, col=1)
        _fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa',
                       line_width=1.2, row=r, col=1)

    _EVENTS = [
        ('2002-10-12', 'Bom Bali I',       '#ef4444', 'circle'),
        ('2005-10-01', 'Bom Bali II',      '#f97316', 'circle'),
        ('2017-11-01', 'Erupsi Agung',     '#fb923c', 'diamond'),
        ('2018-08-05', 'Gempa Lombok',     '#f59e0b', 'diamond'),
        ('2020-03-19', 'Lockdown COVID',   '#ef4444', 'x'),
        ('2021-10-14', 'Bali Dibuka PPLN', '#22c55e', 'triangle-up'),
        ('2022-11-15', 'KTT G20 Bali',    '#a78bfa', 'star'),
        ('2023-02-01', 'Bebas Visa 20 N.', '#60a5fa', 'triangle-up'),
    ]
    for ev_date, ev_label, ev_col, ev_sym in _EVENTS:
        try:
            _ev_dt = pd.to_datetime(ev_date)
            if _ev_dt < _months_dt.min() or _ev_dt > _months_dt.max() + pd.DateOffset(months=3):
                continue
            _fig.add_vline(x=_ev_dt, line_dash='dot', line_color=ev_col,
                           line_width=0.8, opacity=0.55, row=1, col=1)
            _fig.add_annotation(
                x=_ev_dt, y=97, text=ev_label,
                showarrow=False, font=dict(size=8, color=ev_col),
                textangle=-55, xanchor='left',
                bgcolor='rgba(5,13,26,0.7)', borderpad=2,
                row=1, col=1
            )
        except Exception:
            pass

    _fig.update_layout(height=820, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(5,13,26,0.85)', bordercolor='rgba(255,255,255,0.12)',
                    borderwidth=1, font=dict(size=11, color='#e2e8f0')),
        plot_bgcolor='rgba(5,13,26,0.7)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=55, t=50, b=10),
        font=dict(family='DM Sans', size=11, color='#94a3b8'))

    _title_colors = ['#93c5fd', '#7dd3fc', '#fbbf24']
    for i, ann in enumerate(_fig.layout.annotations[:3]):
        ann.update(
            font=dict(size=17, color=_title_colors[i], family='DM Sans'),
            x=0.5, xanchor='center', yshift=18
        )
    for r in [1, 2, 3]:
        _fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                          linecolor='rgba(255,255,255,0.1)', row=r, col=1)
        _fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                          linecolor='rgba(255,255,255,0.1)', row=r, col=1)
    return _fig

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    # Logo HTML di-cache agar tidak rebuild string base64 besar setiap rerun
    if '_sidebar_logo_html' not in st.session_state:
        st.session_state['_sidebar_logo_html'] = (
            "<div style='text-align:center;padding:20px 0 8px'>"
            f"<img src='{_logo_html}' style='width:130px;height:130px;object-fit:contain;margin-bottom:8px;border-radius:16px'/>"
            "<div style='font-family:DM Serif Display;font-size:30px;color:#f1f5f9;letter-spacing:-.01em'>BaliGuard</div>"
            "<div style='font-size:11px;color:#64748b;margin-top:5px;letter-spacing:.1em;font-weight:700'>EARLY WARNING SYSTEM</div>"
            "</div>"
        )
    st.markdown(st.session_state['_sidebar_logo_html'], unsafe_allow_html=True)
    st.divider()

    if '_avail_months' not in st.session_state:
        _avail_hist = sorted(predictions['month'].unique(), reverse=True)
        _ld = predictions['month'].iloc[-1]
        _p  = pd.Period(_ld, freq='M')
        _fut = sorted([str(_p + i) for i in range(1, 25) if str(_p + i) > _ld], reverse=True)
        st.session_state['_avail_months'] = _fut + _avail_hist
        st.session_state['_last_data_sb'] = _ld
    avail      = st.session_state['_avail_months']
    _last_data = st.session_state['_last_data_sb']
    # Format label: tambah tag [PROYEKSI] untuk masa depan
    def _month_label(m):
        if m > _last_data:
            return f"{m}  "
        return m
    st.markdown(
        "<div style='display:flex;align-items:center;gap:7px;margin-bottom:4px;font-size:13px;font-weight:600;color:#e2e8f0'>"
        "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
        "background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0'></span>"
        "Periode Analisis</div>",
        unsafe_allow_html=True)
    sel = st.selectbox("", avail,
                       format_func=_month_label,
                       help="Bulan dengan = proyeksi (belum ada data BPS)",
                       label_visibility="collapsed")
    sel_dt = pd.to_datetime(sel)

    st.divider()
    # ── Navigasi Halaman ──────────────────────────────────
    NAV_ICONS_B64 = _build_nav_icons()  # ✅ FIX: pakai cached version
    NAV_OPTIONS = [
        "Overview & Timeline",
        "Analisis Detail",
        "Sentimen",
        "Prediksi & Proyeksi",
        "Narasi AI",
    ]
    if "selected_nav" not in st.session_state:
        st.session_state.selected_nav = "Overview & Timeline"

    _cur_nav = st.session_state.selected_nav

    # ── Render semua nav item sekaligus + JS highlight instan di browser ──
    _nav_items_html = []
    for _lbl in NAV_OPTIONS:
        _active  = _cur_nav == _lbl
        _img     = NAV_ICONS_B64.get(_lbl, "")
        _bg      = "rgba(59,130,246,0.18)" if _active else "transparent"
        _border  = "1px solid rgba(59,130,246,0.50)" if _active else "1px solid transparent"
        _color   = "#e2e8f0" if _active else "#94a3b8"
        _opacity = "1" if _active else "0.6"
        _fw      = "700" if _active else "500"
        _id      = _lbl.replace(' ', '_').replace('&', 'n')
        _nav_items_html.append(
            f"<div id='nav-item-{_id}' data-nav='{_lbl}' "
            f"style='display:flex;align-items:center;gap:10px;padding:8px 12px;"
            f"border-radius:8px;background:{_bg};border:{_border};"
            f"margin-bottom:3px;cursor:pointer;transition:background 0.12s,border 0.12s'>"
            f"<img src='{_img}' style='width:18px;height:18px;object-fit:contain;opacity:{_opacity}'>"
            f"<span style='font-size:13px;font-weight:{_fw};color:{_color}'>{_lbl}</span>"
            f"</div>"
        )
    st.markdown(
        "<div style='font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;"
        "letter-spacing:.12em;margin-bottom:6px;font-family:"DM Sans"'>NAVIGASI</div>"
        + "".join(_nav_items_html)
        + """<script>
(function(){
  var items = document.querySelectorAll('[data-nav]');
  items.forEach(function(el){
    el.addEventListener('mousedown', function(){
      // Update highlight instan di browser — sebelum Python rerun dimulai
      items.forEach(function(x){
        x.style.background = 'transparent';
        x.style.border = '1px solid transparent';
        var sp = x.querySelector('span');
        if(sp){ sp.style.color='#94a3b8'; sp.style.fontWeight='500'; }
        var img = x.querySelector('img');
        if(img){ img.style.opacity='0.6'; }
      });
      el.style.background = 'rgba(59,130,246,0.18)';
      el.style.border = '1px solid rgba(59,130,246,0.50)';
      var sp = el.querySelector('span');
      if(sp){ sp.style.color='#e2e8f0'; sp.style.fontWeight='700'; }
      var img = el.querySelector('img');
      if(img){ img.style.opacity='1'; }
    });
  });
})();
</script>""",
        unsafe_allow_html=True
    )

    # Button invisible (1 baris) — hanya trigger rerun Python untuk ganti konten halaman
    _btn_cols = st.columns(len(NAV_OPTIONS))
    for i, _lbl in enumerate(NAV_OPTIONS):
        with _btn_cols[i]:
            if st.button("·", key=f"nav_{_lbl}", help=_lbl):
                st.session_state.selected_nav = _lbl

    selected_nav = st.session_state.selected_nav
    _tick("sidebar_render")

    # st.divider()
    # # ── Groq API Key (tersembunyi di expander) ────────────
    # with st.expander("✦ API untuk Aktifkan Narasi AI", expanded=False):
    #     st.caption("Masukkan API key Groq Anda untuk mengaktifkan narasi AI.")
    #     groq_key = st.text_input("API Key", type="password", placeholder="gsk_...",
    #                               label_visibility="collapsed",
    #                               help="Dapatkan gratis di console.groq.com")
    #     if not groq_key:
    #         st.caption("↵ Tekan Enter untuk menerapkan")
    #         st.caption("💡 [Key gratis → console.groq.com](https://console.groq.com/keys)")
    #     else:
    #         st.caption("✅ API key aktif")

    st.divider()
    
    row_s = get_row(sel)
    lv_s  = str(row_s.get('crisis_level','WASPADA'))
    sc_s  = sf(row_s.get('crisis_score_100',0))
    an_s  = int(sf(row_s.get('iso_anomaly',0)))
    st.markdown(f"""
    <div style='background:rgba(255,255,255,0.04);border-radius:12px;padding:14px 16px;
                border:1px solid rgba(255,255,255,0.07)'>
        <div style='font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:10px'>STATUS DIPILIH</div>
        <div style='font-family:"DM Serif Display";font-size:24px;color:{COLOR_MAP.get(lv_s,"#fff")};
                    display:flex;align-items:center;gap:8px'>
            <span class='status-dot dot-{lv_s}' style='width:11px;height:11px;flex-shrink:0'></span>
            {lv_s}
        </div>
        <div style='font-family:"JetBrains Mono";font-size:12px;color:#64748b;margin-top:4px'>
            Score {sc_s:.1f} / 100
        </div>
        <div style='margin-top:8px;font-size:11px;font-weight:600;
                    color:{"#f97316" if an_s else "#22c55e"}'>
            {"⚠️ Anomali Terdeteksi" if an_s else "✅ Tidak Ada Anomali"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style='font-size:11px;color:#374151;line-height:1.9'>
        <b style='color:#64748b'>DATA SUMBER</b><br>
        BPS Bali · Bank Indonesia<br>
        Google Hotels Review · Kaggle<br><br>
        <b style='color:#64748b'>MODEL</b><br>
        Isolation Forest<br>
        Random Forest Classifier<br>
        XLM-RoBERTa Sentiment<br><br>
        <b style='color:#64748b'>NARASI</b><br>
        Groq · Multi-Model LLM
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════
_last_month = predictions['month'].iloc[-1]
_n_months   = len(predictions)
st.markdown(f"""
<div style='background:linear-gradient(135deg,#0a1628 0%,#132349 55%,#0c1d40 100%);
            border-radius:18px;padding:26px 32px;margin-bottom:20px;
            border:1px solid rgba(255,255,255,0.09);
            box-shadow:0 8px 40px rgba(0,0,0,0.5)'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px'>
        <!-- Left: logo + wordmark -->
        <div style='display:flex;align-items:center;gap:16px'>
            <img src='{_logo_html}' style='width:80px;height:80px;object-fit:contain;border-radius:12px'/>
            <div>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.18em;
                            color:rgba(255,255,255,0.5);margin-bottom:5px;font-family:"DM Sans"'>
                    SISTEM DETEKSI DINI PARIWISATA
                </div>
                <div style='font-family:"DM Serif Display";font-size:30px;color:#f1f5f9;
                            letter-spacing:-.02em;line-height:1.1'>BaliGuard</div>
                <div style='font-size:14px;color:rgba(255,255,255,0.6);margin-top:6px;line-height:1.65;font-family:"DM Sans"'>
                    Dashboard Early Warning System &mdash; Multi-Sumber Data,
                    Machine Learning &amp; Analisis Sentimen Multibahasa
                </div>
            </div>
        </div>
        <!-- Right: last data chip -->
        <div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                    border-radius:12px;padding:14px 20px;text-align:center;flex-shrink:0'>
            <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;
                        color:rgba(255,255,255,0.55);margin-bottom:5px;font-family:"DM Sans";text-align:center'>DATA TERAKHIR</div>
            <div style='font-family:"JetBrains Mono";font-size:20px;color:#93c5fd;font-weight:700;letter-spacing:.02em;text-align:center'>
                {_last_month}
            </div>
            <div style='font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;font-family:"DM Sans";text-align:center'>
                {_n_months} bulan data historis
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Current Month Projection Banner ──────────────────
curr_lv   = current_fc['level']
curr_sc   = current_fc['score']
curr_conf = current_fc['confidence']
curr_mo   = current_fc['month']
trend_txt = "↗ MENINGKAT" if fc_trend > 0.5 else ("↘ MENURUN" if fc_trend < -0.5 else "→ STABIL")
# Warna tren: merah jika positif (krisis meningkat = buruk), hijau jika negatif (membaik)
trend_col = "#ef4444" if fc_trend > 0.5 else ("#22c55e" if fc_trend < -0.5 else "#94a3b8")
# Warna TREN/BULAN di stat box: merah jika minus (berdasarkan nilai fc_trend), hijau jika plus
_tren_val_col = "#f87171" if fc_trend < 0 else ("#4ade80" if fc_trend > 0 else "#94a3b8")

st.markdown(f"""
<div style='background:rgba(14,28,60,0.7);
            border:1px solid rgba(255,255,255,0.09);border-radius:14px;
            padding:18px 26px;margin-bottom:14px'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px'>
        <!-- Left: level + score + trend -->
        <div>
            <div style='font-size:12px;font-weight:700;color:#64748b;text-transform:uppercase;
                        letter-spacing:.13em;margin-bottom:8px;font-family:"DM Sans"'>
                PROYEKSI BULAN INI &mdash; {curr_mo}
            </div>
            <div style='display:flex;align-items:center;gap:16px;flex-wrap:wrap'>
                <div style='display:flex;align-items:center;gap:8px'>
                    <span class='status-dot dot-{curr_lv}' style='width:12px;height:12px'></span>
                    <span style='font-family:"DM Serif Display";font-size:26px;
                                 color:{COLOR_MAP.get(curr_lv,"#fff")};line-height:1'>{curr_lv}</span>
                </div>
                <div style='font-family:"JetBrains Mono";font-size:14px;color:#64748b'>
                    Score&nbsp;<span style='color:#e2e8f0;font-weight:700;font-size:17px'>{curr_sc}</span>
                    <span style='color:#334155'>/100</span>
                </div>
                <div style='font-size:12px;color:{trend_col};font-weight:700;
                            font-family:"DM Sans";letter-spacing:.03em'>{trend_txt}</div>
            </div>
        </div>
        <!-- Right: stats strip -->
        <div style='display:flex;gap:6px'>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#64748b;margin-bottom:4px;font-family:"DM Sans";text-align:center'>CONFIDENCE</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:700;line-height:1;text-align:center'>
                    {curr_conf:.0f}%
                </div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#64748b;margin-bottom:4px;font-family:"DM Sans";text-align:center'>PROYEKSI DARI</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:600;line-height:1;text-align:center'>
                    {_last_month}
                </div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#64748b;margin-bottom:4px;font-family:"DM Sans";text-align:center'>TREN/BULAN</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:{_tren_val_col};font-weight:700;line-height:1;text-align:center'>
                    {fc_trend:+.2f}
                </div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Strip ────────────────────────────────────────
row_data    = get_row(sel)
_is_proj    = bool(row_data.get('_is_projected', False))
_proj_conf  = int(row_data.get('_proj_confidence', 85)) if _is_proj else None
level    = str(row_data.get('crisis_level','WASPADA'))
score    = sf(row_data.get('crisis_score_100',0))
wisman   = int(sf(row_data.get('wisman',0)))
tpk      = sf(row_data.get('tpk_bintang',0))
conf     = sf(row_data.get('rf_confidence',0))*100
is_anom  = int(sf(row_data.get('iso_anomaly',0)))
rf_pred  = str(row_data.get('rf_predicted_level','N/A'))
sent     = sf(row_data.get('avg_sentiment_monthly',0))
inflasi  = sf(row_data.get('inflasi_processed',0))
bali_shr = sf(row_data.get('bali_share_pct',0))

# USD/IDR: coba live rate jika bulan dipilih >= last data
_usd_from_row = sf(row_data.get('usd_idr_avg', 0))
_live_rate    = fetch_live_usd_idr()
_now_m        = datetime.now().strftime('%Y-%m')
if sel >= _last_data_month and _live_rate:
    usd_avg     = _live_rate
    _usd_is_live = True
else:
    usd_avg      = _usd_from_row
    _usd_is_live = False

# ── MoM Delta (cached per bulan) ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _get_prev_row_vals(sel_month):
    _sm = sorted(predictions['month'].unique())
    _idx = _sm.index(sel_month) if sel_month in _sm else -1
    _pm  = _sm[_idx - 1] if _idx > 0 else None
    _pr  = get_row(_pm) if _pm else None
    if _pr is None:
        return None, None, None, None, None, None
    return (
        _pm,
        sf(_pr.get('crisis_score_100', 0)),
        sf(_pr.get('wisman', 0)),
        sf(_pr.get('tpk_bintang', 0)),
        sf(_pr.get('avg_sentiment_monthly', 0)),
        sf(_pr.get('usd_idr_avg', 0)),
    )

_prev_month, _p_score, _p_wisman, _p_tpk, _p_sent, _p_usd = _get_prev_row_vals(sel)
_prev_row = get_row(_prev_month) if _prev_month else None

# ── Delta Context ────────────────────────────────────
if not _is_proj:
    delta_ctx = compute_delta_context(dict(row_data), predictions, sel)
else:
    # Untuk proyeksi: hitung precovid_mean dari data historis yang tersedia
    _pre = predictions[
        pd.to_datetime(predictions['month'].astype(str)).dt.year.isin([2017,2018,2019])
    ]['wisman'] if 'wisman' in predictions.columns else pd.Series(dtype=float)
    _pre_mean = float(_pre.mean()) if len(_pre) > 0 else float(predictions['wisman'].mean())
    _proj_wisman = int(sf(row_data.get('wisman', 0)))
    _proj_rec = round(_proj_wisman / _pre_mean * 100, 1) if _pre_mean > 0 else 0.0
    delta_ctx = {
        'score_delta'  : 0,
        'score_trend'  : '→',
        'dominant'     : 'Proyeksi',
        'anomaly_exp'  : 'Data proyeksi — tidak ada anomali historis',
        'recovery_pct' : _proj_rec,
        'precovid_mean': round(_pre_mean, 0),
    }

def _delta_txt(curr, prev_val, fmt="+.1f", suffix="", invert=False):
    if prev_val is None or prev_val == 0:
        return "<span style='color:#64748b;font-size:12px'>— vs bln lalu</span>"
    d    = curr - prev_val
    pct  = (d / abs(prev_val) * 100) if prev_val != 0 else 0
    good = (d < 0) if invert else (d > 0)
    col  = "#4ade80" if good else ("#f87171" if (d < 0 if not invert else d > 0) else "#94a3b8")
    sign = "▲" if d > 0 else ("▼" if d < 0 else "→")
    if suffix == "%":
        txt = f"{sign} {abs(d):.1f}pp vs bln lalu"
    elif suffix == "pct_change":
        txt = f"{sign} {abs(pct):.1f}% vs bln lalu"
    else:
        txt = f"{sign} {abs(d):{fmt}} vs bln lalu"
    return f"<span style='color:{col};font-size:12px;font-weight:700'>{txt}</span>"


_d_score  = _delta_txt(score,  _p_score,  fmt=".1f", invert=True)
_d_wisman = _delta_txt(wisman, _p_wisman, suffix="pct_change")
_d_tpk    = _delta_txt(tpk,    _p_tpk,   suffix="%")
_d_sent   = _delta_txt(sent,   _p_sent,  fmt="+.3f")
_d_usd    = _delta_txt(usd_avg,_p_usd,   suffix="pct_change", invert=True)

# Badge proyeksi / live
_proj_badge = (f"<span style='font-size:9px;background:rgba(167,139,250,0.15);"
               f"color:#a78bfa;padding:2px 7px;border-radius:8px;"
               f"border:1px solid rgba(167,139,250,0.3)'>🔮 PROYEKSI ~{_proj_conf}%</span> "
               if _is_proj else "")
_live_badge = (f"<span style='font-size:9px;background:rgba(74,222,128,0.12);"
               f"color:#4ade80;padding:2px 7px;border-radius:8px;"
               f"border:1px solid rgba(74,222,128,0.25)'>⚡ LIVE</span>"
               if _usd_is_live else "kurs rata-rata")

# KPI card builder
def kpi_html_delta(label, value, sub_static, delta_html, level=None, use_dot=False):
    cls = f"kpi-card kpi-{level}" if level else "kpi-card"
    dot = f"<span class='status-dot dot-{level}' style='display:inline-block;margin-right:7px;vertical-align:middle'></span>" if use_dot else ""
    return (f'<div class="{cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{dot}{value}</div>'
            f'<div class="kpi-sub">{sub_static}</div>'
            f'<div class="kpi-delta">{delta_html}</div>'
            f'</div>')

# ── KPI Swipeable Carousel ───────────────────────────
_proj_badge_html = (
    f"<span style='font-size:9px;background:rgba(167,139,250,0.15);"
    f"color:#a78bfa;padding:2px 7px;border-radius:8px;"
    f"border:1px solid rgba(167,139,250,0.3);font-family:DM Sans'>PROYEKSI ~{_proj_conf}%</span>"
    if _is_proj else ""
)
_usd_sub_html = (
    "<span class='live-badge'><span class='live-pulse'></span>LIVE</span>"
    if _usd_is_live else "kurs rata-rata"
)

def _kpi_card_html(label, value, sub, delta, level=None, use_dot=False):
    accent = {"AMAN":"#22c55e","WASPADA":"#f59e0b","SIAGA":"#f97316","KRISIS":"#ef4444"}.get(level,"#3b82f6")
    dot = (f"<span style='display:inline-block;width:16px;height:16px;border-radius:50%;"
           f"background:{accent};box-shadow:0 0 6px {accent};margin-right:8px;"
           f"vertical-align:middle;flex-shrink:0'></span>") if use_dot else ""
    return f"""
<div class="kpi-c" style="border-top:2px solid {accent}">
  <div class="kpi-c-label">{label}</div>
  <div class="kpi-c-value">{dot}{value}</div>
  <div class="kpi-c-sub">{sub}</div>
  <div class="kpi-c-delta">{delta}</div>
</div>"""

_cards = [
    _kpi_card_html("LEVEL KRISIS", level,
                   (_proj_badge_html + f" RF: {rf_pred}") if _proj_badge_html else f"RF: {rf_pred}",
                   f"<span style='color:#334155;font-size:10px'>{_prev_month or '—'}</span>",
                   level, use_dot=True),
    _kpi_card_html("CRISIS SCORE", f"{score:.1f}",
                   f"dari 100 &nbsp;&middot;&nbsp; conf {conf:.0f}%",
                   _d_score),
    _kpi_card_html("WISMAN", f"{wisman:,}",
                   "est. proyeksi" if _is_proj else "kunjungan bulan ini",
                   _d_wisman),
    _kpi_card_html("TPK BINTANG", f"{tpk:.1f}%",
                   "est. proyeksi" if _is_proj else "tingkat hunian hotel",
                   _d_tpk),
    _kpi_card_html("SENTIMEN", f"{sent:+.3f}",
                   "est. proyeksi" if _is_proj else "rata-rata ulasan",
                   _d_sent),
    _kpi_card_html("USD/IDR", f"Rp {usd_avg:,.0f}",
                   _usd_sub_html,
                   _d_usd),
]

_cards_html = "".join(_cards)

_carousel_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: transparent; overflow: hidden; margin: 0; padding: 0; }
body { height: 100%; }

#kpi-root {
  position: relative;
  overflow: hidden;
  padding: 6px 0 4px;
}
#kpi-root::before, #kpi-root::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  width: 28px;
  pointer-events: none;
  z-index: 10;
}
#kpi-root::before { left: 0;  background: linear-gradient(to right, #060d1c 60%, transparent); }
#kpi-root::after  { right: 0; background: linear-gradient(to left,  #060d1c 60%, transparent); }

#kpi-track {
  display: flex;
  gap: 14px;
  padding: 6px 28px 8px 20px;
  will-change: transform;
  cursor: grab;
}
#kpi-track:active { cursor: grabbing; }

.kpi-c {
  flex: 0 0 260px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 18px 20px 16px;
  text-align: center;
  transition: transform .22s cubic-bezier(.34,1.56,.64,1),
              box-shadow .22s ease,
              border-color .22s ease,
              background .22s ease;
}
.kpi-c:hover {
  transform: translateY(-5px) scale(1.025);
  box-shadow: 0 12px 32px rgba(0,0,0,0.45);
  border-color: rgba(255,255,255,0.16);
  background: rgba(255,255,255,0.07);
}
.kpi-c-label {
  font-size:13px !important;
  font-weight:700 !important;
  color:#94a3b8 !important;
  text-transform:uppercase !important;
  letter-spacing:.1em !important;
  margin-bottom:8px !important;
  font-family:'DM Sans', sans-serif !important;
  text-align:center !important;
}
.kpi-c-value {
  font-size:26px !important;
  font-weight:700 !important;
  color:#f1f5f9 !important;
  line-height:1.1 !important;
  font-family:'DM Serif Display', serif !important;
  letter-spacing:-.01em !important;
  display:flex !important;
  align-items:center !important;
  justify-content:center !important;
  text-align:center !important;
}
.kpi-c-sub {
  font-size:13px !important;
  color:#94a3b8 !important;
  margin-top:6px !important;
  font-family:'DM Sans', sans-serif !important;
  font-weight:400 !important;
  line-height:1.5 !important;
  text-align:center !important;
}
.kpi-c-delta { margin-top: 7px; font-size: 13px; font-weight: 600; font-family: sans-serif; line-height: 1.4; }

.kpi-btn {
  position: absolute;
  top: 50%; transform: translateY(-55%);
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(15,25,50,0.92);
  border: 1px solid rgba(255,255,255,0.15);
  color: #94a3b8;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 20;
  font-size: 22px; line-height: 1; user-select: none;
  box-shadow: 0 2px 10px rgba(0,0,0,0.5);
  transition: background .15s, color .15s, box-shadow .15s;
}
.kpi-btn:hover {
  background: rgba(59,130,246,0.35);
  border-color: rgba(59,130,246,0.6);
  color: #fff;
  box-shadow: 0 4px 16px rgba(59,130,246,0.35);
}
#kpi-btn-l { left: 2px; }
#kpi-btn-r { right: 2px; }

#kpi-dots { display: none !important; }
.kpi-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(255,255,255,0.15); cursor: pointer;
  transition: background .2s, transform .2s;
}
.kpi-dot.active { background: #3b82f6; transform: scale(1.5); }
</style>
</head>
<body>
<div id="kpi-root">
  <div id="kpi-track">CARDS_PLACEHOLDER</div>
  <div class="kpi-btn" id="kpi-btn-l">&#8249;</div>
  <div class="kpi-btn" id="kpi-btn-r">&#8250;</div>
  <div id="kpi-dots"></div>
</div>
<script>
(function() {
  var DUR  = 350;
  var track   = document.getElementById('kpi-track');
  var dotWrap = document.getElementById('kpi-dots');
  var btnL    = document.getElementById('kpi-btn-l');
  var btnR    = document.getElementById('kpi-btn-r');

  var originals = Array.from(track.children);
  var N = originals.length;
  var current = 0;
  var busy = false;

  function getStep() {
    var card = track.children[0];
    if (!card) return 274;
    var style = window.getComputedStyle(track);
    var gap   = parseFloat(style.gap || style.columnGap) || 14;
    return card.getBoundingClientRect().width + gap;
  }

  function maxIdx() {
    var root = document.getElementById('kpi-root');
    var vw   = root ? root.getBoundingClientRect().width : window.innerWidth;
    var step = getStep();
    var totalW = N * step - 14; // total track width minus last gap
    var maxScroll = Math.max(0, totalW - vw + 48); // 48 = left+right padding
    return Math.round(maxScroll / step);
  }

  function xFor(idx) { return -(idx * getStep()); }

  function updateArrows() {
    var mx = maxIdx();
    btnL.style.opacity       = current === 0  ? '0.25' : '1';
    btnL.style.pointerEvents = current === 0  ? 'none' : 'auto';
    btnR.style.opacity       = current >= mx  ? '0.25' : '1';
    btnR.style.pointerEvents = current >= mx  ? 'none' : 'auto';
  }

  function slideTo(idx) {
    if (busy) return;
    idx = Math.max(0, Math.min(idx, maxIdx()));
    if (idx === current) return;
    busy = true;
    current = idx;
    track.style.transition = 'transform ' + DUR + 'ms cubic-bezier(0.4,0,0.2,1)';
    track.style.transform  = 'translateX(' + xFor(current) + 'px)';
    setTimeout(function() { busy = false; }, DUR + 30);
    updateDots();
    updateArrows();
  }

  function buildDots() {
    dotWrap.innerHTML = '';
    for (var i = 0; i < N; i++) {
      (function(idx) {
        var d = document.createElement('div');
        d.className = 'kpi-dot' + (idx === 0 ? ' active' : '');
        d.addEventListener('click', function() { slideTo(idx); });
        dotWrap.appendChild(d);
      })(i);
    }
  }

  function updateDots() {
    dotWrap.querySelectorAll('.kpi-dot').forEach(function(d, i) {
      d.classList.toggle('active', i === current);
    });
  }

  btnL.addEventListener('click', function() { slideTo(current - 1); });
  btnR.addEventListener('click', function() { slideTo(current + 1); });

  // Touch swipe
  var tx = 0;
  track.addEventListener('touchstart', function(e) { tx = e.touches[0].clientX; }, {passive:true});
  track.addEventListener('touchend',   function(e) {
    var dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 40) { dx < 0 ? slideTo(current + 1) : slideTo(current - 1); }
  }, {passive:true});

  buildDots();
  track.style.transition = 'none';
  track.style.transform  = 'translateX(0px)';
  updateArrows();
})();
</script>
</body>
</html>"""

_carousel_html = _carousel_html.replace('CARDS_PLACEHOLDER', _cards_html)
components.html(_carousel_html, height=160, scrolling=False)

# ── Alert Banner ─────────────────────────────────────
ALERTS = {
    'AMAN':    "Pariwisata Bali dalam kondisi <b>normal dan stabil</b>. Tidak ada indikasi krisis yang signifikan.",
    'WASPADA': "Terdapat <b>sinyal awal yang perlu dipantau</b>. Beberapa indikator menunjukkan tekanan ringan.",
    'SIAGA':   "⚠️ <b>Tekanan signifikan terdeteksi</b> pada sektor pariwisata Bali. Respons koordinatif diperlukan.",
    'KRISIS':  "🚨 <b>KRISIS TERDETEKSI.</b> Aktifkan protokol penanganan krisis pariwisata segera."
}
st.markdown(alert_html(level, f"Status Pariwisata Bali — {sel}",
            ALERTS.get(level,"") +
            f" &nbsp;·&nbsp; Faktor dominan: <b>{delta_ctx['dominant']}</b>"
            f" &nbsp;·&nbsp; Delta score: <b>{delta_ctx['score_delta']:+.1f} poin</b> ({delta_ctx['score_trend']})"),
            unsafe_allow_html=True)

# ── Page Title Divider ────────────────────────────────
_NAV_ICONS = {
    "Overview & Timeline":  ("📈", "Overview & Timeline",  "#93c5fd"),
    "Analisis Detail":       ("🔬", "Analisis Detail",       "#c084fc"),
    "Sentimen":              ("💬", "Sentimen",              "#4ade80"),
    "Prediksi & Proyeksi":  ("🔮", "Prediksi & Proyeksi",  "#fbbf24"),
    "Narasi AI":            ("✨", "Narasi AI",            "#f87171"),
}
_icon, _title, _col = _NAV_ICONS.get(selected_nav, ("📈", selected_nav, "#93c5fd"))
st.markdown(f"""
<div style='margin-top:48px;margin-bottom:28px;text-align:center;
            padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.07)'>
    <div style='font-family:"DM Serif Display",serif;font-size:38px;font-weight:400;
                color:#f1f5f9;letter-spacing:-.02em;line-height:1.15'>
        {_title}
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# MAIN CONTENT — navigasi dari sidebar
# ══════════════════════════════════════════════════════

# ─── TAB 1: OVERVIEW ─────────────────────────────────
if selected_nav == "Overview & Timeline":
    _tick("nav_start_overview")
    fig = _build_overview_fig(str(sel))
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary Stats Strip ───────────────────────────────
    _pct_aman   = (predictions['crisis_level']=='AMAN').mean()*100
    _pct_krisis = (predictions['crisis_level']=='KRISIS').mean()*100
    _avg_score  = predictions['crisis_score_100'].mean()
    _peak_wis   = predictions['wisman'].max()

    st.markdown(f"""
<div style='margin-top:24px;margin-bottom:4px;display:flex;justify-content:center;gap:0'>
    <div style='flex:1;text-align:center;padding:18px 12px;
                border-right:1px solid rgba(255,255,255,0.07)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Bulan Level AMAN
        </div>
        <div style='font-family:"DM Serif Display";font-size:28px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_pct_aman:.1f}%
        </div>
    </div>
    <div style='flex:1;text-align:center;padding:18px 12px;
                border-right:1px solid rgba(255,255,255,0.07)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Bulan Level KRISIS
        </div>
        <div style='font-family:"DM Serif Display";font-size:28px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_pct_krisis:.1f}%
        </div>
    </div>
    <div style='flex:1;text-align:center;padding:18px 12px;
                border-right:1px solid rgba(255,255,255,0.07)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Avg Crisis Score
        </div>
        <div style='font-family:"DM Serif Display";font-size:28px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_avg_score:.1f}
        </div>
    </div>
    <div style='flex:1;text-align:center;padding:18px 12px'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Peak Wisman
        </div>
        <div style='font-family:"DM Serif Display";font-size:28px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_peak_wis:,}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── TAB 2: ANALISIS DETAIL ───────────────────────────
if selected_nav == "Analisis Detail":
    _tick("nav_start_analisis")

    # CSS override untuk st.container(border=True) — ini satu-satunya cara
    # yang benar-benar membungkus st.plotly_chart() di Streamlit
    st.markdown("""
    <style>
    /* Override border container Streamlit → jadi styled box */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        padding: 4px 8px 8px !important;
    }
    /* Accent top-border per warna — ditaruh di elemen pertama dalam container */
    .accent-blue   { border-top: 3px solid #3b82f6 !important; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
    .accent-orange { border-top: 3px solid #f97316 !important; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
    .accent-purple { border-top: 3px solid #a855f7 !important; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
    .accent-green  { border-top: 3px solid #22c55e !important; border-radius: 18px 18px 0 0; margin: -4px -8px 10px; padding: 0; height: 3px; }
    .box-heading {
        font-family: 'DM Sans', sans-serif;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: .05em;
        text-transform: uppercase;
        margin-bottom: 4px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    cl, cr = st.columns([1, 1], gap="medium")

    with cl:
        # ── Box 1: Komponen Crisis Score ──────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-blue"></div>', unsafe_allow_html=True)
            st.markdown('<div class="box-heading sec-blue">Komponen Crisis Score</div>', unsafe_allow_html=True)

            mr_rows = master[master['month']==sel]
            if len(mr_rows) > 0:
                mr = mr_rows.iloc[0]
                comp_vals = {
                    'Kunjungan Wisatawan': sf(mr.get('crisis_component_tourism',0)),
                    'Kondisi Ekonomi':     sf(mr.get('crisis_component_economy',0)),
                    'Sentimen Ulasan':     sf(mr.get('crisis_component_sentiment',0)),
                }
                _comp_proj = False
            elif _is_proj:
                # Proyeksi: estimasi komponen dari crisis_score_100
                _sc = score / 100.0
                comp_vals = {
                    'Kunjungan Wisatawan': round(_sc * 0.45, 4),
                    'Kondisi Ekonomi':     round(_sc * 0.30, 4),
                    'Sentimen Ulasan':     round(_sc * 0.25, 4),
                }
                _comp_proj = True
            else:
                comp_vals = None
                _comp_proj = False

            if comp_vals is not None:
                fig_c = go.Figure(go.Bar(
                    x=list(comp_vals.keys()),
                    y=[v*100 for v in comp_vals.values()],
                    marker_color=['#ef4444','#f59e0b','#3b82f6'],
                    marker_line_color='rgba(0,0,0,0)',
                    text=[f'{v*100:.1f}%' for v in comp_vals.values()],
                    textposition='outside',
                    textfont=dict(size=13,color='#f1f5f9')
                ))
                fig_c.update_layout(
                    yaxis=dict(range=[0,115], title='Kontribusi (%)',
                               gridcolor='rgba(255,255,255,0.06)', color='#94a3b8'),
                    xaxis=dict(color='#cbd5e1', tickfont=dict(size=12)),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=300,
                    margin=dict(l=10,r=10,t=10,b=10),
                    font=dict(family='DM Sans',size=12,color='#cbd5e1')
                )
                st.plotly_chart(fig_c, use_container_width=True)
                if _comp_proj:
                    st.markdown(
                        "<div style='font-size:10px;color:#a78bfa;text-align:center;margin-top:-8px'>"
                        "Estimasi proporsi berbasis crisis score proyeksi — bukan data historis</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("Data komponen tidak tersedia untuk bulan ini.")

        # ── Box 2: Indikator Detail ───────────────────────
        indicators = [
            ("Wisman",                f"{wisman:,} orang"),
            ("Recovery vs 2017–2019", f"{delta_ctx['recovery_pct']:.1f}%"),
            ("TPK Hotel Bintang",     f"{tpk:.1f}%"),
            ("Kurs USD/IDR",          f"Rp {usd_avg:,.0f}"),
            ("Inflasi Bali",          f"{inflasi:.2f}%"),
            ("Sentimen Avg",          f"{sent:+.3f}"),
            ("Bali Share",            f"{bali_shr:.1f}%"),
            ("Z-score Wisman",        f"{sf(row_data.get('wisman_zscore',0)):.2f}"),
            ("Penjelasan Anomali",    delta_ctx['anomaly_exp']),
            ("Anomali IF",            "⚠️ Terdeteksi" if is_anom else "✅ Normal"),
            ("RF Prediksi",           rf_pred),
            ("RF Confidence",         f"{conf:.0f}%"),
            ("Delta Score",           f"{delta_ctx['score_delta']:+.1f} ({delta_ctx['score_trend']})"),
            ("Faktor Dominan",        delta_ctx['dominant']),
        ]
        rows_html = "".join(
            f'<div class="risk-row"><span class="risk-name">{k}</span>'
            f'<span class="risk-val">{v}</span></div>'
            for k, v in indicators
        )
        with st.container(border=True):
            st.markdown(
                '<div class="accent-purple"></div>'
                '<div class="box-heading sec-purple">Indikator Detail</div>'
                + rows_html,
                unsafe_allow_html=True
            )

    with cr:
        # ── Box 3: Probabilitas RF ────────────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-orange"></div>', unsafe_allow_html=True)
            st.markdown('<div class="box-heading sec-orange">Probabilitas Prediksi Random Forest</div>', unsafe_allow_html=True)

            prob_labels = ['AMAN','WASPADA','SIAGA','KRISIS']
            prob_vals   = [sf(row_data.get(f'prob_{l.lower()}',0))*100 for l in prob_labels]
            fig_p = go.Figure(go.Bar(
                y=prob_labels, x=prob_vals, orientation='h',
                marker_color=[COLOR_MAP[l] for l in prob_labels],
                marker_line_color='rgba(0,0,0,0)',
                text=[f'{v:.1f}%' for v in prob_vals],
                textposition='outside',
                textfont=dict(size=12,color='#f1f5f9')
            ))
            fig_p.update_layout(
                xaxis=dict(range=[0,100], title='Probabilitas (%)',
                           gridcolor='rgba(255,255,255,0.06)', color='#94a3b8'),
                yaxis=dict(color='#f1f5f9', categoryorder='total ascending'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=300,
                margin=dict(l=10,r=50,t=10,b=10),
                font=dict(family='DM Sans',size=12,color='#cbd5e1')
            )
            st.plotly_chart(fig_p, use_container_width=True)

        # ── Box 4: Feature Importance ─────────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-green"></div>', unsafe_allow_html=True)
            st.markdown('<div class="box-heading sec-green">Feature Importance — Random Forest</div>', unsafe_allow_html=True)

            try:
                fi_available = [f for f in FEATURES if f in master.columns]
                fi = pd.DataFrame({
                    'Fitur': fi_available[:len(rf_model.feature_importances_)],
                    'Importance': rf_model.feature_importances_[:len(fi_available)]
                })
                fi = fi.sort_values('Importance', ascending=True).tail(8)
                fig_fi = go.Figure(go.Bar(
                    x=fi['Importance'], y=fi['Fitur'], orientation='h',
                    marker_color='#3b82f6', marker_line_color='rgba(0,0,0,0)',
                    text=[f'{v:.3f}' for v in fi['Importance']],
                    textposition='outside',
                    textfont=dict(size=11,color='#f1f5f9')
                ))
                fig_fi.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=390,
                    margin=dict(l=10,r=80,t=10,b=10),
                    xaxis=dict(range=[0, fi['Importance'].max()*1.35],
                               gridcolor='rgba(255,255,255,0.06)', color='#94a3b8'),
                    yaxis=dict(color='#f1f5f9', tickfont=dict(size=12)),
                    font=dict(family='DM Sans',size=11,color='#cbd5e1')
                )
                st.plotly_chart(fig_fi, use_container_width=True)
            except Exception:
                st.info("Feature importance tidak tersedia.")

# ─── TAB 3: SENTIMEN ─────────────────────────────────
if selected_nav == "Sentimen":
    _tick("nav_start_sentimen")

    st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.035) !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        padding: 12px 16px 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    sent_color = '#4ade80' if sent >= 0.3 else ('#f87171' if sent < -0.3 else '#fbbf24')
    sent_label = 'POSITIF' if sent >= 0.3 else ('NEGATIF' if sent < -0.3 else 'NETRAL')
    sent_pct   = int((sent + 1) / 2 * 100)

    mr_pct_rows = master[master['month']==sel]

    # ── Proyeksi: tidak ada data review nyata ────────────────
    if _is_proj:
        # Gunakan sentimen proyeksi, tapi tandai review sebagai N/A
        pct_neg         = 0.0
        pct_pos         = 0.0
        pct_netral      = 0.0
        _review_is_proj = True
        _netral_estimated = False
        # Ambil sentimen terakhir yang diketahui dari data historis
        _last_real_sent  = float(predictions[predictions['month'] <= _last_data_month]['avg_sentiment_monthly'].iloc[-1])
        _last_real_month = predictions['month'].iloc[-1]
    else:
        _review_is_proj  = False
        _last_real_sent  = None
        _last_real_month = None
        pct_neg = sf(mr_pct_rows['pct_negative_monthly'].iloc[0] if len(mr_pct_rows) > 0
                     and 'pct_negative_monthly' in master.columns
                     else row_data.get('pct_negative_monthly', 0))

        # pct_positive & pct_neutral tidak ada di master (NB04 hanya simpan pct_negative)
        _avg_sent_raw = float(mr_pct_rows['avg_sentiment_monthly'].iloc[0]
                              if len(mr_pct_rows) > 0 and 'avg_sentiment_monthly' in master.columns
                              else sent)
        _sentiment_est = min(1.0, max(0.0, _avg_sent_raw))

        _nonneg = max(0.0, 100.0 - pct_neg)
        if 'pct_positive_monthly' in master.columns and len(mr_pct_rows) > 0:
            pct_pos    = sf(mr_pct_rows['pct_positive_monthly'].iloc[0])
            pct_netral = max(0.0, round(100.0 - pct_pos - pct_neg, 1))
            _netral_estimated = False
        else:
            _s_norm       = min(1.0, _sentiment_est / 0.8)
            _netral_frac  = 0.30 - 0.20 * _s_norm
            pct_netral    = round(_nonneg * _netral_frac, 1)
            pct_pos       = round(_nonneg - pct_netral, 1)
            _netral_estimated = True

    # ── Hero: pakai kolom native Streamlit, bukan HTML kompleks ──
    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1], gap="medium")
    with h1:
        st.markdown(
            f"<div style='padding:16px 0'>"
            f"<div style='font-size:11px;font-weight:700;letter-spacing:.12em;color:#475569;text-transform:uppercase;margin-bottom:6px'>Sentimen Bulan Ini · {sel}</div>"
            f"<div style='font-family:DM Serif Display,serif;font-size:36px;color:{sent_color};line-height:1'>{sent_label}</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:20px;color:{sent_color};margin-top:4px'>{sent:+.3f}</div>"
            + (f"<div style='font-size:10px;color:#a78bfa;margin-top:6px'>🔮 proyeksi — data terakhir {_last_real_month}</div>" if _review_is_proj else "")
            + f"</div>",
            unsafe_allow_html=True
        )

    if _review_is_proj:
        # Bulan proyeksi: tampilkan 3 kolom info, bukan angka palsu
        with h2:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Positif</div>"
                f"<div style='font-size:22px;color:#475569'>—</div>"
                f"<div style='font-size:10px;color:#334155;margin-top:6px'>tidak tersedia</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with h3:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Negatif</div>"
                f"<div style='font-size:22px;color:#475569'>—</div>"
                f"<div style='font-size:10px;color:#334155;margin-top:6px'>tidak tersedia</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with h4:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Netral</div>"
                f"<div style='font-size:22px;color:#475569'>—</div>"
                f"<div style='font-size:10px;color:#334155;margin-top:6px'>tidak tersedia</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        with h5:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Sentimen Terakhir</div>"
                f"<div style='font-family:JetBrains Mono,monospace;font-size:20px;color:{sent_color}'>{_last_real_sent:+.3f}</div>"
                f"<div style='font-size:10px;color:#a78bfa;margin-top:4px'>{_last_real_month}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.markdown(
            "<div style='background:rgba(167,139,250,0.07);border:1px solid rgba(167,139,250,0.2);"
            "border-radius:10px;padding:10px 16px;margin:8px 0 16px;font-size:11px;color:#a78bfa'>"
            f"🔮 <b>Bulan proyeksi</b> — data review wisatawan belum tersedia. "
            f"Sentimen ditampilkan berdasarkan proyeksi tren dari data terakhir ({_last_real_month}: {_last_real_sent:+.3f})."
            "</div>",
            unsafe_allow_html=True
        )
    else:
        with h2:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Positif</div>"
                f"<div style='font-family:DM Serif Display,serif;font-size:28px;color:#4ade80'>{pct_pos:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='text-align:center;margin-top:-8px'>"
                f"<span style='background:rgba(74,222,128,0.15);color:#4ade80;font-size:11px;font-weight:700;"
                f"padding:3px 10px;border-radius:20px;border:1px solid rgba(74,222,128,0.3)'>"
                f"{'↑ Baik' if pct_pos > 60 else '↓ Perhatian'}</span></div>",
                unsafe_allow_html=True
            )
        with h3:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Negatif</div>"
                f"<div style='font-family:DM Serif Display,serif;font-size:28px;color:#f87171'>{pct_neg:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            neg_ok = pct_neg < 30
            st.markdown(
                f"<div style='text-align:center;margin-top:-8px'>"
                f"<span style='background:{'rgba(74,222,128,0.15)' if neg_ok else 'rgba(239,68,68,0.15)'};"
                f"color:{'#4ade80' if neg_ok else '#f87171'};font-size:11px;font-weight:700;"
                f"padding:3px 10px;border-radius:20px;border:1px solid {'rgba(74,222,128,0.3)' if neg_ok else 'rgba(239,68,68,0.3)'}'>{'↓ Rendah' if neg_ok else '↑ Tinggi'}</span></div>",
                unsafe_allow_html=True
            )
        with h4:
            st.markdown(
                f"<div style='text-align:center;padding:16px 0'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Netral{'  ~est' if _netral_estimated else ''}</div>"
                f"<div style='font-family:DM Serif Display,serif;font-size:28px;color:#fbbf24'>{pct_netral:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            netral_ok = pct_netral < 20
            st.markdown(
                f"<div style='text-align:center;margin-top:-8px'>"
                f"<span style='background:{'rgba(74,222,128,0.15)' if netral_ok else 'rgba(251,191,36,0.15)'};"
                f"color:{'#4ade80' if netral_ok else '#fbbf24'};font-size:11px;font-weight:700;"
                f"padding:3px 10px;border-radius:20px;border:1px solid {'rgba(74,222,128,0.3)' if netral_ok else 'rgba(251,191,36,0.3)'}'>{'→ Normal' if netral_ok else '↑ Tinggi'}</span></div>",
                unsafe_allow_html=True
            )
    with h5:
        st.markdown(
            "<div style='text-align:center;padding:16px 0'>"
            "<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Model</div>"
            "<div style='font-size:13px;font-weight:700;color:#7dd3fc'>XLM-RoBERTa</div>"
            "<div style='font-size:10px;color:#475569;margin-top:2px'>EN / ID / ZH</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Dua kolom bawah ───────────────────────────────────
    sc1, sc2 = st.columns([3, 2], gap="medium")

    with sc1:
        # ── Box: Tren Sentimen Historis ───────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-green"></div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 10px;"
                "border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:4px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#4ade80;"
                "border-left:3px solid #22c55e;padding-left:10px'>Tren Sentimen Historis</span></div>",
                unsafe_allow_html=True
            )
            if 'avg_sentiment_monthly' in master.columns:
                m_dt = pd.to_datetime(master['month'].astype(str))
                fig_s = go.Figure()
                fig_s.add_trace(go.Scatter(
                    x=m_dt, y=[min(float(v),0) for v in master['avg_sentiment_monthly']],
                    fill='tozeroy', fillcolor='rgba(239,68,68,0.08)',
                    line=dict(width=0), showlegend=False, hoverinfo='skip'))
                fig_s.add_trace(go.Scatter(
                    x=m_dt, y=master['avg_sentiment_monthly'],
                    mode='lines', name='Sentimen',
                    line=dict(color='#4ade80', width=2),
                    fill='tozeroy', fillcolor='rgba(74,222,128,0.05)',
                    hovertemplate='<b>%{x|%b %Y}</b><br>Sentimen: %{y:+.3f}<extra></extra>'))
                fig_s.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.12)', line_width=1)
                fig_s.add_vrect(x0='2020-03-01', x1='2021-12-01',
                    fillcolor='rgba(239,68,68,0.05)', line_width=0,
                    annotation_text='COVID-19', annotation_font_color='#ef4444',
                    annotation_font_size=10)
                fig_s.add_vline(x=sel_dt.timestamp() * 1000, line_dash='dot', line_color='#60a5fa', line_width=1.5,
                    annotation_text=sel, annotation_font_color='#60a5fa', annotation_font_size=9)
                fig_s.add_hrect(y0=0.3, y1=1,   fillcolor='rgba(74,222,128,0.03)', line_width=0)
                fig_s.add_hrect(y0=-1,  y1=-0.3, fillcolor='rgba(239,68,68,0.03)', line_width=0)
                fig_s.update_layout(
                    yaxis=dict(title='Sentimen (−1 → +1)', range=[-1,1],
                               gridcolor='rgba(255,255,255,0.04)', color='#64748b',
                               tickvals=[-1,-0.5,0,0.5,1]),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.03)', color='#64748b'),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    height=310, margin=dict(l=0,r=10,t=10,b=0),
                    showlegend=False,
                    font=dict(family='DM Sans', size=11, color='#94a3b8'))
                st.plotly_chart(fig_s, use_container_width=True)

        # ── Box: 6 Bulan Terakhir ──────────────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-green"></div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 10px;"
                "border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:4px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#4ade80;"
                "border-left:3px solid #22c55e;padding-left:10px'>6 Bulan Terakhir</span></div>",
                unsafe_allow_html=True
            )
            if 'avg_sentiment_monthly' in predictions.columns:
                last6 = predictions.tail(6)[['month','avg_sentiment_monthly']].copy()
                colors_bar = ['#4ade80' if v>0.1 else ('#f87171' if v<-0.1 else '#fbbf24')
                              for v in last6['avg_sentiment_monthly']]
                fig_6 = go.Figure(go.Bar(
                    x=last6['month'], y=last6['avg_sentiment_monthly'],
                    marker_color=colors_bar, marker_line_color='rgba(0,0,0,0)',
                    text=[f'{v:+.3f}' for v in last6['avg_sentiment_monthly']],
                    textposition='outside', textfont=dict(color='#e2e8f0', size=11),
                    hovertemplate='<b>%{x}</b><br>Sentimen: %{y:.3f}<extra></extra>'
                ))
                fig_6.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.12)', line_width=1)
                fig_6.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    height=220, margin=dict(l=0,r=0,t=16,b=0),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#64748b', range=[-0.2, last6['avg_sentiment_monthly'].max()*1.25]),
                    xaxis=dict(color='#64748b'),
                    font=dict(family='DM Sans', size=11, color='#94a3b8'))
                st.plotly_chart(fig_6, use_container_width=True)

    with sc2:
        # ── Box Gauge Sentimen — satu box utuh (judul + gauge + legenda + distribusi) ──
        bg_pos  = "rgba(74,222,128,0.10)"  if sent >= 0.3          else "rgba(255,255,255,0.03)"
        bd_pos  = "rgba(74,222,128,0.25)"  if sent >= 0.3          else "rgba(255,255,255,0.06)"
        bg_net  = "rgba(245,158,11,0.10)"  if -0.3 <= sent < 0.3   else "rgba(255,255,255,0.03)"
        bd_net  = "rgba(245,158,11,0.25)"  if -0.3 <= sent < 0.3   else "rgba(255,255,255,0.06)"
        bg_neg  = "rgba(239,68,68,0.10)"   if sent < -0.3          else "rgba(255,255,255,0.03)"
        bd_neg  = "rgba(239,68,68,0.25)"   if sent < -0.3          else "rgba(255,255,255,0.06)"

        with st.container(border=True):
            st.markdown('<div class="accent-teal"></div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 12px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#2dd4bf;"
                "border-left:3px solid #14b8a6;padding-left:10px'>Gauge Sentimen</span></div>",
                unsafe_allow_html=True
            )

            fig_g = go.Figure(go.Indicator(
                mode="gauge+number+delta", value=round(sent, 3),
                delta={'reference': 0, 'valueformat': '.3f'},
                number={'valueformat': '+.3f',
                        'font': {'size': 32, 'color': sent_color, 'family': 'JetBrains Mono'}},
                title={'text': f"<span style='font-size:11px;color:#64748b;letter-spacing:.08em'>SENTIMEN · {sel}</span>",
                       'font': {'size': 11}},
                gauge={
                    'axis': {'range': [-1, 1], 'tickcolor': '#334155', 'tickwidth': 1,
                             'tickvals': [-1, -0.5, 0, 0.5, 1]},
                    'bar': {'color': sent_color, 'thickness': 0.28},
                    'bgcolor': 'rgba(0,0,0,0)',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [-1, -0.3],  'color': 'rgba(239,68,68,0.12)'},
                        {'range': [-0.3, 0.3], 'color': 'rgba(245,158,11,0.08)'},
                        {'range': [0.3, 1],    'color': 'rgba(74,222,128,0.12)'},
                    ],
                }))
            fig_g.update_layout(
                height=240, margin=dict(l=20, r=20, t=50, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='DM Sans', color='#94a3b8'))
            st.plotly_chart(fig_g, use_container_width=True)

            st.markdown(
                f"<div style='display:flex;flex-direction:column;gap:8px;padding:0 4px 4px'>"
                f"<div style='display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-radius:10px;background:{bg_pos};border:1px solid {bd_pos}'>"
                f"<span style='font-size:12px;color:#4ade80;font-weight:600'>● Positif</span>"
                f"<span style='font-size:11px;color:#64748b'>+0.3 ~ +1.0</span></div>"
                f"<div style='display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-radius:10px;background:{bg_net};border:1px solid {bd_net}'>"
                f"<span style='font-size:12px;color:#fbbf24;font-weight:600'>● Netral</span>"
                f"<span style='font-size:11px;color:#64748b'>-0.3 ~ +0.3</span></div>"
                f"<div style='display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-radius:10px;background:{bg_neg};border:1px solid {bd_neg}'>"
                f"<span style='font-size:12px;color:#f87171;font-weight:600'>● Negatif</span>"
                f"<span style='font-size:11px;color:#64748b'>-1.0 ~ -0.3</span></div>"
                f"</div>"
                f"<div style='margin-top:12px;margin-bottom:4px;padding:14px 16px;border-radius:12px;"
                f"background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06)'>"
                f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:.1em;color:#475569;margin-bottom:10px'>DISTRIBUSI REVIEW</div>"
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>"
                f"<div style='font-size:11px;color:#4ade80;width:50px;text-align:right'>{pct_pos:.1f}%</div>"
                f"<div style='flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct_pos:.0f}%;background:#4ade80;border-radius:3px'></div></div>"
                f"<div style='font-size:10px;color:#475569;width:36px'>Positif</div></div>"
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>"
                f"<div style='font-size:11px;color:#fbbf24;width:50px;text-align:right'>{pct_netral:.1f}%</div>"
                f"<div style='flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct_netral:.0f}%;background:#fbbf24;border-radius:3px'></div></div>"
                f"<div style='font-size:10px;color:#475569;width:36px'>Netral</div></div>"
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<div style='font-size:11px;color:#f87171;width:50px;text-align:right'>{pct_neg:.1f}%</div>"
                f"<div style='flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden'>"
                f"<div style='height:100%;width:{pct_neg:.0f}%;background:#f87171;border-radius:3px'></div></div>"
                f"<div style='font-size:10px;color:#475569;width:36px'>Negatif</div></div>"
                f"</div>",
                unsafe_allow_html=True
            )

# ─── TAB 4: PREDIKSI & PROYEKSI ──────────────────────
if selected_nav == "Prediksi & Proyeksi":
    _tick("nav_start_prediksi")

    # ══════════════════════════════════════════════════════
    # CSS TAMBAHAN — REDESIGN PREDIKSI TAB
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <style>
    /* ── Page header ── */
    .pred-page-header { text-align:center; padding:28px 0 20px; margin-bottom:4px; }
    .pred-page-title {
      font-family:'DM Serif Display',serif; font-size:36px; color:#f1f5f9;
      letter-spacing:-.02em; line-height:1.15; margin-bottom:6px;
    }
    .pred-page-sub { font-size:13px; color:#475569; letter-spacing:.04em; }

    /* ── Engine pill ── */
    .engine-pill {
      display:inline-flex; align-items:center; gap:10px;
      background:rgba(15,30,70,0.7); border:1px solid rgba(59,130,246,0.2);
      border-radius:100px; padding:8px 20px; margin:0 auto 28px;
    }
    .engine-label {
      font-size:9px; font-weight:800; color:#3b82f6; text-transform:uppercase;
      letter-spacing:.14em; background:rgba(59,130,246,0.18);
      padding:3px 9px; border-radius:20px; border:1px solid rgba(59,130,246,0.3); white-space:nowrap;
    }
    .engine-desc { font-size:12px; color:#64748b; }

    /* ── Controls bar label ── */
    .ctrl-label {
      font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase;
      letter-spacing:.1em; margin-bottom:6px; display:flex; align-items:center; gap:5px;
    }

    /* ── Section divider ── */
    .pred-section-hdr { display:flex; align-items:center; gap:10px; margin:20px 0 14px; }
    .pred-section-hdr-line { flex:1; height:1px; background:rgba(255,255,255,0.10); }
    .pred-section-hdr-text {
      font-size:12px; font-weight:800; letter-spacing:.14em;
      text-transform:uppercase; color:#94a3b8; white-space:nowrap;
    }

    /* ── Forecast grid cards ── */
    .fc-grid-fixed {
      display:grid; grid-template-columns:repeat(3,1fr);
      gap:10px; margin-bottom:10px;
    }
    .fc-grid-empty {
      background:rgba(255,255,255,0.008);
      border:1px dashed rgba(255,255,255,0.035) !important;
      border-top-color:transparent !important;
      pointer-events:none; min-height:118px; border-radius:14px;
    }
    .fc-grid-card {
      border-radius:14px; padding:16px 18px 15px; position:relative;
      overflow:hidden; transition:transform .2s, box-shadow .2s;
    }
    .fc-grid-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.45); }

    /* ── Confidence-tier card backgrounds ── */
    /* HIGH  76–100 */
    .fc-conf-high {
      background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.28);
    }
    /* MID   51–75 */
    .fc-conf-mid {
      background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28);
    }
    /* LOW   26–50 */
    .fc-conf-low {
      background:rgba(249,115,22,0.09); border:1px solid rgba(249,115,22,0.25);
    }
    /* VLOW  0–25 */
    .fc-conf-vlow {
      background:rgba(100,116,139,0.08); border:1px solid rgba(100,116,139,0.20);
    }

    .fc-card-month {
      font-family:'JetBrains Mono',monospace; font-size:11px;
      color:#94a3b8; letter-spacing:.08em; margin-bottom:8px; font-weight:600;
    }
    .fc-card-level { font-size:16px; font-weight:900; margin-bottom:3px; letter-spacing:.04em; }
    .fc-card-score {
      font-family:'JetBrains Mono',monospace; font-size:12px; color:#94a3b8;
      font-weight:600; margin-bottom:10px;
    }
    .fc-conf-bar-wrap {
      height:5px; background:rgba(255,255,255,0.08); border-radius:3px; overflow:hidden; margin-bottom:7px;
    }
    .fc-conf-bar-fill { height:100%; border-radius:3px; }
    .fc-conf-label { display:flex; justify-content:space-between; align-items:center; }
    .fc-conf-pct {
      font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:800;
    }
    .fc-conf-txt { font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.08em; font-weight:600; }

    /* ── Warning note ── */
    .fc-note {
      display:flex; align-items:center; gap:8px; background:rgba(245,158,11,0.07);
      border:1px solid rgba(245,158,11,0.18); border-left:3px solid rgba(245,158,11,0.55);
      border-radius:8px; padding:11px 16px; font-size:13px; color:#fbbf24;
      font-weight:600; margin-bottom:20px; letter-spacing:.01em;
    }

    /* Sembunyikan tick bar bawaan */
    [data-testid="stTickBarMin"],
    [data-testid="stTickBarMax"] {
      display: none !important;
    }

    /* Range label row manual */
    .slider-range-row {
      display: flex;
      justify-content: space-between;
      margin: 2px 0 10px;
      padding: 0 2px;
    }
    .slider-range-row span {
      font-size: 11px;
      font-weight: 700;
      color: #94a3b8;
      font-family: 'JetBrains Mono', monospace;
    }

    /* ── Simulator hint ── */
    .sim-hint {
      background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.20);
      border-left:3px solid rgba(59,130,246,0.6);
      border-radius:8px; padding:11px 16px; font-size:13px; color:#93c5fd;
      font-weight:600; margin-bottom:14px; letter-spacing:.01em;
    }

    /* ── Slider label row ── */
    .slider-label-row {
      display:flex; justify-content:space-between; align-items:center;
      margin-bottom:2px;
    }
    .slider-label-txt {
      font-size:11px; font-weight:700; color:#94a3b8; display:flex; align-items:center; gap:5px;
    }
    .slider-val-pill {
      font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
      padding:2px 9px; border-radius:20px;
      background:rgba(59,130,246,0.12); color:#7dd3fc;
      border:1px solid rgba(59,130,246,0.2);
    }

    /* ── Result box ── */
    .sim-result {
      border-radius:14px; padding:20px 16px; text-align:center;
      margin:10px 0 6px; border:1px solid rgba(255,255,255,0.07);
      position:relative; overflow:hidden;
    }
    .sim-result-label {
      font-size:9px; font-weight:800; letter-spacing:.16em;
      text-transform:uppercase; color:#1e3a5f; margin-bottom:8px;
    }
    .sim-result-score {
      font-family:'JetBrains Mono',monospace; font-size:52px; font-weight:700;
      line-height:1; color:#f1f5f9; margin-bottom:4px;
    }
    .sim-level-badge {
      display:inline-block; padding:5px 18px; border-radius:100px;
      font-family:'DM Serif Display',serif; font-size:15px; font-weight:400;
    }
    .sim-delta-txt {
      margin-top:10px; font-family:'JetBrains Mono',monospace;
      font-size:11px; color:#1e3a5f;
    }

    /* ── Full-width Breakdown+Rekomendasi row ── */
    .bd-reko-row {
      display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px;
    }
    .bd-panel {
      background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
      border-radius:14px; padding:16px 18px;
    }
    .bd-panel-title {
      font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.12em;
      color:#94a3b8; margin-bottom:14px; display:flex; align-items:center; gap:6px;
    }
    .bd-row {
      display:flex; justify-content:space-between; align-items:center;
      padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04);
    }
    .bd-row:last-child { border-bottom:none; }
    .bd-name { font-size:14px; font-weight:500; color:#cbd5e1; }
    .bd-badge {
      font-size:12px; font-weight:700; padding:4px 12px;
      border-radius:20px; letter-spacing:.04em;
    }
    .bd-badge-rendah { background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.2); }
    .bd-badge-sedang { background:rgba(245,158,11,0.12); color:#fbbf24; border:1px solid rgba(245,158,11,0.2); }
    .bd-badge-tinggi { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.2);  }

    /* ── Rekomendasi panel ── */
    .reko-panel {
      background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
      border-radius:14px; padding:16px 18px;
    }
    .reko-title {
      font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.12em;
      color:#94a3b8; margin-bottom:14px; display:flex; align-items:center; gap:6px;
    }
    .reko-item {
      display:flex; align-items:flex-start; gap:10px; padding:10px 0;
      border-bottom:1px solid rgba(255,255,255,0.05); font-size:14px;
      color:#cbd5e1; line-height:1.7; font-weight:400;
    }
    .reko-item:last-child { border-bottom:none; }
    .reko-num {
      flex-shrink:0; width:24px; height:24px; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      font-size:12px; font-weight:800; margin-top:2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── ENGINE PILL SUBTITLE ──────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:20px;margin-top:-16px'>
        <div class='engine-pill'>
            <span class='engine-label'>Prediction Engine</span>
            <span class='engine-desc'>Random Forest + Isolation Forest + Trend Ekstrapolasi &nbsp;·&nbsp; pola historis 2009–2024</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SELECTOR ROW ─────────────────────────────────────
    _now = datetime.now()
    _MONTH_NAMES = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']

    _sel_left, _sel_right = st.columns([58, 42])
    with _sel_left:
        _sel_c1, _sel_c2 = st.columns([1, 1])
        with _sel_c1:
            st.markdown("<div class='ctrl-label'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;margin-right:6px;vertical-align:middle;flex-shrink:0'></span>TAHUN MULAI</div>", unsafe_allow_html=True)
            _year_opts      = list(range(int(predictions['month'].iloc[-1][:4]), _now.year + 3))
            _default_yr_idx = _year_opts.index(_now.year) if _now.year in _year_opts else 0
            _proj_year      = st.selectbox("Tahun", _year_opts, index=_default_yr_idx,
                                            key="proj_year", label_visibility="collapsed")
        with _sel_c2:
            st.markdown("<div class='ctrl-label'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;margin-right:6px;vertical-align:middle;flex-shrink:0'></span>BULAN MULAI</div>", unsafe_allow_html=True)
            _proj_month_name = st.selectbox("Bulan", _MONTH_NAMES, index=_now.month-1,
                                             key="proj_month", label_visibility="collapsed")
            _proj_month_num  = _MONTH_NAMES.index(_proj_month_name) + 1
    with _sel_right:
        st.markdown("<div class='ctrl-label'>⏱ Jumlah Bulan Proyeksi</div>", unsafe_allow_html=True)
        _proj_n = st.slider("Jumlah Bulan", 3, 12, 6, 1, key="proj_n",
                             label_visibility="collapsed")
        st.markdown("<div class='slider-range-row'><span>3</span><span>12</span></div>", unsafe_allow_html=True)

    if _proj_month_num == 1:
        _from_month_str = f"{_proj_year - 1}-12"
    else:
        _from_month_str = f"{_proj_year}-{_proj_month_num - 1:02d}"

    fc_list_tab, fc_trend_tab = forecast_months(predictions, n=_proj_n, from_month=_from_month_str)

    st.markdown("<div style='margin:4px 0 20px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2-COLUMN LAYOUT  LEFT 58%  |  RIGHT 42%
    # ════════════════════════════════════════════════════
    t4_left, t4_right = st.columns([58, 42])

    # ══ LEFT ═════════════════════════════════════════════
    with t4_left:

        # ── Section header ───────────────────────────────
        st.markdown(
            "<div class='pred-section-hdr'>"
            "<div class='pred-section-hdr-line'></div>"
            "<div class='pred-section-hdr-text'>Proyeksi " + str(_proj_n) + " Bulan — " + _proj_month_name + " " + str(_proj_year) + "</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>",
            unsafe_allow_html=True)

        # ── Forecast grid cards — fixed 12 slots (4 rows x 3 cols) ──
        # Confidence tiers: 76-100 high (green), 51-75 mid (amber), 26-50 low (orange), ≤25 vlow (muted)
        _MAX_SLOTS = 12
        _full_grid_html = "<div class='fc-grid-fixed'>"
        for _gi in range(_MAX_SLOTS):
            if _gi < len(fc_list_tab):
                _fc  = fc_list_tab[_gi]
                _lv  = _fc['level']
                _clr = COLOR_MAP.get(_lv, '#3b82f6')
                _cf  = _fc['confidence']
                _cw  = int(_cf)
                # Confidence tier → warna berdasarkan % confidence
                # 76-100=hijau, 51-75=kuning, 26-50=oranye, 0-25=merah
                if _cf >= 76:
                    _tier_cls  = "fc-conf-high"
                    _pct_color = "#22c55e"   # hijau
                elif _cf >= 51:
                    _tier_cls  = "fc-conf-mid"
                    _pct_color = "#eab308"   # kuning
                elif _cf >= 26:
                    _tier_cls  = "fc-conf-low"
                    _pct_color = "#f97316"   # oranye
                else:
                    _tier_cls  = "fc-conf-vlow"
                    _pct_color = "#ef4444"   # merah
                _full_grid_html += (
                    "<div class='fc-grid-card {tier}'>"
                    "<div style='position:absolute;top:0;left:0;right:0;height:3px;"
                    "background:{pc};border-radius:14px 14px 0 0'></div>"
                    "<div class='fc-card-month'>{mo}</div>"
                    "<div class='fc-card-level' style='color:{pc}'>{lv}</div>"
                    "<div class='fc-card-score'>{sc}/100</div>"
                    "<div class='fc-conf-bar-wrap'>"
                    "<div class='fc-conf-bar-fill' style='width:{cw}%;background:{pc}'></div>"
                    "</div>"
                    "<div class='fc-conf-label'>"
                    "<span class='fc-conf-pct' style='color:{pc}'>{cf:.0f}%</span>"
                    "<span class='fc-conf-txt'>confidence</span>"
                    "</div>"
                    "</div>"
                ).format(tier=_tier_cls, clr=_clr, mo=_fc['month'],
                         lv=_lv, sc=_fc['score'], cw=_cw, cf=_cf, pc=_pct_color)
            else:
                _full_grid_html += "<div class='fc-grid-card fc-grid-empty'></div>"
        _full_grid_html += "</div>"
        st.markdown(_full_grid_html, unsafe_allow_html=True)

        st.markdown(
            "<div class='fc-note'>⚠️ Proyeksi berdasarkan tren historis. Confidence menurun seiring jarak proyeksi.</div>",
            unsafe_allow_html=True)

        # Track chart tab state here (rendered full-width later)
        if 'pred_chart_tab' not in st.session_state:
            st.session_state['pred_chart_tab'] = 'trend'
        _active_chart = st.session_state['pred_chart_tab']

    # ══ RIGHT ════════════════════════════════════════════
    with t4_right:

        # ── Simulator header ─────────────────────────────
        st.markdown(
            "<div class='pred-section-hdr'>"
            "<div class='pred-section-hdr-line'></div>"
            "<div class='pred-section-hdr-text'>Simulator Skenario Risiko</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>",
            unsafe_allow_html=True)

        st.markdown(
            "<div class='sim-hint'>Geser slider untuk simulasi dampak perubahan indikator secara real-time.</div>",
            unsafe_allow_html=True)

        # ── Sliders with value pills rendered via HTML label ──
        w_d = st.slider("Wisman (%)", -80, 50, 0, 5, key="sim_w")
        st.markdown("<div class='slider-range-row'><span>-80%</span><span>+50%</span></div>", unsafe_allow_html=True)
        u_d = st.slider("USD/IDR (%)", -10, 30, 0, 1, key="sim_u")
        st.markdown("<div class='slider-range-row'><span>-10%</span><span>+30%</span></div>", unsafe_allow_html=True)
        s_d = st.slider("Sentimen", -1.0, 1.0, 0.0, 0.1, key="sim_s")
        st.markdown("<div class='slider-range-row'><span>-1.0</span><span>+1.0</span></div>", unsafe_allow_html=True)

        sim_sc = simulate_score(dict(row_data), w_d, u_d, s_d)
        sim_lv = level_from_score(sim_sc)
        _sdelta = sim_sc - score
        _sdcol  = "#ef4444" if _sdelta > 0 else "#10b981"
        _sclr   = COLOR_MAP.get(sim_lv, '#fff')

        # ── Hasil Simulasi box ────────────────────────────
        st.markdown(
            "<div class='sim-result' style='"
            "background:linear-gradient(145deg,rgba(10,20,50,0.95),rgba(18,30,65,0.95));"
            "border-top:3px solid {clr};border-color:{clr}44'>"
            "<div class='sim-result-label' style='color:{clr}99'>Hasil Simulasi &nbsp;·&nbsp; Crisis Score / 100</div>"
            "<div class='sim-result-score' style='color:{clr}'>{sc}</div>"
            "<div>"
            "<span class='sim-level-badge' style='background:{clr}22;"
            "color:{clr};border:1px solid {clr}66;font-weight:700'>{lv}</span>"
            "</div>"
            "<div class='sim-delta-txt'>"
            "dari {base:.1f} → <span style='color:{dc};font-weight:700'>{d:+.1f} poin</span>"
            "</div>"
            "</div>".format(
                sc=sim_sc, clr=_sclr, lv=sim_lv,
                base=score, dc=_sdcol, d=_sdelta),
            unsafe_allow_html=True)

        # Peta Risiko Historis dipindah ke bawah tab (full-width) — lihat bagian _active_chart == 'scatter'

    # ══════════════════════════════════════════════════════════
    # BREAKDOWN RISIKO + REKOMENDASI — full-width, above charts
    # ══════════════════════════════════════════════════════════
    _bd_rows = [
        ("Penurunan Wisman",
         "Tinggi" if w_d<-20 else ("Sedang" if w_d<0 else "Rendah"),
         "tinggi" if w_d<-20 else ("sedang" if w_d<0 else "rendah")),
        ("Tekanan Kurs USD",
         "Tinggi" if u_d>10  else ("Sedang" if u_d>3  else "Rendah"),
         "tinggi" if u_d>10  else ("sedang" if u_d>3  else "rendah")),
        ("Sentimen Negatif",
         "Tinggi" if s_d<-0.3 else ("Sedang" if s_d<0 else "Rendah"),
         "tinggi" if s_d<-0.3 else ("sedang" if s_d<0 else "rendah")),
    ]
    _rclr_btn = COLOR_MAP.get(sim_lv, '#3b82f6')

    _bottom_html = "<div class='bd-reko-row'>"

    # Left: Breakdown Risiko
    _bottom_html += (
        "<div class='bd-panel'>"
        "<div class='bd-panel-title'>"
        "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
        "background:#f59e0b;box-shadow:0 0 6px #f59e0b66'></span>"
        "Breakdown Risiko"
        "</div>"
    )
    for nm, st_txt, cls in _bd_rows:
        _bottom_html += (
            "<div class='bd-row'>"
            "<span class='bd-name'>{nm}</span>"
            "<span class='bd-badge bd-badge-{cls}'>{st}</span>"
            "</div>"
        ).format(nm=nm, st=st_txt, cls=cls)
    _bottom_html += "</div>"

    # Right: Rekomendasi
    _bottom_html += (
        "<div class='reko-panel'>"
        "<div class='reko-title'>"
        "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
        "background:{clr};box-shadow:0 0 6px {clr}88'></span>"
        "Rekomendasi — Level {lv}"
        "</div>"
    ).format(clr=_rclr_btn, lv=sim_lv)
    for i, rec in enumerate(ADVICE_MAP.get(sim_lv, []), 1):
        _bottom_html += (
            "<div class='reko-item'>"
            "<span class='reko-num' style='background:{clr}20;color:{clr}'>{i}</span>"
            "<span>{rec}</span>"
            "</div>"
        ).format(clr=_rclr_btn, i=i, rec=rec)
    _bottom_html += "</div></div>"
    st.markdown(_bottom_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # CHART TABS — full-width, below breakdown
    # ══════════════════════════════════════════════════════════
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    _chart_c1, _chart_c2, _chart_c3 = st.columns(3)
    with _chart_c1:
        if st.button("Tren + Proyeksi", key="pct_trend",
                     type="primary" if st.session_state['pred_chart_tab']=='trend' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'trend'
            st.rerun()
    with _chart_c2:
        if st.button("Recovery Rate vs Baseline", key="pct_rec",
                     type="primary" if st.session_state['pred_chart_tab']=='recovery' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'recovery'
            st.rerun()
    with _chart_c3:
        if st.button("Peta Risiko Historis", key="pct_scatter",
                     type="primary" if st.session_state['pred_chart_tab']=='scatter' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'scatter'
            st.rerun()

    components.html("""
    <script>
    (function() {
        const labels = ["Tren + Proyeksi", "Recovery Rate vs Baseline", "Peta Risiko Historis"];
        function boldTabBtns() {
            window.parent.document.querySelectorAll('.stButton button').forEach(btn => {
                const txt = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                if (labels.includes(txt)) {
                    btn.style.setProperty('font-weight', '800', 'important');
                    btn.style.setProperty('letter-spacing', '.02em', 'important');
                    btn.style.setProperty('font-size', '14px', 'important');
                }
            });
        }
        boldTabBtns();
        setTimeout(boldTabBtns, 200);
        setTimeout(boldTabBtns, 600);
        new MutationObserver(boldTabBtns).observe(
            window.parent.document.body, {childList:true, subtree:true}
        );
    })();
    </script>
    """, height=0)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # ── Chart content — full width ────────────────────────
    if _active_chart == 'trend':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text' style='color:#1e3a5f'>↗ TREN + PROYEKSI</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        last12    = predictions.tail(12)
        l12_dt    = pd.to_datetime(last12['month'].astype(str))
        fc_dt     = pd.to_datetime([f['month'] for f in fc_list_tab])
        fc_scores = [f['score'] for f in fc_list_tab]
        fc_lo     = [max(0,  s - 8) for s in fc_scores]
        fc_hi     = [min(100, s + 8) for s in fc_scores]
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=l12_dt, y=last12['crisis_score_100'],
            mode='lines+markers', name='Historis',
            line=dict(color='#7dd3fc', width=2.5), marker=dict(size=5, color='#7dd3fc')))
        fig_fc.add_trace(go.Scatter(
            x=list(fc_dt)+list(reversed(list(fc_dt))),
            y=fc_hi+list(reversed(fc_lo)),
            fill='toself', fillcolor='rgba(34,197,94,0.07)',
            line=dict(width=0), showlegend=True, name='Interval ±8', hoverinfo='skip'))
        fig_fc.add_trace(go.Scatter(x=fc_dt, y=fc_scores,
            mode='lines+markers', name='Proyeksi',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            marker=dict(size=8, symbol='diamond', color='#f59e0b')))
        for thr,lbl,col in [(60,'KRISIS','#ef4444'),(45,'SIAGA','#f97316'),(30,'WASPADA','#f59e0b')]:
            fig_fc.add_hline(y=thr, line_dash='dot', line_color=col, line_width=0.7, opacity=0.45,
                             annotation_text=lbl, annotation_position='right',
                             annotation_font_size=9, annotation_font_color=col)
        fig_fc.update_layout(
            yaxis=dict(range=[0,100], title='Crisis Score',
                       gridcolor='rgba(255,255,255,0.04)', color='#475569', tickfont=dict(size=10)),
            xaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#475569', tickfont=dict(size=10)),
            plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
            height=320, margin=dict(l=0, r=72, t=10, b=0),
            legend=dict(orientation='h', y=1.04, x=0, bgcolor='rgba(0,0,0,0)',
                        font=dict(size=10, color='#94a3b8')),
            font=dict(family='DM Sans', size=11, color='#94a3b8'))
        st.plotly_chart(fig_fc, use_container_width=True)

    elif _active_chart == 'recovery':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text' style='color:#1e3a5f'>📉 RECOVERY RATE VS BASELINE 2017–2019</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        _precovid_mean = delta_ctx['precovid_mean']
        if _precovid_mean > 0 and 'wisman' in predictions.columns:
            rec_df = predictions.copy()
            rec_df['recovery_pct'] = (rec_df['wisman'] / _precovid_mean * 100).round(1)
            fig_rec = go.Figure()
            fig_rec.add_hline(y=100, line_dash='dot', line_color='#10b981', line_width=1.5,
                              annotation_text='Baseline 100%', annotation_position='right',
                              annotation_font_color='#10b981', annotation_font_size=10)
            fig_rec.add_trace(go.Scatter(
                x=pd.to_datetime(rec_df['month'].astype(str)), y=rec_df['recovery_pct'],
                mode='lines', fill='tozeroy',
                fillcolor='rgba(59,130,246,0.06)', line=dict(color='#3b82f6', width=2)))
            fig_rec.add_vrect(x0='2020-03-01', x1='2021-12-01',
                fillcolor='rgba(239,68,68,0.05)', line_width=0,
                annotation_text='COVID', annotation_font_color='#ef4444')
            fig_rec.add_vline(x=sel_dt, line_dash='dot', line_color='#7dd3fc', line_width=1.2)
            fig_rec.update_layout(
                yaxis=dict(title='Recovery (%)', gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0, r=80, t=8, b=0),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_rec, use_container_width=True)
            _rcol = '#10b981' if delta_ctx['recovery_pct'] >= 90 else \
                    ('#f59e0b' if delta_ctx['recovery_pct'] >= 60 else '#ef4444')
            st.markdown(
                "<div style='background:rgba(255,255,255,0.02);border-radius:8px;"
                "padding:8px 14px;font-size:12px;color:#475569;border:1px solid rgba(255,255,255,0.05)'>"
                "Recovery <b style='color:#e2e8f0'>{mo}</b>: "
                "<span style='color:{rc};font-weight:700;font-size:14px'>{rv:.1f}%</span>"
                " dari baseline ({bsl:,} wisman/bln)</div>".format(
                    mo=sel, rc=_rcol, rv=delta_ctx['recovery_pct'], bsl=int(_precovid_mean)),
                unsafe_allow_html=True)

    elif _active_chart == 'scatter':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text' style='color:#1e3a5f'>🗺️ PETA RISIKO HISTORIS</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        _sc_src = master if 'wisman_growth_mom' in master.columns else predictions
        if 'wisman_growth_mom' in _sc_src.columns and 'crisis_level' in _sc_src.columns:
            fig_r2 = go.Figure()
            for _lv_sc in ['AMAN','WASPADA','SIAGA','KRISIS']:
                _mask = _sc_src['crisis_level'] == _lv_sc
                if _mask.sum() > 0:
                    fig_r2.add_trace(go.Scatter(
                        x=_sc_src.loc[_mask,'wisman_growth_mom']*100,
                        y=_sc_src.loc[_mask,'avg_sentiment_monthly'],
                        mode='markers', name=_lv_sc,
                        marker=dict(color=COLOR_MAP[_lv_sc], size=7, opacity=0.8,
                                    line=dict(width=0.5, color='rgba(0,0,0,0.3)'))))
            fig_r2.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r2.add_vline(x=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r2.update_layout(
                xaxis=dict(title='Wisman Growth MoM (%)',
                           gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                yaxis=dict(title='Avg Sentimen',
                           gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation='h', y=1.04, x=0, bgcolor='rgba(0,0,0,0)',
                            font=dict(size=10, color='#94a3b8')),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_r2, use_container_width=True)

    st.markdown("<div style='margin-bottom:32px'></div>", unsafe_allow_html=True)



# ─── TAB 5: NARASI AI ─────────────────────────────────
if selected_nav == "Narasi AI":
    _tick("nav_start_narasi")

    # ── Hero banner ──────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#052e16 0%,#064e3b 60%,#065f46 100%);
                border-radius:16px;padding:24px 28px;margin-bottom:24px;
                border:1px solid rgba(74,222,128,0.18);box-shadow:0 4px 24px rgba(0,0,0,0.3)'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px'>
            <div>
                <div style='font-size:10px;font-weight:700;color:rgba(74,222,128,0.55);
                            text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px'>
                    🤖 AI NARRATIVE ENGINE · Powered by Groq
                </div>
                <div style='font-size:22px;color:#bbf7d0;line-height:1.3;margin-bottom:8px;font-weight:600'>
                    Mengubah Data Menjadi Laporan Siap Baca
                </div>
                <div style='font-size:13px;color:#6ee7b7;line-height:1.8;max-width:560px'>
                    Narasi AI menganalisis output model ML — crisis score, prediksi RF, anomali,
                    wisman, sentimen — lalu <b>menyusunnya menjadi laporan Bahasa Indonesia</b>
                    yang siap digunakan pemangku kebijakan dan dinas pariwisata.
                </div>
            </div>
            <div style='text-align:center;background:rgba(0,0,0,0.25);border-radius:12px;
                        padding:14px 20px;border:1px solid rgba(74,222,128,0.15)'>
                <div style='font-size:10px;color:rgba(74,222,128,0.6);text-transform:uppercase;
                            letter-spacing:.08em;margin-bottom:4px'>PROVIDER</div>
                <div style='font-family:monospace;font-size:13px;color:#4ade80;font-weight:700'>
                    Groq Cloud API
                </div>
                <div style='font-size:12px;color:#86efac;margin-top:6px'>Latensi &lt; 1 detik · Gratis</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Kegunaan cards ────────────────────────────────────
    st.markdown("""
    <div style='font-size:15px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:.12em;margin-bottom:14px'>APA GUNANYA NARASI AI?</div>
    <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:24px'>
        <div style='background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#93c5fd;margin-bottom:6px;text-align:center'>Laporan Dinas / Rapat</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Draft laporan bulanan siap presentasi ke kepala dinas atau DPRD tanpa tulis manual.
            </div>
        </div>
        <div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#fca5a5;margin-bottom:6px;text-align:center'>Peringatan Dini Krisis</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Saat SIAGA/KRISIS terdeteksi, sistem menyusun teks peringatan + rekomendasi untuk stakeholder.
            </div>
        </div>
        <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#fcd34d;margin-bottom:6px;text-align:center'>Press Release / Media</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Ringkasan berbasis data sebagai bahan siaran pers atau infografis pariwisata Bali.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:4px 0 20px'></div>",
                unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # CONFIG COLUMNS
    # ══════════════════════════════════════════════════════
    # ─ 1. TIPE LAPORAN — FULL WIDTH 4 CARDS ──────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:18px'>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>PILIH TIPE LAPORAN</div>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
    </div>""", unsafe_allow_html=True)

    REPORT_CARDS = {
        'summary': {
            'icon':'⚡','title':'Quick Summary','desc':'2–3 kalimat ringkas',
            'detail':'Cocok untuk KPI card, notifikasi, atau update cepat di grup WhatsApp dinas.',
            'color':'#3b82f6','bg':'rgba(59,130,246,0.10)','border':'rgba(59,130,246,0.30)',
        },
        'alert': {
            'icon':'🚨','title':'Emergency Alert','desc':'Peringatan darurat ≤120 kata',
            'detail':'Status level + 3 indikator kritis + 1 rekomendasi segera. Untuk SIAGA/KRISIS.',
            'color':'#ef4444','bg':'rgba(239,68,68,0.10)','border':'rgba(239,68,68,0.30)',
        },
        'monthly': {
            'icon':'📑','title':'Laporan Bulanan','desc':'Laporan lengkap 4 bagian',
            'detail':'Ringkasan Eksekutif · Analisis Indikator · Faktor Pendorong · Rekomendasi.',
            'color':'#22c55e','bg':'rgba(74,222,128,0.10)','border':'rgba(74,222,128,0.30)',
        },
        'predict': {
            'icon':'🔮','title':'Prediksi AI','desc':'Proyeksi + skenario risiko',
            'detail':'Prediksi 3–6 bulan ke depan berbasis tren ML, faktor risiko, dan rekomendasi antisipatif.',
            'color':'#a855f7','bg':'rgba(168,85,247,0.10)','border':'rgba(168,85,247,0.30)',
        },
    }

    if 'report_type_sel' not in st.session_state:
        st.session_state['report_type_sel'] = 'summary'

    _rt_cols = st.columns(4)
    for _i, (_key, _card) in enumerate(REPORT_CARDS.items()):
        with _rt_cols[_i]:
            _is_sel = st.session_state['report_type_sel'] == _key
            _bdr    = ("2px solid " + _card['color']) if _is_sel else ("1px solid " + _card['border'])
            _shad   = ("box-shadow:0 0 14px " + _card['color'] + "44;") if _is_sel else ""
            _opac   = "1" if _is_sel else "0.90"
            st.markdown(
                "<div style='background:" + _card['bg'] + ";border:" + _bdr + ";"
                "border-radius:12px;padding:20px 16px 16px;min-height:140px;margin-bottom:6px;"
                "opacity:" + _opac + ";" + _shad + ";transition:opacity .2s'>"
                "<div style='font-size:16px;font-weight:800;color:" + _card['color'] + ";margin-bottom:4px;text-align:center'>"
                + _card['title'] + "</div>"
                "<div style='font-size:13px;color:#cbd5e1;font-weight:700;margin-bottom:6px;text-align:center'>"
                + _card['desc'] + "</div>"
                "<div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>" + _card['detail'] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button(_card['title'], key="rt_" + _key, width="stretch"):
                st.session_state['report_type_sel'] = _key
                st.rerun()

    # ── Warna + hover + selected state tombol via JS ──────
    _active_title = REPORT_CARDS[st.session_state['report_type_sel']]['title']
    _btn_map = {c['title']: c['color'] for c in REPORT_CARDS.values()}
    _js_map  = str(_btn_map).replace("'", '"')
    _js_active = _active_title
    components.html(f"""
    <script>
    (function() {{
        const colors  = {_js_map};
        const active  = "{_js_active}";

        function hexToRgba(hex, a) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{a}})`;
        }}

        function style() {{
            const btns = window.parent.document.querySelectorAll('.stButton button');
            btns.forEach(btn => {{
                const label = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                const color = colors[label];
                if (!color) return;

                const isSel = (label === active);

                // base style
                btn.style.setProperty('background',    isSel ? color : hexToRgba(color, 0.45), 'important');
                btn.style.setProperty('color',         '#ffffff', 'important');
                btn.style.setProperty('border',        '1px solid ' + hexToRgba(color, 0.6), 'important');
                btn.style.setProperty('font-weight',   '700', 'important');
                btn.style.setProperty('border-radius', '8px', 'important');
                btn.style.setProperty('transition',    'background .18s, box-shadow .18s', 'important');
                if (isSel) {{
                    btn.style.setProperty('box-shadow', '0 0 12px ' + hexToRgba(color, 0.5), 'important');
                }} else {{
                    btn.style.removeProperty('box-shadow');
                }}

                // hover
                btn.onmouseenter = () => {{
                    btn.style.setProperty('background',  color, 'important');
                    btn.style.setProperty('box-shadow',  '0 0 14px ' + hexToRgba(color, 0.55), 'important');
                    btn.style.setProperty('opacity',     '1', 'important');
                }};
                btn.onmouseleave = () => {{
                    btn.style.setProperty('background',  isSel ? color : hexToRgba(color, 0.45), 'important');
                    btn.style.setProperty('box-shadow',  isSel ? '0 0 12px ' + hexToRgba(color, 0.5) : 'none', 'important');
                }};
            }});
        }}

        style();
        setTimeout(style, 200);
        setTimeout(style, 600);
        new MutationObserver(style).observe(
            window.parent.document.body, {{childList:true, subtree:true}}
        );
    }})();
    </script>
    """, height=0)

    report_type = st.session_state['report_type_sel']
    _sel_card   = REPORT_CARDS[report_type]
    st.markdown(
        "<div style='margin-top:-12px;margin-bottom:20px;background:" + _sel_card['bg'] + ";border-radius:8px;"
        "padding:12px 16px;border-left:3px solid " + _sel_card['color'] + "'>"
        "<span style='font-size:14px;color:#94a3b8'>Tipe dipilih: "
        "<b style='color:" + _sel_card['color'] + "'>" + _sel_card['title'] + "</b>"
        " &nbsp;·&nbsp; <span style='color:#cbd5e1'>" + _sel_card['desc'] + "</span></span></div>",
        unsafe_allow_html=True
    )

    # ─ MODEL (4 kolom horizontal full width) ────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:16px'>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>PILIH MODEL AI</div>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
    </div>""", unsafe_allow_html=True)

    GROQ_MODELS = {
        'llama-3.3-70b-versatile': {
            'label': 'Llama 3.3 70B', 'tag': 'Terbaik',
            'desc': 'Akurasi tinggi, analisis mendalam',
            'color': '#a78bfa', 'bg': 'rgba(167,139,250,0.10)', 'border': 'rgba(167,139,250,0.28)',
            'icon': '🏆',
        },
        'llama-3.1-8b-instant': {
            'label': 'Llama 3.1 8B', 'tag': 'Tercepat',
            'desc': 'Respons < 0.5 detik, ringkas',
            'color': '#34d399', 'bg': 'rgba(52,211,153,0.10)', 'border': 'rgba(52,211,153,0.28)',
            'icon': '⚡',
        },
        'mixtral-8x7b-32768': {
            'label': 'Mixtral 8×7B', 'tag': 'Konteks Panjang',
            'desc': 'Laporan detail & komprehensif',
            'color': '#60a5fa', 'bg': 'rgba(96,165,250,0.10)', 'border': 'rgba(96,165,250,0.28)',
            'icon': '📄',
        },
        'gemma2-9b-it': {
            'label': 'Gemma2 9B', 'tag': 'Bahasa Natural',
            'desc': 'Narasi mengalir & mudah dibaca',
            'color': '#fb923c', 'bg': 'rgba(251,146,60,0.10)', 'border': 'rgba(251,146,60,0.28)',
            'icon': '✍️',
        },
    }

    if 'selected_model_key' not in st.session_state:
        st.session_state['selected_model_key'] = 'llama-3.3-70b-versatile'

    # ── Warna tiap model MENGIKUTI POSISI KOLOM tipe laporan di atasnya ──
    # Kolom 0: Quick Summary (biru), Kolom 1: Emergency Alert (merah),
    # Kolom 2: Laporan Bulanan (hijau), Kolom 3: Prediksi AI (ungu)
    _report_list = list(REPORT_CARDS.values())   # urutan sama: summary, alert, monthly, predict

    _mcols = st.columns(4)
    _model_items = list(GROQ_MODELS.items())
    for _mi, (_mkey, _mcard) in enumerate(_model_items):
        # Ambil warna dari report card sejajar (posisi _mi)
        _paired = _report_list[_mi]
        _pc     = _paired['color']
        _pb     = _paired['bg']
        _pbr    = _paired['border']

        with _mcols[_mi]:
            _is_msel = st.session_state['selected_model_key'] == _mkey
            _m_bdr   = ("2px solid " + _pc) if _is_msel else ("1px solid " + _pbr)
            _m_shad  = ("box-shadow:0 0 14px " + _pc + "55;") if _is_msel else ""
            _m_opac  = "1" if _is_msel else "0.90"
            st.markdown(
                "<div style='background:" + _pb + ";border:" + _m_bdr + ";"
                "border-radius:10px;padding:12px 14px;opacity:" + _m_opac + ";" + _m_shad + ";margin-bottom:6px;"
                "transition:opacity .2s,border .2s,box-shadow .2s'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>"
                "<div style='font-size:16px;font-weight:800;color:" + _pc + "'>" + _mcard['label'] + "</div>"
                "<span style='font-size:11px;font-weight:700;background:" + _pc + "22;"
                "color:" + _pc + ";padding:3px 9px;border-radius:10px'>"
                + _mcard['tag'] + "</span></div>"
                "<div style='font-size:13px;color:#cbd5e1;line-height:1.5'>" + _mcard['desc'] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button(_mcard['label'], key="model_" + _mkey, width="stretch"):
                st.session_state['selected_model_key'] = _mkey
                st.rerun()

    selected_model = st.session_state['selected_model_key']
    _sel_mcard     = GROQ_MODELS[selected_model]

    # ── JS: tiap tombol model pakai warna report sejajarnya (per posisi) ──
    # Bangun map: label → warna report sejajar
    _model_color_map = {
        list(GROQ_MODELS.values())[i]['label']: _report_list[i]['color']
        for i in range(4)
    }
    _sel_model_label  = _sel_mcard['label']
    _js_model_color_map = str(_model_color_map).replace("'", '"')
    components.html(f"""
    <script>
    (function() {{
        const colorMap   = {_js_model_color_map};
        const activeModel = "{_sel_model_label}";

        function hexToRgba(hex, a) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{a}})`;
        }}

        function styleModelBtns() {{
            const btns = window.parent.document.querySelectorAll('.stButton button');
            btns.forEach(btn => {{
                const label = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                const color = colorMap[label];
                if (!color) return;

                const isSel = (label === activeModel);

                btn.style.setProperty('background',    isSel ? color : hexToRgba(color, 0.30), 'important');
                btn.style.setProperty('color',         '#ffffff', 'important');
                btn.style.setProperty('border',        '1px solid ' + hexToRgba(color, isSel ? 0.85 : 0.45), 'important');
                btn.style.setProperty('font-weight',   '700', 'important');
                btn.style.setProperty('border-radius', '8px', 'important');
                btn.style.setProperty('transition',    'background .18s, box-shadow .18s', 'important');
                if (isSel) {{
                    btn.style.setProperty('box-shadow', '0 0 12px ' + hexToRgba(color, 0.50), 'important');
                }} else {{
                    btn.style.setProperty('box-shadow', 'none', 'important');
                }}

                btn.onmouseenter = () => {{
                    btn.style.setProperty('background',  color, 'important');
                    btn.style.setProperty('box-shadow',  '0 0 14px ' + hexToRgba(color, 0.55), 'important');
                    btn.style.setProperty('opacity',     '1', 'important');
                }};
                btn.onmouseleave = () => {{
                    btn.style.setProperty('background',  isSel ? color : hexToRgba(color, 0.30), 'important');
                    btn.style.setProperty('box-shadow',  isSel ? '0 0 12px ' + hexToRgba(color, 0.50) : 'none', 'important');
                }};
            }});
        }}

        styleModelBtns();
        setTimeout(styleModelBtns, 200);
        setTimeout(styleModelBtns, 600);
        new MutationObserver(styleModelBtns).observe(
            window.parent.document.body, {{childList:true, subtree:true}}
        );
    }})();
    </script>
    """, height=0)

    # ── Status bar model: warna ikut warna posisi model yg dipilih ──
    _sel_model_idx   = list(GROQ_MODELS.keys()).index(selected_model)
    _sel_pair_card   = _report_list[_sel_model_idx]
    st.markdown(
        "<div style='margin-top:-12px;background:" + _sel_pair_card['bg'] + ";border-radius:8px;"
        "padding:12px 16px;border-left:3px solid " + _sel_pair_card['color'] + "'>"
        "<span style='font-size:14px;color:#94a3b8'>Model: "
        "<b style='color:" + _sel_pair_card['color'] + "'>" + _sel_mcard['label'] + "</b>"
        " &nbsp;·&nbsp; <span style='color:#cbd5e1'>" + _sel_mcard['tag'] + "</span></span></div>",
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin:16px 0 8px'></div>", unsafe_allow_html=True)

    # ─ API & STATUS — FULL WIDTH ──────────────────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:18px'>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>API &amp; STATUS</div>
        <div style='flex:1;height:1px;background:rgba(255,255,255,0.10)'></div>
    </div>""", unsafe_allow_html=True)

    # ─ PILIH BULAN & TAHUN ────────────────────────────────
    _avail_months_hist = sorted(predictions['month'].unique())
    _last_data_month   = _avail_months_hist[-1]
    _last_p            = pd.Period(_last_data_month, freq='M')
    _fc_extra, _       = forecast_months(predictions, n=18, from_month=str(_last_p - 1))
    _fc_months_only    = [f['month'] for f in _fc_extra]
    _fc_score_map      = {f['month']: f['score'] for f in _fc_extra}
    _fc_level_map      = {f['month']: f['level'] for f in _fc_extra}
    _all_months        = _avail_months_hist + [m for m in _fc_months_only if m not in _avail_months_hist]
    _avail_years       = sorted(set(m[:4] for m in _all_months), reverse=True)

    if 'narasi_year_sel' not in st.session_state:
        st.session_state['narasi_year_sel'] = sel[:4]
    if 'narasi_month_sel' not in st.session_state:
        st.session_state['narasi_month_sel'] = sel

    _MONTH_ID = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
    def _month_label_fn(m):
        base = _MONTH_ID[int(m[5:7])-1]
        return base

    # 4 kolom sejajar: Tahun | Bulan | Status | Cache
    _c_year, _c_month, _c_status, _c_cache = st.columns([1, 1, 1, 1])

    with _c_year:
        st.markdown("""<div style='font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                    letter-spacing:.12em;margin-bottom:12px'>BULAN YANG DIANALISIS</div>""",
                    unsafe_allow_html=True)
        _ny_idx  = _avail_years.index(st.session_state['narasi_year_sel']) \
                   if st.session_state['narasi_year_sel'] in _avail_years else 0
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0;font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:4px'>" "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0;margin-right:7px'></span>Tahun</div>", unsafe_allow_html=True)
        _sel_year = st.selectbox("", _avail_years, index=_ny_idx, key="narasi_year_box", label_visibility="collapsed")
        st.session_state['narasi_year_sel'] = _sel_year

    _months_for_year = [m for m in _all_months if m.startswith(_sel_year)]

    with _c_month:
        st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0;font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:4px'>" "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0;margin-right:7px'></span>Bulan</div>", unsafe_allow_html=True)
        _prev_nm = st.session_state.get('narasi_month_sel', sel)
        _nm_default = _prev_nm if _prev_nm in _months_for_year else _months_for_year[-1]
        _nm_idx  = _months_for_year.index(_nm_default)
        _sel_month = st.selectbox("", _months_for_year,
                                  format_func=_month_label_fn,
                                  index=_nm_idx, key="narasi_month_box", label_visibility="collapsed")
        st.session_state['narasi_month_sel'] = _sel_month

    narasi_target   = st.session_state['narasi_month_sel']
    _is_fc_month    = narasi_target not in _avail_months_hist
    if _is_fc_month:
        _narasi_level = _fc_level_map.get(narasi_target, 'WASPADA')
        _narasi_score = _fc_score_map.get(narasi_target, 0.0)
    else:
        _narasi_row   = get_row(narasi_target)
        _narasi_level = str(_narasi_row.get('crisis_level', 'WASPADA'))
        _narasi_score = sf(_narasi_row.get('crisis_score_100', 0))

    _fc_badge = (
        "<span style='font-size:10px;font-weight:700;background:rgba(167,139,250,0.15);"
        "color:#a78bfa;padding:2px 8px;border-radius:10px'>Proyeksi</span>"
    ) if _is_fc_month else ""

    # Cache status for narasi_target
    _has_cache    = narasi_target in narratives_cache
    _cache_level  = narratives_cache[narasi_target].get('crisis_level','') if _has_cache else ''
    _cache_tokens = narratives_cache[narasi_target].get('tokens', 0)        if _has_cache else 0

    with _c_status:
        _status_clr = COLOR_MAP.get(_narasi_level, '#fff')
        st.markdown("<div style='font-size:13px;font-weight:600;color:#e2e8f0;margin-top:31px;margin-bottom:4px'>Status Bulan</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.10);"
            "border-radius:8px;padding:0 14px;display:flex;align-items:center;gap:12px;"
            "height:42px;box-sizing:border-box'>"
            "<span style='font-size:15px;font-weight:800;color:" + _status_clr + "'>" + _narasi_level + "</span>"
            "<span style='font-family:monospace;font-size:13px;color:#94a3b8'>Score " + str(round(_narasi_score, 1)) + "/100</span>"
            + (_fc_badge if _is_fc_month else "") +
            "</div>",
            unsafe_allow_html=True
        )

    with _c_cache:
        _cache_bg  = "rgba(34,197,94,0.07)"  if _has_cache else "rgba(255,255,255,0.04)"
        _cache_bdr = "rgba(34,197,94,0.25)"  if _has_cache else "rgba(255,255,255,0.10)"
        _cache_inner = (
            "<span style='font-size:15px;color:#4ade80;font-weight:700'>Tersedia</span>"
            "<span style='font-size:13px;color:#94a3b8;margin-left:8px'>Level: <b style='color:#e2e8f0'>" + _cache_level + "</b>"
            " · " + str(_cache_tokens) + " tokens</span>"
        ) if _has_cache else (
            "<span style='font-size:14px;color:#94a3b8'>Belum ada cache untuk bulan ini</span>"
        )
        st.markdown("<div style='font-size:13px;font-weight:600;color:#e2e8f0;margin-top:31px;margin-bottom:4px'>Cache Narasi</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:" + _cache_bg + ";border:1px solid " + _cache_bdr + ";"
            "border-radius:8px;padding:0 14px;display:flex;align-items:center;gap:6px;"
            "height:42px;box-sizing:border-box'>"
            + _cache_inner + "</div>",
            unsafe_allow_html=True
        )

    # ─ API KEY + GENERATE ─────────────────────────────────
    # st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    # if not groq_key:
    #     st.markdown("""
    #     <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);
    #                 border-left:4px solid #f59e0b;border-radius:12px;padding:20px 22px;
    #                 margin-top:12px;display:flex;align-items:center;gap:24px'>
    #         <div style='flex:1'>
    #             <div style='font-size:16px;font-weight:800;color:#fbbf24;margin-bottom:8px;
    #                         letter-spacing:-.01em'>
    #                 Groq API Key Diperlukan
    #             </div>
    #             <div style='font-size:14px;color:#d97706;line-height:1.75;font-weight:500'>
    #                 Masukkan API Key di sidebar <strong style='color:#fbbf24'>(panel kiri)</strong>
    #                 untuk mengaktifkan fitur Narasi AI.<br>
    #                 Key 100% gratis dan bisa didapat dalam <strong style='color:#fbbf24'>30 detik</strong>
    #                 — tidak butuh kartu kredit.
    #             </div>
    #         </div>
    #         <div style='flex-shrink:0'>
    #             <a href='https://console.groq.com/keys' target='_blank'
    #                style='display:inline-flex;align-items:center;gap:8px;
    #                       background:linear-gradient(135deg,#f59e0b,#d97706);
    #                       color:#0a0a0a;font-size:14px;font-weight:800;
    #                       padding:12px 24px;border-radius:8px;text-decoration:none;
    #                       box-shadow:0 4px 16px rgba(245,158,11,0.4);
    #                       white-space:nowrap;letter-spacing:.01em'>
    #                 Dapatkan Key Gratis →
    #             </a>
    #         </div>
    #     </div>
    #     """, unsafe_allow_html=True)
    # else:
    #     st.markdown("""
    #     <div style='background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
    #                 border-radius:12px;padding:12px 16px;margin-top:12px'>
    #         <div style='font-size:12px;color:#4ade80;font-weight:700'>API Key Terhubung</div>
    #         <div style='font-size:10px;color:#475569;margin-top:3px'>Siap generate narasi</div>
    #     </div>
    #     """, unsafe_allow_html=True)
    groq_key = _get_groq_key()
    # ── Generate button — scoped CSS via unique container ─
    st.markdown("""
    <style>
    /* Scope ONLY to main content area, excluding sidebar */
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"] {
        background: #16a34a !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: .08em !important;
        padding: 14px 28px !important;
        border-radius: 10px !important;
        border: 1px solid #22c55e !important;
        box-shadow: 0 2px 14px rgba(22,163,74,0.4) !important;
        transition: all .18s ease !important;
        text-transform: uppercase !important;
    }
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:hover:not(:disabled) {
        background: #15803d !important;
        border-color: #4ade80 !important;
        box-shadow: 0 4px 22px rgba(22,163,74,0.55) !important;
        transform: translateY(-1px) !important;
    }
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:active:not(:disabled) {
        transform: translateY(0) !important;
    }
    /* Disabled — amber tint, tetap kelihatan */
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:disabled {
        background: rgba(245,158,11,0.15) !important;
        color: #f59e0b !important;
        border: 1px solid rgba(245,158,11,0.3) !important;
        box-shadow: none !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _btn_label = "Generate Narasi AI"
    gen_btn = st.button(_btn_label, type="primary",
                        use_container_width=True, disabled=not bool(groq_key))

    # ── Divider ──────────────────────────────────────────
    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:20px 0'></div>",
                unsafe_allow_html=True)

    # ── Output area ──────────────────────────────────────
    if _has_cache and not gen_btn:
        cached_n = narratives_cache[narasi_target]
        _clv  = cached_n.get('crisis_level', '')
        _clr  = COLOR_MAP.get(_clv, '#94a3b8')
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px'>"
            "<div style='font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;"
            "letter-spacing:.1em'>📄 NARASI TERSIMPAN</div>"
            "<span style='background:" + _clr + "22;color:" + _clr + ";font-size:10px;font-weight:700;"
            "padding:3px 10px;border-radius:20px;border:1px solid " + _clr + "44'>"
            + EMOJI_MAP.get(_clv,'') + " " + _clv + "</span>"
            "<span style='font-family:monospace;font-size:10px;color:#475569'>"
            + cached_n.get('month','') + "</span>"
            "<span style='font-size:10px;color:#334155'>·</span>"
            "<span style='font-family:monospace;font-size:10px;color:#334155'>"
            + str(cached_n.get('tokens',0)) + " tokens</span></div>"
            "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);"
            "border-radius:14px;padding:26px 30px;line-height:1.95;font-size:14px;"
            "color:#cbd5e1;border-top:3px solid " + _clr + "'>"
            + cached_n["narrative"].replace('\n', '<br>') + "</div>",
            unsafe_allow_html=True
        )

    if gen_btn and groq_key:
        with st.spinner("🤖 " + selected_model + " sedang menganalisis data " + narasi_target + "..."):
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                sys.path.insert(0, '.')
                from groq import Groq as _Groq
                import numpy as _np

                # Dapatkan data baris — historis atau proyeksi
                if _is_fc_month:
                    # Bulan proyeksi: ambil data terakhir sebagai basis, timpa dengan nilai proyeksi
                    _base_row        = dict(predictions.iloc[-1])
                    _narasi_row_data = _base_row.copy()
                    _narasi_row_data['month']           = narasi_target
                    _narasi_row_data['crisis_score_100'] = _narasi_score
                    _narasi_row_data['crisis_level']     = _narasi_level
                    _narasi_row_data['rf_predicted_level'] = _narasi_level
                    _narasi_row_data['rf_confidence']    = 0.70
                    _history = predictions.tail(3).to_dict('records')
                else:
                    _narasi_row_data = get_row(narasi_target)
                    _idx     = list(predictions['month']).index(narasi_target) \
                               if narasi_target in list(predictions['month']) else len(predictions)-1
                    _history = predictions.iloc[max(0, _idx - 3):_idx].to_dict('records')

                _ctx = {
                    'month'        : str(_narasi_row_data.get('month', narasi_target)),
                    'crisis_score' : round(float(_narasi_row_data.get('crisis_score_100', 0)), 1),
                    'crisis_level' : _narasi_level,
                    'rf_predicted' : str(_narasi_row_data.get('rf_predicted_level', 'N/A')),
                    'rf_confidence': round(float(_narasi_row_data.get('rf_confidence', 0)) * 100, 1),
                    'is_anomaly'   : int(sf(_narasi_row_data.get('iso_anomaly', 0))),
                    'wisman'       : int(sf(_narasi_row_data.get('wisman', 0))),
                    'tpk_bintang'  : round(float(_narasi_row_data.get('tpk_bintang', 0)), 1),
                    'inflasi'      : round(float(_narasi_row_data.get('inflasi_processed', 0)), 2),
                    'usd_idr'      : round(float(_narasi_row_data.get('usd_idr_avg', 0)), 0),
                    'sentiment'    : round(float(_narasi_row_data.get('avg_sentiment_monthly', 0)), 3),
                    'prob_krisis'  : round(float(_narasi_row_data.get('prob_krisis', 0)) * 100, 1),
                    'prob_siaga'   : round(float(_narasi_row_data.get('prob_siaga', 0)) * 100, 1),
                    'bali_share'   : round(float(_narasi_row_data.get('bali_share_pct', 0)), 1),
                    'wisman_zscore': round(float(_narasi_row_data.get('wisman_zscore', 0)), 2),
                }
                if _history:
                    _avg3 = _np.mean([r.get('wisman', 0) for r in _history[-3:]])
                    _ctx['wisman_trend']  = 'naik' if _ctx['wisman'] > _avg3 else 'turun'
                    _ctx['avg_wisman_3m'] = round(_avg3, 0)
                    _ctx['prev_levels']   = [r.get('crisis_level','N/A') for r in _history[-3:]]
                    # MoM delta untuk konteks kausal
                    _prev_r = _history[-1] if _history else {}
                    def _d(a, b, key): 
                        pv = float(_prev_r.get(key,0)); cv = float(a.get(key,0) if isinstance(a,dict) else a)
                        return round(cv - pv, 3) if pv != 0 else 0
                    _prev_w = float(_prev_r.get('wisman', 1))
                    _ctx['wisman_delta_pct'] = round((_ctx['wisman'] - _prev_w) / max(1,_prev_w) * 100, 1)
                    _ctx['score_delta']      = round(_ctx['crisis_score'] - float(_prev_r.get('crisis_score_100', _ctx['crisis_score'])), 1)
                    _ctx['sent_delta']       = round(_ctx['sentiment'] - float(_prev_r.get('avg_sentiment_monthly', _ctx['sentiment'])), 3)
                    _ctx['tpk_delta']        = round(_ctx['tpk_bintang'] - float(_prev_r.get('tpk_bintang', _ctx['tpk_bintang'])), 1)
                    _ctx['usd_delta_pct']    = round((float(_prev_r.get('usd_idr_avg',0)) and
                                               (_ctx['usd_idr'] - float(_prev_r.get('usd_idr_avg',0))) /
                                               float(_prev_r.get('usd_idr_avg',1)) * 100) or 0, 1)
                    _ctx['prev_level']       = _prev_r.get('crisis_level', 'N/A')
                else:
                    _ctx['wisman_trend']     = 'tidak tersedia'
                    _ctx['avg_wisman_3m']    = 0
                    _ctx['prev_levels']      = []
                    _ctx['wisman_delta_pct'] = 0
                    _ctx['score_delta']      = 0
                    _ctx['sent_delta']       = 0
                    _ctx['tpk_delta']        = 0
                    _ctx['usd_delta_pct']    = 0
                    _ctx['prev_level']       = 'N/A'

                LEVEL_DESC = {
                    'AMAN':'kondisi pariwisata normal','WASPADA':'ada sinyal awal yang perlu dipantau',
                    'SIAGA':'tekanan signifikan pada sektor pariwisata',
                    'KRISIS':'krisis pariwisata yang membutuhkan respons segera'
                }
                _lv_text = LEVEL_DESC.get(_ctx['crisis_level'], _ctx['crisis_level'])
                _prev    = ' -> '.join(_ctx['prev_levels']) if _ctx['prev_levels'] else 'N/A'

                # Deteksi kontradiksi (sentimen vs wisman)
                _contradiction = ""
                if _ctx['wisman_delta_pct'] < -5 and _ctx['sent_delta'] > 0.05:
                    _contradiction = "KONTRADIKSI: Wisman turun tapi sentimen naik — kemungkinan tekanan dari faktor akses/ekonomi bukan kepuasan."
                elif _ctx['wisman_delta_pct'] > 5 and _ctx['sent_delta'] < -0.05:
                    _contradiction = "KONTRADIKSI: Wisman naik tapi sentimen turun — perlu investigasi kualitas layanan atau pengalaman wisata."
                elif _ctx['score_delta'] > 5 and _ctx['sent_delta'] > 0.1:
                    _contradiction = "KONTRADIKSI: Crisis score memburuk tapi sentimen publik positif — tekanan mungkin struktural, bukan persepsi."

                _data_block = (
                    f"DATA PARIWISATA BALI - {_ctx['month']}\n"
                    f"Crisis Score: {_ctx['crisis_score']}/100 -> Level {_ctx['crisis_level']} ({_lv_text})\n"
                    f"  Perubahan score vs bulan lalu: {_ctx['score_delta']:+.1f} poin | Level sebelumnya: {_ctx['prev_level']}\n"
                    f"Prediksi RF: {_ctx['rf_predicted']} (confidence: {_ctx['rf_confidence']}%) | "
                    f"Anomali IF: {'Ya' if _ctx['is_anomaly'] else 'Tidak'}\n"
                    f"P(Krisis): {_ctx['prob_krisis']}% | P(Siaga): {_ctx['prob_siaga']}%\n"
                    f"Wisman: {_ctx['wisman']:,.0f} ({_ctx['wisman_delta_pct']:+.1f}% MoM, trend: {_ctx['wisman_trend']}, avg 3bln: {int(_ctx['avg_wisman_3m']):,.0f})\n"
                    f"TPK Hotel: {_ctx['tpk_bintang']}% ({_ctx['tpk_delta']:+.1f}pp MoM)\n"
                    f"USD/IDR: Rp {int(_ctx['usd_idr']):,} ({_ctx['usd_delta_pct']:+.1f}% MoM)\n"
                    f"Inflasi: {_ctx['inflasi']}% | Sentimen: {_ctx['sentiment']} ({_ctx['sent_delta']:+.3f} MoM)\n"
                    f"Pangsa Bali: {_ctx['bali_share']}% | Z-score: {_ctx['wisman_zscore']}\n"
                    f"Histori level: {_prev}\n"
                    + (f"⚠️ {_contradiction}\n" if _contradiction else "")
                )

                if report_type == 'summary':
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard — sistem early warning pariwisata Bali.\n"
                        + _data_block +
                        f"\nTugas: Buat ringkasan analitis kondisi pariwisata Bali bulan {_ctx['month']} "
                        "dalam 2-3 kalimat Bahasa Indonesia yang TAJAM dan KAUSAL — bukan hanya deskriptif.\n"
                        "Panduan:\n"
                        "- Jelaskan MENGAPA kondisi ini terjadi, bukan hanya APA kondisinya\n"
                        "- Sebutkan perubahan MoM yang paling signifikan sebagai pemicu\n"
                        "- Jika ada kontradiksi antar indikator, soroti itu\n"
                        "- Hindari kalimat seperti 'data menunjukkan' — langsung ke analisis\n"
                        "Format: cocok untuk KPI card eksekutif, padat, berbasis data."
                    )
                elif report_type == 'alert':
                    _prompt = (
                        "Kamu adalah sistem BaliGuard. Kondisi kritis terdeteksi.\n"
                        + _data_block +
                        "\nBuat PERINGATAN DARURAT (max 130 kata) Bahasa Indonesia dengan struktur:\n"
                        "STATUS: [level + score + perubahan dari bulan lalu]\n"
                        "PEMICU UTAMA: [3 indikator kritis dengan perubahan MoM-nya]\n"
                        "KONTEKS: [apakah ini anomali? konsisten atau tiba-tiba?]\n"
                        "TINDAKAN: [1 rekomendasi segera yang spesifik dan actionable]\n"
                        "Gaya: tegas, langsung, tidak bertele-tele."
                    )
                elif report_type == 'predict':
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard — sistem early warning pariwisata Bali.\n"
                        + _data_block +
                        f"\nTugas: Buat laporan PREDIKSI & PROYEKSI untuk pariwisata Bali 3–6 bulan ke depan "
                        f"setelah bulan {_ctx['month']}, dalam Bahasa Indonesia yang tajam dan berbasis data.\n\n"
                        "Struktur laporan:\n\n"
                        "1. PROYEKSI KONDISI (2-3 kalimat)\n"
                        "   - Prediksi arah tren crisis score 3 bulan ke depan (naik/turun/stabil)\n"
                        "   - Apakah proyeksi menunjukkan pemulihan atau tekanan berlanjut?\n\n"
                        "2. FAKTOR RISIKO UTAMA (3 poin)\n"
                        "   - Sebutkan 3 indikator yang paling berpotensi mempengaruhi kondisi ke depan\n"
                        "   - Jelaskan arah tekanan (positif/negatif) masing-masing indikator\n\n"
                        "3. SKENARIO RISIKO\n"
                        "   - Skenario Optimis: kondisi terbaik yang mungkin terjadi\n"
                        "   - Skenario Pesimis: kondisi terburuk jika indikator memburuk\n\n"
                        "4. REKOMENDASI ANTISIPATIF (3 poin konkret)\n"
                        "   - Tindakan preventif yang perlu disiapkan SEKARANG sebelum risiko terjadi\n"
                        "   - Tiap poin: [Urgensi] Tindakan spesifik → dampak yang diantisipasi\n\n"
                        "Gaya: forward-looking, actionable, berbasis angka dan tren nyata."
                    )
                else:
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard.\n"
                        + _data_block +
                        "\nBuat laporan bulanan analitis Bahasa Indonesia dengan struktur:\n\n"
                        "1. RINGKASAN EKSEKUTIF (2-3 kalimat)\n"
                        "   - Status bulan ini vs bulan lalu (naik/turun berapa poin)\n"
                        "   - Apakah ini perubahan mendadak atau tren berkelanjutan?\n\n"
                        "2. ANALISIS INDIKATOR (3-4 kalimat)\n"
                        "   - Fokus pada indikator yang BERUBAH paling signifikan bulan ini\n"
                        "   - Jelaskan angka dengan konteks: '+8% wisman itu normal atau luar biasa?'\n"
                        "   - Soroti jika ada kontradiksi antar indikator\n\n"
                        "3. ANALISIS KAUSAL — MENGAPA INI TERJADI? (2-3 kalimat)\n"
                        "   - Identifikasi kemungkinan penyebab utama, bukan sekadar deskripsi\n"
                        "   - Jika ada anomali IF, analisis apa yang mungkin memicunya\n"
                        "   - Apakah tekanan berasal dari faktor internal (layanan) atau eksternal (ekonomi, akses)?\n\n"
                        "4. REKOMENDASI PRIORITAS (3 poin konkret dengan urgensi jelas)\n"
                        "   - Tiap poin: [Prioritas] Tindakan spesifik → target indikator yang diperbaiki"
                    )

                _client   = _Groq(api_key=groq_key)
                _response = _client.chat.completions.create(
                    model=selected_model,
                    messages=[{'role':'user','content':_prompt}],
                    temperature=0.7, max_tokens=1024
                )
                _narr_text = _response.choices[0].message.content
                _tokens    = _response.usage.prompt_tokens + _response.usage.completion_tokens

                result = {
                    'success': True,
                    'narrative': _narr_text,
                    'tokens': _tokens,
                    'month': narasi_target,
                    'crisis_level': _narasi_level,
                    'report_type': report_type,
                    'crisis_score': _narasi_score,
                }

                _rlv  = _narasi_level
                _rclr = COLOR_MAP.get(_rlv, '#94a3b8')
                _fc_tag = " · 🔮 Proyeksi" if _is_fc_month else ""
                _model_short = GROQ_MODELS.get(selected_model, {}).get('label', selected_model)
                st.markdown(
                    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap'>"
                    "<div style='font-size:10px;font-weight:700;color:#4ade80;text-transform:uppercase;"
                    "letter-spacing:.1em'>✅ NARASI BERHASIL DIBUAT</div>"
                    "<span style='background:" + _rclr + "22;color:" + _rclr + ";font-size:10px;font-weight:700;"
                    "padding:3px 10px;border-radius:20px;border:1px solid " + _rclr + "44'>"
                    + EMOJI_MAP.get(_rlv,'') + " " + _rlv + "</span>"
                    "<span style='font-family:monospace;font-size:10px;color:#475569'>"
                    + str(_tokens) + " tokens · " + _model_short + _fc_tag + "</span></div>"
                    "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);"
                    "border-radius:14px;padding:26px 30px;line-height:1.95;font-size:14px;"
                    "color:#cbd5e1;border-top:3px solid " + _rclr + "'>"
                    + _narr_text.replace('\n','<br>') + "</div>",
                    unsafe_allow_html=True
                )
                narratives_cache[narasi_target] = result
                os.makedirs('data/final', exist_ok=True)
                with open('data/final/narratives_cache.json', 'w', encoding='utf-8') as f:
                    json.dump(narratives_cache, f, ensure_ascii=False, indent=2)

            except Exception as e:
                st.error("❌ Error: " + str(e))

    elif not _has_cache and not gen_btn:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.1);
                    border-radius:14px;padding:48px;text-align:center'>
            <div style='font-size:36px;margin-bottom:12px'>🤖</div>
            <div style='font-size:14px;color:#475569;margin-bottom:6px'>Belum ada narasi untuk bulan ini</div>
            <div style='font-size:12px;color:#334155'>
                Pilih tipe laporan &amp; model AI di atas, lalu klik
                <b style='color:#4ade80'>Generate Narasi AI</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Data table ────────────────────────────────────────

# ══════════════════════════════════════════════════════
# DATA TABLE
# ══════════════════════════════════════════════════════
st.divider()
with st.expander("Tabel Data Prediksi Lengkap", expanded=False):
    disp = ['month','wisman','tpk_bintang','inflasi_processed','usd_idr_avg',
            'avg_sentiment_monthly','bali_share_pct','wisman_zscore',
            'crisis_score_100','crisis_level','rf_predicted_level','rf_confidence','iso_anomaly']
    disp = [c for c in disp if c in predictions.columns]
    df_show = predictions[disp].copy()

    # Format columns
    fmt = {
        'wisman':               '{:,.0f}',
        'tpk_bintang':          '{:.1f}%',
        'inflasi_processed':    '{:.2f}%',
        'usd_idr_avg':          'Rp {:,.0f}',
        'avg_sentiment_monthly':'{:+.3f}',
        'bali_share_pct':       '{:.1f}%',
        'wisman_zscore':        '{:.2f}',
        'crisis_score_100':     '{:.1f}',
        'rf_confidence':        '{:.0%}',
    }
    for col, fmt_str in fmt.items():
        if col in df_show.columns:
            try:
                df_show[col] = df_show[col].apply(
                    lambda x: fmt_str.format(x) if pd.notna(x) else '-')
            except Exception:
                pass

    st.dataframe(df_show, width="stretch", height=420,
                 hide_index=True,
                 column_config={
                     'month': st.column_config.TextColumn('Bulan', width='small'),
                     'crisis_level': st.column_config.TextColumn('Level', width='small'),
                     'rf_predicted_level': st.column_config.TextColumn('RF Pred.', width='small'),
                     'iso_anomaly': st.column_config.NumberColumn('Anomali', width='small'),
                 })

    dl_cols = [c for c in ['month','wisman','crisis_score_100','crisis_level',
                            'rf_predicted_level','rf_confidence','iso_anomaly'] if c in predictions.columns]
    st.download_button("⬇️ Download CSV",
        predictions[dl_cols].to_csv(index=False),
        file_name=f"baliguard_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv")

# ══════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════
st.markdown(f"""
<div style='text-align:center;padding:20px 0 8px;color:#334155;font-size:11px;
            line-height:2;border-top:1px solid rgba(255,255,255,0.05);margin-top:12px'>
    <b style='color:#475569'>BaliGuard</b> — Early Warning System Pariwisata Berbasis
    Multi-Sumber Data, Machine Learning &amp; Analisis Sentimen<br>
    <span style='font-size:10px;color:#1e293b'>
        Data: BPS Bali · Bank Indonesia · Google Hotels &nbsp;|&nbsp;
        Model: Isolation Forest + Random Forest + XLM-RoBERTa &nbsp;|&nbsp;
        Narasi: Groq LLM (llama-3.3-70b-versatile / llama-3.1-8b / mixtral / gemma2)
    </span>
</div>
""", unsafe_allow_html=True)
# ── PERFORMANCE REPORT — dicetak ke terminal setiap rerun ──
_tick("SELESAI")
_nav = st.session_state.get("selected_nav", "?")
print(f"\n[PERF] Navigasi: {_nav}")
print(f"  load_data_models : {_t.get('load_data_models',0)*1000:.1f} ms")
print(f"  sidebar_render   : {_t.get('sidebar_render',0)*1000:.1f} ms")
_nav_keys = ["nav_start_overview","nav_start_analisis","nav_start_sentimen",
             "nav_start_prediksi","nav_start_narasi"]
for k in _nav_keys:
    if k in _t:
        print(f"  {k:25s}: {_t[k]*1000:.1f} ms  ← halaman ini mulai render")
print(f"  TOTAL            : {_t['SELESAI']*1000:.1f} ms")
print("─" * 45)
