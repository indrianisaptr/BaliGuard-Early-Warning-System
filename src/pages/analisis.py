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
    FEATURES_CORE, FEATURES_LAG,
    LABEL_MANUSIAWI, interpretasi_indikator,        # [BARU]
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
    anomaly_exp      = ctx.get(
        'anomaly_exp',
        f'{LABEL_MANUSIAWI.get("wisman_zscore", "Penyimpangan dari Rata-rata")}: '
        f'{sf(row_data.get("wisman_zscore",0)):.1f}'
    )

    FEATURES = [f for f in FEATURES_CORE + FEATURES_LAG if f in master.columns]
    _tick("nav_start_analisis")

    # ── CSS override ──────────────────────────────────────────
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
    .why-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .why-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 7px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        gap: 12px;
    }
    .why-row:last-child { border-bottom: none; }
    .why-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        white-space: nowrap;
        min-width: 160px;
    }
    .why-text {
        font-size: 12px;
        color: #94a3b8;
        text-align: right;
        flex: 1;
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
                'Kunjungan Wisatawan': sf(mr.get('crisis_component_tourism', 0))   * 0.45,
                'Kondisi Ekonomi':     sf(mr.get('crisis_component_economy', 0))   * 0.25,
                'Sentimen Ulasan':     sf(mr.get('crisis_component_sentiment', 0)) * 0.10,
                'External Risk':       sf(mr.get('external_risk_score', 0))        * 0.20,
            }
            _comp_proj = False
        elif _is_proj:
            _sc = score / 100.0
            comp_vals = {
                'Kunjungan Wisatawan': round(_sc * 0.45, 4),
                'Kondisi Ekonomi':     round(_sc * 0.25, 4),
                'Sentimen Ulasan':     round(_sc * 0.10, 4),
                'External Risk':       round(sf(ctx.get('external_risk', 0)) * 0.20, 4),
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

        # ── [BARU] Section: Mengapa Status Ini Muncul? ─────
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="box-heading sec-blue">Mengapa Status Ini Muncul?</div>',
                    unsafe_allow_html=True)

        # 5 indikator utama pembentuk status — urutan dari yang paling berpengaruh
        _why_indicators = [
            ("wisman_growth_mom", sf(row_data.get("wisman_growth_mom", 0))),
            ("tpk_bintang",       sf(row_data.get("tpk_bintang", 0))),
            ("usd_idr_avg",       sf(row_data.get("usd_idr_avg", usd_avg))),
            ("avg_sentiment_monthly", sf(row_data.get("avg_sentiment_monthly", sent))),
            ("gdelt_crisis_score",sf(row_data.get("gdelt_crisis_score", 0))),
        ]
        why_rows_html = ""
        for kolom, nilai in _why_indicators:
            label   = LABEL_MANUSIAWI.get(kolom, kolom)
            kalimat = interpretasi_indikator(kolom, nilai)
            why_rows_html += (
                f'<div class="why-row">'
                f'<span class="why-label">{label}</span>'
                f'<span class="why-text">{kalimat}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="why-box">{why_rows_html}</div>',
            unsafe_allow_html=True
        )

        # ── Panel 2: Indikator Detail ───────────────────────
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="box-heading sec-purple">Indikator Detail</div>',
                    unsafe_allow_html=True)

        # [DIUBAH] Label teknis diganti bahasa manusiawi
        _anom_label = "⚠️ Ya, terdeteksi anomali" if is_anom else "✅ Tidak, kondisi normal"
        indicators = [
            (LABEL_MANUSIAWI.get('wisman', "Jumlah Wisatawan Mancanegara"),
                f"{int(round(wisman)):,} orang"),
            (LABEL_MANUSIAWI.get('wisman_recovery_pct', "Tingkat Pemulihan vs 2017–2019"),
                f"{recovery_pct:.1f}%"),
            (LABEL_MANUSIAWI.get('tpk_bintang', "Tingkat Hunian Hotel Berbintang"),
                f"{tpk:.1f}%"),
            (LABEL_MANUSIAWI.get('usd_idr_avg', "Kurs USD/IDR Rata-rata Bulan Ini"),
                f"Rp {usd_avg:,.0f}"),
            (LABEL_MANUSIAWI.get('inflasi_processed', "Tingkat Inflasi Bali"),
                f"{inflasi:.2f}%"),
            (LABEL_MANUSIAWI.get('avg_sentiment_monthly', "Sentimen Rata-rata Ulasan Wisatawan"),
                f"{sent:+.3f}"),
            (LABEL_MANUSIAWI.get('bali_share_pct', "Pangsa Wisatawan Bali dari Nasional"),
                f"{bali_shr:.1f}%"),
            (LABEL_MANUSIAWI.get('wisman_zscore', "Penyimpangan Wisatawan dari Normal"),
                f"{sf(row_data.get('wisman_zscore',0)):.2f}"),
            ("Keterangan Anomali",                   anomaly_exp),
            (LABEL_MANUSIAWI.get('iso_anomaly', "Terdeteksi Anomali oleh Model"),
                _anom_label),
            (LABEL_MANUSIAWI.get('rf_predicted_level', "Prediksi Level Krisis (Random Forest)"),
                rf_pred),
            (LABEL_MANUSIAWI.get('rf_confidence', "Tingkat Keyakinan Prediksi Model"),
                f"{conf:.0f}%"),
            ("Perubahan Skor Krisis",                f"{score_delta:+.1f} ({score_trend})"),
            ("Faktor Paling Dominan",                dominant_factor),
        ]
        rows_html = "".join(
            f'<div class="risk-row"><span class="risk-name">{k}</span>'
            f'<span class="risk-val">{v}</span></div>'
            for k, v in indicators
        )
        st.markdown(rows_html, unsafe_allow_html=True)

    with cr:
        # ── Panel 3: Probabilitas RF ──────────────────────
        st.markdown('<div class="box-heading sec-orange">Probabilitas Prediksi Model</div>',
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
        # [DIUBAH] Judul lebih manusiawi
        st.markdown('<div class="box-heading sec-green">Faktor Paling Berpengaruh pada Prediksi Model</div>',
                    unsafe_allow_html=True)

        try:
            fi_available = [f for f in FEATURES if f in master.columns]
            fi = pd.DataFrame({
                'Fitur': fi_available[:len(rf_model.feature_importances_)],
                'Importance': rf_model.feature_importances_[:len(fi_available)]
            })
            fi = fi.sort_values('Importance', ascending=True).tail(8)

            # [DIUBAH] Label fitur diganti bahasa manusiawi
            fi['Label'] = fi['Fitur'].map(
                lambda c: LABEL_MANUSIAWI.get(c, c)
            )

            fig_fi = go.Figure(go.Bar(
                x=fi['Importance'], y=fi['Label'], orientation='h',
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
            st.info("Data faktor pengaruh tidak tersedia.")