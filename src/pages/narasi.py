"""
src/pages/narasi.py — BaliGuard: Narasi AI
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
from src.services.llm_service import call_groq, get_or_generate, build_narrative_prompt
from src.services.forecast import forecast_months

from src.utils import (
    sf, _tick, kpi_html, alert_html, status_dot,
    LEVEL_COLORS, LABEL_ORDER,
    FEATURES_CORE, FEATURES_LAG,
)
from src.config import COLOR_MAP
EMOJI_MAP = {
    'AMAN':    '🟢',
    'WASPADA': '🟡',
    'SIAGA':   '🟠',
    'KRISIS':  '🔴',
}

def _get_groq_key() -> str:
    """Ambil Groq API key dari st.secrets atau environment variable."""
    try:
        return st.secrets.get("GROQ_API_KEY", "") or st.secrets.get("groq_api_key", "")
    except Exception:
        pass
    import os
    return os.getenv("GROQ_API_KEY", "")

def render(ctx: dict) -> None:
    """Render halaman Narasi AI."""
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

    _tick("nav_start_narasi")

    # ── Hero banner ──────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#052e16 0%,#064e3b 60%,#065f46 100%);
                border-radius:16px;padding:24px 28px;margin-bottom:24px;
                border:1px solid rgba(74,222,128,0.18);box-shadow:0 4px 24px rgba(0,0,0,0.3)'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px'>
            <div>
                <div style='font-size:10px;font-weight:700;color:rgba(74,222,128,0.55);
                            text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px'>
                    🤖 AI NARRATIVE ENGINE · Powered by Groq
                </div>
                <div style='font-size:22px;color:#bbf7d0;line-height:1.3;margin-bottom:8px;font-weight:600'>
                    Mengubah Data Menjadi Laporan Siap Baca
                </div>
                <div style='font-size:13px;color:#6ee7b7;line-height:1.8;max-width:560px'>
                    Narasi AI menganalisis output model ML — crisis score, prediksi RF, anomali,
                    wisman, sentimen — lalu <b>menyusunnya menjadi laporan Bahasa Indonesia</b>
                    yang siap digunakan pemangku kebijakan dan dinas pariwisata.
                </div>
            </div>
            <div style='text-align:center;background:rgba(0,0,0,0.25);border-radius:12px;
                        padding:14px 20px;border:1px solid rgba(74,222,128,0.15)'>
                <div style='font-size:10px;color:rgba(74,222,128,0.6);text-transform:uppercase;
                            letter-spacing:.08em;margin-bottom:4px'>PROVIDER</div>
                <div style='font-family:monospace;font-size:13px;color:#4ade80;font-weight:700'>
                    Groq Cloud API
                </div>
                <div style='font-size:12px;color:#86efac;margin-top:6px'>Latensi &lt; 1 detik · Gratis</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Kegunaan cards ────────────────────────────────────
    st.markdown("""
    <div style='display:flex;align-items:center;gap:0;width:100%;margin-bottom:14px'>
        <div style='flex:1;height:1px;background:#1119FF'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#1119FF;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>APA GUNANYA NARASI AI?</div>
        <div style='flex:1;height:1px;background:#1119FF'></div>
    </div>
    <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:24px'>
        <div style='background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#93c5fd;margin-bottom:6px;text-align:center'>Laporan Dinas / Rapat</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Draft laporan bulanan siap presentasi ke kepala dinas atau DPRD tanpa tulis manual.
            </div>
        </div>
        <div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#d90000;margin-bottom:6px;text-align:center'>Peringatan Dini Krisis</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Saat SIAGA/KRISIS terdeteksi, sistem menyusun teks peringatan + rekomendasi untuk stakeholder.
            </div>
        </div>
        <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                    border-radius:12px;padding:20px 16px 16px'>
            <div style='font-size:16px;font-weight:800;color:#fcd34d;margin-bottom:6px;text-align:center'>Press Release / Media</div>
            <div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>
                Ringkasan berbasis data sebagai bahan siaran pers atau infografis pariwisata Bali.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:4px 0 20px'></div>",
                unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # CONFIG COLUMNS
    # ══════════════════════════════════════════════════════
    # ─ 1. TIPE LAPORAN — FULL WIDTH 4 CARDS ──────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:18px'>
        <div style='flex:1;height:1px;background:#1119FF'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#1119FF;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>PILIH TIPE LAPORAN</div>
        <div style='flex:1;height:1px;background:#1119FF'></div>
    </div>""", unsafe_allow_html=True)

    REPORT_CARDS = {
        'summary': {
            'icon':'⚡','title':'Quick Summary','desc':'2–3 kalimat ringkas',
            'detail':'Cocok untuk KPI card, notifikasi, atau update cepat di grup WhatsApp dinas.',
            'color':'#3b82f6','bg':'rgba(59,130,246,0.10)','border':'rgba(59,130,246,0.30)',
        },
        'alert': {
            'icon':'🚨','title':'Emergency Alert','desc':'Peringatan darurat ≤120 kata',
            'detail':'Status level + 3 indikator kritis + 1 rekomendasi segera. Untuk SIAGA/KRISIS.',
            'color':'#d90000','bg':'rgba(239,68,68,0.10)','border':'rgba(239,68,68,0.30)',
        },
        'monthly': {
            'icon':'📑','title':'Laporan Bulanan','desc':'Laporan lengkap 4 bagian',
            'detail':'Ringkasan Eksekutif · Analisis Indikator · Faktor Pendorong · Rekomendasi.',
            'color':'#22c55e','bg':'rgba(74,222,128,0.10)','border':'rgba(74,222,128,0.30)',
        },
        'predict': {
            'icon':'🔮','title':'Prediksi AI','desc':'Proyeksi + skenario risiko',
            'detail':'Prediksi 3–6 bulan ke depan berbasis tren ML, faktor risiko, dan rekomendasi antisipatif.',
            'color':'#FF6C43','bg':'rgba(251,146,60,0.12)','border':'rgba(255,108,67,0.30)',
        },
    }

    if 'report_type_sel' not in st.session_state:
        st.session_state['report_type_sel'] = 'summary'

    _rt_cols = st.columns(4)
    for _i, (_key, _card) in enumerate(REPORT_CARDS.items()):
        with _rt_cols[_i]:
            _is_sel = st.session_state['report_type_sel'] == _key
            _bdr    = ("2px solid " + _card['color']) if _is_sel else ("1px solid " + _card['border'])
            _shad   = ("box-shadow:0 0 14px " + _card['color'] + "44;") if _is_sel else ""
            _opac   = "1" if _is_sel else "0.90"
            st.markdown(
                "<div style='background:" + _card['bg'] + ";border:" + _bdr + ";"
                "border-radius:12px;padding:20px 16px 16px;min-height:140px;margin-bottom:6px;"
                "opacity:" + _opac + ";" + _shad + ";transition:opacity .2s'>"
                "<div style='font-size:16px;font-weight:800;color:" + _card['color'] + ";margin-bottom:4px;text-align:center'>"
                + _card['title'] + "</div>"
                "<div style='font-size:13px;color:#cbd5e1;font-weight:700;margin-bottom:6px;text-align:center'>"
                + _card['desc'] + "</div>"
                "<div style='font-size:13px;color:#e2e8f0;line-height:1.6;text-align:center'>" + _card['detail'] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button(_card['title'], key="rt_" + _key, width="stretch"):
                st.session_state['report_type_sel'] = _key
                st.rerun()

    # ── Warna + hover + selected state tombol via JS ──────
    _active_title = REPORT_CARDS[st.session_state['report_type_sel']]['title']
    _btn_map = {c['title']: c['color'] for c in REPORT_CARDS.values()}
    _js_map  = str(_btn_map).replace("'", '"')
    _js_active = _active_title
    components.html(f"""
    <script>
    (function() {{
        const colors  = {_js_map};
        const active  = "{_js_active}";

        function hexToRgba(hex, a) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{a}})`;
        }}

        function style() {{
            const btns = window.parent.document.querySelectorAll('.stButton button');
            btns.forEach(btn => {{
                const label = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                const color = colors[label];
                if (!color) return;

                const isSel = (label === active);

                // base style
                btn.style.setProperty('background',    isSel ? color : hexToRgba(color, 0.45), 'important');
                btn.style.setProperty('color',         '#ffffff', 'important');
                btn.style.setProperty('border',        '1px solid ' + hexToRgba(color, 0.6), 'important');
                btn.style.setProperty('font-weight',   '700', 'important');
                btn.style.setProperty('border-radius', '8px', 'important');
                btn.style.setProperty('transition',    'background .18s, box-shadow .18s', 'important');
                if (isSel) {{
                    btn.style.setProperty('box-shadow', '0 0 12px ' + hexToRgba(color, 0.5), 'important');
                }} else {{
                    btn.style.removeProperty('box-shadow');
                }}

                // hover
                btn.onmouseenter = () => {{
                    btn.style.setProperty('background',  color, 'important');
                    btn.style.setProperty('box-shadow',  '0 0 14px ' + hexToRgba(color, 0.55), 'important');
                    btn.style.setProperty('opacity',     '1', 'important');
                }};
                btn.onmouseleave = () => {{
                    btn.style.setProperty('background',  isSel ? color : hexToRgba(color, 0.45), 'important');
                    btn.style.setProperty('box-shadow',  isSel ? '0 0 12px ' + hexToRgba(color, 0.5) : 'none', 'important');
                }};
            }});
        }}

        style();
        setTimeout(style, 200);
        setTimeout(style, 600);
        new MutationObserver(style).observe(
            window.parent.document.body, {{childList:true, subtree:true}}
        );
    }})();
    </script>
    """, height=0)

    report_type = st.session_state['report_type_sel']
    _sel_card   = REPORT_CARDS[report_type]
    st.markdown(
        "<div style='margin-top:-12px;margin-bottom:20px;background:" + _sel_card['bg'] + ";border-radius:8px;"
        "padding:12px 16px;border-left:3px solid " + _sel_card['color'] + "'>"
        "<span style='font-size:15px;color:#94a3b8'>Tipe dipilih: "
        "<b style='color:" + _sel_card['color'] + "'>" + _sel_card['title'] + "</b>"
        " &nbsp;·&nbsp; <span style='color:#cbd5e1'>" + _sel_card['desc'] + "</span></span></div>",
        unsafe_allow_html=True
    )

    # ─ MODEL (4 kolom horizontal full width) ────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:16px'>
        <div style='flex:1;height:1px;background:#1119FF'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#1119FF;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>PILIH MODEL AI</div>
        <div style='flex:1;height:1px;background:#1119FF'></div>
    </div>""", unsafe_allow_html=True)

    GROQ_MODELS = {
        'llama-3.3-70b-versatile': {
            'label': 'Llama 3.3 70B', 'tag': 'Terbaik',
            'desc': 'Akurasi tinggi, analisis mendalam',
            'color': '#a78bfa', 'bg': 'rgba(167,139,250,0.12)', 'border': 'rgba(167,139,250,0.30)',
            'icon': '🏆',
        },
        'llama-3.1-8b-instant': {
            'label': 'Llama 3.1 8B', 'tag': 'Tercepat',
            'desc': 'Respons < 0.5 detik, ringkas',
            'color': '#34d399', 'bg': 'rgba(52,211,153,0.12)', 'border': 'rgba(52,211,153,0.30)',
            'icon': '⚡',
        },
        'qwen/qwen3-32b': {
            'label': 'Qwen3 32B', 'tag': 'Bahasa Natural',
            'desc': 'Narasi mengalir & mudah dibaca',
            'color': '#60a5fa', 'bg': 'rgba(96,165,250,0.12)', 'border': 'rgba(96,165,250,0.30)',
            'icon': '📄',
        },
        'meta-llama/llama-4-scout-17b-16e-instruct': {
            'label': 'Llama 4 Scout', 'tag': 'Konteks Panjang',
            'desc': 'Laporan detail & komprehensif',
            'color': '#fb923c', 'bg': 'rgba(251,146,60,0.12)', 'border': 'rgba(251,146,60,0.30)',
            'icon': '✍️',
        },
    }

    if 'selected_model_key' not in st.session_state:
        st.session_state['selected_model_key'] = 'llama-3.3-70b-versatile'

    # ── Warna tiap model MENGIKUTI POSISI KOLOM tipe laporan di atasnya ──
    # Kolom 0: Quick Summary (biru), Kolom 1: Emergency Alert (merah),
    # Kolom 2: Laporan Bulanan (hijau), Kolom 3: Prediksi AI (ungu)
    _report_list = list(REPORT_CARDS.values())   # urutan sama: summary, alert, monthly, predict

    _mcols = st.columns(4)
    _model_items = list(GROQ_MODELS.items())
    for _mi, (_mkey, _mcard) in enumerate(_model_items):
        # Ambil warna dari report card sejajar (posisi _mi)
        _paired = _report_list[_mi]
        _pc     = _paired['color']
        _pb     = _paired['bg']
        _pbr    = _paired['border']

        with _mcols[_mi]:
            _is_msel = st.session_state['selected_model_key'] == _mkey
            _m_bdr   = ("2px solid " + _pc) if _is_msel else ("1px solid " + _pbr)
            _m_shad  = ("box-shadow:0 0 14px " + _pc + "55;") if _is_msel else ""
            _m_opac  = "1" if _is_msel else "1"
            st.markdown(
                "<div style='background:" + _pb + ";border:" + _m_bdr + ";"
                "border-radius:10px;padding:12px 14px;opacity:" + _m_opac + ";" + _m_shad + ";margin-bottom:6px;"
                "transition:opacity .2s,border .2s,box-shadow .2s'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>"
                "<div style='font-size:16px;font-weight:800;color:" + _pc + "'>" + _mcard['label'] + "</div>"
                "<span style='font-size:11px;font-weight:700;background:" + _pc + "22;"
                "color:" + _pc + ";padding:3px 9px;border-radius:10px'>"
                + _mcard['tag'] + "</span></div>"
                "<div style='font-size:13px;color:#cbd5e1;line-height:1.5'>" + _mcard['desc'] + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button(_mcard['label'], key="model_" + _mkey, width="stretch"):
                st.session_state['selected_model_key'] = _mkey
                st.rerun()

    selected_model = st.session_state['selected_model_key']
    _sel_mcard     = GROQ_MODELS[selected_model]

    # ── JS: tiap tombol model pakai warna report sejajarnya (per posisi) ──
    # Bangun map: label → warna report sejajar
    _model_color_map = {
        list(GROQ_MODELS.values())[i]['label']: _report_list[i]['color']
        for i in range(4)
    }
    _sel_model_label  = _sel_mcard['label']
    _js_model_color_map = str(_model_color_map).replace("'", '"')
    components.html(f"""
    <script>
    (function() {{
        const colorMap   = {_js_model_color_map};
        const activeModel = "{_sel_model_label}";

        function hexToRgba(hex, a) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{a}})`;
        }}

        function styleModelBtns() {{
            const btns = window.parent.document.querySelectorAll('.stButton button');
            btns.forEach(btn => {{
                const label = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                const color = colorMap[label];
                if (!color) return;

                const isSel = (label === activeModel);

                btn.style.setProperty('background',    isSel ? color : hexToRgba(color, 0.30), 'important');
                btn.style.setProperty('color',         '#ffffff', 'important');
                btn.style.setProperty('border',        '1px solid ' + hexToRgba(color, isSel ? 0.85 : 0.45), 'important');
                btn.style.setProperty('font-weight',   '700', 'important');
                btn.style.setProperty('border-radius', '8px', 'important');
                btn.style.setProperty('transition',    'background .18s, box-shadow .18s', 'important');
                if (isSel) {{
                    btn.style.setProperty('box-shadow', '0 0 12px ' + hexToRgba(color, 0.50), 'important');
                }} else {{
                    btn.style.setProperty('box-shadow', 'none', 'important');
                }}

                btn.onmouseenter = () => {{
                    btn.style.setProperty('background',  color, 'important');
                    btn.style.setProperty('box-shadow',  '0 0 14px ' + hexToRgba(color, 0.55), 'important');
                    btn.style.setProperty('opacity',     '1', 'important');
                }};
                btn.onmouseleave = () => {{
                    btn.style.setProperty('background',  isSel ? color : hexToRgba(color, 0.30), 'important');
                    btn.style.setProperty('box-shadow',  isSel ? '0 0 12px ' + hexToRgba(color, 0.50) : 'none', 'important');
                }};
            }});
        }}

        styleModelBtns();
        setTimeout(styleModelBtns, 200);
        setTimeout(styleModelBtns, 600);
        new MutationObserver(styleModelBtns).observe(
            window.parent.document.body, {{childList:true, subtree:true}}
        );
    }})();
    </script>
    """, height=0)

    # ── Status bar model: warna ikut warna posisi model yg dipilih ──
    _sel_model_idx   = list(GROQ_MODELS.keys()).index(selected_model)
    _sel_pair_card   = _report_list[_sel_model_idx]
    st.markdown(
        "<div style='margin-top:-12px;background:" + _sel_pair_card['bg'] + ";border-radius:8px;"
        "padding:12px 16px;border-left:3px solid " + _sel_pair_card['color'] + "'>"
        "<span style='font-size:15px;color:#94a3b8'>Model: "
        "<b style='color:" + _sel_pair_card['color'] + "'>" + _sel_mcard['label'] + "</b>"
        " &nbsp;·&nbsp; <span style='color:#cbd5e1'>" + _sel_mcard['tag'] + "</span></span></div>",
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin:16px 0 8px'></div>", unsafe_allow_html=True)

    # ─ API & STATUS ──────────────────────────
    st.markdown("""<div style='display:flex;align-items:center;gap:0;width:100%;margin-top:28px;margin-bottom:18px'>
        <div style='flex:1;height:1px;background:#1119FF'></div>
        <div style='padding:0 20px;font-size:15px;font-weight:700;color:#1119FF;text-transform:uppercase;
                    letter-spacing:.12em;white-space:nowrap'>API &amp; STATUS</div>
        <div style='flex:1;height:1px;background:#1119FF'></div>
    </div>""", unsafe_allow_html=True)

    # ─ PILIH BULAN & TAHUN ────────────────────────────────
    _avail_months_hist = sorted(predictions['month'].unique())
    _last_data_month   = _avail_months_hist[-1]
    _last_p            = pd.Period(_last_data_month, freq='M')
    _fc_extra, _       = forecast_months(predictions, n=18, from_month=str(_last_p - 1))
    _fc_months_only    = [f['month'] for f in _fc_extra]
    _fc_score_map      = {f['month']: f['score'] for f in _fc_extra}
    _fc_level_map      = {f['month']: f['level'] for f in _fc_extra}
    _all_months        = _avail_months_hist + [m for m in _fc_months_only if m not in _avail_months_hist]
    _avail_years       = sorted(set(m[:4] for m in _all_months), reverse=True)

    if 'narasi_year_sel' not in st.session_state:
        st.session_state['narasi_year_sel'] = sel[:4]
    if 'narasi_month_sel' not in st.session_state:
        st.session_state['narasi_month_sel'] = sel

    _MONTH_ID = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
    def _month_label_fn(m):
        base = _MONTH_ID[int(m[5:7])-1]
        return base

    # 4 kolom sejajar: Tahun | Bulan | Status | Cache
    _c_year, _c_month, _c_status, _c_cache = st.columns([1, 1, 1, 1])

    with _c_year:
        st.markdown("""<div style='font-size:15px;font-weight:700;color:#FF0000;text-transform:uppercase;
                    letter-spacing:.12em;margin-bottom:12px'>BULAN DAN TAHUN YANG DIANALISIS</div>""",
                    unsafe_allow_html=True)
        _ny_idx  = _avail_years.index(st.session_state['narasi_year_sel']) \
                   if st.session_state['narasi_year_sel'] in _avail_years else 0
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0;font-size:16px;font-weight:600;color:#1119FF;margin-bottom:4px'>" "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0;margin-right:7px'></span>Tahun</div>", unsafe_allow_html=True)
        _sel_year = st.selectbox("", _avail_years, index=_ny_idx, key="narasi_year_box", label_visibility="collapsed")
        st.session_state['narasi_year_sel'] = _sel_year

    _months_for_year = [m for m in _all_months if m.startswith(_sel_year)]

    with _c_month:
        st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='display:flex;align-items:center;gap:0;font-size:16px;font-weight:600;color:#1119FF;margin-bottom:4px'>" "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;flex-shrink:0;margin-right:7px'></span>Bulan</div>", unsafe_allow_html=True)
        _prev_nm = st.session_state.get('narasi_month_sel', sel)
        _nm_default = _prev_nm if _prev_nm in _months_for_year else _months_for_year[-1]
        _nm_idx  = _months_for_year.index(_nm_default)
        _sel_month = st.selectbox("", _months_for_year,
                                  format_func=_month_label_fn,
                                  index=_nm_idx, key="narasi_month_box", label_visibility="collapsed")
        st.session_state['narasi_month_sel'] = _sel_month

    narasi_target   = st.session_state['narasi_month_sel']
    _is_fc_month    = narasi_target not in _avail_months_hist
    if _is_fc_month:
        _narasi_level = _fc_level_map.get(narasi_target, 'WASPADA')
        _narasi_score = _fc_score_map.get(narasi_target, 0.0)
    else:
        _narasi_row   = get_row(narasi_target)
        _narasi_level = str(_narasi_row.get('crisis_level', 'WASPADA'))
        _narasi_score = sf(_narasi_row.get('crisis_score_100', 0))

    _fc_badge = (
        "<span style='font-size:10px;font-weight:700;background:rgba(167,139,250,0.15);"
        "color:#a78bfa;padding:2px 8px;border-radius:10px'>Proyeksi</span>"
    ) if _is_fc_month else ""

    # Cache status for narasi_target
    _has_cache    = narasi_target in narratives_cache
    _cache_level  = narratives_cache[narasi_target].get('crisis_level','') if _has_cache else ''
    _cache_tokens = narratives_cache[narasi_target].get('tokens', 0)        if _has_cache else 0

    with _c_status:
        _status_clr = COLOR_MAP.get(_narasi_level, '#fff')
        st.markdown("<div style='font-size:15px;font-weight:600;color:#e2e8f0;margin-top:31px;margin-bottom:4px'>Status Bulan</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.10);"
            "border-radius:8px;padding:0 14px;display:flex;align-items:center;gap:12px;"
            "height:42px;box-sizing:border-box'>"
            "<span style='font-size:15px;font-weight:800;color:" + _status_clr + "'>" + _narasi_level + "</span>"
            "<span style='font-family:monospace;font-size:13px;color:#94a3b8'>Score " + str(round(_narasi_score, 1)) + "/100</span>"
            + (_fc_badge if _is_fc_month else "") +
            "</div>",
            unsafe_allow_html=True
        )

    with _c_cache:
        _cache_bg  = "rgba(34,197,94,0.07)"  if _has_cache else "rgba(255,255,255,0.04)"
        _cache_bdr = "rgba(34,197,94,0.25)"  if _has_cache else "rgba(255,255,255,0.10)"
        _cache_inner = (
            "<span style='font-size:15px;color:#4ade80;font-weight:700'>Tersedia</span>"
            "<span style='font-size:13px;color:#94a3b8;margin-left:8px'>Level: <b style='color:#e2e8f0'>" + _cache_level + "</b>"
            " · " + str(_cache_tokens) + " tokens</span>"
        ) if _has_cache else (
            "<span style='font-size:14px;color:#94a3b8'>Belum ada cache untuk bulan ini</span>"
        )
        st.markdown("<div style='font-size:15px;font-weight:600;color:#e2e8f0;margin-top:31px;margin-bottom:4px'>Cache Narasi</div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:" + _cache_bg + ";border:1px solid " + _cache_bdr + ";"
            "border-radius:8px;padding:0 14px;display:flex;align-items:center;gap:6px;"
            "height:42px;box-sizing:border-box'>"
            + _cache_inner + "</div>",
            unsafe_allow_html=True
        )

    # ─ API KEY + GENERATE ─────────────────────────────────
    # st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    # if not groq_key:
    #     st.markdown("""
    #     <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);
    #                 border-left:4px solid #f59e0b;border-radius:12px;padding:20px 22px;
    #                 margin-top:12px;display:flex;align-items:center;gap:24px'>
    #         <div style='flex:1'>
    #             <div style='font-size:16px;font-weight:800;color:#fbbf24;margin-bottom:8px;
    #                         letter-spacing:-.01em'>
    #                 Groq API Key Diperlukan
    #             </div>
    #             <div style='font-size:14px;color:#d97706;line-height:1.75;font-weight:500'>
    #                 Masukkan API Key di sidebar <strong style='color:#fbbf24'>(panel kiri)</strong>
    #                 untuk mengaktifkan fitur Narasi AI.<br>
    #                 Key 100% gratis dan bisa didapat dalam <strong style='color:#fbbf24'>30 detik</strong>
    #                 — tidak butuh kartu kredit.
    #             </div>
    #         </div>
    #         <div style='flex-shrink:0'>
    #             <a href='https://console.groq.com/keys' target='_blank'
    #                style='display:inline-flex;align-items:center;gap:8px;
    #                       background:linear-gradient(135deg,#f59e0b,#d97706);
    #                       color:#0a0a0a;font-size:14px;font-weight:800;
    #                       padding:12px 24px;border-radius:8px;text-decoration:none;
    #                       box-shadow:0 4px 16px rgba(245,158,11,0.4);
    #                       white-space:nowrap;letter-spacing:.01em'>
    #                 Dapatkan Key Gratis →
    #             </a>
    #         </div>
    #     </div>
    #     """, unsafe_allow_html=True)
    # else:
    #     st.markdown("""
    #     <div style='background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
    #                 border-radius:12px;padding:12px 16px;margin-top:12px'>
    #         <div style='font-size:12px;color:#4ade80;font-weight:700'>API Key Terhubung</div>
    #         <div style='font-size:10px;color:#475569;margin-top:3px'>Siap generate narasi</div>
    #     </div>
    #     """, unsafe_allow_html=True)
    groq_key = _get_groq_key()
    # ── Generate button — scoped CSS via unique container ─
    st.markdown("""
    <style>
    /* Scope ONLY to main content area, excluding sidebar */
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"] {
        background: #16a34a !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: .08em !important;
        padding: 14px 28px !important;
        border-radius: 10px !important;
        border: 1px solid #22c55e !important;
        box-shadow: 0 2px 14px rgba(22,163,74,0.4) !important;
        transition: all .18s ease !important;
        text-transform: uppercase !important;
    }
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:hover:not(:disabled) {
        background: #15803d !important;
        border-color: #4ade80 !important;
        box-shadow: 0 4px 22px rgba(22,163,74,0.55) !important;
        transform: translateY(-1px) !important;
    }
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:active:not(:disabled) {
        transform: translateY(0) !important;
    }
    /* Disabled — amber tint, tetap kelihatan */
    section[data-testid="stMain"] div[data-testid="stButton"] > button[kind="primary"]:disabled {
        background: rgba(245,158,11,0.15) !important;
        color: #f59e0b !important;
        border: 1px solid rgba(245,158,11,0.3) !important;
        box-shadow: none !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _btn_label = "Generate Narasi AI"
    gen_btn = st.button(_btn_label, type="primary",
                        use_container_width=True, disabled=not bool(groq_key))

    # ── Divider ──────────────────────────────────────────
    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:20px 0'></div>",
                unsafe_allow_html=True)

    # ── Output area ──────────────────────────────────────
    if _has_cache and not gen_btn:
        cached_n = narratives_cache[narasi_target]
        _clv  = cached_n.get('crisis_level', '')
        _clr  = COLOR_MAP.get(_clv, '#94a3b8')
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px'>"
            "<div style='font-size:16px;font-weight:700;color:#FFFFFF;text-transform:uppercase;"
            "letter-spacing:.1em'>NARASI TERSIMPAN</div>"
            "<span style='background:" + _clr + "22;color:" + _clr + ";font-size:10px;font-weight:700;"
            "padding:3px 10px;border-radius:20px;border:1px solid " + _clr + "44'>"
            + EMOJI_MAP.get(_clv,'') + " " + _clv + "</span>"
            "<span style='font-family:monospace;font-size:14px;color:#475569'>"
            + cached_n.get('month','') + "</span>"
            "<span style='font-size:10px;color:#334155'>·</span>"
            "<span style='font-family:monospace;font-size:14px;color:#334155'>"
            + str(cached_n.get('tokens',0)) + " tokens</span></div>"
            "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);"
            "border-radius:14px;padding:26px 30px;line-height:1.95;font-size:14px;"
            "color:#cbd5e1;border-top:3px solid " + _clr + "'>"
            + cached_n["narrative"].replace('\n', '<br>') + "</div>",
            unsafe_allow_html=True
        )

    if gen_btn and groq_key:
        with st.spinner("🤖 " + selected_model + " sedang menganalisis data " + narasi_target + "..."):
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                sys.path.insert(0, '.')
                from groq import Groq as _Groq
                import numpy as _np

                # Dapatkan data baris — historis atau proyeksi
                if _is_fc_month:
                    # Bulan proyeksi: ambil data terakhir sebagai basis, timpa dengan nilai proyeksi
                    _base_row        = dict(predictions.iloc[-1])
                    _narasi_row_data = _base_row.copy()
                    _narasi_row_data['month']           = narasi_target
                    _narasi_row_data['crisis_score_100'] = _narasi_score
                    _narasi_row_data['crisis_level']     = _narasi_level
                    _narasi_row_data['rf_predicted_level'] = _narasi_level
                    _narasi_row_data['rf_confidence']    = 0.70
                    _history = predictions.tail(3).to_dict('records')
                else:
                    _narasi_row_data = get_row(narasi_target)
                    _idx     = list(predictions['month']).index(narasi_target) \
                               if narasi_target in list(predictions['month']) else len(predictions)-1
                    _history = predictions.iloc[max(0, _idx - 3):_idx].to_dict('records')

                _ctx = {
                    'month'        : str(_narasi_row_data.get('month', narasi_target)),
                    'crisis_score' : round(float(_narasi_row_data.get('crisis_score_100', 0)), 1),
                    'crisis_level' : _narasi_level,
                    'rf_predicted' : str(_narasi_row_data.get('rf_predicted_level', 'N/A')),
                    'rf_confidence': round(float(_narasi_row_data.get('rf_confidence', 0)) * 100, 1),
                    'is_anomaly'   : int(sf(_narasi_row_data.get('iso_anomaly', 0))),
                    'wisman'       : int(sf(_narasi_row_data.get('wisman', 0))),
                    'tpk_bintang'  : round(float(_narasi_row_data.get('tpk_bintang', 0)), 1),
                    'inflasi'      : round(float(_narasi_row_data.get('inflasi_processed', 0)), 2),
                    'usd_idr'      : round(float(_narasi_row_data.get('usd_idr_avg', 0)), 0),
                    'sentiment'    : round(float(_narasi_row_data.get('avg_sentiment_monthly', 0)), 3),
                    'prob_krisis'  : round(float(_narasi_row_data.get('prob_krisis', 0)) * 100, 1),
                    'prob_siaga'   : round(float(_narasi_row_data.get('prob_siaga', 0)) * 100, 1),
                    'bali_share'   : round(float(_narasi_row_data.get('bali_share_pct', 0)), 1),
                    'wisman_zscore': round(float(_narasi_row_data.get('wisman_zscore', 0)), 2),
                }
                if _history:
                    _avg3 = _np.mean([r.get('wisman', 0) for r in _history[-3:]])
                    _ctx['wisman_trend']  = 'naik' if _ctx['wisman'] > _avg3 else 'turun'
                    _ctx['avg_wisman_3m'] = round(_avg3, 0)
                    _ctx['prev_levels']   = [r.get('crisis_level','N/A') for r in _history[-3:]]
                    # MoM delta untuk konteks kausal
                    _prev_r = _history[-1] if _history else {}
                    def _d(a, b, key): 
                        pv = float(_prev_r.get(key,0)); cv = float(a.get(key,0) if isinstance(a,dict) else a)
                        return round(cv - pv, 3) if pv != 0 else 0
                    _prev_w = float(_prev_r.get('wisman', 1))
                    _ctx['wisman_delta_pct'] = round((_ctx['wisman'] - _prev_w) / max(1,_prev_w) * 100, 1)
                    _ctx['score_delta']      = round(_ctx['crisis_score'] - float(_prev_r.get('crisis_score_100', _ctx['crisis_score'])), 1)
                    _ctx['sent_delta']       = round(_ctx['sentiment'] - float(_prev_r.get('avg_sentiment_monthly', _ctx['sentiment'])), 3)
                    _ctx['tpk_delta']        = round(_ctx['tpk_bintang'] - float(_prev_r.get('tpk_bintang', _ctx['tpk_bintang'])), 1)
                    _ctx['usd_delta_pct']    = round((float(_prev_r.get('usd_idr_avg',0)) and
                                               (_ctx['usd_idr'] - float(_prev_r.get('usd_idr_avg',0))) /
                                               float(_prev_r.get('usd_idr_avg',1)) * 100) or 0, 1)
                    _ctx['prev_level']       = _prev_r.get('crisis_level', 'N/A')
                else:
                    _ctx['wisman_trend']     = 'tidak tersedia'
                    _ctx['avg_wisman_3m']    = 0
                    _ctx['prev_levels']      = []
                    _ctx['wisman_delta_pct'] = 0
                    _ctx['score_delta']      = 0
                    _ctx['sent_delta']       = 0
                    _ctx['tpk_delta']        = 0
                    _ctx['usd_delta_pct']    = 0
                    _ctx['prev_level']       = 'N/A'

                LEVEL_DESC = {
                    'AMAN':'kondisi pariwisata normal','WASPADA':'ada sinyal awal yang perlu dipantau',
                    'SIAGA':'tekanan signifikan pada sektor pariwisata',
                    'KRISIS':'krisis pariwisata yang membutuhkan respons segera'
                }
                _lv_text = LEVEL_DESC.get(_ctx['crisis_level'], _ctx['crisis_level'])
                _prev    = ' -> '.join(_ctx['prev_levels']) if _ctx['prev_levels'] else 'N/A'

                # Deteksi kontradiksi (sentimen vs wisman)
                _contradiction = ""
                if _ctx['wisman_delta_pct'] < -5 and _ctx['sent_delta'] > 0.05:
                    _contradiction = "KONTRADIKSI: Wisman turun tapi sentimen naik — kemungkinan tekanan dari faktor akses/ekonomi bukan kepuasan."
                elif _ctx['wisman_delta_pct'] > 5 and _ctx['sent_delta'] < -0.05:
                    _contradiction = "KONTRADIKSI: Wisman naik tapi sentimen turun — perlu investigasi kualitas layanan atau pengalaman wisata."
                elif _ctx['score_delta'] > 5 and _ctx['sent_delta'] > 0.1:
                    _contradiction = "KONTRADIKSI: Crisis score memburuk tapi sentimen publik positif — tekanan mungkin struktural, bukan persepsi."

                _data_block = (
                    f"DATA PARIWISATA BALI - {_ctx['month']}\n"
                    f"Crisis Score: {_ctx['crisis_score']}/100 -> Level {_ctx['crisis_level']} ({_lv_text})\n"
                    f"  Perubahan score vs bulan lalu: {_ctx['score_delta']:+.1f} poin | Level sebelumnya: {_ctx['prev_level']}\n"
                    f"Prediksi RF: {_ctx['rf_predicted']} (confidence: {_ctx['rf_confidence']}%) | "
                    f"Anomali IF: {'Ya' if _ctx['is_anomaly'] else 'Tidak'}\n"
                    f"P(Krisis): {_ctx['prob_krisis']}% | P(Siaga): {_ctx['prob_siaga']}%\n"
                    f"Wisman: {_ctx['wisman']:,.0f} ({_ctx['wisman_delta_pct']:+.1f}% MoM, trend: {_ctx['wisman_trend']}, avg 3bln: {int(_ctx['avg_wisman_3m']):,.0f})\n"
                    f"TPK Hotel: {_ctx['tpk_bintang']}% ({_ctx['tpk_delta']:+.1f}pp MoM)\n"
                    f"USD/IDR: Rp {int(_ctx['usd_idr']):,} ({_ctx['usd_delta_pct']:+.1f}% MoM)\n"
                    f"Inflasi: {_ctx['inflasi']}% | Sentimen: {_ctx['sentiment']} ({_ctx['sent_delta']:+.3f} MoM)\n"
                    f"Pangsa Bali: {_ctx['bali_share']}% | Z-score: {_ctx['wisman_zscore']}\n"
                    f"Histori level: {_prev}\n"
                    + (f"⚠️ {_contradiction}\n" if _contradiction else "")
                )

                if report_type == 'summary':
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard — sistem early warning pariwisata Bali.\n"
                        + _data_block +
                        f"\nTugas: Buat ringkasan analitis kondisi pariwisata Bali bulan {_ctx['month']} "
                        "dalam 2-3 kalimat Bahasa Indonesia yang TAJAM dan KAUSAL — bukan hanya deskriptif.\n"
                        "Panduan:\n"
                        "- Jelaskan MENGAPA kondisi ini terjadi, bukan hanya APA kondisinya\n"
                        "- Sebutkan perubahan MoM yang paling signifikan sebagai pemicu\n"
                        "- Jika ada kontradiksi antar indikator, soroti itu\n"
                        "- Hindari kalimat seperti 'data menunjukkan' — langsung ke analisis\n"
                        "Format: cocok untuk KPI card eksekutif, padat, berbasis data."
                    )
                elif report_type == 'alert':
                    _prompt = (
                        "Kamu adalah sistem BaliGuard. Kondisi kritis terdeteksi.\n"
                        + _data_block +
                        "\nBuat PERINGATAN DARURAT (max 130 kata) Bahasa Indonesia dengan struktur:\n"
                        "STATUS: [level + score + perubahan dari bulan lalu]\n"
                        "PEMICU UTAMA: [3 indikator kritis dengan perubahan MoM-nya]\n"
                        "KONTEKS: [apakah ini anomali? konsisten atau tiba-tiba?]\n"
                        "TINDAKAN: [1 rekomendasi segera yang spesifik dan actionable]\n"
                        "Gaya: tegas, langsung, tidak bertele-tele."
                    )
                elif report_type == 'predict':
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard — sistem early warning pariwisata Bali.\n"
                        + _data_block +
                        f"\nTugas: Buat laporan PREDIKSI & PROYEKSI untuk pariwisata Bali 3–6 bulan ke depan "
                        f"setelah bulan {_ctx['month']}, dalam Bahasa Indonesia yang tajam dan berbasis data.\n\n"
                        "Struktur laporan:\n\n"
                        "1. PROYEKSI KONDISI (2-3 kalimat)\n"
                        "   - Prediksi arah tren crisis score 3 bulan ke depan (naik/turun/stabil)\n"
                        "   - Apakah proyeksi menunjukkan pemulihan atau tekanan berlanjut?\n\n"
                        "2. FAKTOR RISIKO UTAMA (3 poin)\n"
                        "   - Sebutkan 3 indikator yang paling berpotensi mempengaruhi kondisi ke depan\n"
                        "   - Jelaskan arah tekanan (positif/negatif) masing-masing indikator\n\n"
                        "3. SKENARIO RISIKO\n"
                        "   - Skenario Optimis: kondisi terbaik yang mungkin terjadi\n"
                        "   - Skenario Pesimis: kondisi terburuk jika indikator memburuk\n\n"
                        "4. REKOMENDASI ANTISIPATIF (3 poin konkret)\n"
                        "   - Tindakan preventif yang perlu disiapkan SEKARANG sebelum risiko terjadi\n"
                        "   - Tiap poin: [Urgensi] Tindakan spesifik → dampak yang diantisipasi\n\n"
                        "Gaya: forward-looking, actionable, berbasis angka dan tren nyata."
                    )
                else:
                    _prompt = (
                        "Kamu adalah analis senior BaliGuard.\n"
                        + _data_block +
                        "\nBuat laporan bulanan analitis Bahasa Indonesia dengan struktur:\n\n"
                        "1. RINGKASAN EKSEKUTIF (2-3 kalimat)\n"
                        "   - Status bulan ini vs bulan lalu (naik/turun berapa poin)\n"
                        "   - Apakah ini perubahan mendadak atau tren berkelanjutan?\n\n"
                        "2. ANALISIS INDIKATOR (3-4 kalimat)\n"
                        "   - Fokus pada indikator yang BERUBAH paling signifikan bulan ini\n"
                        "   - Jelaskan angka dengan konteks: '+8% wisman itu normal atau luar biasa?'\n"
                        "   - Soroti jika ada kontradiksi antar indikator\n\n"
                        "3. ANALISIS KAUSAL — MENGAPA INI TERJADI? (2-3 kalimat)\n"
                        "   - Identifikasi kemungkinan penyebab utama, bukan sekadar deskripsi\n"
                        "   - Jika ada anomali IF, analisis apa yang mungkin memicunya\n"
                        "   - Apakah tekanan berasal dari faktor internal (layanan) atau eksternal (ekonomi, akses)?\n\n"
                        "4. REKOMENDASI PRIORITAS (3 poin konkret dengan urgensi jelas)\n"
                        "   - Tiap poin: [Prioritas] Tindakan spesifik → target indikator yang diperbaiki"
                    )

                _client   = _Groq(api_key=groq_key)
                _response = _client.chat.completions.create(
                    model=selected_model,
                    messages=[{'role':'user','content':_prompt}],
                    temperature=0.7, max_tokens=1024,
                    **( {"reasoning_effort": "none"} if "qwen" in selected_model else {} )
                )
                _narr_text = _response.choices[0].message.content
                _tokens    = _response.usage.prompt_tokens + _response.usage.completion_tokens

                result = {
                    'success': True,
                    'narrative': _narr_text,
                    'tokens': _tokens,
                    'month': narasi_target,
                    'crisis_level': _narasi_level,
                    'report_type': report_type,
                    'crisis_score': _narasi_score,
                }

                _rlv  = _narasi_level
                _rclr = COLOR_MAP.get(_rlv, '#94a3b8')
                _fc_tag = " · 🔮 Proyeksi" if _is_fc_month else ""
                _model_short = GROQ_MODELS.get(selected_model, {}).get('label', selected_model)
                st.markdown(
                    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap'>"
                    "<div style='font-size:16px;font-weight:700;color:#FFFFFF;text-transform:uppercase;"
                    "letter-spacing:.1em'>NARASI BERHASIL DIBUAT</div>"
                    "<span style='background:" + _rclr + "22;color:" + _rclr + ";font-size:10px;font-weight:700;"
                    "padding:3px 10px;border-radius:20px;border:1px solid " + _rclr + "44'>"
                    + EMOJI_MAP.get(_rlv,'') + " " + _rlv + "</span>"
                    "<span style='font-family:monospace;font-size:14px;color:#475569'>"
                    + str(_tokens) + " tokens · " + _model_short + _fc_tag + "</span></div>"
                    "<div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);"
                    "border-radius:14px;padding:26px 30px;line-height:1.95;font-size:14px;"
                    "color:#cbd5e1;border-top:3px solid " + _rclr + "'>"
                    + _narr_text.replace('\n','<br>') + "</div>",
                    unsafe_allow_html=True
                )
                narratives_cache[narasi_target] = result
                os.makedirs('data/final', exist_ok=True)
                with open('data/final/narratives_cache.json', 'w', encoding='utf-8') as f:
                    json.dump(narratives_cache, f, ensure_ascii=False, indent=2)

            except Exception as e:
                st.error("❌ Error: " + str(e))

    elif not _has_cache and not gen_btn:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.1);
                    border-radius:14px;padding:48px;text-align:center'>
            <div style='font-size:36px;margin-bottom:12px'>🤖</div>
            <div style='font-size:14px;color:#475569;margin-bottom:6px'>Belum ada narasi untuk bulan ini</div>
            <div style='font-size:12px;color:#334155'>
                Pilih tipe laporan &amp; model AI di atas, lalu klik
                <b style='color:#4ade80'>Generate Narasi AI</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

