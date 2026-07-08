"""
src/pages/prediksi.py — BaliGuard: Prediksi & Proyeksi
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
from src.utils import level_from_score
from src.services.simulation import simulate_score
from src.config import COLOR_MAP
from src.services.forecast import forecast_months
from src.services.forecast import level_from_score

from src.utils import (
    sf, _tick, kpi_html, alert_html, status_dot,
    LEVEL_COLORS, LABEL_ORDER,
    FEATURES_CORE, FEATURES_LAG,
    LABEL_MANUSIAWI, DESKRIPSI_INDIKATOR,
)


ADVICE_MAP = {
    'AMAN': [
        'Pertahankan kualitas layanan dan kebersihan destinasi',
        'Tingkatkan promosi ke pasar potensial baru',
        'Investasi di infrastruktur pariwisata berkelanjutan',
    ],
    'WASPADA': [
        'Pantau indikator wisman secara mingguan',
        'Koordinasi dengan maskapai untuk menjaga frekuensi penerbangan',
        'Siapkan program insentif untuk wisatawan',
        'Review harga paket wisata agar tetap kompetitif',
    ],
    'SIAGA': [
        'Aktifkan satgas pariwisata darurat',
        'Negosiasi dengan platform OTA untuk visibility Bali',
        'Luncurkan kampanye "Visit Bali" secara agresif',
        'Koordinasi dengan Kemenparekraf untuk stimulus fiskal',
    ],
    'KRISIS': [
        'Deklarasi darurat pariwisata — libatkan pemerintah pusat',
        'Buka negosiasi multilateral dengan negara asal turis utama',
        'Beri insentif langsung: voucher, bebas visa, subsidi akomodasi',
        'Aktifkan dana darurat pariwisata Bali',
        'Siapkan program diversifikasi ekonomi untuk pekerja pariwisata',
    ],
}


def render(ctx: dict) -> None:
    """Render halaman Prediksi & Proyeksi."""
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
    physical_risk      = ctx['physical_risk']
    media_risk         = ctx['media_risk']
    tourist_perception = ctx['tourist_perception']
    external_risk      = ctx['external_risk']

    _tick("nav_start_prediksi")

    # ══════════════════════════════════════════════════════
    # CSS TAMBAHAN — REDESIGN PREDIKSI TAB
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <style>
    /* ── Page header ── */
    .pred-page-header { text-align:center; padding:28px 0 20px; margin-bottom:4px; }
    .pred-page-title {
      font-family:'DM Serif Display',serif; font-size:36px; color:#f1f5f9;
      letter-spacing:-.02em; line-height:1.15; margin-bottom:6px;
    }
    .pred-page-sub { font-size:13px; color:#475569; letter-spacing:.04em; }

    /* ── Engine pill ── */
    .engine-pill {
      display:inline-flex; align-items:center; gap:10px;
      background:rgba(15,30,70,0.7); border:1px solid rgba(59,130,246,0.2);
      border-radius:100px; padding:8px 20px; margin:0 auto 28px;
    }
    .engine-label {
      font-size:9px; font-weight:800; color:#3b82f6; text-transform:uppercase;
      letter-spacing:.14em; background:rgba(59,130,246,0.18);
      padding:3px 9px; border-radius:20px; border:1px solid rgba(59,130,246,0.3); white-space:nowrap;
    }
    .engine-desc { font-size:12px; color:#64748b; }

    /* ── Controls bar label ── */
    .ctrl-label {
      font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase;
      letter-spacing:.1em; margin-bottom:6px; display:flex; align-items:center; gap:5px;
    }

    /* ── Section divider ── */
    .pred-section-hdr { display:flex; align-items:center; gap:10px; margin:20px 0 14px; }
    .pred-section-hdr-line { flex:1; height:1px; background:rgba(255,255,255,0.10); }
    .pred-section-hdr-text {
      font-size:12px; font-weight:700; letter-spacing:.08em;
      text-transform:uppercase; color:#64748b; white-space:nowrap;
    }
    /* Tab-content heading (TREN+PROYEKSI dkk.) — sengaja lebih tebal dari
       section heading biasa untuk mempertahankan hierarki visual: tab ini
       adalah judul konten aktif yang sedang dipilih, bukan sekadar label
       seksi pasif. */
    .pred-section-hdr-text.pred-tab-hdr { font-weight:800; }

    /* ── Forecast grid cards ── */
    .fc-grid-fixed {
      display:grid; grid-template-columns:repeat(3,1fr);
      gap:10px; margin-bottom:10px;
    }
    .fc-grid-empty {
      background:rgba(255,255,255,0.008);
      border:1px dashed rgba(255,255,255,0.035) !important;
      border-top-color:transparent !important;
      pointer-events:none; min-height:118px; border-radius:14px;
    }
    .fc-grid-card {
      border-radius:14px; padding:16px 18px 15px; position:relative;
      overflow:hidden; transition:transform .2s, box-shadow .2s;
    }
    .fc-grid-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.45); }

    /* ── Confidence-tier card backgrounds ── */
    /* HIGH  76–100 */
    .fc-conf-high {
      background:rgba(16,185,129,0.10); border:1px solid rgba(16,185,129,0.28);
    }
    /* MID   51–75 */
    .fc-conf-mid {
      background:rgba(245,158,11,0.10); border:1px solid rgba(245,158,11,0.28);
    }
    /* LOW   26–50 */
    .fc-conf-low {
      background:rgba(249,115,22,0.09); border:1px solid rgba(249,115,22,0.25);
    }
    /* VLOW  0–25 */
    .fc-conf-vlow {
      background:rgba(100,116,139,0.08); border:1px solid rgba(100,116,139,0.20);
    }

    .fc-card-month {
      font-family:'JetBrains Mono',monospace; font-size:11px;
      color:#94a3b8; letter-spacing:.08em; margin-bottom:8px; font-weight:600;
    }

    /* ── Data status badge (aktual vs proyeksi) ── */
    .fc-status-badge {
      display:inline-flex; align-items:center; gap:4px;
      font-size:9px; font-weight:800; letter-spacing:.06em;
      text-transform:uppercase; padding:2px 8px; border-radius:20px;
      margin-bottom:8px; line-height:1.6;
    }
    .fc-status-actual {
      background:rgba(34,197,94,0.12); color:#22c55e;
      border:1px solid rgba(34,197,94,0.3);
    }
    .fc-status-proj {
      background:rgba(249,115,22,0.12); color:#f97316;
      border:1px solid rgba(249,115,22,0.3);
    }

    .fc-card-level { font-size:16px; font-weight:900; margin-bottom:3px; letter-spacing:.04em; }
    .fc-card-score {
      font-family:'JetBrains Mono',monospace; font-size:12px; color:#94a3b8;
      font-weight:600; margin-bottom:10px;
    }
    .fc-conf-bar-wrap {
      height:5px; background:rgba(255,255,255,0.08); border-radius:3px; overflow:hidden; margin-bottom:7px;
    }
    .fc-conf-bar-fill { height:100%; border-radius:3px; }
    .fc-conf-label { display:flex; justify-content:space-between; align-items:center; }
    .fc-conf-pct {
      font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:800;
    }
    .fc-conf-txt { font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.08em; font-weight:600; }

    /* Sembunyikan tick bar bawaan */
    [data-testid="stSliderTickBar"] {
    display: none !important;
    }

    /* Range label row manual */
    .slider-range-row {
      display: flex;
      justify-content: space-between;
      margin: 2px 0 10px;
      padding: 0 2px;
    }
    .slider-range-row span {
      font-size: 11px;
      font-weight: 700;
      color: #94a3b8;
      font-family: 'JetBrains Mono', monospace;
    }

    /* ── Simulator hint ── */
    .sim-hint {
      background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.20);
      border-left:3px solid rgba(59,130,246,0.6);
      border-radius:8px; padding:11px 16px; font-size:13px; color:#93c5fd;
      font-weight:600; margin-bottom:14px; letter-spacing:.01em;
    }

    /* ── Slider label row ── */
    .slider-label-row {
      display:flex; justify-content:space-between; align-items:center;
      margin-bottom:2px;
    }
    .slider-label-txt {
      font-size:11px; font-weight:700; color:#94a3b8; display:flex; align-items:center; gap:5px;
    }
    .slider-val-pill {
      font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700;
      padding:2px 9px; border-radius:20px;
      background:rgba(59,130,246,0.12); color:#7dd3fc;
      border:1px solid rgba(59,130,246,0.2);
    }

    /* ── Sembunyikan tooltip/bubble bawaan Streamlit pada proj_n slider ── */
    div[data-testid="stSlider"][aria-label="Jumlah Bulan"] div[role="slider"]::before,
    div[data-testid="stSlider"][aria-label="Jumlah Bulan"] [data-testid="stThumbValue"],
    div[data-testid="stSlider"][aria-label="Jumlah Bulan"] .st-emotion-cache-1cj0yv5,
    div[data-testid="stSlider"] div[class*="StyledThumbValue"],
    div[data-testid="stSlider"] div[class*="thumbValue"],
    div[data-testid="stSlider"] [data-testid="stThumbValue"] {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
    }

    /* ── Result box ── */
    .sim-result {
      border-radius:14px; padding:20px 16px; text-align:center;
      margin:10px 0 6px; border:1px solid rgba(255,255,255,0.07);
      position:relative; overflow:hidden;
    }
    .sim-result-label {
      font-size:9px; font-weight:800; letter-spacing:.16em;
      text-transform:uppercase; color:#1e3a5f; margin-bottom:8px;
    }
    .sim-result-score {
      font-family:'JetBrains Mono',monospace; font-size:52px; font-weight:700;
      line-height:1; color:#f1f5f9; margin-bottom:4px;
    }
    .sim-level-badge {
      display:inline-block; padding:5px 18px; border-radius:100px;
      font-family:'DM Serif Display',serif; font-size:15px; font-weight:400;
    }
    .sim-delta-txt {
      margin-top:10px; font-family:'JetBrains Mono',monospace;
      font-size:11px; color:#94a3b8;
    }

    /* ── Full-width Breakdown+Rekomendasi row ── */
    .bd-reko-row {
      display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px;
    }
    .bd-panel {
      background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
      border-radius:14px; padding:16px 18px;
    }
    .bd-panel-title {
      font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
      color:#64748b; margin-bottom:14px; display:flex; align-items:center; gap:6px;
    }
    .bd-row {
      display:flex; justify-content:space-between; align-items:center;
      padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04);
    }
    .bd-row:last-child { border-bottom:none; }
    .bd-name { font-size:14px; font-weight:500; color:#cbd5e1; }
    .bd-badge {
      font-size:12px; font-weight:700; padding:4px 12px;
      border-radius:20px; letter-spacing:.04em;
    }
    .bd-badge-rendah { background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.2); }
    .bd-badge-sedang { background:rgba(245,158,11,0.12); color:#fbbf24; border:1px solid rgba(245,158,11,0.2); }
    .bd-badge-tinggi { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.2);  }

    /* ── Rekomendasi panel ── */
    .reko-panel {
      background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);
      border-radius:14px; padding:16px 18px;
    }
    .reko-title {
      font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
      color:#64748b; margin-bottom:14px; display:flex; align-items:center; gap:6px;
    }
    .reko-item {
      display:flex; align-items:flex-start; gap:10px; padding:10px 0;
      border-bottom:1px solid rgba(255,255,255,0.05); font-size:14px;
      color:#cbd5e1; line-height:1.7; font-weight:400;
    }
    .reko-item:last-child { border-bottom:none; }
    .reko-num {
      flex-shrink:0; width:24px; height:24px; border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      font-size:12px; font-weight:800; margin-top:2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── ENGINE PILL SUBTITLE ──────────────────────────────
    st.markdown("""
    <div style='text-align:center;margin-bottom:20px;margin-top:-16px'>
        <div class='engine-pill'>
            <span class='engine-label'>Prediction Engine</span>
            <span class='engine-desc'>Historical Data • Machine Learning • Dynamic Forecasting</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SELECTOR ROW ─────────────────────────────────────
    _now = datetime.now()
    _MONTH_NAMES = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']

    _sel_left, _sel_right = st.columns([58, 42])
    with _sel_left:
        _sel_c1, _sel_c2 = st.columns([1, 1])
        with _sel_c1:
            st.markdown("<div class='ctrl-label'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;margin-right:6px;vertical-align:middle;flex-shrink:0'></span>TAHUN MULAI</div>", unsafe_allow_html=True)
            _year_opts      = list(range(int(predictions['month'].iloc[-1][:4]), _now.year + 3))
            _default_yr_idx = _year_opts.index(_now.year) if _now.year in _year_opts else 0
            _proj_year      = st.selectbox("Tahun", _year_opts, index=_default_yr_idx,
                                            key="proj_year", label_visibility="collapsed")
        with _sel_c2:
            st.markdown("<div class='ctrl-label'><span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px #3b82f6;margin-right:6px;vertical-align:middle;flex-shrink:0'></span>BULAN MULAI</div>", unsafe_allow_html=True)
            _proj_month_name = st.selectbox("Bulan", _MONTH_NAMES, index=_now.month-1,
                                             key="proj_month", label_visibility="collapsed")
            _proj_month_num  = _MONTH_NAMES.index(_proj_month_name) + 1
    with _sel_right:
        # ── Label row: judul kiri + nilai aktif kanan ──────────────────
        st.markdown(
            f"<div class='slider-label-row'>"
            f"<span class='slider-label-txt'>⏱ JUMLAH BULAN PROYEKSI</span>"
            f"<span class='slider-val-pill' id='proj-n-val'>{st.session_state.get('proj_n', 6)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        _proj_n = st.slider("Jumlah Bulan", 3, 12, 6, 1, key="proj_n",
                            label_visibility="collapsed")
        st.markdown(
            "<div class='slider-range-row'><span>3</span><span>12</span></div>",
            unsafe_allow_html=True
        )

    if _proj_month_num == 1:
        _from_month_str = f"{_proj_year - 1}-12"
    else:
        _from_month_str = f"{_proj_year}-{_proj_month_num - 1:02d}"

    fc_list_tab, fc_trend_tab = forecast_months(predictions, n=_proj_n, from_month=_from_month_str)

    st.markdown("<div style='margin:4px 0 20px'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2-COLUMN LAYOUT  LEFT 58%  |  RIGHT 42%
    # ════════════════════════════════════════════════════
    t4_left, t4_right = st.columns([58, 42])

    # ══ LEFT ═════════════════════════════════════════════
    with t4_left:

        # ── Section header ───────────────────────────────
        st.markdown(
            "<div class='pred-section-hdr'>"
            "<div class='pred-section-hdr-line'></div>"
            "<div class='pred-section-hdr-text'>Proyeksi " + str(_proj_n) + " Bulan — " + _proj_month_name + " " + str(_proj_year) + "</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>",
            unsafe_allow_html=True)

        # ── Forecast grid cards — fixed 12 slots (4 rows x 3 cols) ──
        # Confidence tiers: 76-100 high (green), 51-75 mid (amber), 26-50 low (orange), ≤25 vlow (muted)
        _MAX_SLOTS = 12

        # Bulan terakhir yang memiliki data aktual, dipakai untuk menentukan
        # badge status (DATA AKTUAL vs PROYEKSI) pada masing-masing card.
        _last_actual_period = pd.Period(str(_last_data_month), freq='M')

        def _fc_card_html(_gi):
            if _gi < len(fc_list_tab):
                _fc  = fc_list_tab[_gi]
                _lv  = _fc['level']
                _clr = COLOR_MAP.get(_lv, '#3b82f6')
                _cf  = _fc['confidence']
                _cw  = int(_cf)
                _card_period = pd.Period(str(_fc['month']), freq='M')
                if _card_period <= _last_actual_period:
                    _status_cls  = "fc-status-actual"
                    _status_text = "● DATA AKTUAL"
                else:
                    _status_cls  = "fc-status-proj"
                    _status_text = "▲ PROYEKSI"
                # Confidence tier → warna berdasarkan % confidence
                # 76-100=hijau, 51-75=kuning, 26-50=oranye, 0-25=merah
                if _cf >= 76:
                    _tier_cls  = "fc-conf-high"
                    _pct_color = "#22c55e"   # hijau
                elif _cf >= 51:
                    _tier_cls  = "fc-conf-mid"
                    _pct_color = "#eab308"   # kuning
                elif _cf >= 26:
                    _tier_cls  = "fc-conf-low"
                    _pct_color = "#f97316"   # oranye
                else:
                    _tier_cls  = "fc-conf-vlow"
                    _pct_color = "#ef4444"   # merah
                return (
                    "<div class='fc-grid-card {tier}'>"
                    "<div style='position:absolute;top:0;left:0;right:0;height:3px;"
                    "background:{pc};border-radius:14px 14px 0 0'></div>"
                    "<div class='fc-card-month'>{mo}</div>"
                    "<div class='fc-status-badge {scls}'>{stxt}</div>"
                    "<div class='fc-card-level' style='color:{pc}'>{lv}</div>"
                    "<div class='fc-card-score'>{sc}/100</div>"
                    "<div class='fc-conf-bar-wrap'>"
                    "<div class='fc-conf-bar-fill' style='width:{cw}%;background:{pc}'></div>"
                    "</div>"
                    "<div class='fc-conf-label'>"
                    "<span class='fc-conf-pct' style='color:{pc}'>{cf:.0f}%</span>"
                    "<span class='fc-conf-txt'>keyakinan</span>"
                    "</div>"
                    "</div>"
                ).format(tier=_tier_cls, clr=_clr, mo=_fc['month'],
                         scls=_status_cls, stxt=_status_text,
                         lv=_lv, sc=_fc['score'], cw=_cw, cf=_cf, pc=_pct_color)
            else:
                return "<div class='fc-grid-card fc-grid-empty'></div>"

        # Catatan disclaimer bersifat interaktif: posisinya mengikuti jumlah
        # baris kartu yang benar-benar terisi (berdasarkan _proj_n), sehingga
        # ia naik ke atas saat proyeksi pendek dan turun saat proyeksi panjang
        # — tidak selalu menempel diam di paling bawah grid 12 slot.
        _COLS = 3
        _filled_n   = min(len(fc_list_tab), _MAX_SLOTS)
        _rows_upto  = -(-_filled_n // _COLS)          # ceil(filled/cols), baris yang berisi data nyata
        _slot_before_note = min(_rows_upto * _COLS, _MAX_SLOTS)  # lengkapi baris terakhir dg slot kosong bila perlu
        _slot_after_note  = _MAX_SLOTS - _slot_before_note

        _grid_before_html = "<div class='fc-grid-fixed'>"
        for _gi in range(_slot_before_note):
            _grid_before_html += _fc_card_html(_gi)
        _grid_before_html += "</div>"
        st.markdown(_grid_before_html, unsafe_allow_html=True)

        if _slot_after_note > 0:
            _grid_after_html = "<div class='fc-grid-fixed'>"
            for _gi in range(_slot_before_note, _MAX_SLOTS):
                _grid_after_html += _fc_card_html(_gi)
            _grid_after_html += "</div>"
            st.markdown(_grid_after_html, unsafe_allow_html=True)

        # Track chart tab state here (rendered full-width later)
        if 'pred_chart_tab' not in st.session_state:
            st.session_state['pred_chart_tab'] = 'trend'
        _active_chart = st.session_state['pred_chart_tab']

    # ══ RIGHT ════════════════════════════════════════════
    with t4_right:

        # ── Simulator header ─────────────────────────────
        st.markdown(
            "<div class='pred-section-hdr'>"
            "<div class='pred-section-hdr-line'></div>"
            "<div class='pred-section-hdr-text'>Simulator Skenario Risiko</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>",
            unsafe_allow_html=True)

        st.markdown(
            "<div class='sim-hint'>Geser slider untuk simulasi dampak perubahan indikator secara real-time.</div>",
            unsafe_allow_html=True)

        # ── Sliders with value pills rendered via HTML label ──
        w_d = st.slider("Wisman (%)", -80, 50, 0, 5, key="sim_w",
                         help=DESKRIPSI_INDIKATOR.get('wisman'))
        st.markdown("<div class='slider-range-row'><span>-80%</span><span>+50%</span></div>", unsafe_allow_html=True)
        u_d = st.slider("USD/IDR (%)", -10, 30, 0, 1, key="sim_u",
                         help=DESKRIPSI_INDIKATOR.get('usd_idr_avg'))
        st.markdown("<div class='slider-range-row'><span>-10%</span><span>+30%</span></div>", unsafe_allow_html=True)
        s_d = st.slider("Sentimen", -1.0, 1.0, 0.0, 0.1, key="sim_s",
                         help=DESKRIPSI_INDIKATOR.get('avg_sentiment_monthly'))
        st.markdown("<div class='slider-range-row'><span>-1.0</span><span>+1.0</span></div>", unsafe_allow_html=True)

        sim_sc = simulate_score(dict(row_data), w_d, u_d, s_d)
        sim_lv = level_from_score(sim_sc)
        _sdelta = sim_sc - score
        _sdcol  = "#ef4444" if _sdelta > 0 else "#10b981"
        _sclr   = COLOR_MAP.get(sim_lv, '#fff')

        # ── Hasil Simulasi box ────────────────────────────
        st.markdown(
            "<div class='sim-result' style='"
            "background:linear-gradient(145deg,rgba(10,20,50,0.95),rgba(18,30,65,0.95));"
            "border-top:3px solid {clr};border-color:{clr}44'>"
            "<div class='sim-result-label' style='color:{clr}99'>Hasil Simulasi &nbsp;·&nbsp; Crisis Score / 100</div>"
            "<div class='sim-result-score' style='color:{clr}'>{sc}</div>"
            "<div>"
            "<span class='sim-level-badge' style='background:{clr}22;"
            "color:{clr};border:1px solid {clr}66;font-weight:700'>{lv}</span>"
            "</div>"
            "<div class='sim-delta-txt'>"
            "dari {base:.1f} → <span style='color:{dc};font-weight:700'>{d:+.1f} poin</span>"
            "</div>"
            "</div>".format(
                sc=f"{sim_sc:.1f}", clr=_sclr, lv=sim_lv,
                base=score, dc=_sdcol, d=_sdelta),
            unsafe_allow_html=True)
        
        # Peta Risiko Historis dipindah ke bawah tab (full-width) — lihat bagian _active_chart == 'scatter'

    # ══════════════════════════════════════════════════════════
    # BREAKDOWN RISIKO + REKOMENDASI — full-width, above charts
    # ══════════════════════════════════════════════════════════
    _bd_rows = [
        ("Penurunan Wisman",
         "Tinggi" if w_d<-20 else ("Sedang" if w_d<0 else "Rendah"),
         "tinggi" if w_d<-20 else ("sedang" if w_d<0 else "rendah")),
        ("Tekanan Kurs USD",
         "Tinggi" if u_d>10  else ("Sedang" if u_d>3  else "Rendah"),
         "tinggi" if u_d>10  else ("sedang" if u_d>3  else "rendah")),
        ("Sentimen Negatif",
         "Tinggi" if s_d<-0.3 else ("Sedang" if s_d<0 else "Rendah"),
         "tinggi" if s_d<-0.3 else ("sedang" if s_d<0 else "rendah")),
    ]
    _rclr_btn = COLOR_MAP.get(sim_lv, '#3b82f6')

    _bottom_html = "<div class='bd-reko-row'>"

    # Left: Breakdown Risiko
    _bottom_html += (
        "<div class='bd-panel'>"
        "<div class='bd-panel-title'>"
        "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
        "background:#f59e0b;box-shadow:0 0 6px #f59e0b66'></span>"
        "Breakdown Risiko"
        "</div>"
    )
    for nm, st_txt, cls in _bd_rows:
        _bottom_html += (
            "<div class='bd-row'>"
            "<span class='bd-name'>{nm}</span>"
            "<span class='bd-badge bd-badge-{cls}'>{st}</span>"
            "</div>"
        ).format(nm=nm, st=st_txt, cls=cls)
    _bottom_html += "</div>"

    # Right: Rekomendasi
    _bottom_html += (
        "<div class='reko-panel'>"
        "<div class='reko-title'>"
        "<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
        "background:{clr};box-shadow:0 0 6px {clr}88'></span>"
        "Rekomendasi — Level {lv}"
        "</div>"
    ).format(clr=_rclr_btn, lv=sim_lv)
    for i, rec in enumerate(ADVICE_MAP.get(sim_lv, []), 1):
        _bottom_html += (
            "<div class='reko-item'>"
            "<span class='reko-num' style='background:{clr}20;color:{clr}'>{i}</span>"
            "<span>{rec}</span>"
            "</div>"
        ).format(clr=_rclr_btn, i=i, rec=rec)
    _bottom_html += "</div></div>"
    st.markdown(_bottom_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # CHART TABS — full-width, below breakdown
    # ══════════════════════════════════════════════════════════
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    _chart_c1, _chart_c2, _chart_c3 = st.columns(3)
    with _chart_c1:
        if st.button("Tren + Proyeksi", key="pct_trend",
                     type="primary" if st.session_state['pred_chart_tab']=='trend' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'trend'
            st.rerun()
    with _chart_c2:
        if st.button("Tingkat Pemulihan vs Baseline", key="pct_rec",
                     type="primary" if st.session_state['pred_chart_tab']=='recovery' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'recovery'
            st.rerun()
    with _chart_c3:
        if st.button("Peta Risiko Historis", key="pct_scatter",
                     type="primary" if st.session_state['pred_chart_tab']=='scatter' else "secondary",
                     use_container_width=True):
            st.session_state['pred_chart_tab'] = 'scatter'
            st.rerun()

    components.html("""
    <script>
    (function() {
        const labels = ["Tren + Proyeksi", "Tingkat Pemulihan vs Baseline", "Peta Risiko Historis"];
        function boldTabBtns() {
            window.parent.document.querySelectorAll('.stButton button').forEach(btn => {
                const txt = (btn.querySelector('p')?.innerText || btn.innerText || '').trim();
                if (labels.includes(txt)) {
                    btn.style.setProperty('font-weight', '800', 'important');
                    btn.style.setProperty('letter-spacing', '.02em', 'important');
                    btn.style.setProperty('font-size', '14px', 'important');
                }
            });
        }
        boldTabBtns();
        setTimeout(boldTabBtns, 200);
        setTimeout(boldTabBtns, 600);
        new MutationObserver(boldTabBtns).observe(
            window.parent.document.body, {childList:true, subtree:true}
        );
    })();
    </script>
    """, height=0)

    st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

    # ── Chart content — full width ────────────────────────
  
    if _active_chart == 'trend':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text pred-tab-hdr'>↗ TREN + PROYEKSI</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        last12    = predictions.tail(12)
        l12_dt    = pd.to_datetime(last12['month'].astype(str))
        fc_dt     = pd.to_datetime([f['month'] for f in fc_list_tab])
        fc_scores = [f['score'] for f in fc_list_tab]
        fc_lo     = [max(0,  s - 8) for s in fc_scores]
        fc_hi     = [min(100, s + 8) for s in fc_scores]
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=l12_dt, y=last12['crisis_score_100'],
            mode='lines+markers', name='Historis',
            line=dict(color='#7dd3fc', width=2.5), marker=dict(size=5, color='#7dd3fc')))
        fig_fc.add_trace(go.Scatter(
            x=list(fc_dt)+list(reversed(list(fc_dt))),
            y=fc_hi+list(reversed(fc_lo)),
            fill='toself', fillcolor='rgba(34,197,94,0.07)',
            line=dict(width=0), showlegend=True, name='Interval ±8', hoverinfo='skip'))
        fig_fc.add_trace(go.Scatter(x=fc_dt, y=fc_scores,
            mode='lines+markers', name='Proyeksi',
            line=dict(color='#f59e0b', width=2, dash='dash'),
            marker=dict(size=8, symbol='diamond', color='#f59e0b')))
        for thr,lbl,col in [(60,'KRISIS','#d90000'),(45,'SIAGA','#ff6c43'),(30,'WASPADA','#F9F871')]:
            fig_fc.add_hline(y=thr, line_dash='dot', line_color=col, line_width=0.7, opacity=0.45,
                             annotation_text=lbl, annotation_position='right',
                             annotation_font_size=9, annotation_font_color=col)
        fig_fc.update_layout(
            yaxis=dict(range=[0,100], title=LABEL_MANUSIAWI.get('crisis_score_100', 'Skor Krisis'),
                       gridcolor='rgba(255,255,255,0.04)', color='#475569', tickfont=dict(size=10)),
            xaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#475569', tickfont=dict(size=10)),
            plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
            height=320, margin=dict(l=0, r=72, t=10, b=0),
            legend=dict(orientation='h', y=1.04, x=0, bgcolor='rgba(0,0,0,0)',
                        font=dict(size=10, color='#94a3b8')),
            font=dict(family='DM Sans', size=11, color='#94a3b8'))
        st.plotly_chart(fig_fc, use_container_width=True, config={'displayModeBar': False})

    elif _active_chart == 'recovery':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text pred-tab-hdr'>📉 TINGKAT PEMULIHAN VS BASELINE 2017–2019</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        _precovid_mean = ctx.get('precovid_mean', 0.0)
        if _precovid_mean > 0 and 'wisman' in predictions.columns:
            rec_df = predictions.copy()
            rec_df['recovery_pct'] = (rec_df['wisman'] / _precovid_mean * 100).round(1)
            fig_rec = go.Figure()
            fig_rec.add_hline(y=100, line_dash='dot', line_color='#10b981', line_width=1.5,
                              annotation_text='Baseline 100%', annotation_position='right',
                              annotation_font_color='#10b981', annotation_font_size=10)
            fig_rec.add_trace(go.Scatter(
                x=pd.to_datetime(rec_df['month'].astype(str)), y=rec_df['recovery_pct'],
                mode='lines', fill='tozeroy',
                fillcolor='rgba(59,130,246,0.06)', line=dict(color='#3b82f6', width=2)))
            fig_rec.add_vrect(x0='2020-03-01', x1='2021-12-01',
                fillcolor='rgba(239,68,68,0.05)', line_width=0,
                annotation_text='COVID', annotation_font_color='#ef4444')
            fig_rec.add_vline(x=sel_dt, line_dash='dot', line_color='#7dd3fc', line_width=1.2)
            fig_rec.update_layout(
                yaxis=dict(title=LABEL_MANUSIAWI.get('wisman_recovery_pct', 'Tingkat Pemulihan (%)'), gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0, r=80, t=8, b=0),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_rec, use_container_width=True, config={'displayModeBar': False})
            _recovery_pct = ctx.get('recovery_pct', 0.0)
            _rcol = '#10b981' if _recovery_pct >= 90 else \
                    ('#f59e0b' if _recovery_pct >= 60 else '#ef4444')
            st.markdown(
                "<div style='background:rgba(255,255,255,0.02);border-radius:8px;"
                "padding:8px 14px;font-size:12px;color:#475569;border:1px solid rgba(255,255,255,0.05)'>"
                "Pemulihan <b style='color:#e2e8f0'>{mo}</b>: "
                "<span style='color:{rc};font-weight:700;font-size:14px'>{rv:.1f}%</span>"
                " dari baseline ({bsl:,} wisman/bln)</div>".format(
                    mo=sel, rc=_rcol, rv=_recovery_pct, bsl=int(_precovid_mean)),
                unsafe_allow_html=True)

    elif _active_chart == 'scatter':
        st.markdown(
            "<div class='pred-section-hdr' style='margin-top:0'>"
            "<div class='pred-section-hdr-text pred-tab-hdr'>🗺️ PETA RISIKO HISTORIS</div>"
            "<div class='pred-section-hdr-line'></div>"
            "</div>", unsafe_allow_html=True)
        _sc_src = master if 'wisman_growth_mom' in master.columns else predictions
        if 'wisman_growth_mom' in _sc_src.columns and 'crisis_level' in _sc_src.columns:
            fig_r2 = go.Figure()
            for _lv_sc in ['AMAN','WASPADA','SIAGA','KRISIS']:
                _mask = _sc_src['crisis_level'] == _lv_sc
                if _mask.sum() > 0:
                    fig_r2.add_trace(go.Scatter(
                        x=_sc_src.loc[_mask,'wisman_growth_mom']*100,
                        y=_sc_src.loc[_mask,'avg_sentiment_monthly'],
                        mode='markers', name=_lv_sc,
                        marker=dict(color=COLOR_MAP[_lv_sc], size=7, opacity=0.8,
                                    line=dict(width=0.5, color='rgba(0,0,0,0.3)'))))
            fig_r2.add_hline(y=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r2.add_vline(x=0, line_dash='dash', line_color='rgba(255,255,255,0.08)', line_width=1)
            fig_r2.update_layout(
                xaxis=dict(title=LABEL_MANUSIAWI.get('wisman_growth_mom', 'Pertumbuhan Wisatawan (%)'),
                           gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                yaxis=dict(title=LABEL_MANUSIAWI.get('avg_sentiment_monthly', 'Sentimen Rata-rata'),
                           gridcolor='rgba(255,255,255,0.04)', color='#475569'),
                plot_bgcolor='rgba(8,16,32,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation='h', y=1.04, x=0, bgcolor='rgba(0,0,0,0)',
                            font=dict(size=10, color='#94a3b8')),
                font=dict(family='DM Sans', size=11, color='#94a3b8'))
            st.plotly_chart(fig_r2, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='margin-bottom:32px'></div>", unsafe_allow_html=True)