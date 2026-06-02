import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib, json, os, sys, urllib.request
from datetime import datetime

st.set_page_config(
    page_title="BaliGuard — Early Warning Pariwisata",
    page_icon="🛡️",
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
.alert-title   { font-family:'DM Sans'; font-size:14px; font-weight:700; color:#f1f5f9; margin-bottom:5px; }
.alert-body    { font-size:13px; color:#94a3b8; line-height:1.75; }

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
@st.cache_data
def load_data():
    master = pd.read_parquet('data/final/master_dataset_clean.parquet')
    pred   = pd.read_csv('data/final/predictions_final.csv')
    cache  = {}
    p = 'data/final/narratives_cache.json'
    if os.path.exists(p):
        with open(p,'r',encoding='utf-8') as f: cache = json.load(f)
    return master, pred, cache

@st.cache_resource
def load_models():
    rf     = joblib.load('data/models/model_random_forest.pkl')
    iso_f  = joblib.load('data/models/model_isolation_forest.pkl')
    scaler = joblib.load('data/models/scaler.pkl')
    le     = joblib.load('data/models/label_encoder.pkl')
    return rf, iso_f, scaler, le

try:
    master, predictions, narratives_cache = load_data()
    rf_model, iso_model, scaler, le = load_models()
    DATA_OK = True
except Exception as e:
    DATA_OK = False; DATA_ERR = str(e)

if not DATA_OK:
    st.error(f"❌ Gagal memuat data/model: {DATA_ERR}")
    st.info("Pastikan semua file ada di `data/final/` dan `data/models/`.")
    st.stop()

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════
def sf(val, d=0.0):
    try: return float(val)
    except: return d

_last_data_month = predictions['month'].iloc[-1]

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
            f'<div class="alert-title">{EMOJI_MAP.get(level,"")} {title}</div>'
            f'<div class="alert-body">{body}</div></div>')

def level_from_score(s):
    if s >= 70: return 'KRISIS'
    if s >= 50: return 'SIAGA'
    if s >= 30: return 'WASPADA'
    return 'AMAN'

# ── Live USD/IDR ──────────────────────────────────────────────
@st.cache_data(ttl=3600)
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

def compute_delta_context(row_data, pred_df, sel_month):
    """Hitung score_delta, dominant_factor, anomaly_explanation, recovery_pct."""
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

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 8px'>
        <div style='display:inline-flex;align-items:center;justify-content:center;
                    width:72px;height:72px;background:rgba(59,130,246,0.12);
                    border:1px solid rgba(59,130,246,0.25);border-radius:18px;margin-bottom:12px'>
            <svg width="38" height="42" viewBox="0 0 26 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 1L2 5.5V13.5C2 19.75 6.8 25.56 13 27C19.2 25.56 24 19.75 24 13.5V5.5L13 1Z"
                      fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="1.5" stroke-linejoin="round"/>
                <path d="M8 14l3.5 3.5L18 10" stroke="#93c5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <div style='font-family:"DM Serif Display";font-size:30px;color:#f1f5f9;letter-spacing:-.01em'>BaliGuard</div>
        <div style='font-size:11px;color:#64748b;margin-top:5px;letter-spacing:.1em;font-weight:700'>EARLY WARNING SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    avail_hist = sorted(predictions['month'].unique(), reverse=True)
    _last_data = predictions['month'].iloc[-1]
    _now_month = datetime.now().strftime('%Y-%m')
    # Tambahkan bulan masa depan sampai 2 tahun ke depan
    _future = []
    _p = pd.Period(_last_data, freq='M')
    for i in range(1, 25):
        _p2 = _p + i
        _future.append(str(_p2))
    # Future: urutan terbaru di atas (descending), lalu historical terbaru ke terlama
    _future_filtered = sorted([m for m in _future if m > _last_data], reverse=True)
    avail = _future_filtered + avail_hist
    # Format label: tambah tag [PROYEKSI] untuk masa depan
    def _month_label(m):
        if m > _last_data:
            return f"{m}  "
        return m
    sel = st.selectbox("📅 Periode Analisis", avail,
                       format_func=_month_label,
                       help="Bulan dengan = proyeksi (belum ada data BPS)")
    sel_dt = pd.to_datetime(sel)

    st.divider()
    # ── Navigasi Halaman ──────────────────────────────────
    NAV_OPTIONS = [
        ("📈", "Overview & Timeline"),
        ("🔬", "Analisis Detail"),
        ("💬", "Sentimen"),
        ("🔮", "Prediksi & Proyeksi"),
        ("✨", "Narasi AI"),
    ]
    if "selected_nav" not in st.session_state:
        st.session_state.selected_nav = "📈 Overview & Timeline"

    st.markdown("""
    <div style='font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;
                letter-spacing:.12em;margin-bottom:6px;font-family:"DM Sans"'>NAVIGASI</div>
    """, unsafe_allow_html=True)

    for _em, _lbl in NAV_OPTIONS:
        _full = f"{_em} {_lbl}"
        _active = st.session_state.selected_nav == _full
        # 🤖 renders narrower than other emoji — CSS handles alignment
        _display = f"{_em} {_lbl}"
        if st.button(
            _display,
            key=f"nav_{_lbl}",
            use_container_width=True,
            type="primary" if _active else "secondary",
        ):
            st.session_state.selected_nav = _full
            st.rerun()

    selected_nav = st.session_state.selected_nav

    st.divider()
    # ── Groq API Key (tersembunyi di expander) ────────────
    with st.expander("⚙️ Groq Narrative Engine", expanded=False):
        st.caption("Masukkan API key Groq Anda untuk mengaktifkan narasi AI.")
        groq_key = st.text_input("API Key", type="password", placeholder="gsk_...",
                                  label_visibility="collapsed",
                                  help="Dapatkan gratis di console.groq.com")
        if not groq_key:
            st.caption("↵ Tekan Enter untuk menerapkan")
            st.caption("💡 [Key gratis → console.groq.com](https://console.groq.com/keys)")
        else:
            st.caption("✅ API key aktif")

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
            <div style='flex-shrink:0;width:48px;height:48px;
                        background:rgba(59,130,246,0.15);border-radius:12px;
                        border:1px solid rgba(59,130,246,0.3);
                        display:flex;align-items:center;justify-content:center'>
                <svg width="26" height="28" viewBox="0 0 26 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M13 1L2 5.5V13.5C2 19.75 6.8 25.56 13 27C19.2 25.56 24 19.75 24 13.5V5.5L13 1Z"
                          fill="rgba(59,130,246,0.25)" stroke="#3b82f6" stroke-width="1.5" stroke-linejoin="round"/>
                    <path d="M8 14l3.5 3.5L18 10" stroke="#93c5fd" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div>
                <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.18em;
                            color:rgba(255,255,255,0.35);margin-bottom:5px;font-family:"DM Sans"'>
                    SISTEM DETEKSI DINI PARIWISATA
                </div>
                <div style='font-family:"DM Serif Display";font-size:30px;color:#f1f5f9;
                            letter-spacing:-.02em;line-height:1.1'>BaliGuard</div>
                <div style='font-size:12.5px;color:rgba(255,255,255,0.45);margin-top:6px;line-height:1.65;font-family:"DM Sans"'>
                    Dashboard Early Warning System &mdash; Multi-Sumber Data,
                    Machine Learning &amp; Analisis Sentimen Multibahasa
                </div>
            </div>
        </div>
        <!-- Right: last data chip -->
        <div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                    border-radius:12px;padding:14px 20px;text-align:center;flex-shrink:0'>
            <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;
                        color:rgba(255,255,255,0.35);margin-bottom:5px;font-family:"DM Sans";text-align:center'>DATA TERAKHIR</div>
            <div style='font-family:"JetBrains Mono";font-size:20px;color:#93c5fd;font-weight:700;letter-spacing:.02em;text-align:center'>
                {_last_month}
            </div>
            <div style='font-size:11px;color:rgba(255,255,255,0.3);margin-top:4px;font-family:"DM Sans";text-align:center'>
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
            <div style='font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;
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
                <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#475569;margin-bottom:4px;font-family:"DM Sans";text-align:center'>CONFIDENCE</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:700;line-height:1;text-align:center'>
                    {curr_conf:.0f}%
                </div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#475569;margin-bottom:4px;font-family:"DM Sans";text-align:center'>PROYEKSI DARI</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:600;line-height:1;text-align:center'>
                    {_last_month}
                </div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#475569;margin-bottom:4px;font-family:"DM Sans";text-align:center'>TREN/BULAN</div>
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

# ── MoM Delta ─────────────────────────────────────────
_sorted_months = sorted(predictions['month'].unique())
_sel_idx       = _sorted_months.index(sel) if sel in _sorted_months else -1
_prev_month    = _sorted_months[_sel_idx - 1] if _sel_idx > 0 else None
_prev_row      = get_row(_prev_month) if _prev_month else None

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
        return "<span style='color:#475569;font-size:10px'>— vs bln lalu</span>"
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
    return f"<span style='color:{col};font-size:10px;font-weight:700'>{txt}</span>"

_p_score  = sf(_prev_row.get('crisis_score_100',0))     if _prev_row is not None else None
_p_wisman = sf(_prev_row.get('wisman',0))               if _prev_row is not None else None
_p_tpk    = sf(_prev_row.get('tpk_bintang',0))          if _prev_row is not None else None
_p_sent   = sf(_prev_row.get('avg_sentiment_monthly',0))if _prev_row is not None else None
_p_usd    = sf(_prev_row.get('usd_idr_avg',0))          if _prev_row is not None else None

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
  padding: 6px 14px 8px 40px;
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
  font-size:10px !important;
  font-weight:700 !important;
  color:#64748b !important;
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
  font-size:11px !important;
  color:#475569 !important;
  margin-top:6px !important;
  font-family:'DM Sans', sans-serif !important;
  font-weight:400 !important;
  line-height:1.5 !important;
  text-align:center !important;
}
.kpi-c-delta { margin-top: 7px; font-size: 11px; font-weight: 600; font-family: sans-serif; line-height: 1.4; }

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
    var visible = Math.round((vw + 14) / step);
    return Math.max(0, N - visible);
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
    "📈 Overview & Timeline":  ("📈", "Overview & Timeline",  "#93c5fd"),
    "🔬 Analisis Detail":       ("🔬", "Analisis Detail",       "#c084fc"),
    "💬 Sentimen":              ("💬", "Sentimen",              "#4ade80"),
    "🔮 Prediksi & Proyeksi":  ("🔮", "Prediksi & Proyeksi",  "#fbbf24"),
    "✨ Narasi AI":            ("✨", "Narasi AI",            "#f87171"),
}
_icon, _title, _col = _NAV_ICONS.get(selected_nav, ("📈", selected_nav, "#93c5fd"))
st.markdown(f"""
<div style='margin-top:56px;margin-bottom:28px;text-align:center;
            padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.08)'>
    <div style='font-family:"DM Serif Display";font-size:26px;color:{_col};line-height:1.2'>
        {_icon} {_title}
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# MAIN CONTENT — navigasi dari sidebar
# ══════════════════════════════════════════════════════

# ─── TAB 1: OVERVIEW ─────────────────────────────────
if selected_nav == "📈 Overview & Timeline":
    months_dt = pd.to_datetime(predictions['month'].astype(str))

    fig = make_subplots(rows=3, cols=1,
        subplot_titles=(
            'Crisis Score & Level Krisis',
            'Kunjungan Wisatawan Mancanegara',
            'Kurs USD/IDR'
        ),
        vertical_spacing=0.18, row_heights=[0.44,0.30,0.26])

    # Row 1: Crisis Score
    fig.add_trace(go.Scatter(x=months_dt, y=predictions['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#cbd5e1', width=2),
        fill='tozeroy', fillcolor='rgba(148,163,184,0.06)'), row=1, col=1)
    for lv, col in COLOR_MAP.items():
        mask = predictions['crisis_level']==lv
        if mask.sum()>0:
            fig.add_trace(go.Scatter(
                x=months_dt[mask], y=predictions.loc[mask,'crisis_score_100'],
                mode='markers', name=lv,
                marker=dict(color=col,size=7,line=dict(width=1.2,color='#050d1a')),
                hovertemplate=f'<b>{lv}</b><br>%{{x|%b %Y}}<br>Score: %{{y:.1f}}<extra></extra>'
            ), row=1, col=1)
    for thr,lbl,col in [(70,'KRISIS','#ef4444'),(50,'SIAGA','#f97316'),(30,'WASPADA','#f59e0b')]:
        fig.add_hline(y=thr, line_dash='dot', line_color=col, line_width=1, opacity=0.7,
                      annotation_text=lbl, annotation_position='right',
                      annotation_font_size=9, annotation_font_color=col,
                      annotation_xanchor='left', annotation_xshift=-52,
                      row=1, col=1)

    # Row 2: Wisman
    fig.add_trace(go.Scatter(x=months_dt, y=predictions['wisman'],
        mode='lines', name='Wisman', showlegend=False,
        line=dict(color='#7dd3fc', width=2),
        fill='tozeroy', fillcolor='rgba(96,165,250,0.09)'), row=2, col=1)

    # Row 3: USD/IDR
    if 'usd_idr_avg' in predictions.columns:
        fig.add_trace(go.Scatter(x=months_dt, y=predictions['usd_idr_avg'],
            mode='lines', name='USD/IDR', showlegend=False,
            line=dict(color='#fbbf24', width=2)), row=3, col=1)

    for r in [1,2,3]:
        fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
            fillcolor='rgba(239,68,68,0.06)', line_width=0,
            annotation_text='COVID-19' if r==1 else '',
            annotation_font_color='#ef4444',
            annotation_font_size=10, row=r, col=1)
        fig.add_vline(x=sel_dt, line_dash='dot', line_color='#60a5fa',
                      line_width=1.2, row=r, col=1)

    # ── Event annotations (real-world context) ───────────
    EVENTS = [
        # (date_str, label, color, symbol)
        ('2002-10-12', 'Bom Bali I',       '#ef4444', 'circle'),
        ('2005-10-01', 'Bom Bali II',      '#f97316', 'circle'),
        ('2017-11-01', 'Erupsi Agung',     '#fb923c', 'diamond'),
        ('2018-08-05', 'Gempa Lombok',     '#f59e0b', 'diamond'),
        ('2020-03-19', 'Lockdown COVID',   '#ef4444', 'x'),
        ('2021-10-14', 'Bali Dibuka PPLN', '#22c55e', 'triangle-up'),
        ('2022-11-15', 'KTT G20 Bali',    '#a78bfa', 'star'),
        ('2023-02-01', 'Bebas Visa 20 N.', '#60a5fa', 'triangle-up'),
    ]
    for ev_date, ev_label, ev_col, ev_sym in EVENTS:
        try:
            _ev_dt = pd.to_datetime(ev_date)
            if _ev_dt < months_dt.min() or _ev_dt > months_dt.max() + pd.DateOffset(months=3):
                continue
            fig.add_vline(x=_ev_dt, line_dash='dot', line_color=ev_col,
                          line_width=0.8, opacity=0.55, row=1, col=1)
            fig.add_annotation(
                x=_ev_dt, y=97, text=ev_label,
                showarrow=False, font=dict(size=8, color=ev_col),
                textangle=-55, xanchor='left',
                bgcolor='rgba(5,13,26,0.7)', borderpad=2,
                row=1, col=1
            )
        except Exception:
            pass

    fig.update_layout(height=820, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(5,13,26,0.85)', bordercolor='rgba(255,255,255,0.12)',
                    borderwidth=1, font=dict(size=11,color='#e2e8f0')),
        plot_bgcolor='rgba(5,13,26,0.7)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0,r=55,t=50,b=10),
        font=dict(family='DM Sans',size=11,color='#94a3b8'))

    # Warnai judul subplot (3 pertama di layout.annotations adalah subplot_titles)
    _title_colors = ['#93c5fd', '#7dd3fc', '#fbbf24']
    for i, ann in enumerate(fig.layout.annotations[:3]):
        ann.update(
            font=dict(size=17, color=_title_colors[i], family='DM Sans'),
            x=0.5, xanchor='center', yshift=18
        )
    for r in [1,2,3]:
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                         linecolor='rgba(255,255,255,0.1)', row=r, col=1)
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                         linecolor='rgba(255,255,255,0.1)', row=r, col=1)
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
if selected_nav == "🔬 Analisis Detail":

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
            st.markdown('<div class="box-heading sec-blue">📊 Komponen Crisis Score</div>', unsafe_allow_html=True)

            mr_rows = master[master['month']==sel]
            if len(mr_rows)>0:
                mr = mr_rows.iloc[0]
                comp_vals = {
                    'Kunjungan Wisatawan': sf(mr.get('crisis_component_tourism',0)),
                    'Kondisi Ekonomi':     sf(mr.get('crisis_component_economy',0)),
                    'Sentimen Ulasan':     sf(mr.get('crisis_component_sentiment',0)),
                }
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
            else:
                st.info("Data bulan ini tidak ada di master dataset.")

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
                '<div class="box-heading sec-purple">📋 Indikator Detail</div>'
                + rows_html,
                unsafe_allow_html=True
            )

    with cr:
        # ── Box 3: Probabilitas RF ────────────────────────
        with st.container(border=True):
            st.markdown('<div class="accent-orange"></div>', unsafe_allow_html=True)
            st.markdown('<div class="box-heading sec-orange">🎯 Probabilitas Prediksi Random Forest</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="box-heading sec-green">🌲 Feature Importance — Random Forest</div>', unsafe_allow_html=True)

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
if selected_nav == "💬 Sentimen":

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
    pct_neg = sf(mr_pct_rows['pct_negative_monthly'].iloc[0] if len(mr_pct_rows) > 0
                 and 'pct_negative_monthly' in master.columns
                 else row_data.get('pct_negative_monthly', 0))
    pct_pos = sf(mr_pct_rows['pct_positive_monthly'].iloc[0] if len(mr_pct_rows) > 0
                 and 'pct_positive_monthly' in master.columns
                 else (100 - pct_neg))
    pct_netral = sf(mr_pct_rows['pct_neutral_monthly'].iloc[0] if len(mr_pct_rows) > 0
                 and 'pct_neutral_monthly' in master.columns
                 else max(0.0, 100.0 - pct_pos - pct_neg))

    # ── Hero: pakai kolom native Streamlit, bukan HTML kompleks ──
    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1], gap="medium")
    with h1:
        st.markdown(
            f"<div style='padding:16px 0'>"
            f"<div style='font-size:11px;font-weight:700;letter-spacing:.12em;color:#475569;text-transform:uppercase;margin-bottom:6px'>Sentimen Bulan Ini · {sel}</div>"
            f"<div style='font-family:DM Serif Display,serif;font-size:36px;color:{sent_color};line-height:1'>{sent_label}</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:20px;color:{sent_color};margin-top:4px'>{sent:+.3f}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
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
            f"<div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#475569;margin-bottom:8px'>Review Netral</div>"
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
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 10px;"
                "border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:4px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#4ade80;"
                "border-left:3px solid #22c55e;padding-left:10px'>📈 Tren Sentimen Historis</span></div>",
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
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 10px;"
                "border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:4px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#4ade80;"
                "border-left:3px solid #22c55e;padding-left:10px'>📊 6 Bulan Terakhir</span></div>",
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
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 12px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#2dd4bf;"
                "border-left:3px solid #14b8a6;padding-left:10px'>🎯 Gauge Sentimen</span></div>",
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
if selected_nav == "🔮 Prediksi & Proyeksi":

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
    .pred-section-hdr-line { flex:1; height:1px; background:rgba(255,255,255,0.06); }
    .pred-section-hdr-text {
      font-size:10px; font-weight:800; letter-spacing:.14em;
      text-transform:uppercase; color:#334155; white-space:nowrap;
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
      border-radius:14px; padding:14px 16px 13px; position:relative;
      overflow:hidden; transition:transform .2s, box-shadow .2s;
    }
    .fc-grid-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.35); }

    /* ── Confidence-tier card backgrounds ── */
    /* HIGH  76–100 */
    .fc-conf-high {
      background:rgba(16,185,129,0.07); border:1px solid rgba(16,185,129,0.18);
    }
    /* MID   51–75 */
    .fc-conf-mid {
      background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.18);
    }
    /* LOW   26–50 */
    .fc-conf-low {
      background:rgba(249,115,22,0.05); border:1px solid rgba(249,115,22,0.15);
    }
    /* VLOW  0–25 */
    .fc-conf-vlow {
      background:rgba(100,116,139,0.04); border:1px solid rgba(100,116,139,0.1);
    }

    .fc-card-month {
      font-family:'JetBrains Mono',monospace; font-size:10px;
      color:#334155; letter-spacing:.06em; margin-bottom:8px;
    }
    .fc-card-level { font-size:13px; font-weight:800; margin-bottom:2px; letter-spacing:.03em; }
    .fc-card-score {
      font-family:'JetBrains Mono',monospace; font-size:11px; color:#475569; margin-bottom:9px;
    }
    .fc-conf-bar-wrap {
      height:4px; background:rgba(255,255,255,0.06); border-radius:3px; overflow:hidden; margin-bottom:6px;
    }
    .fc-conf-bar-fill { height:100%; border-radius:3px; }
    .fc-conf-label { display:flex; justify-content:space-between; align-items:center; }
    .fc-conf-pct {
      font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700;
    }
    .fc-conf-txt { font-size:9px; color:#1e3a5f; text-transform:uppercase; letter-spacing:.06em; }

    /* ── Warning note ── */
    .fc-note {
      display:flex; align-items:center; gap:8px; background:rgba(245,158,11,0.05);
      border:1px solid rgba(245,158,11,0.12); border-left:3px solid rgba(245,158,11,0.4);
      border-radius:8px; padding:9px 14px; font-size:11px; color:#92400e; margin-bottom:20px;
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
      background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.12);
      border-radius:8px; padding:7px 12px; font-size:11px; color:#3b82f6; margin-bottom:10px;
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
      font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.12em;
      color:#334155; margin-bottom:12px; display:flex; align-items:center; gap:6px;
    }
    .bd-row {
      display:flex; justify-content:space-between; align-items:center;
      padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04);
    }
    .bd-row:last-child { border-bottom:none; }
    .bd-name { font-size:12px; color:#94a3b8; }
    .bd-badge {
      font-size:10px; font-weight:700; padding:3px 10px;
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
      font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.12em;
      color:#334155; margin-bottom:12px; display:flex; align-items:center; gap:6px;
    }
    .reko-item {
      display:flex; align-items:flex-start; gap:10px; padding:8px 0;
      border-bottom:1px solid rgba(255,255,255,0.04); font-size:12px;
      color:#94a3b8; line-height:1.6;
    }
    .reko-item:last-child { border-bottom:none; }
    .reko-num {
      flex-shrink:0; width:20px; height:20px; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      font-size:10px; font-weight:800; margin-top:1px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── PAGE HEADER ──────────────────────────────────────
    st.markdown("""
    <div class='pred-page-header'>
        <div class='pred-page-title'>Prediksi &amp; Proyeksi</div>
        <div class='pred-page-sub'>Sistem prediksi berbasis ML &nbsp;·&nbsp; pola historis 2009–2024</div>
    </div>
    <div style='text-align:center;margin-bottom:24px'>
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
            st.markdown("<div class='ctrl-label'>📅 Tahun Mulai</div>", unsafe_allow_html=True)
            _year_opts      = list(range(int(predictions['month'].iloc[-1][:4]), _now.year + 3))
            _default_yr_idx = _year_opts.index(_now.year) if _now.year in _year_opts else 0
            _proj_year      = st.selectbox("Tahun", _year_opts, index=_default_yr_idx,
                                            key="proj_year", label_visibility="collapsed")
        with _sel_c2:
            st.markdown("<div class='ctrl-label'>🗓️ Bulan Mulai</div>", unsafe_allow_html=True)
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
            "<div class='pred-section-hdr-text'>🔮 Proyeksi " + str(_proj_n) + " Bulan — " + _proj_month_name + " " + str(_proj_year) + "</div>"
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
            "<div class='pred-section-hdr-text'>🎮 Simulator Skenario Risiko</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>",
            unsafe_allow_html=True)

        st.markdown(
            "<div class='sim-hint'>💡 Geser slider untuk simulasi dampak perubahan indikator secara real-time.</div>",
            unsafe_allow_html=True)

        # ── Sliders with value pills rendered via HTML label ──
        w_d = st.slider("📉 Wisman (%)", -80, 50, 0, 5, key="sim_w")
        st.markdown("<div class='slider-range-row'><span>-80%</span><span>+50%</span></div>", unsafe_allow_html=True)
        u_d = st.slider("💱 USD/IDR (%)", -10, 30, 0, 1, key="sim_u")
        st.markdown("<div class='slider-range-row'><span>-10%</span><span>+30%</span></div>", unsafe_allow_html=True)
        s_d = st.slider("💬 Sentimen", -1.0, 1.0, 0.0, 0.1, key="sim_s")
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
        "⚠️&nbsp; Breakdown Risiko"
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
        "✅&nbsp; Rekomendasi — Level {lv}"
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
        if st.button("↗ Tren + Proyeksi", key="pct_trend",
                     type="primary" if st.session_state['pred_chart_tab']=='trend' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'trend'
            st.rerun()
    with _chart_c2:
        if st.button("📉 Recovery Rate vs Baseline", key="pct_rec",
                     type="primary" if st.session_state['pred_chart_tab']=='recovery' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'recovery'
            st.rerun()
    with _chart_c3:
        if st.button("🗺️ Peta Risiko Historis", key="pct_scatter",
                     type="primary" if st.session_state['pred_chart_tab']=='scatter' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'scatter'
            st.rerun()

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
        for thr,lbl,col in [(70,'KRISIS','#ef4444'),(50,'SIAGA','#f97316'),(30,'WASPADA','#f59e0b')]:
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
if selected_nav == "✨ Narasi AI":

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
                <div style='font-size:10px;color:rgba(74,222,128,0.5);text-transform:uppercase;
                            letter-spacing:.08em;margin-bottom:4px'>PROVIDER</div>
                <div style='font-family:monospace;font-size:12px;color:#4ade80;font-weight:600'>
                    Groq Cloud API
                </div>
                <div style='font-size:10px;color:#059669;margin-top:6px'>⚡ Latensi &lt; 1 detik · Gratis</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Kegunaan cards ────────────────────────────────────
    st.markdown("""
    <div style='font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;
                letter-spacing:.1em;margin-bottom:12px'>💡 APA GUNANYA NARASI AI?</div>
    <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:24px'>
        <div style='background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);
                    border-radius:12px;padding:16px'>
            <div style='font-size:18px;margin-bottom:8px'>📋</div>
            <div style='font-size:12px;font-weight:700;color:#93c5fd;margin-bottom:6px'>Laporan Dinas / Rapat</div>
            <div style='font-size:11px;color:#64748b;line-height:1.7'>
                Draft laporan bulanan siap presentasi ke kepala dinas atau DPRD tanpa tulis manual.
            </div>
        </div>
        <div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px;padding:16px'>
            <div style='font-size:18px;margin-bottom:8px'>🚨</div>
            <div style='font-size:12px;font-weight:700;color:#fca5a5;margin-bottom:6px'>Peringatan Dini Krisis</div>
            <div style='font-size:11px;color:#64748b;line-height:1.7'>
                Saat SIAGA/KRISIS terdeteksi, sistem menyusun teks peringatan + rekomendasi untuk stakeholder.
            </div>
        </div>
        <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                    border-radius:12px;padding:16px'>
            <div style='font-size:18px;margin-bottom:8px'>📰</div>
            <div style='font-size:12px;font-weight:700;color:#fcd34d;margin-bottom:6px'>Press Release / Media</div>
            <div style='font-size:11px;color:#64748b;line-height:1.7'>
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
    st.markdown("""<div style='font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                letter-spacing:.1em;margin-bottom:14px'>📝 PILIH TIPE LAPORAN</div>""",
                unsafe_allow_html=True)

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
                "border-radius:12px;padding:16px 14px 14px;min-height:140px;"
                "opacity:" + _opac + ";" + _shad + ";transition:opacity .2s'>"
                "<div style='font-size:24px;margin-bottom:8px'>" + _card['icon'] + "</div>"
                "<div style='font-size:12px;font-weight:700;color:" + _card['color'] + ";margin-bottom:4px'>"
                + _card['title'] + "</div>"
                "<div style='font-size:10px;color:#94a3b8;font-weight:600;margin-bottom:6px'>"
                + _card['desc'] + "</div>"
                "<div style='font-size:10px;color:#64748b;line-height:1.65'>" + _card['detail'] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
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
        "<div style='margin-top:12px;margin-bottom:20px;background:" + _sel_card['bg'] + ";border-radius:8px;"
        "padding:10px 14px;border-left:3px solid " + _sel_card['color'] + "'>"
        "<span style='font-size:11px;color:#94a3b8'>Tipe dipilih: "
        "<b style='color:" + _sel_card['color'] + "'>" + _sel_card['icon'] + " " + _sel_card['title'] + "</b>"
        " &nbsp;·&nbsp; " + _sel_card['desc'] + "</span></div>",
        unsafe_allow_html=True
    )

    # ─ MODEL + API STATUS (2 kolom di bawah cards) ────────
    na_l, na_r = st.columns([3, 2])

    with na_l:
        # ─ 2. PILIH MODEL AI ──────────────────────────────
        st.markdown("""<div style='font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:12px'>🧠 PILIH MODEL AI</div>""",
                    unsafe_allow_html=True)

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

        _mc1, _mc2 = st.columns(2)
        _model_items = list(GROQ_MODELS.items())
        for _mi, (_mkey, _mcard) in enumerate(_model_items):
            _col = _mc1 if _mi % 2 == 0 else _mc2
            with _col:
                _is_msel  = st.session_state['selected_model_key'] == _mkey
                _m_bdr    = ("2px solid " + _mcard['color']) if _is_msel else ("1px solid " + _mcard['border'])
                _m_shad   = ("box-shadow:0 0 10px " + _mcard['color'] + "30;") if _is_msel else ""
                _m_opac   = "1" if _is_msel else "0.6"
                st.markdown(
                    "<div style='background:" + _mcard['bg'] + ";border:" + _m_bdr + ";"
                    "border-radius:10px;padding:10px 12px;opacity:" + _m_opac + ";" + _m_shad + ";margin-bottom:6px'>"
                    "<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
                    "<span style='font-size:16px'>" + _mcard['icon'] + "</span>"
                    "<span style='font-size:9px;font-weight:700;background:" + _mcard['color'] + "22;"
                    "color:" + _mcard['color'] + ";padding:2px 7px;border-radius:10px'>"
                    + _mcard['tag'] + "</span></div>"
                    "<div style='font-size:11px;font-weight:700;color:" + _mcard['color'] + ";margin:5px 0 2px'>"
                    + _mcard['label'] + "</div>"
                    "<div style='font-size:10px;color:#64748b;line-height:1.5'>" + _mcard['desc'] + "</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
                if st.button(_mcard['label'], key="model_" + _mkey, width="stretch"):
                    st.session_state['selected_model_key'] = _mkey
                    st.rerun()

        selected_model = st.session_state['selected_model_key']
        _sel_mcard     = GROQ_MODELS[selected_model]
        st.markdown(
            "<div style='margin-top:6px;background:" + _sel_mcard['bg'] + ";border-radius:8px;"
            "padding:8px 12px;border-left:3px solid " + _sel_mcard['color'] + "'>"
            "<span style='font-size:11px;color:#94a3b8'>Model: "
            "<b style='color:" + _sel_mcard['color'] + "'>" + _sel_mcard['icon'] + " " + _sel_mcard['label'] + "</b>"
            " &nbsp;·&nbsp; <span style='color:#64748b'>" + _sel_mcard['tag'] + "</span></span></div>",
            unsafe_allow_html=True
        )

    with na_r:
        st.markdown("""<div style='font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:14px'>🔑 API & STATUS</div>""",
                    unsafe_allow_html=True)

        # ─ 3. PILIH BULAN & TAHUN ─────────────────────────
        # Gabungkan bulan historis + proyeksi hingga 18 bulan ke depan
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

        st.markdown("""<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                    border-radius:12px;padding:14px 16px;margin-bottom:10px'>
            <div style='font-size:10px;color:#475569;margin-bottom:10px;text-transform:uppercase;
                        letter-spacing:.07em;font-weight:700'>📅 BULAN YANG DIANALISIS</div>""",
                    unsafe_allow_html=True)

        _ny_col, _nm_col = st.columns(2)
        with _ny_col:
            _ny_idx  = _avail_years.index(st.session_state['narasi_year_sel']) \
                       if st.session_state['narasi_year_sel'] in _avail_years else 0
            _sel_year = st.selectbox("Tahun", _avail_years, index=_ny_idx, key="narasi_year_box")
            st.session_state['narasi_year_sel'] = _sel_year

        _months_for_year = [m for m in _all_months if m.startswith(_sel_year)]
        _MONTH_ID = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
        def _month_label_fn(m):
            base = _MONTH_ID[int(m[5:7])-1]
            return (base + " 🔮") if m not in _avail_months_hist else base

        with _nm_col:
            _prev_nm = st.session_state.get('narasi_month_sel', sel)
            _nm_default = _prev_nm if _prev_nm in _months_for_year else _months_for_year[-1]
            _nm_idx  = _months_for_year.index(_nm_default)
            _sel_month = st.selectbox("Bulan", _months_for_year,
                                      format_func=_month_label_fn,
                                      index=_nm_idx, key="narasi_month_box")
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
            "color:#a78bfa;padding:2px 8px;border-radius:10px;margin-left:6px'>🔮 Proyeksi</span>"
        ) if _is_fc_month else ""
        st.markdown(
            "<div style='display:flex;gap:8px;margin-top:8px;align-items:center;flex-wrap:wrap'>"
            "<span style='font-size:13px;font-weight:700;color:" + COLOR_MAP.get(_narasi_level,'#fff') + "'>"
            + EMOJI_MAP.get(_narasi_level,'') + " " + _narasi_level + "</span>"
            "<span style='font-size:10px;color:#475569'>·</span>"
            "<span style='font-family:monospace;font-size:11px;color:#64748b'>Score "
            + str(round(_narasi_score, 1)) + "/100</span>"
            + _fc_badge +
            "</div></div>",
            unsafe_allow_html=True
        )

        # Cache status for narasi_target
        _has_cache    = narasi_target in narratives_cache
        _cache_level  = narratives_cache[narasi_target].get('crisis_level','') if _has_cache else ''
        _cache_tokens = narratives_cache[narasi_target].get('tokens', 0)        if _has_cache else 0

        _cache_bg  = "rgba(34,197,94,0.07)"  if _has_cache else "rgba(255,255,255,0.03)"
        _cache_bdr = "rgba(34,197,94,0.2)"   if _has_cache else "rgba(255,255,255,0.06)"
        _cache_inner = (
            "<div style='font-size:12px;color:#4ade80;font-weight:600'>✅ Tersedia</div>"
            "<div style='font-size:10px;color:#475569;margin-top:2px'>Level: " + _cache_level +
            " · " + str(_cache_tokens) + " tokens</div>"
        ) if _has_cache else "<div style='font-size:12px;color:#475569'>Belum ada cache untuk bulan ini</div>"

        st.markdown(
            "<div style='background:" + _cache_bg + ";border:1px solid " + _cache_bdr + ";"
            "border-radius:12px;padding:12px 16px;margin-bottom:10px'>"
            "<div style='font-size:10px;color:#475569;margin-bottom:4px;text-transform:uppercase;"
            "letter-spacing:.07em'>💾 CACHE NARASI</div>" + _cache_inner + "</div>",
            unsafe_allow_html=True
        )

        if not groq_key:
            st.markdown("""
            <div style='background:rgba(245,158,11,0.09);border:1px solid rgba(245,158,11,0.2);
                        border-radius:12px;padding:14px 16px;'>
                <div style='font-size:12px;font-weight:700;color:#fbbf24;margin-bottom:6px'>
                    🔑 Groq API Key Diperlukan
                </div>
                <div style='font-size:11px;color:#92400e;line-height:1.7;margin-bottom:10px'>
                    Masukkan API Key di sidebar (kiri) untuk mengaktifkan Narasi AI.
                    Key gratis dan bisa didapat dalam 30 detik.
                </div>
                <a href='https://console.groq.com/keys' target='_blank'
                   style='display:inline-block;background:rgba(245,158,11,0.2);
                          color:#fbbf24;font-size:11px;font-weight:700;
                          padding:6px 14px;border-radius:6px;text-decoration:none'>
                    → Dapatkan Key Gratis
                </a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
                        border-radius:12px;padding:12px 16px;margin-bottom:10px'>
                <div style='font-size:12px;color:#4ade80;font-weight:700'>✅ API Key Terhubung</div>
                <div style='font-size:10px;color:#475569;margin-top:3px'>Siap generate narasi</div>
            </div>
            """, unsafe_allow_html=True)

        gen_btn = st.button("🚀 Generate Narasi AI", type="primary",
                            width="stretch", disabled=not bool(groq_key))

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
with st.expander("📋 Tabel Data Prediksi Lengkap", expanded=False):
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