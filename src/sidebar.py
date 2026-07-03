"""
src/sidebar.py — BaliGuard Sidebar
====================================
Navigasi + status panel kiri.
Ekspor satu fungsi: render_sidebar(ctx) → selected_nav, sel
"""
import streamlit as st

NAV_OPTIONS = [
    'Gambaran Umum & Garis Waktu',
    'Analisis Detail',
    'Sentimen',
    'Prediksi & Proyeksi',
    'Narasi AI',
]
NAV_ICONS_FALLBACK = {
    'Gambaran Umum & Garis Waktu': '📊',
    'Analisis Detail':             '🔍',
    'Sentimen':                    '💬',
    'Prediksi & Proyeksi':         '📅',
    'Narasi AI':                   '🤖',
}

"""
src/sidebar.py — BaliGuard Sidebar
"""
import streamlit as st
import pandas as pd
from src.config import COLOR_MAP

NAV_OPTIONS = [
    "Overview & Timeline",
    "Analisis Detail",
    "Sentimen",
    "Prediksi & Proyeksi",
    "Narasi AI",
]

NAMA_BULAN_ID = {
    '01':'Januari','02':'Februari','03':'Maret','04':'April',
    '05':'Mei','06':'Juni','07':'Juli','08':'Agustus',
    '09':'September','10':'Oktober','11':'November','12':'Desember',
}


def render_sidebar(ctx: dict) -> tuple:
    predictions = ctx['predictions']
    logo_html   = ctx.get('logo_html', '')
    nav_icons   = ctx.get('nav_icons', {})

    if 'selected_nav' not in st.session_state:
        st.session_state.selected_nav = NAV_OPTIONS[0]

    # Daftar bulan: historis + 2 tahun ke depan
    avail_hist = sorted(predictions['month'].unique(), reverse=True)
    _last_data = predictions['month'].iloc[-1]
    _p = pd.Period(_last_data, freq='M')
    _future = sorted(
        [str(_p + i) for i in range(1, 25) if str(_p + i) > _last_data],
        reverse=True
    )
    avail = _future + avail_hist

    with st.sidebar:
        # ── Logo + BaliGuard title ────────────────────────
        if '_sidebar_logo_html' not in st.session_state:
            st.session_state['_sidebar_logo_html'] = (
                "<div style='text-align:center;padding:20px 0 8px'>"
                f"<img src='{logo_html}' style='width:130px;height:130px;"
                f"object-fit:contain;margin-bottom:8px;border-radius:16px'/>"
                "<div style='font-family:DM Serif Display;font-size:30px;"
                "color:#f1f5f9;letter-spacing:-.01em'>BaliGuard</div>"
                "<div style='font-size:11px;color:#64748b;margin-top:5px;"
                "letter-spacing:.1em;font-weight:700'>EARLY WARNING SYSTEM</div>"
                "</div>"
            )
        st.markdown(st.session_state['_sidebar_logo_html'], unsafe_allow_html=True)
        st.divider()

        # ── Pilih Periode Analisis ────────────────────────
        st.markdown(
            "<div style='display:flex;align-items:center;gap:7px;margin-bottom:8px;"
            "font-size:13px;font-weight:600;color:#e2e8f0'>"
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
            "background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0'></span>"
            "Pilih Periode Analisis</div>",
            unsafe_allow_html=True
        )

        # Tahun dropdown
        list_tahun = sorted(set(m[:4] for m in avail), reverse=True)

        default_year = "2026"
        year_index = list_tahun.index(default_year) if default_year in list_tahun else 0

        selected_year = st.selectbox(
            "Tahun",
            list_tahun,
            index=year_index,
            key="year_sel"
        )

        # Bulan dropdown
        avail_months = sorted(
            [m for m in avail if m.startswith(selected_year)],
            reverse=True
        )

        format_bulan = {}
        for m in avail_months:
            label = NAMA_BULAN_ID.get(m[5:7], m[5:7])
            if m > _last_data:
                label += " [PROYEKSI]"
            format_bulan[m] = label

        default_month = "2026-04"
        month_index = (
            avail_months.index(default_month)
            if default_month in avail_months
            else 0
        )

        sel = st.selectbox(
            "Bulan",
            avail_months,
            index=month_index,
            format_func=lambda x: format_bulan.get(x, x),
            key="month_sel"
        )

        st.divider()

        # ── Navigasi ──────────────────────────────────────
        st.markdown(
            "<div style='font-size:12px;font-weight:700;color:#94a3b8;"
            "text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;"
            "font-family:\"DM Sans\"'>NAVIGASI</div>",
            unsafe_allow_html=True
        )

        import base64
        from pathlib import Path

        _NAV_IMG_MAP = {
            'Overview & Timeline': 'assets/icons/overview&timeline.png',
            'Analisis Detail':     'assets/icons/analisis_detail.png',
            'Sentimen':            'assets/icons/sentimen.png',
            'Prediksi & Proyeksi': 'assets/icons/prediksi&proyeksi.png',
            'Narasi AI':           'assets/icons/narasi_ai.png',
        }
        _SVG_ICONS = {
            'Overview & Timeline': '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            'Analisis Detail':     '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
            'Sentimen':            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
            'Prediksi & Proyeksi': '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
            'Narasi AI':           '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        }

        # Pre-load semua icon sekali di luar loop
        _nav_icon_cache = {}
        for _k, _fpath_str in _NAV_IMG_MAP.items():
            _fpath = Path(_fpath_str)
            if _fpath.exists():
                _ext = _fpath.suffix[1:]
                _b64 = base64.b64encode(_fpath.read_bytes()).decode()
                _nav_icon_cache[_k] = f'data:image/{_ext};base64,{_b64}'

        for _lbl in NAV_OPTIONS:
            _active  = st.session_state.selected_nav == _lbl
            _bg      = "rgba(249,247,113,0.15)" if _active else "transparent"
            _border  = "1px solid rgba(249,247,113,0.60)" if _active else "1px solid transparent"
            _color   = "#F9F871" if _active else "#94a3b8"
            _opacity = "1" if _active else "0.6"
            _fw      = "700" if _active else "500"

            _img = nav_icons.get(_lbl, '') or _nav_icon_cache.get(_lbl, '')
            if _img:
                icon_html = (
                    f"<img src='{_img}' style='width:18px;height:18px;"
                    f"object-fit:contain;opacity:{_opacity}'>"
                )
            else:
                _svg = _SVG_ICONS.get(_lbl, '')
                icon_html = (
                    f"<span style='display:inline-flex;align-items:center;"
                    f"color:{_color};opacity:{_opacity}'>{_svg}</span>"
                )

            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;padding:8px 12px;"
                f"border-radius:8px;background:{_bg};border:{_border};"
                f"margin-bottom:3px;cursor:pointer'>"
                f"{icon_html}"
                f"<span style='font-size:13px;font-weight:{_fw};color:{_color}'>"
                f"{_lbl}</span></div>",
                unsafe_allow_html=True
            )
            if st.button(_lbl, key=f"nav_{_lbl}", use_container_width=True,
                         type="primary" if _active else "secondary"):
                st.session_state.selected_nav = _lbl
                st.rerun()

        selected_nav = st.session_state.selected_nav
        st.divider()

        # ── Status Dipilih ────────────────────────────────
        try:
            rows = predictions[predictions['month'] == sel]
            row_s = rows.iloc[0] if len(rows) else predictions.iloc[-1]
            lv_s  = str(row_s.get('crisis_level', 'WASPADA'))
            sc_s  = float(row_s.get('crisis_score_100', 0))
            an_s  = int(float(row_s.get('iso_anomaly', 0)))
            col_s = COLOR_MAP.get(lv_s, '#fff')
            st.markdown(f"""
<div style='background:rgba(255,255,255,0.04);border-radius:12px;padding:14px 16px;
            border:1px solid rgba(255,255,255,0.07)'>
    <div style='font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;
                letter-spacing:.1em;margin-bottom:10px'>STATUS DIPILIH</div>
    <div style='font-family:"DM Serif Display";font-size:24px;color:{col_s};
                display:flex;align-items:center;gap:8px'>
        <span class='status-dot dot-{lv_s}' style='width:11px;height:11px;flex-shrink:0'></span>
        {lv_s}
    </div>
    <div style='font-family:"JetBrains Mono";font-size:12px;color:#64748b;margin-top:4px'>
        Score {sc_s:.1f} / 100
    </div>
    <div style='margin-top:8px;font-size:11px;font-weight:600;
                color:{"#f97316" if an_s else "#22c55e"}'>
        {"⚠️ Terdeteksi Perubahan Mendadak" if an_s else "✅ Tidak Terdeteksi Perubahan Mendadak"}
    </div>
</div>""", unsafe_allow_html=True)
        except Exception:
            pass

        st.divider()

        # ── Data Sumber, Model, Narasi ────────────────────
        st.markdown("""
<div style='font-size:11px;color:#64748b;line-height:1.9'>
    <b>DATA SUMBER</b><br>
    BPS Bali<br>
    Bank Indonesia<br>
    BMKG & USGS<br>
    GDELT<br>
    Google Trends<br>
    World Bank<br>
    Hotel Reviews<br>
    Kaggle<br>
    Tourist Reviews
</div>""", unsafe_allow_html=True)
        
        st.markdown("""
<div style='font-size:11px;color:#64748b;line-height:1.9'>
    <b>MODEL</b><br>
    Isolation Forest<br>
    Random Forest<br>
    XLM-RoBERTa<br>
    External Risk Engine
</div>""", unsafe_allow_html=True)
        
        st.markdown("""
<div style='font-size:11px;color:#64748b;line-height:1.9'>
    <b>AI & ANALYTICS</b><br>
    Groq LLM<br>
    SWOT Generator<br>
    Narrative Engine
</div>""", unsafe_allow_html=True)

    return selected_nav, sel