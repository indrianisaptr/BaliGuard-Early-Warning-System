"""
src/pages/overview.py — BaliGuard: Gambaran Umum & Garis Waktu
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
from src.utils import kpi_html, alert_html, status_dot

from src.utils import (
    sf,
    _tick,
    LEVEL_COLORS,
    LABEL_ORDER,
    FEATURES_CORE,
    FEATURES_LAG,
)

from src.components.cards import (
    kpi_card,
    alert_card,
)

from src.components.badges import (
    status_dot,
)

# kpi_html = kpi_card
# alert_html = alert_card

from src.config import COLOR_MAP

# ── Layout constants untuk chart overview ─────────────────────────────
_OVERVIEW_AXIS_STYLE = dict(
    gridcolor='rgba(255,255,255,0.06)', showline=True,
    linecolor='rgba(255,255,255,0.1)'
)
_OVERVIEW_LAYOUT_BASE = dict(
    plot_bgcolor='rgba(5,13,26,0.7)', paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=55, t=50, b=10),
    font=dict(family='DM Sans', size=11, color='#94a3b8')
)

# ── Chart builders — di-cache, perlu akses predictions di module level ─
@st.cache_data(show_spinner=False)
def _build_overview_fig1(sel_month_str: str, _predictions: pd.DataFrame) -> go.Figure:
    """Crisis Score & Level Krisis chart."""
    _months_dt = pd.to_datetime(_predictions['month'].astype(str))
    _sel_dt    = pd.to_datetime(sel_month_str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_months_dt, y=_predictions['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#cbd5e1', width=2),
        fill='tozeroy', fillcolor='rgba(148,163,184,0.06)'
    ))
    for lv, col in COLOR_MAP.items():
        mask = _predictions['crisis_level'] == lv
        if mask.sum() > 0:
            fig.add_trace(go.Scatter(
                x=_months_dt[mask], y=_predictions.loc[mask, 'crisis_score_100'],
                mode='markers', name=lv,
                marker=dict(color=col, size=7, line=dict(width=1.2, color='#050d1a')),
                hovertemplate=f'<b>{lv}</b><br>%{{x|%b %Y}}<br>Score: %{{y:.1f}}<extra></extra>'
            ))
    for thr, lbl, col in [(60,'KRISIS','#d90000'),(45,'SIAGA','#ff6c43'),(30,'WASPADA','#F9F871')]:
        fig.add_hline(y=thr, line_dash='dot', line_color=col, line_width=1, opacity=0.7,
                      annotation_text=lbl, annotation_position='right',
                      annotation_font_size=9, annotation_font_color=col,
                      annotation_xanchor='left', annotation_xshift=-52)
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.06)', line_width=0,
                  annotation_text='COVID-19', annotation_font_color='#ef4444',
                  annotation_font_size=10)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1.2)
    _EVENTS = [
        ('2002-10-12','Bom Bali I','#ef4444'), ('2005-10-01','Bom Bali II','#f97316'),
        ('2017-11-01','Erupsi Agung','#fb923c'), ('2018-08-05','Gempa Lombok','#f59e0b'),
        ('2020-03-19','Lockdown COVID','#ef4444'), ('2021-10-14','Bali Dibuka PPLN','#22c55e'),
        ('2022-11-15','KTT G20 Bali','#a78bfa'), ('2023-02-01','Bebas Visa 20 N.','#60a5fa'),
    ]
    for ev_date, ev_label, ev_col in _EVENTS:
        try:
            _ev_dt = pd.to_datetime(ev_date)
            if _ev_dt < _months_dt.min() or _ev_dt > _months_dt.max() + pd.DateOffset(months=3):
                continue
            fig.add_vline(x=_ev_dt, line_dash='dot', line_color=ev_col, line_width=0.8, opacity=0.55)
            fig.add_annotation(x=_ev_dt, y=97, text=ev_label, showarrow=False,
                                font=dict(size=8, color=ev_col), textangle=-55,
                                xanchor='left', bgcolor='rgba(5,13,26,0.7)', borderpad=2)
        except Exception:
            pass
    fig.update_layout(
    height=340,
    showlegend=True,

    title=dict(
        text='Crisis Score & Level Krisis',
        x=0.5,
        y=0.97,
        xanchor='center',
        yanchor='top',
        font=dict(
            size=17,
            color='#93c5fd',
            family='DM Sans'
        )
    ),

    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.12,
        xanchor='right',
        x=1.0,
        bgcolor='rgba(5,13,26,0.85)',
        bordercolor='rgba(255,255,255,0.12)',
        borderwidth=1,
        font=dict(
            size=11,
            color='#e2e8f0'
        )
    ),

    margin=dict(
        l=0,
        r=55,
        t=90,
        b=10
    ),

    **_OVERVIEW_LAYOUT_BASE
)
    fig.update_xaxes(**_OVERVIEW_AXIS_STYLE)
    fig.update_yaxes(**_OVERVIEW_AXIS_STYLE)
    return fig


@st.cache_data(show_spinner=False)
def _build_overview_fig2(sel_month_str: str, _predictions: pd.DataFrame) -> go.Figure:
    """Kunjungan Wisatawan Mancanegara chart."""
    _months_dt = pd.to_datetime(_predictions['month'].astype(str))
    _sel_dt    = pd.to_datetime(sel_month_str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_months_dt, y=_predictions['wisman'],
        mode='lines', name='Wisman', showlegend=False,
        line=dict(color='#7dd3fc', width=2),
        fill='tozeroy', fillcolor='rgba(96,165,250,0.09)'
    ))
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.06)', line_width=0)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1.2)
    fig.update_layout(height=240, showlegend=False,
                      title=dict(text='Kunjungan Wisatawan Mancanegara', x=0.5, xanchor='center',
                                 font=dict(size=17, color='#7dd3fc', family='DM Sans')),
                      **_OVERVIEW_LAYOUT_BASE)
    fig.update_xaxes(**_OVERVIEW_AXIS_STYLE)
    fig.update_yaxes(**_OVERVIEW_AXIS_STYLE)
    return fig


@st.cache_data(show_spinner=False)
def _build_overview_fig3(sel_month_str: str, _predictions: pd.DataFrame) -> go.Figure:
    """Kurs USD/IDR chart."""
    _months_dt = pd.to_datetime(_predictions['month'].astype(str))
    _sel_dt    = pd.to_datetime(sel_month_str)
    fig = go.Figure()
    if 'usd_idr_avg' in _predictions.columns:
        fig.add_trace(go.Scatter(
            x=_months_dt, y=_predictions['usd_idr_avg'],
            mode='lines', name='USD/IDR', showlegend=False,
            line=dict(color='#fbbf24', width=2)
        ))
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.06)', line_width=0)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1.2)
    fig.update_layout(height=220, showlegend=False,
                      title=dict(text='Kurs USD/IDR', x=0.5, xanchor='center',
                                 font=dict(size=17, color='#fbbf24', family='DM Sans')),
                      **_OVERVIEW_LAYOUT_BASE)
    fig.update_xaxes(**_OVERVIEW_AXIS_STYLE)
    fig.update_yaxes(**_OVERVIEW_AXIS_STYLE)
    return fig


def render(ctx: dict) -> None:
    """Render halaman Gambaran Umum & Garis Waktu."""
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

    _tick("nav_start_overview")

    st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1.5px solid rgba(59,130,246,0.55) !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 28px rgba(59,130,246,0.10), inset 0 1px 0 rgba(255,255,255,0.06) !important;
        padding: 4px 8px 8px !important;
        margin-bottom: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<div class="accent-overview-2"></div>', unsafe_allow_html=True)
        st.plotly_chart(_build_overview_fig2(str(sel), predictions), use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="accent-overview-3"></div>', unsafe_allow_html=True)
        st.plotly_chart(_build_overview_fig3(str(sel), predictions), use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="accent-overview-3"></div>', unsafe_allow_html=True)
        st.plotly_chart(_build_overview_fig1(str(sel), predictions), use_container_width=True, config={'displayModeBar': False})

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
