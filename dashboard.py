"""
dashboard.py — BaliGuard Early Warning System
==============================================
Entry point. File ini hanya berisi 5 tanggung jawab:
  1. Page config & inject CSS
  2. Load data & model (cached via src/utils.py)
  3. Render sidebar → dapat selected_nav & sel
  4. Build shared context (src/shared.py)
  5. Route ke halaman yang sesuai (src/pages/)
"""
import time
import streamlit as st
from pathlib import Path
import pandas as pd

_t0 = time.perf_counter()

# ── Logo ─────────────────────────────────────────────────────────────
@st.cache_resource
def _load_logo():
    from PIL import Image
    import base64
    for fname in ['assets/icons/FIX.webp', 'assets/icons/FIX.png']:
        p = Path(fname)
        if p.exists():
            ext = p.suffix[1:]
            with open(p, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            img = Image.open(p)
            return img, f'data:image/{ext};base64,{b64}'
    return None, ''

_logo_img, _logo_html = _load_logo()

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title='BaliGuard — Early Warning Pariwisata',
    page_icon=_logo_img if _logo_img else '🛡️',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── CSS dari file eksternal ───────────────────────────────────────────
@st.cache_resource
def _load_css() -> str:
    p = Path('assets/styles.css')
    return p.read_text(encoding='utf-8') if p.exists() else ''

st.markdown(f'<style>{_load_css()}</style>', unsafe_allow_html=True)

# ── Load data & model ─────────────────────────────────────────────────
from src.utils   import load_data, load_models, load_nav_icons
from src.sidebar import render_sidebar
from src.shared  import build_context

try:
    master, predictions, narratives_cache = load_data()
    rf_model, iso_model, scaler, le       = load_models()
    nav_icons                             = load_nav_icons()
    DATA_OK = True
except Exception as e:
    DATA_OK, DATA_ERR = False, str(e)

if not DATA_OK:
    st.error(f'❌ Gagal memuat data: {DATA_ERR}')
    st.info('Jalankan `python update_pipeline.py` lalu `python retrain_model.py` terlebih dahulu.')
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────
selected_nav, sel = render_sidebar({
    'predictions': predictions,
    'logo_html':   _logo_html,
    'nav_icons':   nav_icons,
})

# ── Build context ─────────────────────────────────────────────────────
ctx = build_context(
    predictions=predictions, master=master,
    narratives_cache=narratives_cache,
    rf_model=rf_model, iso_model=iso_model,
    scaler=scaler, le=le,
    sel=sel, logo_html=_logo_html, nav_icons=nav_icons,
)
ctx['selected_nav'] = selected_nav

# ══════════════════════════════════════════════════════
# HEADER, KPI, ALERT — sama persis dengan dashboard.py asli
# ══════════════════════════════════════════════════════
import streamlit.components.v1 as components

_last_month = predictions['month'].iloc[-1]
_n_months   = len(predictions)

st.markdown(f"""
<div style='background:linear-gradient(135deg,#0a1628 0%,#132349 55%,#0c1d40 100%);
            border-radius:18px;padding:26px 32px;margin-bottom:20px;
            border:1px solid rgba(255,255,255,0.09);
            box-shadow:0 8px 40px rgba(0,0,0,0.5)'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px'>
        <div style='display:flex;align-items:center;gap:16px'>
            <img src='{_logo_html}' style='width:80px;height:80px;object-fit:contain;border-radius:12px'/>
            <div>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.18em;
                            color:rgba(255,255,255,0.5);margin-bottom:5px;font-family:"DM Sans"'>
                    SISTEM DETEKSI DINI PARIWISATA
                </div>
                <div style='font-family:"DM Serif Display";font-size:30px;color:#f1f5f9;
                            letter-spacing:-.02em;line-height:1.1'>BaliGuard</div>
                <div style='font-size:14px;color:rgba(255,255,255,0.6);margin-top:6px;line-height:1.65;font-family:"DM Sans"'>
                    Dashboard Early Warning System &mdash; Multi-Sumber Data,
                    Machine Learning &amp; Analisis Sentimen Multibahasa
                </div>
            </div>
        </div>
        <div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                    border-radius:12px;padding:14px 20px;text-align:center;flex-shrink:0'>
            <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;
                        color:rgba(255,255,255,0.55);margin-bottom:5px;font-family:"DM Sans"'>DATA TERAKHIR</div>
            <div style='font-family:"JetBrains Mono";font-size:20px;color:#93c5fd;font-weight:700'>
                {_last_month}
            </div>
            <div style='font-size:13px;color:rgba(255,255,255,0.45);margin-top:4px;font-family:"DM Sans"'>
                {_n_months} bulan data historis
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Projection Banner ─────────────────────────────────
from src.services.forecast import forecast_months as _fc_fn
import pandas as _pd_h
from datetime import datetime
_current_real  = _pd_h.Period(datetime.now().strftime('%Y-%m'), freq='M')
_prev_real     = _current_real - 1
_fc_list_h, _fc_trend_h = _fc_fn(predictions, n=6, from_month=str(_prev_real))
_current_fc    = _fc_list_h[0]
_curr_lv       = _current_fc['level']
_curr_sc       = _current_fc['score']
_curr_conf     = _current_fc['confidence']
_curr_mo       = _current_fc['month']
_fc_trend      = _fc_trend_h
_trend_txt     = "↗ MENINGKAT" if _fc_trend > 0.5 else ("↘ MENURUN" if _fc_trend < -0.5 else "→ STABIL")
_trend_col     = "#d90000" if _fc_trend > 0.5 else ("#22c55e" if _fc_trend < -0.5 else "#FFBC37")
_tren_val_col  = "#f87171" if _fc_trend < 0 else ("#4ade80" if _fc_trend > 0 else "#94a3b8")

COLOR_MAP_H = {'AMAN':'#236A26','WASPADA':'#F9F871','SIAGA':'#ff6c43','KRISIS':'#d90000'}

st.markdown(f"""
<div style='background:rgba(14,28,60,0.7);border:1px solid rgba(255,255,255,0.09);
            border-radius:14px;padding:18px 26px;margin-bottom:14px'>
    <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px'>
        <div>
            <div style='font-size:12px;font-weight:700;color:#FFBC37;text-transform:uppercase;
                        letter-spacing:.13em;margin-bottom:8px;font-family:"DM Sans"'>
                PROYEKSI BULAN INI &mdash; {_curr_mo}
            </div>
            <div style='display:flex;align-items:center;gap:16px;flex-wrap:wrap'>
                <div style='display:flex;align-items:center;gap:8px'>
                    <span class='status-dot dot-{_curr_lv}' style='width:12px;height:12px'></span>
                    <span style='font-family:"DM Serif Display";font-size:26px;
                                 color:{COLOR_MAP_H.get(_curr_lv,"#E0A226")};line-height:1'>{_curr_lv}</span>
                </div>
                <div style='font-family:"JetBrains Mono";font-size:14px;color:#FFFFFF'>
                    Score&nbsp;<span style='color:#FFBC37;font-weight:700;font-size:17px'>{_curr_sc}</span>/100
                </div>
                <div style='font-size:12px;color:#ffffff;font-weight:700;font-family:"DM Sans"'>{_trend_txt}</div>
            </div>
        </div>
        <div style='display:flex;gap:6px'>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#FFBC37;margin-bottom:4px;font-family:"DM Sans"'>CONFIDENCE</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:700'>{_curr_conf:.0f}%</div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#FFBC37;margin-bottom:4px;font-family:"DM Sans"'>PROYEKSI DARI</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:#93c5fd;font-weight:600'>{_last_month}</div>
            </div>
            <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);
                        border-radius:10px;padding:10px 18px;text-align:center;min-width:82px'>
                <div style='font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                            color:#FFBC37;margin-bottom:4px;font-family:"DM Sans"'>TREN/BULAN</div>
                <div style='font-family:"JetBrains Mono";font-size:18px;color:{_tren_val_col};font-weight:700'>{_fc_trend:+.2f}</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI + Alert — ambil dari ctx ──────────────────────
_row_data   = ctx['row_data']
_is_proj    = ctx['is_projection']
_level      = ctx['level']
_score      = ctx['score']
_wisman     = ctx['wisman']
_tpk        = ctx['tpk']
_conf_kpi   = ctx['conf'] * 100
_rf_pred    = ctx['rf_pred']
_sent       = ctx['sent']
_usd_avg    = ctx['usd_avg']
_usd_live   = ctx['usd_is_live']
_delta_ctx  = ctx['delta_ctx']
_prev_month = ctx['prev_row'].get('month') if ctx['prev_row'] else None
_p_score    = float(ctx['prev_row'].get('crisis_score_100', _score)) if ctx['prev_row'] else _score
_p_wisman   = float(ctx['prev_row'].get('wisman', _wisman)) if ctx['prev_row'] else _wisman
_p_tpk      = float(ctx['prev_row'].get('tpk_bintang', _tpk)) if ctx['prev_row'] else _tpk
_p_sent     = float(ctx['prev_row'].get('avg_sentiment_monthly', _sent)) if ctx['prev_row'] else _sent
_p_usd      = float(ctx['prev_row'].get('usd_idr_avg', _usd_avg)) if ctx['prev_row'] else _usd_avg
_proj_conf  = int(_row_data.get('_proj_confidence', 85)) if _is_proj else None

def _delta_txt(curr, prev_val, fmt=".1f", suffix="", invert=False):
    if prev_val is None or prev_val == 0:
        return "<span style='color:#64748b;font-size:12px'>— vs bln lalu</span>"
    d    = curr - prev_val
    pct  = (d / abs(prev_val) * 100) if prev_val != 0 else 0
    good = (d < 0) if invert else (d > 0)
    col  = "#4ade80" if good else ("#f87171" if (d < 0 if not invert else d > 0) else "#94a3b8")
    sign = "▲" if d > 0 else ("▼" if d < 0 else "→")
    if suffix == "%":
        txt = f"{sign} {abs(d):.1f}pp vs bln lalu"
    elif suffix == "pct_change":
        txt = f"{sign} {abs(pct):.1f}% vs bln lalu"
    else:
        txt = f"{sign} {abs(d):{fmt}} vs bln lalu"
    return f"<span style='color:{col};font-size:12px;font-weight:700'>{txt}</span>"

_d_score  = _delta_txt(_score,   _p_score,  fmt=".1f", invert=True)
_d_wisman = _delta_txt(_wisman,  _p_wisman, suffix="pct_change")
_d_tpk    = _delta_txt(_tpk,     _p_tpk,   suffix="%")
_d_sent   = _delta_txt(_sent,    _p_sent,   fmt="+.3f")
_d_usd    = _delta_txt(_usd_avg, _p_usd,    suffix="pct_change", invert=True)

_proj_badge_html = (
    f"<span style='font-size:9px;background:rgba(167,139,250,0.15);"
    f"color:#a78bfa;padding:2px 7px;border-radius:8px;"
    f"border:1px solid rgba(167,139,250,0.3);font-family:DM Sans'>PROYEKSI ~{_proj_conf}%</span>"
    if _is_proj else ""
)
_usd_sub_html = (
    "<span style='display:inline-flex;align-items:center;gap:5px;font-size:10px;"
    "font-weight:700;background:rgba(239,68,68,0.15);color:#ef4444;padding:3px 8px;"
    "border-radius:20px;border:1px solid rgba(239,68,68,0.3);letter-spacing:.04em'>"
    "<span style='width:6px;height:6px;border-radius:50%;background:#ef4444;"
    "animation:pulse 1.5s infinite;flex-shrink:0;display:inline-block'></span>LIVE</span>"
    if _usd_live else "kurs rata-rata"
)

def _kpi_card_html(label, value, sub, delta, level=None, use_dot=False):
    accent = {"AMAN":"#00c794","WASPADA":"#F9F871","SIAGA":"#ff6c43","KRISIS":"#d90000"}.get(level,"#3b82f6")
    label_color = accent if level else "#1119FF"
    dot = (f"<span style='display:inline-block;width:16px;height:16px;border-radius:50%;"
           f"background:{accent};box-shadow:0 0 6px {accent};margin-right:8px;"
           f"vertical-align:middle;flex-shrink:0'></span>") if use_dot else ""
    value_color = f"color:{accent} !important" if level else ""
    return f"""
<div class="kpi-c" style="border-top:2px solid {accent}">
  <div class="kpi-c-label" style="color:{label_color} !important">{label}</div>
  <div class="kpi-c-value" style="{value_color}">{dot}{value}</div>
  <div class="kpi-c-sub">{sub}</div>
  <div class="kpi-c-delta">{delta}</div>
</div>"""

_cards = [
    _kpi_card_html("LEVEL KRISIS", _level,
                   (_proj_badge_html + f" RF: {_rf_pred}") if _proj_badge_html else f"RF: {_rf_pred}",
                   f"<span style='color:#334155;font-size:10px'>{_prev_month or '—'}</span>",
                   _level, use_dot=True),
    _kpi_card_html("USD/IDR", f"Rp {_usd_avg:,.0f}", _usd_sub_html, _d_usd),
    _kpi_card_html("CRISIS SCORE", f"{_score:.1f}",
                   f"dari 100 &nbsp;·&nbsp; conf {_conf_kpi:.0f}%", _d_score),
    _kpi_card_html("WISMAN", f"{int(_wisman):,}",
                   "est. proyeksi" if _is_proj else "kunjungan bulan ini", _d_wisman),
    _kpi_card_html("TPK BINTANG", f"{_tpk:.1f}%",
                   "est. proyeksi" if _is_proj else "tingkat hunian hotel", _d_tpk),
    _kpi_card_html("SENTIMEN", f"{_sent:+.3f}",
                   "est. proyeksi" if _is_proj else "rata-rata ulasan", _d_sent),
    
]

# Carousel HTML (sama persis dengan dashboard.py asli, diambil dari sana)
_carousel_html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:transparent;overflow:hidden;margin:0;padding:0}
#kpi-root{position:relative;overflow:hidden;padding:6px 0 4px}
#kpi-root::before,#kpi-root::after{content:'';position:absolute;top:0;bottom:0;width:28px;pointer-events:none;z-index:10}
#kpi-root::before{left:0;background:linear-gradient(to right,#060d1c 60%,transparent)}
#kpi-root::after{right:0;background:linear-gradient(to left,#060d1c 60%,transparent)}
#kpi-track{display:flex;gap:14px;padding:6px 28px 8px 20px;will-change:transform;cursor:grab}
#kpi-track:active{cursor:grabbing}
.kpi-c{flex:0 0 260px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:18px 20px 16px;text-align:center;transition:transform .22s cubic-bezier(.34,1.56,.64,1),box-shadow .22s ease,border-color .22s ease,background .22s ease}
.kpi-c:hover{transform:translateY(-5px) scale(1.025);box-shadow:0 12px 32px rgba(0,0,0,0.45);border-color:rgba(255,255,255,0.16);background:rgba(255,255,255,0.07)}
.kpi-c-label{font-size:15px!important;font-weight:700!important;color:#94a3b8!important;text-transform:uppercase!important;letter-spacing:.1em!important;margin-bottom:8px!important;font-family:'DM Sans',sans-serif!important;text-align:center!important}
.kpi-c-value{font-size:26px!important;font-weight:700!important;color:#f1f5f9!important;line-height:1.1!important;font-family:'DM Serif Display',serif!important;letter-spacing:-.01em!important;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important}
.kpi-c-sub{font-size:13px!important;color:#94a3b8!important;margin-top:6px!important;font-family:'DM Sans',sans-serif!important;line-height:1.5!important;text-align:center!important}
.kpi-c-delta{margin-top:7px;font-size:13px;font-weight:600;font-family:sans-serif;line-height:1.4}
.kpi-btn{position:absolute;top:50%;transform:translateY(-55%);width:32px;height:32px;border-radius:50%;background:rgba(15,25,50,0.92);border:1px solid rgba(255,255,255,0.15);color:#94a3b8;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:20;font-size:22px;line-height:1;user-select:none;box-shadow:0 2px 10px rgba(0,0,0,0.5);transition:background .15s,color .15s,box-shadow .15s}
.kpi-btn:hover{background:rgba(59,130,246,0.35);border-color:rgba(59,130,246,0.6);color:#fff;box-shadow:0 4px 16px rgba(59,130,246,0.35)}
#kpi-btn-l{left:2px}#kpi-btn-r{right:2px}
</style></head><body>
<div id="kpi-root">
  <div id="kpi-track">CARDS_PLACEHOLDER</div>
  <div class="kpi-btn" id="kpi-btn-l">&#8249;</div>
  <div class="kpi-btn" id="kpi-btn-r">&#8250;</div>
</div>
<script>
(function(){
  var DUR=350,track=document.getElementById('kpi-track');
  var btnL=document.getElementById('kpi-btn-l'),btnR=document.getElementById('kpi-btn-r');
  var N=track.children.length,current=0,busy=false;
  function getStep(){var c=track.children[0];if(!c)return 274;var s=window.getComputedStyle(track);return c.getBoundingClientRect().width+(parseFloat(s.gap||s.columnGap)||14);}
  function maxIdx(){var root=document.getElementById('kpi-root');var vw=root?root.getBoundingClientRect().width:window.innerWidth;var step=getStep();return Math.round(Math.max(0,N*step-14-vw+48)/step);}
  function updateArrows(){var mx=maxIdx();btnL.style.opacity=current===0?'0.25':'1';btnL.style.pointerEvents=current===0?'none':'auto';btnR.style.opacity=current>=mx?'0.25':'1';btnR.style.pointerEvents=current>=mx?'none':'auto';}
  function slideTo(idx){if(busy)return;idx=Math.max(0,Math.min(idx,maxIdx()));if(idx===current)return;busy=true;current=idx;track.style.transition='transform '+DUR+'ms cubic-bezier(0.4,0,0.2,1)';track.style.transform='translateX('+(-current*getStep())+'px)';setTimeout(function(){busy=false;},DUR+30);updateArrows();}
  btnL.addEventListener('click',function(){slideTo(current-1);});
  btnR.addEventListener('click',function(){slideTo(current+1);});
  var tx=0;
  track.addEventListener('touchstart',function(e){tx=e.touches[0].clientX;},{passive:true});
  track.addEventListener('touchend',function(e){var dx=e.changedTouches[0].clientX-tx;if(Math.abs(dx)>40){dx<0?slideTo(current+1):slideTo(current-1);}},{passive:true});
  track.style.transition='none';track.style.transform='translateX(0px)';updateArrows();
})();
</script>
</body></html>"""

_carousel_html = _carousel_html.replace('CARDS_PLACEHOLDER', "".join(_cards))
components.html(_carousel_html, height=160, scrolling=False)

# ── Alert Banner ──────────────────────────────────────
ALERTS = {
    'AMAN':    "Pariwisata Bali dalam kondisi <b>normal dan stabil</b>. Tidak ada indikasi krisis.",
    'WASPADA': "Terdapat <b>sinyal awal yang perlu dipantau</b>. Beberapa indikator menunjukkan tekanan ringan.",
    'SIAGA':   "⚠️ <b>Tekanan signifikan terdeteksi</b> pada sektor pariwisata Bali. Respons koordinatif diperlukan.",
    'KRISIS':  "🚨 <b>KRISIS TERDETEKSI.</b> Aktifkan protokol penanganan krisis pariwisata segera.",
}
ALERT_MAP_H = {'AMAN':'alert-aman','WASPADA':'alert-waspada','SIAGA':'alert-siaga','KRISIS':'alert-krisis'}

def _alert_html(level, title, body):
    return (f'<div class="{ALERT_MAP_H.get(level,"alert-aman")}">'
            f'<div class="alert-title">{title}</div>'
            f'<div class="alert-body">{body}</div></div>')

_dominant = _delta_ctx.get('dominant', _delta_ctx.get('dominant_factor', 'N/A'))
_score_delta = _delta_ctx.get('score_delta', 0)
_score_trend = _delta_ctx.get('score_trend', 'STABIL')

st.markdown(_alert_html(
    _level,
    f"Status Pariwisata Bali — {sel}",
    ALERTS.get(_level, "") +
    f" &nbsp;·&nbsp; Faktor dominan: <b>{_dominant}</b>"
    f" &nbsp;·&nbsp; Delta score: <b>{_score_delta:+.1f} poin</b> ({_score_trend})"
), unsafe_allow_html=True)

# ── Page Title ────────────────────────────────────────
_title_style = (
    "background-image:linear-gradient(to left top,"
    "#1119ff,#0054ff,#0072ff,#0088ed,#0099d6,"
    "#3694c4,#4c8eb2,#5b88a1,#4f708d,#465877,#3e4160,#352b48);"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;"
)
st.markdown(f"""
<div style='margin-top:48px;margin-bottom:28px;text-align:center;
            padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.07)'>
    <div style='font-family:"DM Serif Display",serif;font-size:38px;font-weight:400;
                letter-spacing:-.02em;line-height:1.15;display:inline-block;{_title_style}'>
        {selected_nav}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Route ─────────────────────────────────────────────────────────────
match selected_nav:
    case 'Overview & Timeline' | 'Gambaran Umum & Garis Waktu':
        from src.pages.overview import render
    case 'Analisis Detail':
        from src.pages.analisis import render
    case 'Sentimen':
        from src.pages.sentimen import render
    case 'Prediksi & Proyeksi':
        from src.pages.prediksi import render
    case 'Narasi AI':
        from src.pages.narasi   import render
    case _:
        from src.pages.overview import render

render(ctx)

# ══════════════════════════════════════════════════════
# TABEL DATA PREDIKSI — muncul di semua navigasi
# ══════════════════════════════════════════════════════
with st.expander("Tabel Data Prediksi Lengkap", expanded=False):
    _disp = ['month','wisman','tpk_bintang','inflasi_processed','usd_idr_avg',
             'avg_sentiment_monthly','bali_share_pct','wisman_zscore',
             'crisis_score_100','crisis_level','rf_predicted_level','rf_confidence','iso_anomaly']
    _disp    = [c for c in _disp if c in predictions.columns]
    _df_show = predictions[_disp].copy()

    _fmt = {
        'wisman':               '{:,.0f}',
        'tpk_bintang':          '{:.1f}%',
        'inflasi_processed':    '{:.2f}%',
        'usd_idr_avg':          'Rp {:,.0f}',
        'avg_sentiment_monthly':'{:+.3f}',
        'bali_share_pct':       '{:.1f}%',
        'wisman_zscore':        '{:.2f}',
        'crisis_score_100':     '{:.1f}',
        'rf_confidence':        '{:.0%}',
    }
    for _col, _fmt_str in _fmt.items():
        if _col in _df_show.columns:
            try:
                _df_show[_col] = _df_show[_col].apply(
                    lambda x: _fmt_str.format(x) if pd.notna(x) else '-')
            except Exception:
                pass

    st.dataframe(_df_show, use_container_width=True, height=420,
                 hide_index=True,
                 column_config={
                     'month':              st.column_config.TextColumn('Bulan',    width='small'),
                     'crisis_level':       st.column_config.TextColumn('Level',    width='small'),
                     'rf_predicted_level': st.column_config.TextColumn('RF Pred.', width='small'),
                     'iso_anomaly':        st.column_config.NumberColumn('Anomali', width='small'),
                 })

    _dl_cols = [c for c in ['month','wisman','crisis_score_100','crisis_level',
                             'rf_predicted_level','rf_confidence','iso_anomaly']
                if c in predictions.columns]
    st.download_button("⬇️ Download CSV",
        predictions[_dl_cols].to_csv(index=False),
        file_name=f"baliguard_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="dl_csv_global")

# ══════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center;padding:20px 0 8px;color:#334155;font-size:11px;
            line-height:2;border-top:1px solid rgba(255,255,255,0.05);margin-top:12px'>
    <b style='color:#475569'>BaliGuard</b> — Early Warning System Pariwisata Berbasis
    Multi-Sumber Data, Machine Learning &amp; Analisis Sentimen<br>
    <span style='font-size:10px;color:#1e293b'>
        Data: BPS Bali · Bank Indonesia · Google Hotels &nbsp;|&nbsp;
        Model: Isolation Forest + Random Forest + XLM-RoBERTa &nbsp;|&nbsp;
        Narasi: Groq LLM (llama-3.3-70b-versatile / llama-3.1-8b / qwen3-32b / llama-4-scout)
    </span>
</div>
""", unsafe_allow_html=True)

# ── Render timer di sidebar ───────────────────────────────────────────
st.sidebar.caption(f'⏱ Render: {time.perf_counter() - _t0:.2f}s')
