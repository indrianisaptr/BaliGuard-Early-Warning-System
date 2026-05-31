import streamlit as st
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
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: #050d1a;
  color: #e2e8f0;
}
.main { background: #050d1a; }
.block-container { padding: 1rem 2rem 2rem; }
[data-testid="stSidebar"] { background: #0a1628 !important; border-right: 1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label { font-size: 12.5px !important; line-height: 1.75 !important; }
[data-testid="stSidebar"] b { color: #e2e8f0 !important; }

/* ── KPI Cards ── */
.kpi-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 18px 20px;
  border-top: 3px solid #3b82f6;
  position: relative; overflow: hidden;
}
.kpi-card::before {
  content:''; position:absolute; inset:0;
  background: radial-gradient(circle at top right, rgba(255,255,255,0.03), transparent 70%);
}
.kpi-label { font-size:10px; font-weight:700; color:#64748b;
             text-transform:uppercase; letter-spacing:.1em; margin-bottom:8px; font-family:'DM Sans'; }
.kpi-value { font-size:26px; font-weight:700; color:#f1f5f9; line-height:1.1; font-family:'DM Serif Display'; }
.kpi-sub   { font-size:11px; color:#475569; margin-top:6px; }
.kpi-AMAN    { border-top-color: #22c55e; }
.kpi-WASPADA { border-top-color: #f59e0b; }
.kpi-SIAGA   { border-top-color: #f97316; }
.kpi-KRISIS  { border-top-color: #ef4444; }

/* ── Alert Boxes ── */
.alert-aman    { background:rgba(34,197,94,0.08);  border-left:4px solid #22c55e; padding:16px 20px; border-radius:10px; }
.alert-waspada { background:rgba(245,158,11,0.08); border-left:4px solid #f59e0b; padding:16px 20px; border-radius:10px; }
.alert-siaga   { background:rgba(249,115,22,0.08); border-left:4px solid #f97316; padding:16px 20px; border-radius:10px; }
.alert-krisis  { background:rgba(239,68,68,0.10);  border-left:4px solid #ef4444; padding:16px 20px; border-radius:10px; }
.alert-title   { font-family:'DM Serif Display'; font-size:16px; color:#f1f5f9; margin-bottom:6px; }
.alert-body    { font-size:13px; color:#94a3b8; line-height:1.7; }

/* ── Section Title ── */
.section-title {
  font-family: 'DM Serif Display'; font-size:16px; font-weight:700;
  padding:4px 0 12px; font-style:normal; letter-spacing:-.01em;
  display:block; margin-top:0;
}
/* ── Section title color variants with left-border accent ── */
.sec-blue   { color:#60a5fa !important; border-left:3px solid #3b82f6; padding-left:10px !important; margin-top:4px; }
.sec-orange { color:#fb923c !important; border-left:3px solid #f97316; padding-left:10px !important; margin-top:4px; }
.sec-green  { color:#4ade80 !important; border-left:3px solid #22c55e; padding-left:10px !important; margin-top:4px; }
.sec-purple { color:#c084fc !important; border-left:3px solid #a855f7; padding-left:10px !important; margin-top:4px; }
.sec-amber  { color:#fcd34d !important; border-left:3px solid #f59e0b; padding-left:10px !important; margin-top:4px; }
.sec-red    { color:#f87171 !important; border-left:3px solid #ef4444; padding-left:10px !important; margin-top:4px; }
.sec-teal   { color:#2dd4bf !important; border-left:3px solid #14b8a6; padding-left:10px !important; margin-top:4px; }
.sec-sky    { color:#38bdf8 !important; border-left:3px solid #0ea5e9; padding-left:10px !important; margin-top:4px; }
/* ── Section spacing wrapper ── */
.sec-gap-sm  { margin-top:16px; }
.sec-gap-md  { margin-top:24px; }
.sec-gap-lg  { margin-top:32px; }

/* ── Narrative Box ── */
.narrative-box {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px; padding: 24px 28px;
  line-height: 1.9; font-size: 14px; color: #cbd5e1;
  white-space: pre-wrap; font-family: 'DM Sans';
}

/* ── Prediction Forecast Card ── */
.fc-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px; padding: 18px 20px;
  margin-bottom: 10px;
  transition: border-color .2s;
}
.fc-card:hover { border-color: rgba(255,255,255,0.15); }

/* ── Projection selector styling ── */
.proj-selector {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 18px;
}

/* ── Risk Row ── */
.risk-row {
  display:flex; justify-content:space-between; align-items:center;
  padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 13px;
}
.risk-name { color: #94a3b8; }
.risk-val  { color: #e2e8f0; font-weight: 700; font-family: 'JetBrains Mono'; font-size: 12px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; border-bottom: 1px solid rgba(255,255,255,0.08); }
.stTabs [data-baseweb="tab"] {
  border-radius: 8px 8px 0 0; padding: 8px 18px;
  font-weight: 600; font-size: 13px; color: #64748b !important;
  background: transparent !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: #f1f5f9 !important;
  background: rgba(255,255,255,0.06) !important;
  border-bottom: 2px solid #3b82f6 !important;
}

/* ── Badge ── */
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-green  { background:rgba(34,197,94,0.15);  color:#4ade80; }
.badge-yellow { background:rgba(245,158,11,0.15); color:#fbbf24; }
.badge-orange { background:rgba(249,115,22,0.15); color:#fb923c; }
.badge-red    { background:rgba(239,68,68,0.15);  color:#f87171; }

/* ── Metric override ── */
[data-testid="stMetricValue"] { color: #f1f5f9 !important; font-family: 'DM Serif Display' !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 10px !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { background: transparent !important; }
.dvn-scroller { background: rgba(255,255,255,0.02) !important; }

/* ── Selectbox / slider ── */
[data-baseweb="select"] { background: rgba(255,255,255,0.05) !important; }
.stSlider [data-baseweb="slider"] { background: rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════
COLOR_MAP  = {'AMAN':'#22c55e','WASPADA':'#f59e0b','SIAGA':'#f97316','KRISIS':'#ef4444'}
EMOJI_MAP  = {'AMAN':'🟢','WASPADA':'🟡','SIAGA':'🟠','KRISIS':'🔴'}
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
    <div style='text-align:center;padding:16px 0 4px'>
        <div style='font-size:38px'>🛡️</div>
        <div style='font-family:"DM Serif Display";font-size:22px;color:#f1f5f9;margin-top:4px'>BaliGuard</div>
        <div style='font-size:11px;color:#475569;margin-top:3px;letter-spacing:.05em'>EARLY WARNING SYSTEM</div>
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
    avail = avail_hist + list(reversed([m for m in _future if m > _last_data]))
    # Format label: tambah tag [PROYEKSI] untuk masa depan
    def _month_label(m):
        if m > _last_data:
            return f"{m}  🔮"
        return m
    sel = st.selectbox("📅 Periode Analisis", avail,
                       format_func=_month_label,
                       help="Bulan dengan 🔮 = proyeksi (belum ada data BPS)")
    sel_dt = pd.to_datetime(sel)

    st.divider()
    st.markdown("**🤖 Groq Narrative Engine**")
    groq_key = st.text_input("API Key", type="password", placeholder="gsk_...",
                              help="Dapatkan gratis di console.groq.com")
    if not groq_key:
        st.caption("💡 [Key gratis → console.groq.com](https://console.groq.com/keys)")

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
        <div style='font-family:"DM Serif Display";font-size:24px;color:{COLOR_MAP.get(lv_s,"#fff")}'>
            {EMOJI_MAP.get(lv_s,"")} {lv_s}
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
<div style='background:linear-gradient(135deg,#0c1a3a 0%,#1a3166 50%,#0e2151 100%);
            border-radius:18px;padding:28px 36px;margin-bottom:24px;
            border:1px solid rgba(255,255,255,0.08);
            box-shadow:0 8px 32px rgba(0,0,0,0.4)'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px'>
        <div>
            <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.15em;
                        color:rgba(255,255,255,0.4);margin-bottom:8px'>SISTEM DETEKSI DINI PARIWISATA</div>
            <div style='font-family:"DM Serif Display";font-size:32px;color:white;
                        letter-spacing:-.02em;line-height:1'>🛡️ BaliGuard</div>
            <div style='font-size:13px;color:rgba(255,255,255,0.55);margin-top:8px;line-height:1.7'>
                Dashboard Early Warning System berbasis Multi-Sumber Data,<br>
                Machine Learning &amp; Analisis Sentimen Multibahasa
            </div>
        </div>
        <div style='text-align:right'>
            <div style='font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:.08em;margin-bottom:4px'>DATA TERAKHIR</div>
            <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:600'>
                {_last_month}
            </div>
            <div style='font-size:11px;color:rgba(255,255,255,0.35);margin-top:3px'>
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
trend_col = "#ef4444" if fc_trend > 0.5 else ("#22c55e" if fc_trend < -0.5 else "#94a3b8")

st.markdown(f"""
<div style='background:linear-gradient(90deg,rgba(14,33,81,0.9),rgba(20,40,80,0.6));
            border:1px solid rgba(255,255,255,0.1);border-radius:14px;
            padding:16px 24px;margin-bottom:20px;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px'>
    <div>
        <div style='font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:6px'>🔮 PROYEKSI BULAN INI — {curr_mo}</div>
        <div style='display:flex;align-items:center;gap:14px'>
            <div style='font-family:"DM Serif Display";font-size:26px;
                        color:{COLOR_MAP.get(curr_lv,"#fff")}'>{EMOJI_MAP.get(curr_lv,"")} {curr_lv}</div>
            <div style='font-family:"JetBrains Mono";font-size:14px;color:#94a3b8'>
                Score <span style='color:#e2e8f0;font-weight:700'>{curr_sc}</span>/100
            </div>
            <div style='font-size:12px;color:{trend_col};font-weight:700'>{trend_txt}</div>
        </div>
    </div>
    <div style='display:flex;gap:28px'>
        <div style='text-align:center'>
            <div style='font-size:10px;color:#475569;margin-bottom:3px'>CONFIDENCE</div>
            <div style='font-family:"JetBrains Mono";font-size:16px;color:#93c5fd;font-weight:700'>
                {curr_conf:.0f}%
            </div>
        </div>
        <div style='text-align:center'>
            <div style='font-size:10px;color:#475569;margin-bottom:3px'>PROYEKSI DARI</div>
            <div style='font-family:"JetBrains Mono";font-size:13px;color:#64748b'>
                {_last_month}
            </div>
        </div>
        <div style='text-align:center'>
            <div style='font-size:10px;color:#475569;margin-bottom:3px'>TREN/BULAN</div>
            <div style='font-family:"JetBrains Mono";font-size:16px;color:{trend_col};font-weight:700'>
                {fc_trend:+.2f}
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
    delta_ctx = {'score_delta':0,'score_trend':'→','dominant':'wisman',
                 'anomaly_exp':'Data proyeksi','recovery_pct':0,'precovid_mean':0}

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
def kpi_html_delta(label, value, sub_static, delta_html, level=None):
    cls = f"kpi-card kpi-{level}" if level else "kpi-card"
    return (f'<div class="{cls}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub_static}</div>'
            f'<div style="margin-top:5px">{delta_html}</div></div>')

c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.markdown(kpi_html_delta(
    "LEVEL KRISIS", f"{EMOJI_MAP.get(level,'')} {level}",
    _proj_badge + f"RF: {rf_pred}",
    f"<span style='color:#475569;font-size:10px'>{_prev_month or '—'}</span>",
    level), unsafe_allow_html=True)
with c2: st.markdown(kpi_html_delta(
    "CRISIS SCORE",  f"{score:.1f}",
    _proj_badge + f"dari 100 · conf {conf:.0f}%",
    _d_score), unsafe_allow_html=True)
with c3: st.markdown(kpi_html_delta(
    "WISMAN",        f"{wisman:,}",
    _proj_badge + ("est. proyeksi" if _is_proj else "orang bulan ini"),
    _d_wisman), unsafe_allow_html=True)
with c4: st.markdown(kpi_html_delta(
    "TPK BINTANG",   f"{tpk:.1f}%",
    _proj_badge + ("est. proyeksi" if _is_proj else "hunian hotel"),
    _d_tpk), unsafe_allow_html=True)
with c5: st.markdown(kpi_html_delta(
    "SENTIMEN",      f"{sent:+.3f}",
    _proj_badge + ("est. proyeksi" if _is_proj else "avg ulasan"),
    _d_sent), unsafe_allow_html=True)
with c6: st.markdown(kpi_html_delta(
    "USD/IDR",       f"Rp {usd_avg:,.0f}",
    _live_badge,
    _d_usd), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

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
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📈 Overview & Timeline","🔬 Analisis Detail",
    "💬 Sentimen","🔮 Prediksi & Proyeksi","🤖 Narasi AI"
])

# ─── TAB 1: OVERVIEW ─────────────────────────────────
with tab1:
    months_dt = pd.to_datetime(predictions['month'].astype(str))

    fig = make_subplots(rows=3, cols=1,
        subplot_titles=('Crisis Score & Level Krisis','Kunjungan Wisatawan Mancanegara','Kurs USD/IDR'),
        vertical_spacing=0.14, row_heights=[0.46,0.28,0.26])

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
                      annotation_font_size=9, annotation_font_color=col, row=1, col=1)

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

    fig.update_layout(height=640, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1,
                    bgcolor='rgba(5,13,26,0.85)', bordercolor='rgba(255,255,255,0.12)',
                    borderwidth=1, font=dict(size=11,color='#e2e8f0')),
        plot_bgcolor='rgba(5,13,26,0.7)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0,r=80,t=50,b=10), font=dict(family='DM Sans',size=11,color='#94a3b8'))
    for r in [1,2,3]:
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                         linecolor='rgba(255,255,255,0.1)', row=r, col=1)
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.06)', showline=True,
                         linecolor='rgba(255,255,255,0.1)', row=r, col=1)
    st.plotly_chart(fig, width="stretch")

    c_a,c_b,c_c,c_d = st.columns(4)
    with c_a: st.metric("Bulan Level AMAN",    f"{(predictions['crisis_level']=='AMAN').mean()*100:.1f}%")
    with c_b: st.metric("Bulan Level KRISIS",  f"{(predictions['crisis_level']=='KRISIS').mean()*100:.1f}%")
    with c_c: st.metric("Avg Crisis Score",    f"{predictions['crisis_score_100'].mean():.1f}")
    with c_d: st.metric("Peak Wisman",         f"{predictions['wisman'].max():,}")

# ─── TAB 2: ANALISIS DETAIL ───────────────────────────
with tab2:
    cl, cr = st.columns(2)
    with cl:
        st.markdown('<div class="section-title sec-blue">📊 Komponen Crisis Score</div>', unsafe_allow_html=True)
        mr_rows = master[master['month']==sel]
        if len(mr_rows)>0:
            mr = mr_rows.iloc[0]
            comp_vals = {
                'Kunjungan Wisatawan': sf(mr.get('crisis_component_tourism',0)),
                'Kondisi Ekonomi':     sf(mr.get('crisis_component_economy',0)),
                'Sentimen Ulasan':     sf(mr.get('crisis_component_sentiment',0)),
            }
            fig_c = go.Figure(go.Bar(
                x=list(comp_vals.keys()), y=[v*100 for v in comp_vals.values()],
                marker_color=['#ef4444','#f59e0b','#3b82f6'],
                marker_line_color='rgba(0,0,0,0)', marker_line_width=0,
                text=[f'{v*100:.1f}%' for v in comp_vals.values()],
                textposition='outside', textfont=dict(size=12,color='#e2e8f0')
            ))
            fig_c.update_layout(
                yaxis=dict(range=[0,115],title='Kontribusi (%)',gridcolor='rgba(255,255,255,0.05)',color='#64748b'),
                xaxis=dict(color='#64748b'),
                plot_bgcolor='rgba(5,13,26,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=260, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(family='DM Sans',size=11,color='#94a3b8'))
            st.plotly_chart(fig_c, width="stretch")
        else:
            st.info("Data bulan ini tidak ada di master dataset.")

        st.markdown('<div class="section-title sec-purple sec-gap-md">📋 Indikator Detail</div>', unsafe_allow_html=True)
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
        for k,v in indicators:
            st.markdown(f'<div class="risk-row"><span class="risk-name">{k}</span>'
                        f'<span class="risk-val">{v}</span></div>', unsafe_allow_html=True)

    with cr:
        st.markdown('<div class="section-title sec-orange">🎯 Probabilitas Prediksi Random Forest</div>', unsafe_allow_html=True)
        prob_labels = ['AMAN','WASPADA','SIAGA','KRISIS']
        prob_vals   = [sf(row_data.get(f'prob_{l.lower()}',0))*100 for l in prob_labels]
        fig_p = go.Figure(go.Bar(
            y=prob_labels, x=prob_vals, orientation='h',
            marker_color=[COLOR_MAP[l] for l in prob_labels],
            marker_line_color='rgba(0,0,0,0)',
            text=[f'{v:.1f}%' for v in prob_vals], textposition='outside',
            textfont=dict(size=12,color='#e2e8f0')
        ))
        fig_p.update_layout(
            xaxis=dict(range=[0,115],title='Probabilitas (%)',gridcolor='rgba(255,255,255,0.05)',color='#64748b'),
            yaxis=dict(color='#94a3b8'),
            plot_bgcolor='rgba(5,13,26,0.5)', paper_bgcolor='rgba(0,0,0,0)',
            height=230, margin=dict(l=0,r=60,t=10,b=0),
            font=dict(family='DM Sans',size=11,color='#94a3b8'))
        st.plotly_chart(fig_p, width="stretch")

        st.markdown('<div class="section-title sec-green sec-gap-md">🌲 Feature Importance — Random Forest</div>', unsafe_allow_html=True)
        try:
            fi_available = [f for f in FEATURES if f in master.columns]
            fi = pd.DataFrame({'Fitur': fi_available[:len(rf_model.feature_importances_)],
                               'Importance': rf_model.feature_importances_[:len(fi_available)]})
            fi = fi.sort_values('Importance', ascending=True).tail(8)
            fig_fi = go.Figure(go.Bar(
                x=fi['Importance'], y=fi['Fitur'], orientation='h',
                marker_color='#3b82f6', marker_line_color='rgba(0,0,0,0)',
                text=[f'{v:.3f}' for v in fi['Importance']], textposition='outside',
                textfont=dict(size=10,color='#e2e8f0')
            ))
            fig_fi.update_layout(
                plot_bgcolor='rgba(5,13,26,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=290, margin=dict(l=0,r=70,t=10,b=0),
                xaxis=dict(range=[0,fi['Importance'].max()*1.4],gridcolor='rgba(255,255,255,0.05)',color='#64748b'),
                yaxis=dict(color='#94a3b8'),
                font=dict(family='DM Sans',size=10,color='#94a3b8'))
            st.plotly_chart(fig_fi, width="stretch")
        except Exception:
            st.info("Feature importance tidak tersedia.")

# ─── TAB 3: SENTIMEN ─────────────────────────────────
with tab3:
    cs1, cs2 = st.columns([2,1])
    with cs1:
        st.markdown('<div class="section-title sec-green">💚 Tren Sentimen Wisatawan Bulanan</div>', unsafe_allow_html=True)
        if 'avg_sentiment_monthly' in master.columns:
            m_dt = pd.to_datetime(master['month'].astype(str))
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=m_dt, y=master['avg_sentiment_monthly'],
                mode='lines+markers', name='Sentimen',
                line=dict(color='#4ade80',width=2),
                marker=dict(size=3,color='#4ade80'),
                fill='tozeroy', fillcolor='rgba(74,222,128,0.06)'))
            fig_s.add_hline(y=0,line_dash='dash',line_color='rgba(255,255,255,0.15)',line_width=1)
            fig_s.add_vrect(x0='2020-03-01',x1='2021-12-01',
                fillcolor='rgba(239,68,68,0.06)',line_width=0,
                annotation_text='COVID',annotation_font_color='#ef4444')
            fig_s.add_vline(x=sel_dt,line_dash='dot',line_color='#60a5fa',line_width=1.2)
            fig_s.update_layout(
                yaxis=dict(title='Sentimen (-1 → +1)',gridcolor='rgba(255,255,255,0.04)',color='#64748b'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)',color='#64748b'),
                plot_bgcolor='rgba(5,13,26,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=290, margin=dict(l=0,r=0,t=10,b=0),
                font=dict(family='DM Sans',size=11,color='#94a3b8'))
            st.plotly_chart(fig_s, width="stretch")

        st.markdown('<div class="section-title sec-green sec-gap-md">📊 Sentimen 6 Bulan Terakhir</div>', unsafe_allow_html=True)
        if 'avg_sentiment_monthly' in predictions.columns:
            last6 = predictions.tail(6)[['month','avg_sentiment_monthly']].copy()
            colors_bar = ['#4ade80' if v>0.1 else ('#f87171' if v<-0.1 else '#fbbf24')
                          for v in last6['avg_sentiment_monthly']]
            fig_6 = go.Figure(go.Bar(
                x=last6['month'], y=last6['avg_sentiment_monthly'],
                marker_color=colors_bar, marker_line_color='rgba(0,0,0,0)',
                text=[f'{v:+.3f}' for v in last6['avg_sentiment_monthly']],
                textposition='outside', textfont=dict(color='#e2e8f0'),
                hovertemplate='<b>%{x}</b><br>Sentimen: %{y:.3f}<extra></extra>'
            ))
            fig_6.add_hline(y=0,line_dash='dash',line_color='rgba(255,255,255,0.15)',line_width=1)
            fig_6.update_layout(
                plot_bgcolor='rgba(5,13,26,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=190, margin=dict(l=0,r=0,t=10,b=0),
                yaxis=dict(gridcolor='rgba(255,255,255,0.04)',color='#64748b'),
                xaxis=dict(color='#64748b'),
                font=dict(family='DM Sans',size=11,color='#94a3b8'))
            st.plotly_chart(fig_6, width="stretch")

    with cs2:
        st.markdown('<div class="section-title sec-teal">🎛️ Gauge Sentimen</div>', unsafe_allow_html=True)
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=sent,
            delta={'reference':0,'valueformat':'.3f'},
            number={'valueformat':'+.3f','font':{'size':24,'color':'#e2e8f0','family':'JetBrains Mono'}},
            title={'text':"Sentimen Bulan Ini",'font':{'size':12,'color':'#64748b'}},
            gauge={
                'axis':{'range':[-1,1],'tickcolor':'#475569','tickwidth':1},
                'bar':{'color':'#4ade80' if sent>=0 else '#f87171','thickness':0.25},
                'bgcolor':'rgba(5,13,26,0)',
                'borderwidth':0,
                'steps':[{'range':[-1,-0.3],'color':'rgba(239,68,68,0.15)'},
                         {'range':[-0.3,0.3],'color':'rgba(245,158,11,0.1)'},
                         {'range':[0.3,1],  'color':'rgba(74,222,128,0.15)'}],
            }))
        fig_g.update_layout(height=210, margin=dict(l=20,r=20,t=40,b=10),
                             paper_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Sans',color='#94a3b8'))
        st.plotly_chart(fig_g, width="stretch")

        # pct_negative_monthly is in master, not predictions — look it up correctly
        mr_pct_rows = master[master['month']==sel]
        pct_neg = sf(mr_pct_rows['pct_negative_monthly'].iloc[0] if len(mr_pct_rows) > 0
                     and 'pct_negative_monthly' in master.columns
                     else row_data.get('pct_negative_monthly', 0))
        pct_pos = 100 - pct_neg
        st.metric("Review Positif", f"{pct_pos:.1f}%", "↑ Baik" if pct_pos>60 else "↓ Perhatian")
        st.metric("Review Negatif", f"{pct_neg:.1f}%", "↓ Rendah" if pct_neg<30 else "↑ Tinggi")
        st.metric("Vs Netral (0)",  f"{sent:+.3f}", "Positif" if sent>=0 else "Negatif")

        st.markdown("""
        <div style='background:rgba(3,105,161,0.12);border-radius:10px;padding:12px 14px;
                    font-size:11px;color:#7dd3fc;margin-top:12px;border:1px solid rgba(3,105,161,0.2)'>
            <b>ℹ️ Interpretasi</b><br><br>
            −1.0 ~ −0.3 → Sangat negatif<br>
            −0.3 ~ +0.3 → Netral<br>
            +0.3 ~ +1.0 → Positif<br><br>
            Model: XLM-RoBERTa (EN/ID/ZH)
        </div>
        """, unsafe_allow_html=True)

# ─── TAB 4: PREDIKSI & PROYEKSI ──────────────────────
with tab4:
    # ── Engine info bar ──────────────────────────────────
    st.markdown(
        "<div style='background:rgba(14,33,81,0.6);border-radius:10px;padding:10px 18px;"
        "margin-bottom:12px;border:1px solid rgba(59,130,246,0.15);"
        "display:flex;align-items:center;gap:12px'>"
        "<span style='font-size:9px;font-weight:700;color:#3b82f6;text-transform:uppercase;"
        "letter-spacing:.12em'>PREDICTION ENGINE</span>"
        "<span style='font-size:12px;color:#475569'>"
        "Random Forest + Isolation Forest + Trend Ekstrapolasi · pola historis 2009–2024</span>"
        "</div>",
        unsafe_allow_html=True)

    # ── Selector ─────────────────────────────────────────
    _sc1, _sc2, _sc3 = st.columns([1, 1, 2])
    _now = datetime.now()
    _MONTH_NAMES = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
    with _sc1:
        st.caption("📅 Tahun Mulai")
        _year_opts      = list(range(int(predictions['month'].iloc[-1][:4]), _now.year + 3))
        _default_yr_idx = _year_opts.index(_now.year) if _now.year in _year_opts else 0
        _proj_year      = st.selectbox("Tahun", _year_opts, index=_default_yr_idx,
                                        key="proj_year", label_visibility="collapsed")
    with _sc2:
        st.caption("🗓️ Bulan Mulai")
        _proj_month_name = st.selectbox("Bulan", _MONTH_NAMES, index=_now.month-1,
                                         key="proj_month", label_visibility="collapsed")
        _proj_month_num  = _MONTH_NAMES.index(_proj_month_name) + 1
    with _sc3:
        st.caption("📊 Jumlah Bulan Proyeksi")
        _proj_n = st.slider("Jumlah Bulan", 3, 12, 6, 1, key="proj_n",
                             label_visibility="collapsed")

    if _proj_month_num == 1:
        _from_month_str = f"{_proj_year - 1}-12"
    else:
        _from_month_str = f"{_proj_year}-{_proj_month_num - 1:02d}"

    fc_list_tab, fc_trend_tab = forecast_months(predictions, n=_proj_n, from_month=_from_month_str)

    st.markdown("<div style='margin:8px 0 12px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2-COLUMN LAYOUT  LEFT 58%  |  RIGHT 42%
    # ════════════════════════════════════════════════════
    t4_left, t4_right = st.columns([58, 42])

    # ══ LEFT ═════════════════════════════════════════════
    with t4_left:

        # ── Horizontal forecast timeline ─────────────────
        st.markdown(
            "<div class='section-title'>"
            "🔮 Proyeksi " + str(_proj_n) + " Bulan — " +
            _proj_month_name + " " + str(_proj_year) + "</div>",
            unsafe_allow_html=True)

        _rows_of_3 = [fc_list_tab[i:i+3] for i in range(0, len(fc_list_tab), 3)]
        for _r_idx, _row_fc in enumerate(_rows_of_3):
            _row_html = "<div style='display:grid;grid-template-columns:repeat({n},1fr);gap:8px;margin-bottom:8px'>".format(n=len(_row_fc))
            for _fi, _fc in enumerate(_row_fc):
                _lv   = _fc['level']
                _clr  = COLOR_MAP.get(_lv, '#3b82f6')
                _gi   = _r_idx * 3 + _fi
                _op   = "0.55" if _gi > 2 else "1"
                _cw   = int(_fc['confidence'])
                _row_html += (
                    "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);"
                    "border-top:2px solid {clr};border-radius:12px;padding:12px 14px;"
                    "text-align:center;opacity:{op}'>"
                    "<div style='font-family:\"JetBrains Mono\";font-size:9px;color:#475569;"
                    "margin-bottom:5px;letter-spacing:.05em'>{mo}</div>"
                    "<div style='font-size:16px;margin-bottom:3px'>{em}</div>"
                    "<div style='font-size:12px;font-weight:700;color:{clr};margin-bottom:2px'>{lv}</div>"
                    "<div style='font-family:\"JetBrains Mono\";font-size:10px;color:#475569;margin-bottom:7px'>{sc}/100</div>"
                    "<div style='height:3px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;margin-bottom:4px'>"
                    "<div style='height:100%;width:{cw}%;background:{clr};border-radius:2px'></div></div>"
                    "<div style='font-family:\"JetBrains Mono\";font-size:12px;font-weight:700;color:#7dd3fc'>{cf:.0f}%</div>"
                    "<div style='font-size:9px;color:#334155;letter-spacing:.05em'>confidence</div>"
                    "</div>"
                ).format(clr=_clr, op=_op, mo=_fc['month'],
                         em=EMOJI_MAP.get(_lv,''), lv=_lv, sc=_fc['score'],
                         cw=_cw, cf=_fc['confidence'])
            _row_html += "</div>"
            st.markdown(_row_html, unsafe_allow_html=True)

        st.markdown(
            "<div style='background:rgba(245,158,11,0.05);border-radius:8px;padding:7px 11px;"
            "font-size:11px;color:#78350f;border:1px solid rgba(245,158,11,0.1);margin-bottom:12px'>"
            "⚠️ Proyeksi berdasarkan tren historis. Confidence menurun seiring jarak proyeksi.</div>",
            unsafe_allow_html=True)

        # ── Trend + Proyeksi chart ────────────────────────
        st.markdown('<div class="section-title">📈 Tren + Proyeksi</div>', unsafe_allow_html=True)
        last12    = predictions.tail(12)
        l12_dt    = pd.to_datetime(last12['month'].astype(str))
        fc_dt     = pd.to_datetime([f['month'] for f in fc_list_tab])
        fc_scores = [f['score'] for f in fc_list_tab]
        fc_lo     = [max(0,  s - 8) for s in fc_scores]
        fc_hi     = [min(100, s + 8) for s in fc_scores]
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=l12_dt, y=last12['crisis_score_100'],
            mode='lines+markers', name='Historis',
            line=dict(color='#7dd3fc', width=2), marker=dict(size=4, color='#7dd3fc')))
        fig_fc.add_trace(go.Scatter(
            x=list(fc_dt) + list(reversed(list(fc_dt))),
            y=fc_hi + list(reversed(fc_lo)),
            fill='toself', fillcolor='rgba(245,158,11,0.08)',
            line=dict(width=0), showlegend=True, name='Interval ±8',
            hoverinfo='skip'))
        fig_fc.add_trace(go.Scatter(x=fc_dt, y=fc_scores,
            mode='lines+markers', name='Proyeksi',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            marker=dict(size=7, symbol='diamond', color='#f59e0b')))
        for thr,lbl,col in [(70,'KRISIS','#ef4444'),(50,'SIAGA','#f97316'),(30,'WASPADA','#f59e0b')]:
            fig_fc.add_hline(y=thr, line_dash='dot', line_color=col, line_width=0.7, opacity=0.5,
                             annotation_text=lbl, annotation_position='right',
                             annotation_font_size=9, annotation_font_color=col)
        fig_fc.update_layout(
            yaxis=dict(range=[0,100], title='Crisis Score',
                       gridcolor='rgba(255,255,255,0.05)', color='#475569'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#475569'),
            plot_bgcolor='rgba(8,16,32,0.6)', paper_bgcolor='rgba(0,0,0,0)',
            height=235, margin=dict(l=0, r=72, t=8, b=0),
            legend=dict(orientation='h', y=1.02, x=0, bgcolor='rgba(0,0,0,0)',
                        font=dict(size=11, color='#94a3b8')),
            font=dict(family='DM Sans', size=11, color='#94a3b8'))
        st.plotly_chart(fig_fc, width="stretch")

        # ── Recovery Rate ─────────────────────────────────
        st.markdown('<div class="section-title">📉 Recovery Rate vs Baseline 2017–2019</div>',
                    unsafe_allow_html=True)
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
                yaxis=dict(title='Recovery (%)', gridcolor='rgba(255,255,255,0.05)', color='#475569'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.6)', paper_bgcolor='rgba(0,0,0,0)',
                height=195, margin=dict(l=0, r=80, t=8, b=0),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_rec, width="stretch")
            _rcol = '#10b981' if delta_ctx['recovery_pct'] >= 90 else \
                    ('#f59e0b' if delta_ctx['recovery_pct'] >= 60 else '#ef4444')
            st.markdown(
                "<div style='background:rgba(255,255,255,0.02);border-radius:8px;"
                "padding:7px 12px;font-size:12px;color:#475569'>"
                "Recovery <b style='color:#e2e8f0'>{mo}</b>: "
                "<span style='color:{rc};font-weight:700;font-size:14px'>{rv:.1f}%</span>"
                " dari baseline ({bsl:,} wisman/bln)</div>".format(
                    mo=sel, rc=_rcol,
                    rv=delta_ctx['recovery_pct'], bsl=int(_precovid_mean)),
                unsafe_allow_html=True)

    # ══ RIGHT ════════════════════════════════════════════
    with t4_right:

        # ── Risk Simulator ────────────────────────────────
        st.markdown('<div class="section-title">🎮 Simulator Skenario Risiko</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(59,130,246,0.06);border-radius:8px;padding:7px 11px;"
            "font-size:11px;color:#7dd3fc;margin-bottom:10px;border:1px solid rgba(59,130,246,0.12)'>"
            "Geser slider untuk simulasi dampak perubahan indikator secara real-time.</div>",
            unsafe_allow_html=True)

        w_d = st.slider("📉 Wisman (%)", -80, 50, 0, 5, key="sim_w")
        u_d = st.slider("💱 USD/IDR (%)", -10, 30, 0, 1, key="sim_u")
        s_d = st.slider("💬 Sentimen", -1.0, 1.0, 0.0, 0.1, key="sim_s")

        sim_sc = simulate_score(dict(row_data), w_d, u_d, s_d)
        sim_lv = level_from_score(sim_sc)
        _sdelta = sim_sc - score
        _sdcol  = "#ef4444" if _sdelta > 0 else "#10b981"
        _sclr   = COLOR_MAP.get(sim_lv, '#fff')

        st.markdown(
            "<div style='background:linear-gradient(135deg,rgba(12,26,58,0.95),rgba(22,37,80,0.95));"
            "border:1px solid rgba(255,255,255,0.07);border-radius:12px;"
            "padding:16px;margin:8px 0;text-align:center'>"
            "<div style='font-size:9px;font-weight:700;color:#1e3a5f;text-transform:uppercase;"
            "letter-spacing:.12em;margin-bottom:6px'>HASIL SIMULASI</div>"
            "<div style='font-family:\"JetBrains Mono\";font-size:42px;font-weight:700;"
            "color:#f1f5f9;line-height:1'>{sc}</div>"
            "<div style='font-size:10px;color:#334155;margin-bottom:8px'>Crisis Score / 100</div>"
            "<div style='background:rgba(255,255,255,0.06);border-radius:8px;"
            "padding:6px 14px;display:inline-block;"
            "font-family:\"DM Serif Display\";font-size:16px;color:{clr}'>"
            "{em} {lv}</div>"
            "<div style='margin-top:8px;font-family:\"JetBrains Mono\";font-size:12px;color:#334155'>"
            "dari {base:.1f} → <span style='color:{dc};font-weight:700'>{d:+.1f} poin</span>"
            "</div></div>".format(
                sc=sim_sc, clr=_sclr, em=EMOJI_MAP.get(sim_lv,''), lv=sim_lv,
                base=score, dc=_sdcol, d=_sdelta),
            unsafe_allow_html=True)

        # ── Breakdown Risiko ──────────────────────────────
        st.markdown('<div class="section-title">⚠️ Breakdown Risiko</div>', unsafe_allow_html=True)
        for nm, st_txt, c in [
            ("Penurunan Wisman",
             "Tinggi" if w_d<-20 else ("Sedang" if w_d<0 else "Rendah"),
             "#ef4444" if w_d<-20 else ("#f59e0b" if w_d<0 else "#10b981")),
            ("Tekanan Kurs USD",
             "Tinggi" if u_d>10  else ("Sedang" if u_d>3  else "Rendah"),
             "#ef4444" if u_d>10  else ("#f59e0b" if u_d>3  else "#10b981")),
            ("Sentimen Negatif",
             "Tinggi" if s_d<-0.3 else ("Sedang" if s_d<0 else "Rendah"),
             "#ef4444" if s_d<-0.3 else ("#f59e0b" if s_d<0 else "#10b981")),
        ]:
            st.markdown(
                "<div class='risk-row'><span class='risk-name'>{nm}</span>"
                "<span style='color:{c};font-weight:700;font-size:11px;"
                "font-family:\"JetBrains Mono\"'>{st}</span></div>".format(nm=nm, c=c, st=st_txt),
                unsafe_allow_html=True)

        # ── Rekomendasi ───────────────────────────────────
        _rclr_btn = COLOR_MAP.get(sim_lv, '#3b82f6')
        st.markdown(
            "<div class='section-title'>✅ Rekomendasi — Level {lv}</div>".format(lv=sim_lv),
            unsafe_allow_html=True)
        for i, rec in enumerate(ADVICE_MAP.get(sim_lv, []), 1):
            st.markdown(
                "<div style='background:rgba(255,255,255,0.02);border-radius:8px;"
                "padding:8px 11px;margin-bottom:5px;border-left:2px solid {clr};"
                "font-size:12px;color:#94a3b8;line-height:1.6'>"
                "<span style='font-weight:700;color:{clr}'>{i}.</span> {rec}"
                "</div>".format(clr=_rclr_btn, i=i, rec=rec),
                unsafe_allow_html=True)

        # ── Risk Scatter ──────────────────────────────────
        st.markdown('<div class="section-title">🗺️ Peta Risiko Historis</div>', unsafe_allow_html=True)
        _sc_src = master if 'wisman_growth_mom' in master.columns else predictions
        if 'wisman_growth_mom' in _sc_src.columns and 'crisis_level' in _sc_src.columns:
            fig_r = go.Figure()
            for _lv_sc in ['AMAN','WASPADA','SIAGA','KRISIS']:
                _mask = _sc_src['crisis_level'] == _lv_sc
                if _mask.sum() > 0:
                    fig_r.add_trace(go.Scatter(
                        x=_sc_src.loc[_mask,'wisman_growth_mom']*100,
                        y=_sc_src.loc[_mask,'avg_sentiment_monthly'],
                        mode='markers', name=_lv_sc,
                        marker=dict(color=COLOR_MAP[_lv_sc], size=5, opacity=0.75,
                                    line=dict(width=0.4, color='rgba(0,0,0,0.3)'))))
            fig_r.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r.add_vline(x=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r.update_layout(
                xaxis=dict(title='Wisman Growth MoM (%)',
                           gridcolor='rgba(255,255,255,0.05)', color='#475569'),
                yaxis=dict(title='Avg Sentimen',
                           gridcolor='rgba(255,255,255,0.05)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.6)', paper_bgcolor='rgba(0,0,0,0)',
                height=225, margin=dict(l=0, r=0, t=8, b=0),
                legend=dict(orientation='h', y=1.02, x=0, bgcolor='rgba(0,0,0,0)',
                            font=dict(size=10, color='#94a3b8')),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_r, width="stretch")

# ─── TAB 5: NARASI AI ─────────────────────────────────
with tab5:

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
    na_l, na_r = st.columns([3, 2])

    with na_l:
        # ─ 1. TIPE LAPORAN ────────────────────────────────
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
                'color':'#4ade80','bg':'rgba(74,222,128,0.10)','border':'rgba(74,222,128,0.30)',
            },
        }

        if 'report_type_sel' not in st.session_state:
            st.session_state['report_type_sel'] = 'summary'

        _rt_cols = st.columns(3)
        for _i, (_key, _card) in enumerate(REPORT_CARDS.items()):
            with _rt_cols[_i]:
                _is_sel   = st.session_state['report_type_sel'] == _key
                _bdr      = ("2px solid " + _card['color']) if _is_sel else ("1px solid " + _card['border'])
                _shad     = ("box-shadow:0 0 12px " + _card['color'] + "33;") if _is_sel else ""
                _opac     = "1" if _is_sel else "0.65"
                st.markdown(
                    "<div style='background:" + _card['bg'] + ";border:" + _bdr + ";"
                    "border-radius:12px;padding:14px 12px;opacity:" + _opac + ";" + _shad + "'>"
                    "<div style='font-size:22px;margin-bottom:6px'>" + _card['icon'] + "</div>"
                    "<div style='font-size:12px;font-weight:700;color:" + _card['color'] + ";margin-bottom:3px'>"
                    + _card['title'] + "</div>"
                    "<div style='font-size:10px;color:#94a3b8;font-weight:600;margin-bottom:5px'>"
                    + _card['desc'] + "</div>"
                    "<div style='font-size:10px;color:#64748b;line-height:1.6'>" + _card['detail'] + "</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
                if st.button(_card['title'], key="rt_" + _key, width="stretch"):
                    st.session_state['report_type_sel'] = _key
                    st.rerun()

        report_type = st.session_state['report_type_sel']
        _sel_card   = REPORT_CARDS[report_type]
        st.markdown(
            "<div style='margin-top:10px;background:" + _sel_card['bg'] + ";border-radius:8px;"
            "padding:10px 14px;border-left:3px solid " + _sel_card['color'] + "'>"
            "<span style='font-size:11px;color:#94a3b8'>Tipe dipilih: "
            "<b style='color:" + _sel_card['color'] + "'>" + _sel_card['icon'] + " " + _sel_card['title'] + "</b>"
            " &nbsp;·&nbsp; " + _sel_card['desc'] + "</span></div>",
            unsafe_allow_html=True
        )

        # ─ 2. PILIH MODEL AI ──────────────────────────────
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
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
    <b style='color:#475569'>🛡️ BaliGuard</b> — Early Warning System Pariwisata Berbasis
    Multi-Sumber Data, Machine Learning &amp; Analisis Sentimen<br>
    <span style='font-size:10px;color:#1e293b'>
        Data: BPS Bali · Bank Indonesia · Google Hotels &nbsp;|&nbsp;
        Model: Isolation Forest + Random Forest + XLM-RoBERTa &nbsp;|&nbsp;
        Narasi: Groq LLM (llama-3.3-70b-versatile / llama-3.1-8b / mixtral / gemma2)
    </span>
</div>
""", unsafe_allow_html=True)
