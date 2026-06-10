"""
src/components/charts.py — BaliGuard: Reusable Chart Builders
Setiap fungsi return fig Plotly, dipanggil dari pages/*.py
Cache ditaruh di sini supaya tab apapun yang memanggilnya dapat manfaat cache.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from src.components.badges import LEVEL_COLORS

_FONT = dict(family='Inter, sans-serif', size=12, color='#94a3b8')
_PAPER_BG = 'rgba(0,0,0,0)'
_PLOT_BG  = 'rgba(255,255,255,0.02)'
_GRID_COLOR = 'rgba(255,255,255,0.06)'


def _base_layout(title: str = '', height: int = 380) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=14, color='#e2e8f0'), x=0.01, xanchor='left'),
        paper_bgcolor=_PAPER_BG,
        plot_bgcolor=_PLOT_BG,
        font=_FONT,
        height=height,
        margin=dict(l=10, r=10, t=40, b=30),
        xaxis=dict(showgrid=False, color='#64748b'),
        yaxis=dict(gridcolor=_GRID_COLOR, color='#64748b', zerolinecolor=_GRID_COLOR),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
        hovermode='x unified',
    )


# ── 1. Crisis Score Timeline ────────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_crisis_timeline(predictions: pd.DataFrame, sel_month: str,
                          height: int = 380) -> go.Figure:
    """Garis crisis_score_100 sepanjang waktu + threshold bands + marker bulan dipilih."""
    df = predictions.sort_values('month')
    fig = go.Figure()

    # Threshold bands
    for label, lo, hi, color in [
        ('KRISIS',  60, 100, 'rgba(239,68,68,.10)'),
        ('SIAGA',   45,  60, 'rgba(249,115,22,.08)'),
        ('WASPADA', 30,  45, 'rgba(245,158,11,.06)'),
        ('AMAN',     0,  30, 'rgba(34,197,94,.05)'),
    ]:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=color, line_width=0, annotation_text=label,
                      annotation_position='right', annotation_font_size=10,
                      annotation_font_color='#64748b')

    # Line
    fig.add_trace(go.Scatter(
        x=df['month'], y=df['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#3b82f6', width=2),
        fill='tozeroy', fillcolor='rgba(59,130,246,.06)',
    ))

    # Selected month marker
    sel_rows = df[df['month'] == sel_month]
    if len(sel_rows):
        r = sel_rows.iloc[0]
        fig.add_trace(go.Scatter(
            x=[r['month']], y=[r['crisis_score_100']],
            mode='markers+text',
            marker=dict(size=12, color=LEVEL_COLORS.get(str(r.get('crisis_level','AMAN')), '#3b82f6'),
                        line=dict(color='white', width=2)),
            text=[f"  {r.get('crisis_level','')} {r['crisis_score_100']:.1f}"],
            textposition='top right', textfont=dict(size=11, color='#e2e8f0'),
            name='Bulan dipilih', showlegend=False,
        ))

    fig.update_layout(**_base_layout('Timeline Crisis Score', height))
    return fig


# ── 2. Wisman Bar Chart ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_wisman_bar(predictions: pd.DataFrame, sel_month: str,
                     n_last: int = 36, height: int = 300) -> go.Figure:
    df = predictions.sort_values('month').tail(n_last)
    colors = [LEVEL_COLORS.get(str(lv), '#3b82f6')
              for lv in df.get('crisis_level', ['AMAN']*len(df))]
    fig = go.Figure(go.Bar(
        x=df['month'], y=df['wisman'],
        marker_color=colors, name='Wisman',
        hovertemplate='%{x}<br>Wisman: %{y:,.0f}<extra></extra>',
    ))
    # Highlight selected
    sel_rows = df[df['month'] == sel_month]
    if len(sel_rows):
        fig.add_vline(x=sel_month, line_dash='dash',
                      line_color='rgba(255,255,255,.3)', line_width=1)
    fig.update_layout(**_base_layout('Kunjungan Wisman (36 Bulan Terakhir)', height))
    return fig


# ── 3. Probability Donut ────────────────────────────────────────────
def build_probability_donut(row_data: dict, height: int = 280) -> go.Figure:
    """Donut chart probabilitas level krisis untuk bulan dipilih."""
    labels = ['AMAN','WASPADA','SIAGA','KRISIS']
    values = [
        float(row_data.get('prob_aman', 0.25)),
        float(row_data.get('prob_waspada', 0.25)),
        float(row_data.get('prob_siaga', 0.25)),
        float(row_data.get('prob_krisis', 0.25)),
    ]
    colors = [LEVEL_COLORS[l] for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker_colors=colors,
        textfont_size=11,
        hovertemplate='%{label}: %{percent}<extra></extra>',
    ))
    level = str(row_data.get('rf_predicted_level', 'AMAN'))
    score = float(row_data.get('crisis_score_100', 0))
    fig.add_annotation(
        text=f"<b>{score:.0f}</b><br><span style='font-size:11px'>{level}</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=18, color=LEVEL_COLORS.get(level,'#3b82f6')),
    )
    fig.update_layout(
        paper_bgcolor=_PAPER_BG, height=height,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
        font=_FONT,
    )
    return fig


# ── 4. Feature Importance Bar ───────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_feature_importance(rf_model, feature_names: list,
                              top_n: int = 13, height: int = 380) -> go.Figure:
    fi = pd.Series(rf_model.feature_importances_, index=feature_names)
    fi = fi.sort_values(ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        x=fi.values, y=fi.index, orientation='h',
        marker_color=[f'rgba(59,130,246,{0.4+v*0.6})' for v in fi.values/fi.max()],
        hovertemplate='%{y}: %{x:.4f}<extra></extra>',
    ))
    fig.update_layout(**{**_base_layout('Feature Importance — Random Forest', height),
                         'yaxis': dict(gridcolor=_GRID_COLOR, color='#94a3b8'),
                         'xaxis': dict(gridcolor=_GRID_COLOR, color='#94a3b8')})
    return fig


# ── 5. Sentiment Trend Line ─────────────────────────────────────────
@st.cache_data(show_spinner=False)
def build_sentiment_trend(predictions: pd.DataFrame, height: int = 320) -> go.Figure:
    df = predictions.sort_values('month').dropna(subset=['avg_sentiment_monthly'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['month'], y=df['avg_sentiment_monthly'],
        mode='lines', fill='tozeroy',
        line=dict(color='#8b5cf6', width=2),
        fillcolor='rgba(139,92,246,.08)',
        name='Sentimen Rata-rata',
        hovertemplate='%{x}<br>Sentimen: %{y:.3f}<extra></extra>',
    ))
    fig.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,.2)')
    fig.update_layout(**_base_layout('Tren Sentimen Wisatawan', height))
    return fig


# ── 6. Forecast Line ────────────────────────────────────────────────
def build_forecast_chart(predictions: pd.DataFrame,
                          forecast_data: list[dict],
                          height: int = 360) -> go.Figure:
    """Garis historis + proyeksi 6 bulan ke depan."""
    hist = predictions.sort_values('month').tail(24)
    proj = pd.DataFrame(forecast_data)

    fig = go.Figure()
    # Historical
    fig.add_trace(go.Scatter(
        x=hist['month'], y=hist['crisis_score_100'],
        mode='lines', name='Historis',
        line=dict(color='#3b82f6', width=2),
    ))
    # Forecast
    if len(proj):
        fig.add_trace(go.Scatter(
            x=proj['month'], y=proj['crisis_score_100'],
            mode='lines+markers', name='Proyeksi',
            line=dict(color='#f59e0b', width=2, dash='dot'),
            marker=dict(size=8, symbol='diamond'),
        ))
    # Boundary
    if len(hist) and len(proj):
        fig.add_vline(x=hist['month'].iloc[-1], line_dash='dash',
                      line_color='rgba(255,255,255,.2)', line_width=1,
                      annotation_text='sekarang', annotation_font_size=10,
                      annotation_font_color='#64748b')
    fig.update_layout(**_base_layout('Crisis Score — Historis & Proyeksi 6 Bulan', height))
    return fig
