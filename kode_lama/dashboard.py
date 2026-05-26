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

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BaliGuard — Early Warning Pariwisata",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.block-container { padding-top: 1.5rem; }
.kpi-card {
    background: white; border-radius: 12px; padding: 20px;
    border-left: 5px solid #378ADD;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 8px;
}
.kpi-label { font-size: 12px; color: #888; font-weight: 500;
             text-transform: uppercase; letter-spacing:.05em; }
.kpi-value { font-size: 26px; font-weight: 700; color: #1a1a2e; margin: 4px 0 0; }
.kpi-sub   { font-size: 12px; color: #666; margin-top: 4px; }
.level-AMAN    { border-left-color: #639922 !important; }
.level-WASPADA { border-left-color: #EF9F27 !important; }
.level-SIAGA   { border-left-color: #E24B4A !important; }
.level-KRISIS  { border-left-color: #A32D2D !important; background: #fff5f5 !important; }
.narrative-box {
    background: white; border-radius: 12px; padding: 20px;
    border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    line-height: 1.8; white-space: pre-wrap; font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
COLOR_MAP = {
    'AMAN':    '#639922',
    'WASPADA': '#EF9F27',
    'SIAGA':   '#E24B4A',
    'KRISIS':  '#A32D2D'
}
EMOJI_MAP = {'AMAN': '🟢', 'WASPADA': '🟡', 'SIAGA': '🟠', 'KRISIS': '🔴'}
FEATURES = [
    'wisman_growth_mom','wisman_growth_yoy','wisman_zscore',
    'usd_idr_avg','usd_volatility_3m','usd_change_mom',
    'tpk_bintang','tpk_change_mom','inflasi_processed',
    'bali_share_pct','avg_sentiment_monthly','month_num','is_peak_season'
]

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
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
except Exception as e:
    st.error(f"❌ Error loading data/model: {e}")
    st.info("Pastikan NB05 dan NB06 sudah dijalankan dan semua file ada di data/final/ dan data/models/")
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌴 BaliGuard")
    st.markdown("*Early Warning System Krisis Pariwisata Bali*")
    st.divider()

    available_months = sorted(predictions['month'].unique(), reverse=True)
    selected_month   = st.selectbox("📅 Pilih Bulan Analisis", available_months)

    st.divider()
    st.markdown("**🤖 LLM Narrative Engine**")
    api_key_input = st.text_input(
        "Anthropic API Key", type="password",
        placeholder="sk-ant-...",
        help="Dapatkan di console.anthropic.com"
    )

    st.divider()
    st.markdown("**Tentang**")
    st.caption(
        "Data: BPS Bali · BI · Google Hotels  \n"
        "Model: Isolation Forest + Random Forest  \n"
        "Sentimen: XLM-RoBERTa  \n"
        "Narasi: Claude claude-sonnet-4-5"
    )

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_row(month_str):
    row = predictions[predictions['month'] == month_str]
    return row.iloc[0] if len(row) else predictions.iloc[-1]

def kpi_card(label, value, sub="", level=None):
    cls = f"kpi-card level-{level}" if level else "kpi-card"
    return (f'<div class="{cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>')

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("# 🌴 BaliGuard — Dashboard Early Warning Krisis Pariwisata Bali")
st.markdown(f"**Bulan analisis: {selected_month}** &nbsp;|&nbsp; Periode data: 2009–2024 &nbsp;|&nbsp; 178 observasi bulanan")
st.divider()

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
row_data = get_row(selected_month)
level    = str(row_data['crisis_level'])
score    = float(row_data['crisis_score_100'])
wisman   = int(row_data['wisman'])
tpk      = float(row_data.get('tpk_bintang', 0))
conf     = float(row_data.get('rf_confidence', 0)) * 100
is_anom  = int(row_data.get('iso_anomaly', 0))
rf_pred  = str(row_data.get('rf_predicted_level', 'N/A'))
sent     = float(row_data.get('avg_sentiment_monthly', 0))

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(kpi_card("LEVEL KRISIS",
        f"{EMOJI_MAP.get(level,'')} {level}",
        f"RF Prediksi: {rf_pred}", level), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("CRISIS SCORE",
        f"{score:.1f}/100",
        f"Confidence: {conf:.0f}%"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card("WISMAN",
        f"{wisman:,}",
        "Wisatawan mancanegara"), unsafe_allow_html=True)
with col4:
    st.markdown(kpi_card("TPK HOTEL BINTANG",
        f"{tpk:.1f}%",
        "Tingkat hunian kamar"), unsafe_allow_html=True)
with col5:
    anom_txt = "⚠️ Terdeteksi" if is_anom else "✅ Normal"
    st.markdown(kpi_card("ANOMALI (IF)",
        anom_txt, "Isolation Forest"), unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────
# CRISIS TIMELINE
# ─────────────────────────────────────────────
st.subheader("📈 Timeline Crisis Score (2009–2024)")

months_dt  = pd.to_datetime(predictions['month'].astype(str))
selected_dt = pd.to_datetime(selected_month)

fig = make_subplots(rows=2, cols=1,
    subplot_titles=('Crisis Score + Level', 'Kunjungan Wisatawan Mancanegara'),
    vertical_spacing=0.12, row_heights=[0.55, 0.45])

# Crisis score line
fig.add_trace(go.Scatter(x=months_dt, y=predictions['crisis_score_100'],
    mode='lines', name='Crisis Score',
    line=dict(color='#854F0B', width=1.5),
    fill='tozeroy', fillcolor='rgba(133,79,11,0.08)'), row=1, col=1)

# Level scatter
for lvl, color in COLOR_MAP.items():
    mask = predictions['crisis_level'] == lvl
    fig.add_trace(go.Scatter(x=months_dt[mask],
        y=predictions['crisis_score_100'][mask],
        mode='markers', name=lvl,
        marker=dict(color=color, size=6),
        hovertemplate=f'<b>{lvl}</b><br>%{{x}}<br>Score: %{{y:.1f}}<extra></extra>'),
        row=1, col=1)

# Threshold lines
for thr, lbl, col in [(70,'KRISIS','#A32D2D'),(50,'SIAGA','#E24B4A'),(30,'WASPADA','#EF9F27')]:
    fig.add_hline(y=thr, line_dash='dash', line_color=col,
                  line_width=0.8, opacity=0.6, row=1, col=1,
                  annotation_text=lbl, annotation_position='right')

fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
    fillcolor='rgba(226,75,74,0.10)', line_width=0,
    annotation_text='COVID', annotation_position='top left', row=1, col=1)
fig.add_vline(x=selected_dt, line_dash='dot', line_color='#185FA5',
              line_width=1.5, row=1, col=1)

# Wisman
fig.add_trace(go.Scatter(x=months_dt, y=predictions['wisman'],
    mode='lines', name='Wisman', showlegend=False,
    line=dict(color='steelblue', width=1.5),
    fill='tozeroy', fillcolor='rgba(70,130,180,0.12)'), row=2, col=1)
fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
    fillcolor='rgba(226,75,74,0.10)', line_width=0, row=2, col=1)
fig.add_vline(x=selected_dt, line_dash='dot', line_color='#185FA5',
              line_width=1.5, row=2, col=1)

fig.update_layout(height=500, showlegend=True,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    plot_bgcolor='white', paper_bgcolor='white',
    margin=dict(l=0, r=80, t=60, b=0))
fig.update_yaxes(title_text='Score (0-100)', row=1, col=1, gridcolor='#f0f0f0')
fig.update_yaxes(title_text='Jumlah Wisman', row=2, col=1, gridcolor='#f0f0f0')
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# DETAIL & PROBABILITAS
# ─────────────────────────────────────────────
st.divider()
col_l, col_r = st.columns(2)

with col_l:
    st.subheader(f"🔍 Detail: {selected_month}")

    mr = master[master['month'] == selected_month]
    if len(mr) > 0:
        mr = mr.iloc[0]
        comp = {
            'Tourism' : float(mr.get('crisis_component_tourism', 0)),
            'Economy' : float(mr.get('crisis_component_economy', 0)),
            'Sentiment': float(mr.get('crisis_component_sentiment', 0)),
        }
        fig_c = go.Figure(go.Bar(
            x=list(comp.keys()),
            y=[v*100 for v in comp.values()],
            marker_color=['#E24B4A','#EF9F27','#378ADD'],
            text=[f'{v*100:.1f}%' for v in comp.values()],
            textposition='outside'
        ))
        fig_c.update_layout(title='Komponen Crisis Score', yaxis_title='Kontribusi (%)',
            plot_bgcolor='white', paper_bgcolor='white',
            height=260, margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_c, use_container_width=True)

    indicators = {
        'Wisman'       : f"{wisman:,}",
        'TPK Bintang'  : f"{tpk:.1f}%",
        'USD/IDR'      : f"Rp {float(row_data.get('usd_idr_avg',0)):,.0f}",
        'Inflasi'      : f"{float(row_data.get('inflasi_processed',0)):.2f}%",
        'Sentimen'     : f"{sent:.3f}",
        'Bali Share'   : f"{float(row_data.get('bali_share_pct',0)):.1f}%",
        'Anomali IF'   : '⚠️ Ya' if is_anom else '✅ Tidak',
    }
    st.dataframe(pd.DataFrame(list(indicators.items()), columns=['Indikator','Nilai']),
                 use_container_width=True, hide_index=True)

with col_r:
    st.subheader("📊 Probabilitas RF")

    prob_labels = ['AMAN','WASPADA','SIAGA','KRISIS']
    prob_vals   = [float(row_data.get(f'prob_{l.lower()}', 0))*100 for l in prob_labels]
    fig_p = go.Figure(go.Bar(
        y=prob_labels, x=prob_vals, orientation='h',
        marker_color=[COLOR_MAP[l] for l in prob_labels],
        text=[f'{v:.1f}%' for v in prob_vals], textposition='outside'
    ))
    fig_p.update_layout(title='Probabilitas Prediksi Random Forest',
        xaxis=dict(range=[0,105]), xaxis_title='Probabilitas (%)',
        plot_bgcolor='white', paper_bgcolor='white',
        height=260, margin=dict(l=0,r=40,t=40,b=0))
    st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("**Top 5 Fitur Terpenting**")
    fi = pd.DataFrame({'Fitur': FEATURES, 'Importance': rf_model.feature_importances_})
    fi = fi.sort_values('Importance', ascending=False).head(5)
    fig_fi = go.Figure(go.Bar(
        x=fi['Importance'], y=fi['Fitur'], orientation='h',
        marker_color='#185FA5',
        text=[f'{v:.3f}' for v in fi['Importance']], textposition='outside'
    ))
    fig_fi.update_layout(title='Feature Importance (RF)',
        plot_bgcolor='white', paper_bgcolor='white',
        height=220, margin=dict(l=0,r=50,t=40,b=0),
        xaxis=dict(range=[0, fi['Importance'].max()*1.3]))
    st.plotly_chart(fig_fi, use_container_width=True)

# ─────────────────────────────────────────────
# SENTIMEN
# ─────────────────────────────────────────────
st.divider()
st.subheader("💬 Sentimen Wisatawan")

col_s1, col_s2 = st.columns([1.5, 1])
with col_s1:
    months_dt_m = pd.to_datetime(master['month'].astype(str))
    fig_s = go.Figure()
    fig_s.add_trace(go.Scatter(x=months_dt_m, y=master['avg_sentiment_monthly'],
        mode='lines+markers', name='Avg Sentiment',
        line=dict(color='#1D9E75', width=1.5), marker=dict(size=3),
        fill='tozeroy', fillcolor='rgba(29,158,117,0.08)'))
    fig_s.add_hline(y=0, line_dash='dash', line_color='gray', line_width=0.8)
    fig_s.add_vrect(x0='2020-03-01', x1='2021-12-01',
        fillcolor='rgba(226,75,74,0.10)', line_width=0, annotation_text='COVID')
    fig_s.add_vline(x=selected_dt, line_dash='dot', line_color='#185FA5', line_width=1.5)
    fig_s.update_layout(title='Rata-rata Sentimen Bulanan (-1 negatif → +1 positif)',
        yaxis_title='Avg Sentiment', plot_bgcolor='white', paper_bgcolor='white',
        height=300, margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_s, use_container_width=True)

with col_s2:
    pct_neg = float(row_data.get('pct_negative_monthly', 0))
    st.metric("Avg Sentiment Bulan Ini", f"{sent:.3f}",
              "Positif" if sent > 0 else "Negatif")
    st.metric("% Review Negatif", f"{pct_neg:.1f}%",
              "Lebih baik" if pct_neg < 30 else "Perlu perhatian")
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=sent,
        title={'text': "Sentiment Score"},
        gauge={'axis': {'range': [-1,1]},
               'bar': {'color': '#1D9E75' if sent > 0 else '#E24B4A'},
               'steps': [
                   {'range': [-1,-0.3], 'color': '#FCEBEB'},
                   {'range': [-0.3,0.3], 'color': '#FAEEDA'},
                   {'range': [0.3,1],   'color': '#EAF3DE'}
               ]}
    ))
    fig_g.update_layout(height=200, margin=dict(l=20,r=20,t=40,b=0))
    st.plotly_chart(fig_g, use_container_width=True)

# ─────────────────────────────────────────────
# LLM NARRATIVE ENGINE
# ─────────────────────────────────────────────
st.divider()
st.subheader("🤖 Laporan Naratif AI — BaliGuard Narrative Engine")

col_rt, col_btn, col_info = st.columns([1, 1, 2])
with col_rt:
    report_type = st.radio("Tipe Laporan",
        ['summary', 'alert', 'monthly'], horizontal=False,
        help="summary: 2-3 kalimat | alert: peringatan darurat | monthly: laporan lengkap")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
with col_info:
    if not api_key_input:
        st.info("💡 Masukkan Anthropic API key di sidebar untuk mengaktifkan fitur ini")
    else:
        # Cek apakah ada cache untuk bulan ini
        if selected_month in narratives_cache:
            cached = narratives_cache[selected_month]
            st.success(f"💾 Narasi tersedia di cache ({cached.get('crisis_level','')}, {cached.get('report_type','monthly')})")

# Tampilkan cache jika ada
if selected_month in narratives_cache and not generate_btn:
    cached_narr = narratives_cache[selected_month]
    st.markdown(f'<div class="narrative-box">{cached_narr["narrative"]}</div>',
                unsafe_allow_html=True)
    st.caption(f"📦 Dari cache · {cached_narr.get('crisis_level','')} · {cached_narr.get('month','')}")

if generate_btn:
    if not api_key_input:
        st.warning("⚠️ API key belum diisi. Masukkan di sidebar kiri.")
    else:
        with st.spinner("🤖 BaliGuard sedang menganalisis dan membuat laporan..."):
            try:
                sys.path.insert(0, '.')
                from src.narrative_engine import generate, build_context

                idx = list(predictions['month']).index(selected_month)
                history = predictions.iloc[max(0, idx-3):idx].to_dict('records')
                row_dict = dict(row_data)

                result = generate(row_dict, report_type, api_key_input, history)

                if result['success']:
                    st.success(f"✅ Laporan berhasil digenerate ({result.get('tokens',0)} tokens)")
                    st.markdown(f'<div class="narrative-box">{result["narrative"]}</div>',
                                unsafe_allow_html=True)
                else:
                    st.error(f"❌ {result.get('error','Unknown error')}")
            except ImportError:
                st.error("❌ src/narrative_engine.py tidak ditemukan. Jalankan NB06 dulu.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ─────────────────────────────────────────────
# DATA TABLE
# ─────────────────────────────────────────────
st.divider()
with st.expander("📋 Tabel Data Lengkap", expanded=False):
    display_cols = ['month','wisman','tpk_bintang','inflasi_processed',
                    'usd_idr_avg','avg_sentiment_monthly','bali_share_pct',
                    'crisis_score_100','crisis_level','rf_predicted_level',
                    'rf_confidence','iso_anomaly']
    display_cols = [c for c in display_cols if c in predictions.columns]

    def highlight(row):
        colors = {'AMAN':'#f0f7e8','WASPADA':'#fef9ec',
                  'SIAGA':'#fef0ee','KRISIS':'#fce8e8'}
        c = colors.get(row.get('crisis_level',''),'')
        return [f'background-color: {c}']*len(row)

    st.dataframe(
        predictions[display_cols].style.apply(highlight, axis=1),
        use_container_width=True, height=400
    )

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:12px;padding:10px 0'>"
    "🌴 <b>BaliGuard</b> — Early Warning System Krisis Pariwisata Bali<br>"
    "Data: BPS Bali · Bank Indonesia · Google Hotels Review &nbsp;|&nbsp; "
    "Model: Isolation Forest + Random Forest + XLM-RoBERTa &nbsp;|&nbsp; "
    "Narasi: Claude claude-sonnet-4-5"
    "</div>",
    unsafe_allow_html=True
)
