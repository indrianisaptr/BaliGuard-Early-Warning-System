"""
src/components/badges.py — BaliGuard: Status & Level Badges
Komponen kecil yang dipakai hampir di semua halaman.
"""

from src.config import COLOR_MAP as LEVEL_COLORS, BG_MAP as LEVEL_BG
TREND_ICONS = {'up': '▲', 'down': '▼', 'flat': '─'}


def status_dot(level: str, size: int = 10) -> str:
    """Bulatan kecil berwarna sesuai level."""
    color = LEVEL_COLORS.get(level, '#64748b')
    return (f"<span style='display:inline-block;width:{size}px;height:{size}px;"
            f"border-radius:50%;background:{color};margin-right:5px'></span>")


def level_badge(level: str, show_dot: bool = True) -> str:
    """Badge pill berteks level dengan warna yang sesuai."""
    color = LEVEL_COLORS.get(level, '#64748b')
    bg    = LEVEL_BG.get(level, 'rgba(100,116,139,.15)')
    dot   = status_dot(level) if show_dot else ''
    return (f"<span style='background:{bg};color:{color};border:1px solid {color}40;"
            f"padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700'>"
            f"{dot}{level}</span>")


def trend_badge(delta: float, unit: str = '', fmt: str = '+.1f') -> str:
    """Badge tren ▲/▼ dengan warna hijau/merah."""
    if abs(delta) < 0.01:
        color, icon = '#64748b', '─'
    elif delta > 0:
        color, icon = '#22c55e', '▲'
    else:
        color, icon = '#ef4444', '▼'
    val = f"{delta:{fmt}}{unit}"
    return (f"<span style='color:{color};font-size:12px;font-weight:600'>"
            f"{icon} {val}</span>")


def confidence_bar(conf: float, width: int = 120) -> str:
    """Mini progress bar untuk confidence model."""
    pct   = conf * 100
    color = '#22c55e' if pct >= 70 else '#f59e0b' if pct >= 50 else '#ef4444'
    return (f"<div style='width:{width}px;background:rgba(255,255,255,.1);"
            f"border-radius:4px;height:6px;overflow:hidden'>"
            f"<div style='width:{pct:.0f}%;height:100%;background:{color};"
            f"border-radius:4px'></div></div>"
            f"<span style='font-size:11px;color:{color}'>{pct:.0f}%</span>")


def anomaly_badge(is_anomaly: int) -> str:
    """Badge anomali / normal."""
    if is_anomaly:
        return ("<span style='background:rgba(239,68,68,.2);color:#ef4444;"
                "border:1px solid #ef444440;padding:2px 8px;border-radius:12px;"
                "font-size:11px;font-weight:700'>⚠ ANOMALI</span>")
    return ("<span style='background:rgba(34,197,94,.1);color:#22c55e;"
            "border:1px solid #22c55e40;padding:2px 8px;border-radius:12px;"
            "font-size:11px;font-weight:700'>✓ NORMAL</span>")
