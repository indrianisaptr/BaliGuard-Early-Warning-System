"""
src/pages/analisis.py — BaliGuard: Analisis Detail
Semua variabel tersedia via ctx dict dari src/shared.build_context()
"""
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json, os, time, requests
from datetime import datetime

from src.utils import (
    sf, _tick, kpi_html, alert_html, status_dot,
    LEVEL_COLORS, LABEL_ORDER,
    FEATURES_CORE, FEATURES_LAG,
)


def render(ctx: dict) -> None:
    """Render halaman Analisis Detail."""
    # ── Unpack ctx ────────────────────────────────────────────
    predictions      = ctx['predictions']
    master           = ctx['master']
    narratives_cache = ctx['narratives_cache']
    rf_model         = ctx['rf_model']
    iso_model        = ctx['iso_model']
    scaler           = ctx['scaler']
    le               = ctx['le']
    sel              = ctx['sel']
    sorted_months    = ctx['sorted_months']
    _last_data_month = ctx['last_data_month']
    _is_proj         = ctx['is_projection']
    row_data         = ctx['row_data']
    level            = ctx['level']
    score            = ctx['score']
    rf_pred          = ctx['rf_pred']
    conf             = ctx['conf']
    is_anom          = ctx['is_anom']
    wisman           = ctx['wisman']
    tpk              = ctx['tpk']
    inflasi          = ctx['inflasi']
    sent             = ctx['sent']
    bali_shr         = ctx['bali_shr']
    usd_avg          = ctx['usd_avg']
    _usd_is_live     = ctx['usd_is_live']
    delta_ctx        = ctx['delta_ctx']
    forecast         = ctx['forecast']
    prev_row         = ctx['prev_row']
    _pct_aman        = ctx['pct_aman']
    _pct_krisis      = ctx['pct_krisis']
    _avg_score       = ctx['avg_score']
    color            = ctx['color']
    recovery_pct     = ctx.get('recovery_pct', sf(row_data.get('wisman_recovery_pct', 0)))
    score_delta      = ctx.get('score_delta', 0)
    score_trend      = ctx.get('score_trend', 'STABIL')
    dominant_factor  = ctx.get('dominant_factor', 'N/A')
    anomaly_exp      = ctx.get('anomaly_exp', f'Z-score {sf(row_data.get("wisman_zscore",0)):.1f}')

    FEATURES = [f for f in FEATURES_CORE + FEATURES_LAG if f in master.columns]
    _tick("nav_start_analisis")

    # ── CSS override — flat/divider style ──
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 20px 0 !important;
        margin-bottom: 0 !important;
    }
    .box-heading {
        font-family: 'DM Sans', sans-serif;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .10em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    </style>
    """, unsafe_allow_html=True)

    cl, cr = st.columns([1, 1], gap="large")

    with cl:
        # ── Panel 1: Komponen Crisis Score ─────────────────
        st.markdown('<div class="box-heading sec-blue">Komponen Crisis Score</div>',
                    unsafe_allow_html=True)

        mr_rows = master[master['month']==sel]
        if len(mr_rows) > 0:
            mr = mr_rows.iloc[0]
            comp_vals = {
                'Kunjungan Wisatawan': sf(mr.get('crisis_component_tourism',0)),
                'Kondisi Ekonomi':     sf(mr.get('crisis_component_economy',0)),
                'Sentimen Ulasan':     sf(mr.get('crisis_component_sentiment',0)),
                'External Risk':       sf(ctx.get('external_risk', 0)),
            }
            _comp_proj = False
        elif _is_proj:
            _sc = score / 100.0
            comp_vals = {
                'Kunjungan Wisatawan': round(_sc * 0.45, 4),
                'Kondisi Ekonomi':     round(_sc * 0.25, 4),
                'External Risk':       round(_sc * 0.20, 4),
                'Sentimen Ulasan':     round(_sc * 0.10, 4),
            }
            _comp_proj = True
        else:
            comp_vals = None
            _comp_proj = False

        if comp_vals is not None:
            fig_c = go.Figure(go.Bar(
                x=list(comp_vals.keys()),
                y=[v*100 for v in comp_vals.values()],
                marker_color=['#D90000','#f59e0b','#3b82f6','#a78bfa'],
                marker_line_color='rgba(0,0,0,0)',
                text=[f'{v*100:.1f}%' for v in comp_vals.values()],
                textposition='outside',
                textfont=dict(size=12, color='#94a3b8')
            ))
            fig_c.update_layout(
                yaxis=dict(
                    range=[0,115],
                    title=dict(text='Kontribusi (%)', font=dict(size=11, color='#64748b')),
                    gridcolor='rgba(255,255,255,0.04)',
                    color='#64748b',
                    tickfont=dict(size=11),
                    showline=False,
                ),
                xaxis=dict(color='#94a3b8', tickfont=dict(size=11), showline=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=280,
                margin=dict(l=0,r=10,t=10,b=10),
                font=dict(family='DM Sans', size=11, color='#94a3b8')
            )
            st.plotly_chart(fig_c, use_container_width=True, config={'displayModeBar': False})
            if _comp_proj:
                st.markdown(
                    "<div style='font-size:11px;color:#64748b;margin-top:-6px'>"
                    "Estimasi proporsi berbasis crisis score proyeksi</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Data komponen tidak tersedia untuk bulan ini.")

        # ── Panel 2: Indikator Detail ───────────────────────
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="box-heading sec-purple">Indikator Detail</div>',
                    unsafe_allow_html=True)

        indicators = [
            ("Wisman", f"{int(round(wisman)):,} orang"),
            ("Recovery vs 2017–2019", f"{ctx.get('recovery_pct', sf(row_data.get('wisman_recovery_pct', 0))):.1f}%"),
            ("TPK Hotel Bintang",     f"{tpk:.1f}%"),
            ("Kurs USD/IDR",          f"Rp {usd_avg:,.0f}"),
            ("Inflasi Bali",          f"{inflasi:.2f}%"),
            ("Sentimen Avg",          f"{sent:+.3f}"),
            ("Bali Share",            f"{bali_shr:.1f}%"),
            ("Z-score Wisman",        f"{sf(row_data.get('wisman_zscore',0)):.2f}"),
            ("Penjelasan Anomali",    ctx.get('anomaly_exp', '')),
            ("Anomali IF",            "⚠️ Terdeteksi" if is_anom else "✅ Normal"),
            ("RF Prediksi",           rf_pred),
            ("RF Confidence",         f"{conf:.0f}%"),
            ("Delta Score",           f"{ctx.get('score_delta', 0):+.1f} ({ctx.get('score_trend', 'STABIL')})"),
            ("Faktor Dominan",        ctx.get('dominant_factor', 'N/A')),
        ]
        rows_html = "".join(
            f'<div class="risk-row"><span class="risk-name">{k}</span>'
            f'<span class="risk-val">{v}</span></div>'
            for k, v in indicators
        )
        st.markdown(rows_html, unsafe_allow_html=True)

    with cr:
        # ── Panel 3: Probabilitas RF ──────────────────────
        st.markdown('<div class="box-heading sec-orange">Probabilitas Prediksi Random Forest</div>',
                    unsafe_allow_html=True)

        prob_labels = ['AMAN','WASPADA','SIAGA','KRISIS']
        prob_vals   = [sf(row_data.get(f'prob_{l.lower()}',0))*100 for l in prob_labels]
        fig_p = go.Figure(go.Bar(
            y=prob_labels, x=prob_vals, orientation='h',
            marker_color=['#00C794', '#F9F871', '#FF6C43', '#D90000'],
            marker_line_color='rgba(0,0,0,0)',
            text=[f'{v:.1f}%' for v in prob_vals],
            textposition='outside',
            textfont=dict(size=12, color='#94a3b8')
        ))
        fig_p.update_layout(
            xaxis=dict(
                range=[0, 100],
                title=dict(text='Probabilitas (%)', font=dict(size=11, color='#64748b')),
                gridcolor='rgba(255,255,255,0.04)',
                color='#64748b',
                tickfont=dict(size=11),
                showline=False,
            ),
            yaxis=dict(
                color='#94a3b8',
                categoryorder='total ascending',
                tickfont=dict(size=12),
                showline=False,
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=280,
            margin=dict(l=0, r=50, t=10, b=10),
            font=dict(family='DM Sans', size=11, color='#94a3b8')
        )
        st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

        # ── Panel 4: Feature Importance ───────────────────
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="box-heading sec-green">Feature Importance — Random Forest</div>',
                    unsafe_allow_html=True)

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
                textfont=dict(size=11, color='#94a3b8')
            ))
            fig_fi.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=370,
                margin=dict(l=0,r=80,t=10,b=10),
                xaxis=dict(range=[0, fi['Importance'].max()*1.35],
                           gridcolor='rgba(255,255,255,0.04)',
                           color='#64748b', showline=False),
                yaxis=dict(color='#94a3b8', tickfont=dict(size=11), showline=False),
                font=dict(family='DM Sans', size=11, color='#94a3b8')
            )
            st.plotly_chart(fig_fi, use_container_width=True, config={'displayModeBar': False})
        except Exception:
            st.info("Feature importance tidak tersedia.")
