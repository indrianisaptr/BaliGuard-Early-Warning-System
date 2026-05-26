import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
import json
import os
import sys

# ══════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="BaliGuard — Early Warning System Pariwisata",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
# CSS — DESIGN SYSTEM
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #f0f4f8; }
.block-container { padding: 1.2rem 2rem 2rem; }

/* ── KPI Cards ── */
.kpi-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }
.kpi-card {
    flex: 1; min-width: 140px;
    background: white;
    border-radius: 14px;
    padding: 18px 20px;
    border-top: 4px solid #3B82F6;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    position: relative; overflow: hidden;
}
.kpi-card::after {
    content: ''; position: absolute; right: -16px; top: -16px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(59,130,246,0.06);
}
.kpi-label { font-size: 11px; color: #94a3b8; font-weight: 600;
             text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #0f172a; line-height: 1.1; }
.kpi-sub   { font-size: 11px; color: #64748b; margin-top: 5px; }
.kpi-AMAN    { border-top-color: #16a34a; }
.kpi-WASPADA { border-top-color: #d97706; }
.kpi-SIAGA   { border-top-color: #ea580c; }
.kpi-KRISIS  { border-top-color: #dc2626; background: #fff8f8; }

/* ── Section Headers ── */
.section-title {
    font-size: 15px; font-weight: 700; color: #1e293b;
    padding: 6px 0 14px; letter-spacing: -0.02em;
}

/* ── Alert Boxes ── */
.alert-aman    { background:#f0fdf4; border-left:4px solid #16a34a; padding:14px 18px; border-radius:8px; }
.alert-waspada { background:#fffbeb; border-left:4px solid #d97706; padding:14px 18px; border-radius:8px; }
.alert-siaga   { background:#fff7ed; border-left:4px solid #ea580c; padding:14px 18px; border-radius:8px; }
.alert-krisis  { background:#fef2f2; border-left:4px solid #dc2626; padding:14px 18px; border-radius:8px; }
.alert-title   { font-weight:700; font-size:14px; margin-bottom:6px; }
.alert-body    { font-size:13px; color:#374151; line-height:1.6; }

/* ── Narrative ── */
.narrative-box {
    background: white; border-radius: 12px; padding: 22px 24px;
    border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    line-height: 1.85; font-size: 14px; color: #1e293b; white-space: pre-wrap;
}

/* ── Prediction Card ── */
.pred-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
    border-radius: 14px; padding: 22px 24px; color: white; margin-bottom: 12px;
}
.pred-title { font-size: 12px; font-weight: 600; text-transform: uppercase;
              letter-spacing: 0.06em; opacity: 0.7; margin-bottom: 8px; }
.pred-level { font-size: 32px; font-weight: 800; margin-bottom: 4px; }
.pred-sub   { font-size: 12px; opacity: 0.75; }

/* ── Gauge wrapper ── */
.gauge-wrap { background: white; border-radius: 14px; padding: 8px;
              box-shadow: 0 1px 6px rgba(0,0,0,0.07); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background: transparent;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    font-weight: 600; font-size: 13px;
}

/* ── Tag badges ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
}
.badge-green  { background:#dcfce7; color:#15803d; }
.badge-yellow { background:#fef9c3; color:#a16207; }
.badge-orange { background:#ffedd5; color:#c2410c; }
.badge-red    { background:#fee2e2; color:#b91c1c; }

/* ── Risk row ── */
.risk-row { display:flex; justify-content:space-between; align-items:center;
            padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:13px; }
.risk-name { color: #374151; font-weight: 500; }
.risk-val  { color: #0f172a; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════
COLOR_MAP = {
    'AMAN':    '#16a34a',
    'WASPADA': '#d97706',
    'SIAGA':   '#ea580c',
    'KRISIS':  '#dc2626',
}
BG_MAP = {
    'AMAN':    'rgba(22,163,74,0.10)',
    'WASPADA': 'rgba(217,119,6,0.10)',
    'SIAGA':   'rgba(234,88,12,0.10)',
    'KRISIS':  'rgba(220,38,38,0.12)',
}
EMOJI_MAP   = {'AMAN': '🟢', 'WASPADA': '🟡', 'SIAGA': '🟠', 'KRISIS': '🔴'}
BADGE_MAP   = {'AMAN': 'badge-green', 'WASPADA': 'badge-yellow',
               'SIAGA': 'badge-orange', 'KRISIS': 'badge-red'}
ALERT_MAP   = {'AMAN': 'alert-aman', 'WASPADA': 'alert-waspada',
               'SIAGA': 'alert-siaga', 'KRISIS': 'alert-krisis'}

FEATURES = [
    'wisman_growth_mom','wisman_growth_yoy','wisman_zscore',
    'usd_idr_avg','usd_volatility_3m','usd_change_mom',
    'tpk_bintang','tpk_change_mom','inflasi_processed',
    'bali_share_pct','avg_sentiment_monthly','month_num','is_peak_season'
]

ADVICE_MAP = {
    'AMAN':    [
        "Manfaatkan momentum positif untuk promosi pariwisata ke segmen baru.",
        "Lanjutkan pemantauan rutin indikator bulanan.",
        "Siapkan cadangan protokol respons untuk antisipasi perubahan."
    ],
    'WASPADA': [
        "Tingkatkan frekuensi pemantauan data wisman dan sentimen mingguan.",
        "Koordinasikan dengan dinas terkait untuk identifikasi faktor risiko.",
        "Pertimbangkan kampanye promosi untuk menstabilkan arus wisatawan."
    ],
    'SIAGA': [
        "Aktifkan tim satgas pariwisata dan lakukan rapat koordinasi darurat.",
        "Evaluasi faktor penyebab: kurs, sentimen negatif, atau faktor eksternal.",
        "Siapkan paket insentif wisatawan dan stimulus industri perhotelan."
    ],
    'KRISIS': [
        "Deklarasikan status darurat pariwisata dan aktivasi protokol krisis.",
        "Lakukan intervensi langsung: subsidi, relaksasi regulasi, stimulus fiskal.",
        "Koordinasi lintas kementerian dan bentuk posko penanganan krisis pariwisata."
    ]
}

# ══════════════════════════════════════════════════════════
# LOAD DATA & MODELS
# ══════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    master = pd.read_parquet('data/final/master_dataset_clean.parquet')
    pred   = pd.read_csv('data/final/predictions_final.csv')
    cache  = {}
    if os.path.exists('data/final/narratives_cache.json'):
        with open('data/final/narratives_cache.json', 'r', encoding='utf-8') as f:
            cache = json.load(f)
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
    DATA_OK = False
    DATA_ERR = str(e)

if not DATA_OK:
    st.error(f"❌ Gagal memuat data/model: {DATA_ERR}")
    st.info("Jalankan NB05 dan NB06 terlebih dahulu, lalu pastikan semua file ada di `data/final/` dan `data/models/`.")
    st.stop()

# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════
def get_row(month_str):
    r = predictions[predictions['month'] == month_str]
    return r.iloc[0] if len(r) else predictions.iloc[-1]

def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def kpi(label, value, sub="", level=None):
    cls = f"kpi-card kpi-{level}" if level else "kpi-card"
    return (f'<div class="{cls}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')

def badge(text, level):
    return f'<span class="badge {BADGE_MAP.get(level,"badge-green")}">{text}</span>'

def alert_box(level, title, body):
    return (f'<div class="{ALERT_MAP.get(level,"alert-aman")}">'
            f'<div class="alert-title">{EMOJI_MAP.get(level,"")} {title}</div>'
            f'<div class="alert-body">{body}</div></div>')

def simulate_crisis_score(base_row, wisman_delta_pct, usd_delta_pct, sentiment_delta):
    """Simulasikan crisis score berdasarkan perubahan input."""
    comp_t = safe_float(base_row.get('crisis_component_tourism', 0.4))
    comp_e = safe_float(base_row.get('crisis_component_economy', 0.3))
    comp_s = safe_float(base_row.get('crisis_component_sentiment', 0.25))

    # Adjust komponen berdasarkan delta
    comp_t_new = max(0, min(1, comp_t - (wisman_delta_pct / 100) * 0.5))
    comp_e_new = max(0, min(1, comp_e + (usd_delta_pct / 100) * 0.3))
    comp_s_new = max(0, min(1, comp_s - sentiment_delta * 0.2))

    new_score = (0.45 * comp_t_new + 0.30 * comp_e_new + 0.25 * comp_s_new) * 100
    return round(new_score, 1)

def level_from_score(score):
    if score >= 70: return 'KRISIS'
    if score >= 50: return 'SIAGA'
    if score >= 30: return 'WASPADA'
    return 'AMAN'

def predict_next_months(predictions_df, rf_model, scaler, le, n=3):
    """Prediksi level krisis N bulan ke depan menggunakan trend ekstrapolasi."""
    results = []
    last_rows = predictions_df.tail(6)
    base_score = last_rows['crisis_score_100'].values[-1]
    trend = np.polyfit(range(len(last_rows)), last_rows['crisis_score_100'].values, 1)[0]

    last_month = pd.Period(predictions_df['month'].iloc[-1], freq='M')
    for i in range(1, n + 1):
        next_month = last_month + i
        proj_score = max(0, min(100, base_score + trend * i))
        proj_level = level_from_score(proj_score)

        # Estimasi confidence berdasarkan jarak proyeksi (semakin jauh semakin tidak pasti)
        confidence = max(0.4, 0.85 - (i - 1) * 0.15)
        results.append({
            'month': str(next_month),
            'proj_score': round(proj_score, 1),
            'proj_level': proj_level,
            'confidence': round(confidence * 100, 0),
            'trend_per_month': round(trend, 2)
        })
    return results

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0 4px'>
        <span style='font-size:36px'>🛡️</span><br>
        <span style='font-size:18px;font-weight:800;color:#1e3a5f;letter-spacing:-0.03em'>BaliGuard</span><br>
        <span style='font-size:11px;color:#64748b;font-weight:500'>Early Warning System Pariwisata</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    available_months = sorted(predictions['month'].unique(), reverse=True)
    selected_month   = st.selectbox("📅 Bulan Analisis", available_months,
                                    help="Pilih periode untuk analisis detail")
    selected_dt = pd.to_datetime(selected_month)

    st.divider()
    st.markdown("**🤖 Narasi AI — Groq Engine**")
    groq_key = st.text_input(
        "Groq API Key", type="password",
        placeholder="gsk_...",
        help="Dapatkan gratis di console.groq.com"
    )
    if not groq_key:
        st.caption("💡 [Dapatkan key gratis →](https://console.groq.com/keys)")

    st.divider()

    # Mini status sidebar
    row_side = get_row(selected_month)
    lvl_side = str(row_side.get('crisis_level', 'WASPADA'))
    sc_side  = safe_float(row_side.get('crisis_score_100', 0))
    anom_side = int(row_side.get('iso_anomaly', 0))

    st.markdown(f"""
    <div style='background:#f8fafc;border-radius:10px;padding:12px 14px'>
        <div style='font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin-bottom:8px'>STATUS TERKINI</div>
        <div style='font-size:22px;font-weight:800;color:{COLOR_MAP.get(lvl_side,"#333")}'>{EMOJI_MAP.get(lvl_side,"")} {lvl_side}</div>
        <div style='font-size:12px;color:#64748b;margin-top:3px'>Score: {sc_side:.1f}/100</div>
        <div style='font-size:11px;color:{"#ea580c" if anom_side else "#16a34a"};margin-top:6px;font-weight:600'>
            {"⚠️ Anomali Terdeteksi" if anom_side else "✅ Tidak Ada Anomali"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style='font-size:11px;color:#94a3b8;line-height:1.7'>
        <b>Data Sumber:</b><br>
        BPS Bali · Bank Indonesia<br>
        Google Hotels Review<br><br>
        <b>Model:</b><br>
        Isolation Forest (Anomali)<br>
        Random Forest (Klasifikasi)<br>
        XLM-RoBERTa (Sentimen)<br><br>
        <b>Narasi Engine:</b><br>
        Groq LLM · llama-3.3-70b-versatile
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div style='background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 60%,#0ea5e9 100%);
            border-radius:16px;padding:24px 32px;margin-bottom:20px;
            display:flex;align-items:center;gap:16px'>
    <div>
        <div style='font-size:11px;font-weight:600;text-transform:uppercase;
                    letter-spacing:0.1em;color:rgba(255,255,255,0.6);margin-bottom:6px'>
            SISTEM DETEKSI DINI
        </div>
        <div style='font-size:26px;font-weight:800;color:white;letter-spacing:-0.04em;line-height:1'>
            🛡️ BaliGuard
        </div>
        <div style='font-size:13px;color:rgba(255,255,255,0.75);margin-top:6px;line-height:1.5'>
            Dashboard Early Warning System Pariwisata Berbasis<br>
            Multi-Sumber Data, Machine Learning &amp; Analisis Sentimen
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

row_data = get_row(selected_month)
level    = str(row_data.get('crisis_level', 'WASPADA'))
score    = safe_float(row_data.get('crisis_score_100', 0))
wisman   = int(safe_float(row_data.get('wisman', 0)))
tpk      = safe_float(row_data.get('tpk_bintang', 0))
conf     = safe_float(row_data.get('rf_confidence', 0)) * 100
is_anom  = int(safe_float(row_data.get('iso_anomaly', 0)))
rf_pred  = str(row_data.get('rf_predicted_level', 'N/A'))
sent     = safe_float(row_data.get('avg_sentiment_monthly', 0))
usd_avg  = safe_float(row_data.get('usd_idr_avg', 0))
inflasi  = safe_float(row_data.get('inflasi_processed', 0))

# ══════════════════════════════════════════════════════════
# KPI STRIP
# ══════════════════════════════════════════════════════════
c1, c2, c3, c4, c5, c6 = st.columns(6)
cards_data = [
    (c1, "LEVEL KRISIS",     f"{EMOJI_MAP.get(level,'')} {level}",   f"RF: {rf_pred}",          level),
    (c2, "CRISIS SCORE",     f"{score:.1f}",                          f"dari 100 · conf {conf:.0f}%", None),
    (c3, "WISATAWAN MANCA.", f"{wisman:,}",                           "orang bulan ini",          None),
    (c4, "TPK HOTEL BINTANG",f"{tpk:.1f}%",                          "tingkat hunian kamar",      None),
    (c5, "ANOMALI (IF)",     "⚠️ Ya" if is_anom else "✅ Normal",    "Isolation Forest",          None),
    (c6, "SENTIMEN",         f"{sent:+.3f}",                          "avg wisatawan reviews",     None),
]
for col, lbl, val, sub, lv in cards_data:
    with col:
        st.markdown(kpi(lbl, val, sub, lv), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# ALERT BANNER
# ══════════════════════════════════════════════════════════
alert_messages = {
    'AMAN':    "Pariwisata Bali dalam kondisi <b>normal dan stabil</b>. Tidak ada indikasi krisis yang signifikan pada periode ini.",
    'WASPADA': "Terdapat <b>sinyal awal yang perlu dipantau</b>. Beberapa indikator menunjukkan tekanan ringan — lakukan pemantauan lebih ketat.",
    'SIAGA':   "⚠️ <b>Tekanan signifikan terdeteksi</b> pada sektor pariwisata Bali. Koordinasi antarlembaga dan respons segera diperlukan.",
    'KRISIS':  "🚨 <b>KRISIS PARIWISATA TERDETEKSI.</b> Sistem mendeteksi kondisi kritis — aktifkan protokol penanganan krisis segera."
}
st.markdown(alert_box(level,
    f"Status Pariwisata Bali — {selected_month}",
    alert_messages.get(level, "")), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TABS UTAMA
# ══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview & Timeline",
    "🔬 Analisis Detail",
    "💬 Sentimen Multibahasa",
    "🔮 Prediksi Early Warning",
    "🤖 Narasi AI"
])

# ─────────────────────────────────────────────
# TAB 1 — OVERVIEW & TIMELINE
# ─────────────────────────────────────────────
with tab1:
    months_dt = pd.to_datetime(predictions['month'].astype(str))

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Crisis Score + Level Krisis', 'Kunjungan Wisatawan Mancanegara (Orang)', 'Kurs USD/IDR'),
        vertical_spacing=0.09,
        row_heights=[0.45, 0.30, 0.25]
    )

    # Row 1: Crisis Score
    fig.add_trace(go.Scatter(
        x=months_dt, y=predictions['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#334155', width=1.8),
        fill='tozeroy', fillcolor='rgba(51,65,85,0.06)'
    ), row=1, col=1)

    for lvl, color in COLOR_MAP.items():
        mask = predictions['crisis_level'] == lvl
        fig.add_trace(go.Scatter(
            x=months_dt[mask], y=predictions['crisis_score_100'][mask],
            mode='markers', name=lvl,
            marker=dict(color=color, size=7, line=dict(width=1, color='white')),
            hovertemplate=f'<b>{lvl}</b><br>%{{x|%b %Y}}<br>Score: %{{y:.1f}}<extra></extra>'
        ), row=1, col=1)

    for thr, lbl, col in [(70,'KRISIS','#dc2626'), (50,'SIAGA','#ea580c'), (30,'WASPADA','#d97706')]:
        fig.add_hline(y=thr, line_dash='dot', line_color=col, line_width=1, opacity=0.7,
                      annotation_text=lbl, annotation_position='right',
                      annotation_font_size=10, row=1, col=1)

    # Row 2: Wisman
    fig.add_trace(go.Scatter(
        x=months_dt, y=predictions['wisman'],
        mode='lines', name='Wisman', showlegend=False,
        line=dict(color='#2563eb', width=1.6),
        fill='tozeroy', fillcolor='rgba(37,99,235,0.08)'
    ), row=2, col=1)

    # Row 3: USD/IDR (dari master)
    if 'usd_idr_avg' in predictions.columns:
        fig.add_trace(go.Scatter(
            x=months_dt, y=predictions['usd_idr_avg'],
            mode='lines', name='USD/IDR', showlegend=False,
            line=dict(color='#d97706', width=1.6),
        ), row=3, col=1)

    # Shading COVID
    for r in [1, 2, 3]:
        fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
            fillcolor='rgba(220,38,38,0.08)', line_width=0,
            annotation_text='COVID-19' if r == 1 else '',
            annotation_position='top left',
            annotation_font_color='#dc2626', row=r, col=1)
        fig.add_vline(x=selected_dt, line_dash='dot',
            line_color='#2563eb', line_width=1.5, row=r, col=1)

    fig.update_layout(
        height=580, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1,
                    bgcolor='rgba(255,255,255,0.9)', bordercolor='#e2e8f0',
                    borderwidth=1, font_size=11),
        plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=80, t=60, b=0),
        font=dict(family='Inter', size=11)
    )
    fig.update_yaxes(title_text='Score (0-100)', row=1, col=1, gridcolor='#f1f5f9', gridwidth=1)
    fig.update_yaxes(title_text='Jumlah Wisman', row=2, col=1, gridcolor='#f1f5f9')
    fig.update_yaxes(title_text='IDR/USD', row=3, col=1, gridcolor='#f1f5f9')
    st.plotly_chart(fig, use_container_width=True)

    # Statistik ringkas
    st.markdown("**📊 Ringkasan Statistik Historis**")
    cA, cB, cC, cD = st.columns(4)
    with cA:
        pct_aman = (predictions['crisis_level'] == 'AMAN').mean() * 100
        st.metric("Bulan Level AMAN",     f"{pct_aman:.1f}%")
    with cB:
        pct_krisis = (predictions['crisis_level'] == 'KRISIS').mean() * 100
        st.metric("Bulan Level KRISIS",   f"{pct_krisis:.1f}%")
    with cC:
        avg_score = predictions['crisis_score_100'].mean()
        st.metric("Rata-rata Crisis Score", f"{avg_score:.1f}")
    with cD:
        max_wisman = predictions['wisman'].max()
        st.metric("Peak Wisman",          f"{max_wisman:,}")

# ─────────────────────────────────────────────
# TAB 2 — ANALISIS DETAIL
# ─────────────────────────────────────────────
with tab2:
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown(f'<div class="section-title">🔍 Komponen Crisis Score — {selected_month}</div>',
                    unsafe_allow_html=True)

        mr_rows = master[master['month'] == selected_month]
        if len(mr_rows) > 0:
            mr = mr_rows.iloc[0]
            comp = {
                'Kunjungan\nWisatawan': safe_float(mr.get('crisis_component_tourism', 0)),
                'Kondisi\nEkonomi':     safe_float(mr.get('crisis_component_economy', 0)),
                'Sentimen\nWisatawan':  safe_float(mr.get('crisis_component_sentiment', 0)),
            }
            bar_colors = [COLOR_MAP.get(level, '#3B82F6')] * 3

            fig_c = go.Figure(go.Bar(
                x=list(comp.keys()),
                y=[v * 100 for v in comp.values()],
                marker_color=['#ef4444', '#f97316', '#3b82f6'],
                marker_line_color='white', marker_line_width=1.5,
                text=[f'{v*100:.1f}%' for v in comp.values()],
                textposition='outside', textfont=dict(size=12, color='#1e293b')
            ))
            fig_c.update_layout(
                yaxis=dict(range=[0, 115], title='Kontribusi (%)', gridcolor='#f1f5f9'),
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                height=280, margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family='Inter', size=11)
            )
            st.plotly_chart(fig_c, use_container_width=True)

        # Tabel indikator
        st.markdown('<div class="section-title">📋 Indikator Detail</div>', unsafe_allow_html=True)
        indicators = {
            'Wisman':         f"{wisman:,} orang",
            'TPK Hotel Bintang': f"{tpk:.1f}%",
            'Kurs USD/IDR':   f"Rp {usd_avg:,.0f}",
            'Inflasi Bali':   f"{inflasi:.2f}%",
            'Sentimen Avg':   f"{sent:+.3f}",
            'Bali Share':     f"{safe_float(row_data.get('bali_share_pct',0)):.1f}%",
            'Z-score Wisman': f"{safe_float(row_data.get('wisman_zscore',0)):.2f}",
            'Anomali IF':     '⚠️ Terdeteksi' if is_anom else '✅ Normal',
            'RF Prediksi':    f"{rf_pred}",
            'RF Confidence':  f"{conf:.0f}%",
        }
        for k, v in indicators.items():
            st.markdown(f'<div class="risk-row"><span class="risk-name">{k}</span>'
                        f'<span class="risk-val">{v}</span></div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-title">📊 Probabilitas Prediksi Random Forest</div>',
                    unsafe_allow_html=True)

        prob_labels = ['AMAN', 'WASPADA', 'SIAGA', 'KRISIS']
        prob_vals   = [safe_float(row_data.get(f'prob_{l.lower()}', 0)) * 100 for l in prob_labels]

        fig_p = go.Figure(go.Bar(
            y=prob_labels, x=prob_vals, orientation='h',
            marker_color=[COLOR_MAP[l] for l in prob_labels],
            marker_line_color='white', marker_line_width=1,
            text=[f'{v:.1f}%' for v in prob_vals], textposition='outside',
            textfont=dict(size=12, color='#1e293b')
        ))
        fig_p.update_layout(
            xaxis=dict(range=[0, 110], title='Probabilitas (%)', gridcolor='#f1f5f9'),
            plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
            height=240, margin=dict(l=0, r=50, t=10, b=0),
            font=dict(family='Inter', size=11)
        )
        st.plotly_chart(fig_p, use_container_width=True)

        st.markdown('<div class="section-title">🌲 Feature Importance — Random Forest</div>',
                    unsafe_allow_html=True)

        try:
            fi = pd.DataFrame({'Fitur': FEATURES, 'Importance': rf_model.feature_importances_})
            fi = fi.sort_values('Importance', ascending=True).tail(8)
            fig_fi = go.Figure(go.Bar(
                x=fi['Importance'], y=fi['Fitur'], orientation='h',
                marker_color='#2563eb', marker_line_color='white',
                text=[f'{v:.3f}' for v in fi['Importance']], textposition='outside',
                textfont=dict(size=10, color='#1e293b')
            ))
            fig_fi.update_layout(
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                height=280, margin=dict(l=0, r=60, t=10, b=0),
                xaxis=dict(range=[0, fi['Importance'].max() * 1.35], gridcolor='#f1f5f9'),
                font=dict(family='Inter', size=10)
            )
            st.plotly_chart(fig_fi, use_container_width=True)
        except Exception:
            st.info("Feature importance tidak tersedia.")

# ─────────────────────────────────────────────
# TAB 3 — SENTIMEN MULTIBAHASA
# ─────────────────────────────────────────────
with tab3:
    col_s1, col_s2 = st.columns([2, 1])

    with col_s1:
        st.markdown('<div class="section-title">📈 Tren Sentimen Wisatawan Bulanan</div>',
                    unsafe_allow_html=True)

        if 'avg_sentiment_monthly' in master.columns:
            months_dt_m = pd.to_datetime(master['month'].astype(str))
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(
                x=months_dt_m, y=master['avg_sentiment_monthly'],
                mode='lines+markers', name='Avg Sentiment',
                line=dict(color='#059669', width=2),
                marker=dict(size=4, color='#059669'),
                fill='tozeroy', fillcolor='rgba(5,150,105,0.08)'
            ))
            fig_s.add_hline(y=0, line_dash='dash', line_color='#94a3b8', line_width=1)
            fig_s.add_vrect(x0='2020-03-01', x1='2021-12-01',
                fillcolor='rgba(220,38,38,0.08)', line_width=0,
                annotation_text='COVID', annotation_font_color='#dc2626')
            fig_s.add_vline(x=selected_dt, line_dash='dot', line_color='#2563eb', line_width=1.5)
            fig_s.update_layout(
                yaxis_title='Rata-rata Sentimen (-1 → +1)',
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family='Inter', size=11),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("Kolom `avg_sentiment_monthly` tidak ditemukan di master dataset.")

        # Tren sentimen 6 bulan terakhir
        st.markdown('<div class="section-title">📊 Sentimen 6 Bulan Terakhir</div>',
                    unsafe_allow_html=True)
        if 'avg_sentiment_monthly' in predictions.columns:
            last6 = predictions.tail(6)[['month','avg_sentiment_monthly','crisis_level']].copy()
            last6['warna'] = last6['avg_sentiment_monthly'].apply(
                lambda x: '#059669' if x > 0.1 else ('#dc2626' if x < -0.1 else '#d97706'))
            fig_6 = go.Figure(go.Bar(
                x=last6['month'], y=last6['avg_sentiment_monthly'],
                marker_color=last6['warna'],
                text=[f'{v:+.3f}' for v in last6['avg_sentiment_monthly']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Sentimen: %{y:.3f}<extra></extra>'
            ))
            fig_6.add_hline(y=0, line_dash='dash', line_color='#94a3b8', line_width=1)
            fig_6.update_layout(
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                height=200, margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_6, use_container_width=True)

    with col_s2:
        st.markdown('<div class="section-title">🎯 Gauge Sentimen</div>',
                    unsafe_allow_html=True)

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=sent,
            delta={'reference': 0, 'valueformat': '.3f'},
            number={'valueformat': '+.3f', 'font': {'size': 26}},
            title={'text': "Sentimen Bulan Ini", 'font': {'size': 13}},
            gauge={
                'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': '#94a3b8'},
                'bar': {'color': '#059669' if sent >= 0 else '#dc2626', 'thickness': 0.25},
                'bgcolor': 'white',
                'borderwidth': 0,
                'steps': [
                    {'range': [-1, -0.3], 'color': '#fee2e2'},
                    {'range': [-0.3, 0.3], 'color': '#fef9c3'},
                    {'range': [0.3, 1],   'color': '#dcfce7'}
                ],
                'threshold': {
                    'line': {'color': '#1e293b', 'width': 2},
                    'thickness': 0.8, 'value': sent
                }
            }
        ))
        fig_gauge.update_layout(
            height=220, margin=dict(l=20, r=20, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter')
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        pct_neg = safe_float(row_data.get('pct_negative_monthly', 0))
        pct_pos = 100 - pct_neg

        st.metric("% Review Positif",  f"{pct_pos:.1f}%",
                  "↑ Baik" if pct_pos > 60 else "↓ Perlu perhatian")
        st.metric("% Review Negatif",  f"{pct_neg:.1f}%",
                  "↓ Rendah" if pct_neg < 30 else "↑ Tinggi")
        st.metric("Sentimen vs 0 (netral)", f"{sent:+.3f}",
                  "Positif" if sent >= 0 else "Negatif")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#f0f9ff;border-radius:10px;padding:12px 14px;font-size:12px;color:#0369a1'>
            <b>ℹ️ Interpretasi Sentimen</b><br><br>
            <b>-1.0 hingga -0.3</b> → Sentimen sangat negatif<br>
            <b>-0.3 hingga +0.3</b> → Sentimen netral<br>
            <b>+0.3 hingga +1.0</b> → Sentimen positif<br><br>
            Model: XLM-RoBERTa (EN/ID/ZH)
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 4 — PREDIKSI EARLY WARNING ⭐ (BARU)
# ─────────────────────────────────────────────
with tab4:
    st.markdown("""
    <div style='background:linear-gradient(90deg,#1e3a5f,#1d4ed8);border-radius:12px;
                padding:16px 22px;margin-bottom:20px;color:white'>
        <div style='font-size:13px;font-weight:700;opacity:0.7;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:4px'>EARLY WARNING PREDICTION ENGINE</div>
        <div style='font-size:14px;opacity:0.9;line-height:1.6'>
            Modul prediksi ini menggunakan <b>Random Forest + Isolation Forest + trend ekstrapolasi</b>
            untuk memproyeksikan kondisi pariwisata Bali ke depan dan menganalisis skenario risiko.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_pred_l, col_pred_r = st.columns([1, 1])

    with col_pred_l:
        # ── 3-Bulan Forecast ──
        st.markdown('<div class="section-title">📅 Proyeksi 3 Bulan ke Depan</div>',
                    unsafe_allow_html=True)

        forecast = predict_next_months(predictions, rf_model, scaler, le, n=3)

        for fc in forecast:
            lv = fc['proj_level']
            trend_icon = "↗" if fc['trend_per_month'] > 0 else "↘"
            trend_color = "#dc2626" if fc['trend_per_month'] > 0 else "#16a34a"
            st.markdown(f"""
            <div style='background:white;border-radius:12px;padding:16px 18px;
                        margin-bottom:10px;border-left:4px solid {COLOR_MAP.get(lv,"#3b82f6")};
                        box-shadow:0 1px 4px rgba(0,0,0,0.07)'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <div style='font-size:11px;font-weight:600;color:#94a3b8;
                                    text-transform:uppercase;margin-bottom:4px'>{fc["month"]}</div>
                        <div style='font-size:22px;font-weight:800;
                                    color:{COLOR_MAP.get(lv,"#3b82f6")}'>{EMOJI_MAP.get(lv,"")} {lv}</div>
                        <div style='font-size:12px;color:#64748b;margin-top:3px'>
                            Crisis Score: <b>{fc["proj_score"]}</b>/100
                        </div>
                    </div>
                    <div style='text-align:right'>
                        <div style='font-size:24px;font-weight:800;color:{trend_color}'>{trend_icon}</div>
                        <div style='font-size:11px;color:#94a3b8'>Confidence</div>
                        <div style='font-size:16px;font-weight:700;color:#1e293b'>{fc["confidence"]:.0f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Disclaimer proyeksi
        st.markdown("""
        <div style='background:#fefce8;border-radius:8px;padding:10px 14px;
                    font-size:11px;color:#713f12;border:1px solid #fef08a'>
            ⚠️ <b>Catatan:</b> Proyeksi didasarkan pada tren historis dan model ML.
            Faktor eksternal tak terduga (bencana, pandemi, krisis geopolitik)
            tidak tercakup dalam model. Confidence menurun seiring jarak proyeksi.
        </div>
        """, unsafe_allow_html=True)

        # ── Trend Chart ──
        st.markdown('<br><div class="section-title">📈 Tren Crisis Score + Proyeksi</div>',
                    unsafe_allow_html=True)

        last_12 = predictions.tail(12).copy()
        last_12_dt = pd.to_datetime(last_12['month'].astype(str))
        fc_months = pd.to_datetime([f['month'] for f in forecast])
        fc_scores = [f['proj_score'] for f in forecast]

        # Confidence interval (±10% for illustration)
        fc_upper = [min(100, s + 8) for s in fc_scores]
        fc_lower = [max(0, s - 8) for s in fc_scores]

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=last_12_dt, y=last_12['crisis_score_100'],
            mode='lines+markers', name='Historis',
            line=dict(color='#2563eb', width=2),
            marker=dict(size=5)
        ))
        fig_fc.add_trace(go.Scatter(
            x=fc_months, y=fc_scores,
            mode='lines+markers', name='Proyeksi',
            line=dict(color='#ea580c', width=2, dash='dash'),
            marker=dict(size=7, symbol='diamond')
        ))
        fig_fc.add_trace(go.Scatter(
            x=list(fc_months) + list(fc_months[::-1]),
            y=fc_upper + fc_lower[::-1],
            fill='toself', fillcolor='rgba(234,88,12,0.10)',
            line=dict(width=0), name='Interval Kepercayaan',
            showlegend=True
        ))
        for thr, lbl, col in [(70,'KRISIS','#dc2626'), (50,'SIAGA','#ea580c'), (30,'WASPADA','#d97706')]:
            fig_fc.add_hline(y=thr, line_dash='dot', line_color=col,
                             line_width=0.8, opacity=0.6,
                             annotation_text=lbl, annotation_position='right',
                             annotation_font_size=9)
        fig_fc.update_layout(
            yaxis=dict(range=[0, 100], title='Crisis Score', gridcolor='#f1f5f9'),
            plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
            height=280, margin=dict(l=0, r=60, t=10, b=0),
            legend=dict(orientation='h', yanchor='bottom', y=1.01, x=0),
            font=dict(family='Inter', size=11)
        )
        st.plotly_chart(fig_fc, use_container_width=True)

    with col_pred_r:
        # ── Scenario Simulator ──
        st.markdown('<div class="section-title">🎛️ Simulator Skenario Risiko</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#f0f9ff;border-radius:8px;padding:10px 14px;
                    font-size:12px;color:#0369a1;margin-bottom:14px'>
            Geser slider untuk mensimulasikan bagaimana perubahan indikator
            mempengaruhi Crisis Score secara real-time.
        </div>
        """, unsafe_allow_html=True)

        wisman_delta = st.slider(
            "📉 Perubahan Jumlah Wisman (%)",
            min_value=-80, max_value=50, value=0, step=5,
            help="Negatif = penurunan wisatawan → meningkatkan risiko krisis"
        )
        usd_delta = st.slider(
            "💱 Perubahan Kurs USD/IDR (%)",
            min_value=-10, max_value=30, value=0, step=1,
            help="Positif = IDR melemah → meningkatkan tekanan ekonomi"
        )
        sent_delta = st.slider(
            "💬 Perubahan Sentimen Wisatawan",
            min_value=-1.0, max_value=1.0, value=0.0, step=0.1,
            help="Positif = sentimen membaik → menurunkan risiko krisis"
        )

        sim_score = simulate_crisis_score(dict(row_data), wisman_delta, usd_delta, sent_delta)
        sim_level = level_from_score(sim_score)
        score_delta = sim_score - score
        delta_icon = "↑" if score_delta > 0 else "↓"
        delta_color = "#dc2626" if score_delta > 0 else "#16a34a"

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1e3a5f,#1d4ed8);
                    border-radius:14px;padding:22px;margin:14px 0;color:white;text-align:center'>
            <div style='font-size:11px;font-weight:600;opacity:0.65;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>
                HASIL SIMULASI
            </div>
            <div style='font-size:38px;font-weight:800;margin-bottom:4px'>{sim_score}</div>
            <div style='font-size:13px;opacity:0.75;margin-bottom:10px'>Crisis Score / 100</div>
            <div style='background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;
                        display:inline-block;font-size:16px;font-weight:700'>
                {EMOJI_MAP.get(sim_level,"")} {sim_level}
            </div>
            <div style='margin-top:10px;font-size:12px;opacity:0.7'>
                Dari {score:.1f} 
                <span style="color:{"#fca5a5" if score_delta > 0 else "#86efac"}">
                    {delta_icon} {abs(score_delta):.1f} poin
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Risk breakdown simulasi
        st.markdown('<div class="section-title">⚠️ Breakdown Risiko Simulasi</div>',
                    unsafe_allow_html=True)

        risk_items = [
            ("Risiko Penurunan Wisman",
             "Tinggi" if wisman_delta < -20 else ("Sedang" if wisman_delta < 0 else "Rendah"),
             "#dc2626" if wisman_delta < -20 else ("#d97706" if wisman_delta < 0 else "#16a34a")),
            ("Risiko Tekanan Kurs",
             "Tinggi" if usd_delta > 10 else ("Sedang" if usd_delta > 3 else "Rendah"),
             "#dc2626" if usd_delta > 10 else ("#d97706" if usd_delta > 3 else "#16a34a")),
            ("Risiko Sentimen Negatif",
             "Tinggi" if sent_delta < -0.3 else ("Sedang" if sent_delta < 0 else "Rendah"),
             "#dc2626" if sent_delta < -0.3 else ("#d97706" if sent_delta < 0 else "#16a34a")),
        ]
        for name, status, color in risk_items:
            st.markdown(f"""
            <div class="risk-row">
                <span class="risk-name">{name}</span>
                <span style='color:{color};font-weight:700;font-size:12px'>{status}</span>
            </div>
            """, unsafe_allow_html=True)

        # ── Rekomendasi Kebijakan ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📋 Rekomendasi Kebijakan — Level {sim_level}</div>',
                    unsafe_allow_html=True)

        for i, rec in enumerate(ADVICE_MAP.get(sim_level, []), 1):
            st.markdown(f"""
            <div style='background:white;border-radius:8px;padding:10px 14px;
                        margin-bottom:8px;border-left:3px solid {COLOR_MAP.get(sim_level,"#3b82f6")};
                        font-size:13px;color:#374151;box-shadow:0 1px 3px rgba(0,0,0,0.06)'>
                <span style='font-weight:700;color:{COLOR_MAP.get(sim_level,"#3b82f6")}'>{i}.</span> {rec}
            </div>
            """, unsafe_allow_html=True)

        # ── Matriks Risiko ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🗺️ Peta Risiko Historis</div>',
                    unsafe_allow_html=True)

        if 'wisman_growth_mom' in predictions.columns and 'avg_sentiment_monthly' in predictions.columns:
            fig_risk = go.Figure()
            for lv in ['AMAN', 'WASPADA', 'SIAGA', 'KRISIS']:
                mask = predictions['crisis_level'] == lv
                if mask.sum() > 0:
                    fig_risk.add_trace(go.Scatter(
                        x=predictions.loc[mask, 'wisman_growth_mom'] * 100,
                        y=predictions.loc[mask, 'avg_sentiment_monthly'],
                        mode='markers', name=lv,
                        marker=dict(color=COLOR_MAP[lv], size=7,
                                    line=dict(width=1, color='white')),
                        hovertemplate=(f'<b>{lv}</b><br>'
                                       'Growth: %{x:.1f}%<br>'
                                       'Sentimen: %{y:.3f}<extra></extra>')
                    ))
            fig_risk.add_hline(y=0, line_dash='dash', line_color='#94a3b8', line_width=0.8)
            fig_risk.add_vline(x=0, line_dash='dash', line_color='#94a3b8', line_width=0.8)
            fig_risk.update_layout(
                xaxis_title='Wisman Growth MoM (%)',
                yaxis_title='Avg Sentimen',
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                height=260, margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation='h', yanchor='bottom', y=1.01, x=0, font_size=10),
                font=dict(family='Inter', size=11),
                xaxis=dict(gridcolor='#f1f5f9'),
                yaxis=dict(gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_risk, use_container_width=True)

# ─────────────────────────────────────────────
# TAB 5 — NARASI AI
# ─────────────────────────────────────────────
with tab5:
    st.markdown("""
    <div style='background:linear-gradient(90deg,#064e3b,#065f46);border-radius:12px;
                padding:16px 22px;margin-bottom:20px;color:white'>
        <div style='font-size:13px;font-weight:700;opacity:0.7;text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:4px'>AI NARRATIVE ENGINE</div>
        <div style='font-size:14px;opacity:0.9;line-height:1.6'>
            Menggunakan <b>Groq LLM (llama-3.3-70b-versatile)</b> untuk mengubah seluruh output model
            menjadi laporan naratif otomatis Bahasa Indonesia yang siap dibaca pemangku kebijakan.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_rt, col_btn = st.columns([1, 1])
    with col_rt:
        report_type = st.radio(
            "Tipe Laporan", ['summary', 'alert', 'monthly'],
            captions=['2-3 kalimat ringkas', 'Peringatan darurat (max 120 kata)', 'Laporan lengkap 4 bagian'],
            horizontal=False
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if not groq_key:
            st.warning("💡 Masukkan Groq API Key di sidebar untuk mengaktifkan narasi AI.")
            st.caption("[Dapatkan key gratis →](https://console.groq.com/keys)")
        else:
            if selected_month in narratives_cache:
                cached = narratives_cache[selected_month]
                st.success(f"💾 Narasi tersedia di cache — {cached.get('crisis_level','')} — {cached.get('month','')}")

        generate_btn = st.button("🚀 Generate Narasi", type="primary", use_container_width=True,
                                 disabled=not bool(groq_key))

    st.markdown("<br>", unsafe_allow_html=True)

    # Tampilkan cache jika ada & belum tekan generate
    if selected_month in narratives_cache and not generate_btn:
        cached_narr = narratives_cache[selected_month]
        st.markdown(f'<div class="narrative-box">{cached_narr["narrative"]}</div>',
                    unsafe_allow_html=True)
        st.caption(f"📦 Dari cache · Level: {cached_narr.get('crisis_level','')} · Periode: {cached_narr.get('month','')}")

    if generate_btn and groq_key:
        with st.spinner("🤖 BaliGuard Narrative Engine sedang menganalisis..."):
            try:
                sys.path.insert(0, '.')
                from src.narrative_engine import generate, build_context

                idx = list(predictions['month']).index(selected_month)
                history = predictions.iloc[max(0, idx - 3):idx].to_dict('records')
                row_dict = dict(row_data)

                result = generate(row_dict, report_type, groq_key, history)

                if result['success']:
                    st.success(f"✅ Laporan berhasil dibuat ({result.get('tokens', 0)} tokens)")
                    st.markdown(f'<div class="narrative-box">{result["narrative"]}</div>',
                                unsafe_allow_html=True)

                    # Simpan ke cache lokal
                    narratives_cache[selected_month] = result
                    os.makedirs('data/final', exist_ok=True)
                    with open('data/final/narratives_cache.json', 'w', encoding='utf-8') as f:
                        json.dump(narratives_cache, f, ensure_ascii=False, indent=2)
                else:
                    st.error(f"❌ Gagal: {result.get('error', 'Unknown error')}")
            except ImportError:
                st.error("❌ `src/narrative_engine.py` tidak ditemukan. Jalankan NB06 terlebih dahulu.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Info tentang model
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("ℹ️ Tentang Groq Narrative Engine"):
        st.markdown("""
        **Model:** llama-3.3-70b-versatile via Groq API (latency < 1 detik)

        **Tipe Laporan:**
        - **summary** — Ringkasan 2-3 kalimat, cocok untuk KPI card atau notifikasi cepat
        - **alert** — Peringatan darurat max 120 kata dengan top-3 indikator kritis dan rekomendasi tindakan
        - **monthly** — Laporan lengkap 4 bagian: Ringkasan Eksekutif, Analisis Indikator, Faktor Pendorong, Rekomendasi

        **Data yang dikirim ke LLM:**
        Crisis Score, Level, RF Prediction, Anomali, Wisman, TPK, USD/IDR, Inflasi, Sentimen, dan histori 3 bulan terakhir

        **Privacy:** API request dikirim langsung ke Groq. Tidak ada data yang disimpan oleh pihak ketiga selain Groq.
        """)

# ══════════════════════════════════════════════════════════
# DATA TABLE (Expander)
# ══════════════════════════════════════════════════════════
st.divider()
with st.expander("📋 Tabel Data Prediksi Lengkap", expanded=False):
    display_cols = [
        'month', 'wisman', 'tpk_bintang', 'inflasi_processed',
        'usd_idr_avg', 'avg_sentiment_monthly', 'bali_share_pct',
        'wisman_zscore', 'crisis_score_100', 'crisis_level',
        'rf_predicted_level', 'rf_confidence', 'iso_anomaly'
    ]
    display_cols = [c for c in display_cols if c in predictions.columns]

    def highlight_row(row):
        bg = {'AMAN': '#f0fdf4', 'WASPADA': '#fefce8', 'SIAGA': '#fff7ed', 'KRISIS': '#fef2f2'}
        c = bg.get(row.get('crisis_level', ''), '')
        return [f'background-color: {c}'] * len(row)

    st.dataframe(
        predictions[display_cols].style.apply(highlight_row, axis=1),
        use_container_width=True, height=400
    )
    st.download_button(
        "⬇️ Download CSV",
        predictions[display_cols].to_csv(index=False),
        file_name=f"baliguard_predictions_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ══════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center;padding:18px 0 8px;color:#94a3b8;font-size:11px;line-height:2'>
    🛡️ <b style='color:#1e3a5f'>BaliGuard</b> — Dashboard Early Warning System Pariwisata Berbasis
    Multi-Sumber Data, Machine Learning &amp; Analisis Sentimen<br>
    <span style='font-size:10px'>
        Data: BPS Bali · Bank Indonesia · Google Hotels Review &nbsp;|&nbsp;
        Model: Isolation Forest + Random Forest + XLM-RoBERTa &nbsp;|&nbsp;
        Narasi: Groq LLM (llama-3.3-70b-versatile)
    </span>
</div>
""", unsafe_allow_html=True)
