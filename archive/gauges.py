"""
src/components/gauges.py — BaliGuard: Gauge & Ring Charts
"""
import plotly.graph_objects as go
from src.components.badges import LEVEL_COLORS

_PAPER_BG = 'rgba(0,0,0,0)'


def build_crisis_gauge(score: float, level: str, height: int = 260) -> go.Figure:
    """Gauge setengah lingkaran untuk crisis_score_100."""
    color = LEVEL_COLORS.get(level, '#64748b')
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=score,
        number=dict(font=dict(size=36, color=color, family='DM Serif Display'),
                    suffix='', valueformat='.1f'),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor='#475569',
                      tickfont=dict(size=10, color='#64748b')),
            bar=dict(color=color, thickness=0.25),
            bgcolor='rgba(255,255,255,.04)',
            borderwidth=0,
            steps=[
                dict(range=[0,  30], color='rgba(34,197,94,.12)'),
                dict(range=[30, 45], color='rgba(245,158,11,.12)'),
                dict(range=[45, 60], color='rgba(249,115,22,.12)'),
                dict(range=[60,100], color='rgba(239,68,68,.12)'),
            ],
            threshold=dict(line=dict(color=color, width=3), value=score),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))
    fig.add_annotation(
        text=level,
        x=0.5, y=0.15, showarrow=False,
        font=dict(size=14, color=color, family='Inter'),
    )
    fig.update_layout(
        paper_bgcolor=_PAPER_BG, height=height,
        margin=dict(l=20, r=20, t=30, b=10),
        font=dict(family='Inter, sans-serif', color='#94a3b8'),
    )
    return fig


def build_confidence_gauge(conf: float, rf_pred: str, height: int = 200) -> go.Figure:
    """Ring kecil untuk confidence model."""
    pct   = conf * 100
    color = '#22c55e' if pct >= 70 else '#f59e0b' if pct >= 50 else '#ef4444'
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct], hole=0.72,
        marker_colors=[color, 'rgba(255,255,255,.05)'],
        textinfo='none', hoverinfo='skip', showlegend=False,
    ))
    fig.add_annotation(
        text=f"<b>{pct:.0f}%</b><br><span style='font-size:10px'>conf</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=color),
    )
    fig.update_layout(
        paper_bgcolor=_PAPER_BG, height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig
