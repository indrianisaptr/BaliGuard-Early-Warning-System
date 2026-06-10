"""
src/pages/sentimen.py — BaliGuard: Sentimen
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
    """Render halaman Sentimen."""
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
    sel_dt           = pd.to_datetime(str(sel))

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

    mr_pct_rows = master[master['month']==sel]

    # ── Proyeksi: tidak ada data review nyata ────────────────
    if _is_proj:
        pct_neg           = 0.0
        pct_pos           = 0.0
        pct_netral        = 0.0
        _review_is_proj   = True
        _netral_estimated = False
        _last_real_sent   = float(predictions[predictions['month'] <= _last_data_month]['avg_sentiment_monthly'].iloc[-1])
        _last_real_month  = predictions['month'].iloc[-1]
    else:
        _review_is_proj   = False
        _last_real_sent   = None
        _last_real_month  = None
        _netral_estimated = False

        pct_neg    = sf(mr_pct_rows['pct_negative_monthly'].iloc[0] if len(mr_pct_rows) > 0
                        and 'pct_negative_monthly' in master.columns
                        else row_data.get('pct_negative_monthly', 0))
        pct_pos    = sf(mr_pct_rows['pct_positive_monthly'].iloc[0] if len(mr_pct_rows) > 0
                        and 'pct_positive_monthly' in master.columns
                        else (100 - pct_neg))
        pct_netral = sf(mr_pct_rows['pct_neutral_monthly'].iloc[0] if len(mr_pct_rows) > 0
                        and 'pct_neutral_monthly' in master.columns
                        else max(0.0, 100.0 - pct_pos - pct_neg))

    # ── Sent label: score dulu, lalu fallback ke distribusi pct ──
    if sent >= 0.3:
        sent_label = 'POSITIF'
    elif sent < -0.3:
        sent_label = 'NEGATIF'
    elif pct_pos >= 55:
        sent_label = 'POSITIF'
    elif pct_neg >= 55:
        sent_label = 'NEGATIF'
    else:
        sent_label = 'NETRAL'

    sent_color = '#4ade80' if sent_label == 'POSITIF' else ('#f87171' if sent_label == 'NEGATIF' else '#fbbf24')
    sent_pct   = int((sent + 1) / 2 * 100)

    # ── Hero: pakai kolom native Streamlit, bukan HTML kompleks ──
    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 1], gap="medium")
    with h1:
        st.markdown(
            f"<div style='padding:16px 0'>"
            f"<div style='font-size:11px;font-weight:700;letter-spacing:.12em;color:#475569;text-transform:uppercase;margin-bottom:6px'>Sentimen Bulan Ini · {sel}</div>"
            f"<div style='font-family:DM Serif Display,serif;font-size:36px;color:{sent_color};line-height:1'>{sent_label}</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:20px;color:{sent_color};margin-top:4px'>{sent:+.3f}</div>"
            + (f"<div style='font-size:14px;color:#a78bfa;margin-top:6px'>proyeksi — data terakhir {_last_real_month}</div>" if _review_is_proj else "")
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
            "border-radius:10px;padding:10px 16px;margin:8px 0 16px;font-size:16px;color:#a78bfa'>"
            f"<b>Bulan proyeksi</b> — data review wisatawan belum tersedia. "
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
                st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})

        # ── Box: 6 Bulan Terakhir ──────────────────────────
        
        with st.container(border=True):
            st.markdown('<div class="accent-blue2" style="background: #1119FF !important; border-color: #1119FF !important;"></div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;padding:4px 0 10px;"
                "border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:4px'>"
                "<span style='font-family:DM Sans,sans-serif;font-size:15px;font-weight:700;"
                "letter-spacing:.05em;text-transform:uppercase;color:#1119FF;"
                "border-left:3px solid #1119FF;padding-left:10px'>6 Bulan Terakhir</span></div>",
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
                    textposition='outside', textfont=dict(color='#e2e8f0', size=12),
                    hovertemplate='<b>%{x}</b><br>Sentimen: %{y:.3f}<extra></extra>'
                ))
                fig_6.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.12)', line_width=1)
                fig_6.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    height=220, margin=dict(l=0,r=0,t=16,b=0),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#64748b', range=[-0.2, last6['avg_sentiment_monthly'].max()*1.25], tickfont=dict(size=12)),
                    xaxis=dict(color='#64748b', tickfont=dict(size=12)),
                    font=dict(family='DM Sans', size=11, color='#94a3b8'))
                st.plotly_chart(fig_6, use_container_width=True, config={'displayModeBar': False})

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
            st.plotly_chart(fig_g, use_container_width=True, config={'displayModeBar': False})

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
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:9px'>"
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
