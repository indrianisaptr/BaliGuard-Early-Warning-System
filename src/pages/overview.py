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

from src.config import COLOR_MAP

# ── Layout constants untuk chart overview ─────────────────────────────
_OVERVIEW_AXIS_STYLE = dict(
    gridcolor='rgba(255,255,255,0.04)', showline=False,
    linecolor='rgba(255,255,255,0.06)'
)
_OVERVIEW_LAYOUT_BASE = dict(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=55, t=50, b=10),
    font=dict(family='DM Sans', size=11, color='#94a3b8')
)

# ── Chart builders ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _build_overview_fig1(sel_month_str: str, _predictions: pd.DataFrame) -> go.Figure:
    """Crisis Score & Level Krisis chart."""
    _months_dt = pd.to_datetime(_predictions['month'].astype(str))
    _sel_dt    = pd.to_datetime(sel_month_str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_months_dt, y=_predictions['crisis_score_100'],
        mode='lines', name='Crisis Score',
        line=dict(color='#cbd5e1', width=1.5),
        fill='tozeroy', fillcolor='rgba(148,163,184,0.04)'
    ))
    for lv, col in COLOR_MAP.items():
        mask = _predictions['crisis_level'] == lv
        if mask.sum() > 0:
            fig.add_trace(go.Scatter(
                x=_months_dt[mask], y=_predictions.loc[mask, 'crisis_score_100'],
                mode='markers', name=lv,
                marker=dict(color=col, size=6, line=dict(width=0)),
                hovertemplate=f'<b>{lv}</b><br>%{{x|%b %Y}}<br>Score: %{{y:.1f}}<extra></extra>'
            ))
    for thr, lbl, col in [(60,'KRISIS','#d90000'),(45,'SIAGA','#ff6c43'),(30,'WASPADA','#F9F871')]:
        fig.add_hline(y=thr, line_dash='dot', line_color=col, line_width=0.6, opacity=0.5,
                      annotation_text=lbl, annotation_position='right',
                      annotation_font_size=7, annotation_font_color=col,
                      annotation_xanchor='left', annotation_xshift=-52)
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.04)', line_width=0,
                  annotation_text='COVID-19', annotation_font_color='#ef4444',
                  annotation_font_size=10)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1)
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
            fig.add_vline(x=_ev_dt, line_dash='dot', line_color=ev_col, line_width=0.6, opacity=0.4)
            fig.add_annotation(x=_ev_dt, y=97, text=ev_label, showarrow=False,
                                font=dict(size=8, color=ev_col), textangle=-55,
                                xanchor='left', bgcolor='rgba(0,0,0,0)', borderpad=2)
        except Exception:
            pass
    fig.update_layout(height=340, showlegend=True,
                      title=dict(text='Crisis Score & Level Krisis', x=0.5, xanchor='center',
                                 font=dict(size=25, color='#ff6c43', family='DM Sans')),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                                bgcolor='rgba(15,15,25,0.6)', bordercolor='rgba(255,255,255,0.08)',
                                borderwidth=1, font=dict(size=9, color='#e2e8f0'),
                                itemsizing='constant'),
                      **_OVERVIEW_LAYOUT_BASE)
    fig.update_xaxes(**_OVERVIEW_AXIS_STYLE)
    fig.update_yaxes(**_OVERVIEW_AXIS_STYLE)
    fig.update_layout(margin=dict(l=0, r=55, t=90, b=10))
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
        line=dict(color='#7dd3fc', width=1.5),
        fill='tozeroy', fillcolor='rgba(96,165,250,0.06)'
    ))
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.04)', line_width=0)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1)
    fig.update_layout(height=240, showlegend=False,
                      title=dict(text='Kunjungan Wisatawan Mancanegara', x=0.5, xanchor='center',
                                 font=dict(size=25, color='#ff6c43', family='DM Sans')),
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
            line=dict(color='#fbbf24', width=1.5)
        ))
    fig.add_vrect(x0='2020-03-01', x1='2021-12-01',
                  fillcolor='rgba(239,68,68,0.04)', line_width=0)
    fig.add_vline(x=_sel_dt, line_dash='dot', line_color='#60a5fa', line_width=1)
    fig.update_layout(height=220, showlegend=False,
                      title=dict(text='Kurs USD/IDR', x=0.5, xanchor='center',
                                 font=dict(size=25, color='#ff6c43', family='DM Sans')),
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
    #revisi/tambahan — sesuai kunci yang disediakan src/shared.build_context()
    physical_risk_score      = ctx.get('physical_risk', row_data.get('physical_risk_score'))
    media_risk_score         = ctx.get('media_risk', row_data.get('media_risk_score'))
    tourist_perception_score = ctx.get('tourist_perception', row_data.get('tourist_perception_score'))
    external_risk_score      = ctx.get('external_risk', row_data.get('external_risk_score'))
    # ── [BARU – Sprint 1A] field tambahan, SUDAH tersedia di ctx (shared.py) ──
    # Tidak ada perhitungan baru — hanya membaca key yang sudah dibangun build_context().
    dominant_factor  = ctx.get('dominant_factor', 'N/A')
    score_delta      = ctx.get('score_delta', 0)
    score_trend      = ctx.get('score_trend', 'STABIL')
    # ── [BARU – Refinement] evidence numerik, SUDAH tersedia di ctx/row_data ──
    # Sama seperti baris di atas: hanya .get(), tidak ada hitung ulang apa pun.
    crisis_score_100    = ctx.get('crisis_score_100', score)
    _wisman_delta       = delta_ctx.get('wisman') if isinstance(delta_ctx, dict) else None
    wisman_growth_mom   = (
        _wisman_delta.get('delta_pct')
        if isinstance(_wisman_delta, dict)
        else row_data.get('wisman_growth_mom')
    )
    usd_volatility_3m   = ctx.get('usd_volatility_3m', row_data.get('usd_volatility_3m'))
    pct_negative_monthly = ctx.get('pct_negative_monthly', row_data.get('pct_negative_monthly'))

    _tick("nav_start_overview")

    # ── Override container: hapus border tebal, pakai divider tipis ──
    st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 20px 0 !important;
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # [BARU – Sprint 1A / Refinement] Section: Mengapa Status Saat Ini Muncul?
    # Tujuan: explainability tampil SEBELUM grafik, bukan setelah.
    # Sumber data: 100% dari ctx/row_data/prev_row yang sudah dihitung
    # shared.build_context(). Tidak ada pemanggilan model atau
    # perhitungan ulang crisis score di sini.
    # ── [Refinement kedua] Disederhanakan dari 4 card menjadi 3 blok:
    # Faktor Dominan → Mengapa? → Dampaknya. Grid 4-kolom (Physical/Media/
    # Tourist/External) DIHAPUS dari sini karena sudah tampil lengkap di
    # section "External Risk Monitor" di bawah — panel ini cukup menyebut
    # SATU-DUA kontributor terbesar secara kalimat, bukan mengulang tabel.
    # ══════════════════════════════════════════════════════════════
    st.markdown("""
    <style>
    .why-now-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .why-now-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .why-now-flow {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0;
    }
    .flow-arrow {
        font-size: 13px;
        color: #475569;
        padding: 4px 0;
        line-height: 1;
    }
    .ev-section {
        width: 100%;
        background: rgba(255,255,255,0.025);
        border-left: 3px solid rgba(255,255,255,0.15);
        border-radius: 8px;
        padding: 12px 16px;
    }
    .ev-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .1em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 8px;
    }
    .ev-main-row {
        display: flex;
        align-items: baseline;
        gap: 10px;
        flex-wrap: wrap;
    }
    .ev-name {
        font-size: 13.5px;
        color: #e2e8f0;
        font-weight: 600;
    }
    .ev-value {
        font-family: 'DM Serif Display', serif;
        font-size: 20px;
        font-weight: 700;
    }
    .ev-status {
        font-size: 12px;
        color: #94a3b8;
    }
    .ev-text {
        font-size: 13px;
        color: #cbd5e1;
        line-height: 1.6;
    }
    .ev-text b { color: #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

    # ── Bucket Rendah/Sedang/Tinggi: AMBANG SAMA PERSIS dengan _risk_color()
    # di bagian "External Risk Monitor" di bawah (30 / 60). Ini bukan
    # threshold baru — hanya dipakai ulang supaya panel & monitor konsisten.
    def _ev_bucket(pct):
        if pct is None:
            return ("N/A", "#64748b")
        pct = float(pct)
        pct = pct * 100 if pct <= 1 else pct
        if pct < 30:
            return ("rendah", "#00c794")
        if pct < 60:
            return ("sedang", "#fbbf24")
        return ("tinggi", "#d90000")

    def _ev_pct_fmt(pct):
        if pct is None:
            return "N/A"
        pct = float(pct)
        pct = pct * 100 if pct <= 1 else pct
        return f"{pct:.1f}%"

    def _ev_wisman_fmt(val):
        return f"{val:,.0f}".replace(",", ".") + " wisatawan"

    # ── 1. FAKTOR DOMINAN ──────────────────────────────────────────
    # dominant_factor & anomaly_exp 100% dari ctx (build_context()).
    # Tidak ada z-score atau kalkulasi baru — hanya format tampilan.
    _anomaly_exp = ctx.get('anomaly_exp', '')

    if dominant_factor == 'Kunjungan Wisatawan':
        _dom_name, _dom_clr = "Kunjungan Wisatawan", "#f87171"
        _dom_value = _ev_wisman_fmt(wisman)
    elif dominant_factor == 'Risiko Eksternal':
        _dom_name, _dom_clr = "External Risk", "#fbbf24"
        _dom_value = _ev_pct_fmt(external_risk_score)
    elif dominant_factor == 'Tekanan Kurs':
        _dom_name, _dom_clr = "Kurs USD/IDR", "#fbbf24"
        _dom_value = f"Rp {usd_avg:,.0f}"
    elif dominant_factor == 'Sentimen Negatif':
        _dom_name, _dom_clr = "Sentimen Wisatawan", "#f87171"
        _dom_value = f"{sent:.2f}"
    else:
        _dom_name, _dom_clr = "Tidak Ada Faktor Dominan", "#4ade80"
        _dom_value = "Normal"

    _section1_html = f"""
        <div class='ev-section' style='border-left-color:{_dom_clr}'>
            <div class='ev-label'>Faktor Dominan</div>
            <div class='ev-main-row'>
                <span class='ev-name'>{_dom_name}</span>
                <span class='ev-value' style='color:{_dom_clr}'>{_dom_value}</span>
            </div>
        </div>
    """

    # ── 2. MENGAPA? ─────────────────────────────────────────────────
    # Hanya menyebut 1–2 kontributor TERBESAR sebagai kalimat, bukan
    # tabel/grid lengkap — nilai sub-komponen (Physical/Media/Tourist)
    # sengaja TIDAK diulang di sini karena sudah tersaji lengkap di
    # "External Risk Monitor" di bawah. Ini hanya jembatan, bukan duplikat.
    if dominant_factor == 'Risiko Eksternal':
        _components = [("Media Risk", media_risk_score), ("Tourist Perception", tourist_perception_score),
                        ("Physical Risk", physical_risk_score)]
        _components = [(lab, v) for lab, v in _components if v is not None]
        _components.sort(key=lambda c: (c[1] if c[1] > 1 else c[1] * 100), reverse=True)
        if _components:
            _top_lab, _top_val = _components[0]
            _why_txt = f"<b>{_top_lab}</b> menjadi komponen terbesar (<b>{_ev_pct_fmt(_top_val)}</b>)."
            if len(_components) > 1:
                _lbl2, _ = _ev_bucket(_components[1][1])
                _why_txt += f" <b>{_components[1][0]}</b> berada pada kategori {_lbl2} (<b>{_ev_pct_fmt(_components[1][1])}</b>)."
        else:
            _why_txt = "Rincian komponen risiko eksternal dapat dilihat pada External Risk Monitor di bawah."
    elif dominant_factor == 'Kunjungan Wisatawan':
        if wisman_growth_mom is not None:
            _g = float(wisman_growth_mom)
            _arah = "naik" if _g > 0 else "turun" if _g < 0 else "stabil"
            _why_txt = f"Kunjungan wisatawan tercatat <b>{_arah} {abs(_g):.1f}%</b> dibanding bulan sebelumnya."
        elif _anomaly_exp:
            _why_txt = f"Kunjungan wisatawan {_anomaly_exp}."
        else:
            _why_txt = "Data pertumbuhan wisatawan bulan ini tidak tersedia."
    elif dominant_factor == 'Tekanan Kurs':
        _why_txt = f"Kurs USD/IDR naik menjadi <b>Rp {usd_avg:,.0f}</b> dibanding bulan sebelumnya, menambah beban biaya kunjungan wisatawan asing."
    elif dominant_factor == 'Sentimen Negatif':
        _why_txt = f"Sentimen ulasan wisatawan melemah menjadi <b>{sent:.2f}</b> dibanding bulan sebelumnya."
        if pct_negative_monthly is not None:
            _why_txt += f" Proporsi ulasan negatif tercatat <b>{_ev_pct_fmt(pct_negative_monthly)}</b>."
    else:
        _why_txt = "Seluruh indikator utama berada dalam rentang aman, tidak ada faktor yang menonjol signifikan bulan ini."

    _section2_html = f"""
        <div class='ev-section'>
            <div class='ev-label'>Mengapa?</div>
            <div class='ev-text'>{_why_txt}</div>
        </div>
    """

    # ── 3. DAMPAKNYA ─────────────────────────────────────────────────
    # crisis_score_100, score_delta, score_trend, level, color 100% dari
    # ctx — tidak ada logika klasifikasi atau hitungan baru di sini.
    _trend_verb = {'MENINGKAT': 'Naik', 'MENURUN': 'Turun', 'STABIL': 'Relatif stabil'}[score_trend]
    _trend_clr  = {'MENINGKAT': '#f87171', 'MENURUN': '#00c794', 'STABIL': '#93c5fd'}[score_trend]
    if score_trend == 'STABIL':
        _score_status = f"{_trend_verb} (perubahan {score_delta:+.1f} poin) dibanding bulan sebelumnya"
    else:
        _score_status = f"{_trend_verb} {abs(score_delta):.1f} poin dibanding bulan sebelumnya"

    _section3_html = f"""
        <div class='ev-section' style='border-left-color:{color}'>
            <div class='ev-label'>Dampaknya</div>
            <div class='ev-main-row'>
                <span class='ev-name'>Crisis Score</span>
                <span class='ev-value' style='color:#93c5fd'>{crisis_score_100:.1f}</span>
            </div>
            <div class='ev-status' style='color:{_trend_clr};margin-bottom:8px'>{_score_status}</div>
            <div class='ev-value' style='color:{color};font-size:22px'>{level}</div>
        </div>
    """

    _arrow = "<div class='flow-arrow'>&#8595;</div>"
    _panel_html = _arrow.join([_section1_html, _section2_html, _section3_html])

    st.markdown(f"""
    <div class='why-now-box'>
        <div class='why-now-title'>Mengapa Status Saat Ini Muncul?</div>
        <div class='why-now-flow'>{_panel_html}</div>
    </div>
    """, unsafe_allow_html=True)
    # ── [AKHIR SISIPAN Sprint 1A / Refinement Evidence Panel] ────────

    # ══════════════════════════════════════════════════════════════
    # [REVISI – Sprint 2.2] Panel Transparansi: Metodologi Crisis Score
    # Sesuai revisi: bukan panel terpisah yang selalu tampil (redundan
    # dengan panel "Mengapa Status Saat Ini Muncul?" di atas), tapi
    # expander tertutup ("klik kalau ingin tahu") dan disederhanakan
    # dari 5 langkah menjadi 3 (Input → Analisis → Output). Tanpa
    # menyebut Random Forest / Isolation Forest / SHAP / istilah teknis
    # lain. Semua angka via ctx.get(...) — tidak ada perhitungan ulang.
    # Reuse class CSS why-now-flow/flow-arrow/ev-section/ev-label/
    # ev-main-row/ev-name/ev-value/ev-status/ev-text yang sudah ada —
    # tidak menambah CSS global baru.
    # ══════════════════════════════════════════════════════════════
    with st.expander("Bagaimana Crisis Score dihitung?"):
        _meta_input_html = """
            <div class='ev-section'>
                <div class='ev-label'>Input</div>
                <div class='ev-text'>
                    Wisatawan · Hunian Hotel · Inflasi · Kurs · Sentimen Wisatawan · Risiko Eksternal
                </div>
            </div>
        """

        _meta_analisis_html = """
            <div class='ev-section'>
                <div class='ev-label'>Analisis</div>
                <div class='ev-text'>
                    Sistem menganalisis seluruh indikator di atas untuk menghasilkan Crisis Score.
                </div>
            </div>
        """

        _meta_crisis_score = ctx.get("crisis_score_100", ctx.get("score"))
        _meta_level = ctx["level"]
        _meta_color = ctx["color"]
        _meta_kategori = [
            ("0–29", "AMAN"),
            ("30–44", "WASPADA"),
            ("45–59", "SIAGA"),
            ("60–100", "KRISIS"),
        ]
        _meta_kategori_html = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(
            f"<span style='color:#94a3b8'>{_rng}</span> "
            f"<b style='color:{_this_clr}'>{_lv}</b>"
            for _rng, _lv, _this_clr in (
                (r, lv, _meta_color if lv == _meta_level else "#94a3b8")
                for r, lv in _meta_kategori
            )
        )
        _meta_output_html = f"""
            <div class='ev-section' style='border-left-color:{_meta_color}'>
                <div class='ev-label'>Output</div>
                <div class='ev-main-row'>
                    <span class='ev-name'>Crisis Score</span>
                    <span class='ev-value' style='color:#93c5fd'>{_meta_crisis_score:.1f}</span>
                </div>
                <div class='ev-status'>Semakin tinggi skor, semakin tinggi tingkat risiko.</div>
                <div class='ev-value' style='color:{_meta_color};font-size:18px;margin-top:6px'>{_meta_level}</div>
                <div class='ev-text' style='margin-top:6px'>{_meta_kategori_html}</div>
                <div class='ev-text' style='margin-top:8px'>
                    Level risiko digunakan sebagai dasar rekomendasi tindakan pada dashboard.
                </div>
            </div>
        """

        _meta_panel_html = _arrow.join([
            _meta_input_html, _meta_analisis_html, _meta_output_html,
        ])
        st.markdown(f"<div class='why-now-flow'>{_meta_panel_html}</div>", unsafe_allow_html=True)
    # ── [AKHIR REVISI Sprint 2.2 / Panel Metodologi Crisis Score] ───

    # ── Charts — langsung tanpa container blok ──────────────────────
    st.plotly_chart(_build_overview_fig2(str(sel), predictions),
                    use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:4px;border-top:1px solid rgba(255,255,255,0.06)'></div>",
                unsafe_allow_html=True)

    st.plotly_chart(_build_overview_fig3(str(sel), predictions),
                    use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:4px;border-top:1px solid rgba(255,255,255,0.06)'></div>",
                unsafe_allow_html=True)

    st.plotly_chart(_build_overview_fig1(str(sel), predictions),
                    use_container_width=True, config={'displayModeBar': False})

    #Revisi + Tambahan
    # ── External Risk Monitor ──────────────────────────────
    def _risk_pct(val):
        if val is None:
            return None
        val = float(val)
        return val * 100 if val <= 1 else val

    def _risk_color(pct):
        if pct is None:
            return '#64748b'
        if pct < 30:
            return '#00c794'
        if pct < 60:
            return '#fbbf24'
        return '#d90000'

    def _fmt_pct(pct):
        return f"{pct:.1f}%" if pct is not None else "N/A"

    _phys_pct = _risk_pct(physical_risk_score)
    _media_pct = _risk_pct(media_risk_score)
    _tourist_pct = _risk_pct(tourist_perception_score)
    _ext_pct = _risk_pct(external_risk_score)

    _risk_cards = [
        ("Physical Risk", _phys_pct, "BMKG + Gempa + Cuaca"),
        ("Media Risk", _media_pct, "GDELT + Tone Berita"),
        ("Tourist Perception", _tourist_pct, "Google Trends + Economic Risk"),
        ("External Risk", _ext_pct, "Gabungan ketiga komponen di atas"),
    ]
    
    _risk_cards_html = "".join(f"""
      <div style='flex:1;text-align:center;padding:14px 16px;
                  {'border-right:1px solid rgba(255,255,255,0.06)' if i < 3 else ''}'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            {label}
        </div>
        <div style='font-family:"DM Serif Display";font-size:26px;font-weight:700;
                    color:{_risk_color(pct)};line-height:1;margin-bottom:8px'>
            {_fmt_pct(pct)}
        </div>
        <div style='font-size:11px;color:#94a3b8;font-family:"DM Sans";line-height:1.4'>
            {desc}
        </div>
      </div>
    """ for i, (label, pct, desc) in enumerate(_risk_cards))

    st.markdown(f"""
    <div style='margin-top:32px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.07)'>
      <div style='text-align:center;font-family:"DM Sans";font-size:25px;font-weight:700;
                  color:#ff6c43;margin-bottom:16px'>
          External Risk Monitor
      </div>
      <div style='display:flex;justify-content:center;gap:0'>
        {_risk_cards_html}
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── [SISIPKAN DI SINI] Metodologi External Risk ───────────────────
    with st.expander("Metodologi External Risk Score", expanded=False):
        st.markdown("""
        <div style='font-size:13px;color:#94a3b8;line-height:1.9;font-family:"DM Sans"'>

          <div style='margin-bottom:14px;color:#cbd5e1;font-size:13px;line-height:1.7'>
            External Risk Score merupakan indeks komposit yang mengintegrasikan tiga
            dimensi risiko eksterior pariwisata Bali melalui pembobotan tertimbang
            (<em>weighted composite index</em>). Setiap komponen dinormalisasi ke skala
            0–100 sebelum diagregasi.
          </div>

          <!-- Tabel Komponen -->
          <table style='width:100%;border-collapse:collapse;margin-bottom:16px;font-size:12px'>
            <thead>
              <tr style='border-bottom:1px solid rgba(255,255,255,0.08)'>
                <th style='text-align:left;padding:6px 10px;color:#64748b;
                           font-weight:700;letter-spacing:.06em;text-transform:uppercase'>
                  Komponen
                </th>
                <th style='text-align:left;padding:6px 10px;color:#64748b;
                           font-weight:700;letter-spacing:.06em;text-transform:uppercase'>
                  Sumber Data
                </th>
                <th style='text-align:center;padding:6px 10px;color:#64748b;
                           font-weight:700;letter-spacing:.06em;text-transform:uppercase'>
                  Bobot
                </th>
              </tr>
            </thead>
            <tbody>
              <tr style='border-bottom:1px solid rgba(255,255,255,0.05)'>
                <td style='padding:8px 10px;color:#e2e8f0;font-weight:600'>Physical Risk</td>
                <td style='padding:8px 10px;color:#94a3b8'>
                  BMKG · Frekuensi Gempa · Indeks Cuaca Ekstrem
                </td>
                <td style='padding:8px 10px;text-align:center;
                           color:#fbbf24;font-weight:700;font-family:"DM Serif Display"'>
                  35%
                </td>
              </tr>
              <tr style='border-bottom:1px solid rgba(255,255,255,0.05)'>
                <td style='padding:8px 10px;color:#e2e8f0;font-weight:600'>Media Risk</td>
                <td style='padding:8px 10px;color:#94a3b8'>
                  GDELT · Tone Rata-rata Berita · Event Risiko Terpublikasi
                </td>
                <td style='padding:8px 10px;text-align:center;
                           color:#fbbf24;font-weight:700;font-family:"DM Serif Display"'>
                  35%
                </td>
              </tr>
              <tr>
                <td style='padding:8px 10px;color:#e2e8f0;font-weight:600'>Tourist Perception</td>
                <td style='padding:8px 10px;color:#94a3b8'>
                  Google Trends · Economic Risk Index
                </td>
                <td style='padding:8px 10px;text-align:center;
                           color:#fbbf24;font-weight:700;font-family:"DM Serif Display"'>
                  30%
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Formula -->
          <div style='background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                      border-radius:8px;padding:12px 16px;margin-bottom:12px'>
            <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                        letter-spacing:.1em;color:#64748b;margin-bottom:8px'>
              Fungsi Agregasi
            </div>
            <div style='font-family:monospace;font-size:13px;color:#e2e8f0;line-height:1.8'>
              <span style='color:#fbbf24'>External Risk</span> =
              0.35 × <span style='color:#f87171'>Physical Risk</span> +
              0.35 × <span style='color:#fb923c'>Media Risk</span> +
              0.30 × <span style='color:#a78bfa'>Tourist Perception</span>
            </div>
          </div>

          <div style='font-size:11px;color:#475569;font-style:italic'>
            Pembobotan ditentukan melalui expert judgment dan validasi korelasi terhadap
            data historis krisis pariwisata Bali (2002–2024). Total bobot = 1.00.
          </div>

        </div>
        """, unsafe_allow_html=True)
    # ── [AKHIR SISIPAN] ────────────────────────────────────────────────

    # ── Summary Stats Strip ───────────────────────────────
    _pct_aman   = (predictions['crisis_level']=='AMAN').mean()*100
    _pct_krisis = (predictions['crisis_level']=='KRISIS').mean()*100
    _avg_score  = predictions['crisis_score_100'].mean()
    _peak_wis   = predictions['wisman'].max()

    # AFTER
    st.markdown(f"""
    <div style='margin-top:32px;padding-top:20px;padding-bottom:20px;margin-bottom:48px;
                border-top:1px solid rgba(255,255,255,0.07);
                display:flex;justify-content:center;gap:0'>
      <div style='flex:1;text-align:center;padding:12px 16px;
                  border-right:1px solid rgba(255,255,255,0.06)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Bulan Level AMAN
        </div>
        <div style='font-family:"DM Serif Display";font-size:26px;font-weight:700;
                    color:#00c794;line-height:1'>
            {_pct_aman:.1f}%
        </div>
      </div>
      <div style='flex:1;text-align:center;padding:12px 16px;
                  border-right:1px solid rgba(255,255,255,0.06)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Bulan Level KRISIS
        </div>
        <div style='font-family:"DM Serif Display";font-size:26px;font-weight:700;
                    color:#d90000;line-height:1'>
            {_pct_krisis:.1f}%
        </div>
      </div>
      <div style='flex:1;text-align:center;padding:12px 16px;
                  border-right:1px solid rgba(255,255,255,0.06)'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Avg Crisis Score
        </div>
        <div style='font-family:"DM Serif Display";font-size:26px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_avg_score:.1f}
        </div>
      </div>
      <div style='flex:1;text-align:center;padding:12px 16px'>
        <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.12em;color:#64748b;margin-bottom:8px;font-family:"DM Sans"'>
            Peak Wisman
        </div>
        <div style='font-family:"DM Serif Display";font-size:26px;font-weight:700;
                    color:#93c5fd;line-height:1'>
            {_peak_wis:,}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
