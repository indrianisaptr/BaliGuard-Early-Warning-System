"""
src/components/html_blocks.py — BaliGuard: Structural HTML Blocks
Elemen layout yang muncul berulang di semua halaman.
"""
import streamlit as st
from src.components.badges import LEVEL_COLORS


def page_title(title: str, subtitle: str = '', level: str = None) -> None:
    """Header utama di atas setiap halaman."""
    color = LEVEL_COLORS.get(level, '#3b82f6') if level else '#3b82f6'
    sub_html = (f"<div style='font-size:13px;color:#64748b;margin-top:4px'>"
                f"{subtitle}</div>") if subtitle else ''
    st.markdown(
        f"<div style='padding:8px 0 16px'>"
        f"<div style='font-size:22px;font-weight:800;color:#f1f5f9;"
        f"font-family:\"DM Serif Display\";line-height:1.2'>{title}</div>"
        f"{sub_html}"
        f"<div style='height:2px;background:linear-gradient(90deg,{color},transparent);"
        f"margin-top:8px;border-radius:2px'></div>"
        f"</div>",
        unsafe_allow_html=True
    )


def thin_divider(color: str = 'rgba(255,255,255,.07)',
                 margin: str = '20px 0') -> None:
    """Garis tipis sebagai pengganti st.divider() bawaan."""
    st.markdown(
        f"<hr style='border:none;border-top:1px solid {color};"
        f"margin:{margin}'/>",
        unsafe_allow_html=True
    )


def accent_line(label: str, color: str = '#3b82f6') -> None:
    """Label dengan garis vertikal di kiri — pengganti subheader."""
    st.markdown(
        f"<div style='border-left:3px solid {color};padding:3px 10px;"
        f"margin:14px 0 8px'>"
        f"<span style='font-size:13px;font-weight:700;color:#e2e8f0;"
        f"letter-spacing:.05em'>{label}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


def spacer(height: int = 12) -> None:
    st.markdown(f"<div style='height:{height}px'></div>", unsafe_allow_html=True)


def two_col_stat(left_label: str, left_val: str,
                 right_label: str, right_val: str,
                 left_color: str = '#f1f5f9',
                 right_color: str = '#f1f5f9') -> None:
    """Dua statistik kecil berdampingan tanpa st.columns."""
    st.markdown(
        f"<div style='display:flex;gap:20px;padding:8px 0'>"
        f"<div><div style='font-size:10px;color:#64748b'>{left_label}</div>"
        f"<div style='font-size:16px;font-weight:700;color:{left_color}'>{left_val}</div></div>"
        f"<div><div style='font-size:10px;color:#64748b'>{right_label}</div>"
        f"<div style='font-size:16px;font-weight:700;color:{right_color}'>{right_val}</div></div>"
        f"</div>",
        unsafe_allow_html=True
    )


def live_badge(is_live: bool, label: str = '') -> str:
    """Badge 🔴 LIVE atau ⚪ HISTORIS."""
    if is_live:
        return (f"<span style='background:rgba(239,68,68,.15);color:#ef4444;"
                f"border:1px solid #ef444440;padding:2px 7px;border-radius:10px;"
                f"font-size:10px;font-weight:700'>● LIVE{' ' + label if label else ''}</span>")
    return (f"<span style='background:rgba(100,116,139,.15);color:#64748b;"
            f"border:1px solid #64748b40;padding:2px 7px;border-radius:10px;"
            f"font-size:10px'>○ HISTORIS</span>")
