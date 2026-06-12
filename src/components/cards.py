"""
src/components/cards.py — BaliGuard: Reusable Card Components
Semua fungsi return HTML string, dirender dengan st.markdown(..., unsafe_allow_html=True)
"""
import streamlit as st
from src.components.badges import LEVEL_COLORS, LEVEL_BG, status_dot


def kpi_card(label: str, value: str, sub: str = '',
             level: str = None, width: str = '100%',
             color: str = None) -> str:                          # ← tambah param
    """Card KPI dengan border warna level di atas.

    Args:
        color: Override warna eksplisit (hex/rgba). Bila diisi, mengabaikan `level`.
               Berguna untuk kasus di mana warna ditentukan oleh logika non-level
               (mis. threshold persentase di External Risk Monitor).
    """
    _color = color or (LEVEL_COLORS.get(level, '#3b82f6') if level else None)  # ← resolusi warna
    border = f"border-top:3px solid {_color};" if _color else ''
    val_color = _color or '#f1f5f9'                                             # ← value ikut warna
    return (
        f"<div style='background:rgba(255,255,255,.04);border-radius:10px;"
        f"padding:14px 16px;{border}text-align:center;width:{width}'>"
        f"<div style='font-size:11px;color:#64748b;letter-spacing:.08em;"
        f"margin-bottom:4px;font-weight:600'>{label}</div>"
        f"<div style='font-size:22px;font-weight:700;color:{val_color};"    # ← pakai val_color
        f"font-family:\"DM Serif Display\"'>{value}</div>"
        f"<div style='font-size:12px;color:#94a3b8;margin-top:3px'>{sub}</div>"
        f"</div>"
    )


def alert_card(level: str, title: str, body: str) -> str:
    """Alert box dengan accent color sesuai level."""
    c  = LEVEL_COLORS.get(level, '#3b82f6')
    bg = LEVEL_BG.get(level, 'rgba(59,130,246,.1)')
    return (
        f"<div style='border-left:4px solid {c};background:{bg};"
        f"border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:12px'>"
        f"<div style='font-size:13px;font-weight:700;color:{c};"
        f"margin-bottom:4px'>{title}</div>"
        f"<div style='font-size:13px;color:#cbd5e1;line-height:1.5'>{body}</div>"
        f"</div>"
    )


def section_header(title: str, level: str = None, subtitle: str = '') -> None:
    """Header seksi dengan accent line kiri. Langsung render ke st."""
    color = LEVEL_COLORS.get(level, '#3b82f6') if level else '#3b82f6'
    sub_html = (f"<div style='font-size:12px;color:#64748b;margin-top:3px'>"
                f"{subtitle}</div>") if subtitle else ''
    st.markdown(
        f"<div style='border-left:3px solid {color};padding:4px 12px;"
        f"margin:16px 0 12px'>"
        f"<div style='font-size:15px;font-weight:700;color:#e2e8f0'>{title}</div>"
        f"{sub_html}</div>",
        unsafe_allow_html=True
    )


def metric_row(items: list[tuple]) -> None:
    """
    Render satu baris KPI cards.
    items = [(label, value, sub, level), ...]
    """
    cols = st.columns(len(items))
    for col, (label, value, sub, level) in zip(cols, items):
        with col:
            st.markdown(kpi_card(label, value, sub, level), unsafe_allow_html=True)


def status_summary_card(level: str, score: float, month: str,
                         rf_pred: str, conf: float) -> str:
    """Card ringkasan status untuk sidebar atau overview."""
    color = LEVEL_COLORS.get(level, '#64748b')
    bg    = LEVEL_BG.get(level, 'rgba(100,116,139,.1)')
    return (
        f"<div style='background:{bg};border:1px solid {color}30;"
        f"border-radius:12px;padding:16px;text-align:center'>"
        f"<div style='font-size:11px;color:#64748b;letter-spacing:.1em;"
        f"margin-bottom:8px;font-weight:700'>CRISIS SCORE</div>"
        f"<div style='font-size:48px;font-weight:800;color:{color};"
        f"font-family:\"DM Serif Display\";line-height:1'>{score:.1f}"
        f"<span style='font-size:18px;color:#64748b'>/100</span></div>"
        f"<div style='margin-top:8px'>{status_dot(level, 12)}"
        f"<span style='font-size:15px;font-weight:700;color:{color}'>{level}</span></div>"
        f"<div style='font-size:11px;color:#64748b;margin-top:6px'>{month}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:4px'>"
        f"RF: {rf_pred} · conf {conf*100:.0f}%</div>"
        f"</div>"
    )


def info_box(text: str, icon: str = 'ℹ️') -> None:
    """Info box biru untuk catatan."""
    st.markdown(
        f"<div style='background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.25);"
        f"border-radius:8px;padding:10px 14px;font-size:13px;color:#94a3b8'>"
        f"{icon} {text}</div>",
        unsafe_allow_html=True
    )


def divider_line(color: str = None, margin: str = '16px 0') -> None:
    """Garis tipis sebagai pemisah seksi."""
    c = color or 'rgba(255,255,255,.08)'
    st.markdown(
        f"<hr style='border:none;border-top:1px solid {c};"
        f"margin:{margin}'/>",
        unsafe_allow_html=True
    )
