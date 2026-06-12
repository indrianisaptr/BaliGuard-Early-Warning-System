"""
src/shared.py — BaliGuard: Shared Context Builder
build_context() dipanggil sekali di dashboard.py,
hasilnya di-pass ke semua render() halaman.
"""
import numpy as np
import pandas as pd

from src.utils import (sf, level_from_score, get_current_usd_idr,
                        compute_delta_context)
from src.services.forecast import forecast_months, project_future_row
from src.config import COLOR_MAP as LEVEL_COLORS


def build_context(
    predictions: pd.DataFrame, master: pd.DataFrame,
    narratives_cache: dict,
    rf_model, iso_model, scaler, le,
    sel: str, logo_html: str, nav_icons: dict,
) -> dict:
    """Kumpulkan semua variabel shared ke satu dict ctx."""
    ctx: dict = {
        'predictions': predictions, 'master': master,
        'narratives_cache': narratives_cache,
        'rf_model': rf_model, 'iso_model': iso_model,
        'scaler': scaler, 'le': le,
        'sel': sel, 'logo_html': logo_html, 'nav_icons': nav_icons,
    }

    sorted_months           = sorted(predictions['month'].dropna().unique().tolist())
    ctx['sorted_months']    = sorted_months
    ctx['last_data_month']  = sorted_months[-1] if sorted_months else sel
    ctx['is_projection']    = sel > ctx['last_data_month']

    # Row data
    if ctx['is_projection']:
        row_data = project_future_row(predictions, sel)
    else:
        rows = predictions[predictions['month'] == sel]
        row_data = rows.iloc[0].to_dict() if len(rows) else {}
    ctx['row_data'] = row_data

    # KPI values
    ctx.update({
        'level':    str(row_data.get('crisis_level', 'AMAN')),
        'score':    sf(row_data.get('crisis_score_100', 0)),
        'rf_pred':  str(row_data.get('rf_predicted_level', 'AMAN')),
        'conf':     sf(row_data.get('rf_confidence', 0)),
        'is_anom':  int(sf(row_data.get('iso_anomaly', 0))),
        'wisman':   sf(row_data.get('wisman', 0)),
        'tpk':      sf(row_data.get('tpk_bintang', 0)),
        'inflasi':  sf(row_data.get('inflasi_processed', 0)),
        'sent':     sf(row_data.get('avg_sentiment_monthly', 0)),
        'bali_shr': sf(row_data.get('bali_share_pct', 0)),
        # ── 4 indikator risiko baru ──────────────────────────────────
        'physical_risk':      sf(row_data.get('physical_risk_score', 0)),
        'media_risk':         sf(row_data.get('media_risk_score', 0)),
        'tourist_perception': sf(row_data.get('tourist_perception_score', 0)),
        'external_risk':      sf(row_data.get('external_risk_score', 0)),
    })
    ctx['color'] = LEVEL_COLORS.get(ctx['level'], '#64748b')

    # USD/IDR
    usd_val, usd_live = get_current_usd_idr(predictions, sel)
    ctx['usd_avg']     = usd_val if usd_val else sf(row_data.get('usd_idr_avg', 0))
    ctx['usd_is_live'] = usd_live

    # Delta MoM
    try:
        ctx['delta_ctx'] = compute_delta_context(row_data, predictions, sel)
    except Exception:
        ctx['delta_ctx'] = {}

    # Forecast 6 bulan — returns (list, trend)
    try:
        _fc_list, _fc_trend   = forecast_months(predictions, n=6, from_month=sel)
        ctx['forecast']       = _fc_list
        ctx['forecast_trend'] = _fc_trend
    except Exception:
        ctx['forecast']       = []
        ctx['forecast_trend'] = 0.0

    # Summary stats
    ctx['pct_aman']   = (predictions['crisis_level'] == 'AMAN').mean() * 100
    ctx['pct_krisis'] = (predictions['crisis_level'] == 'KRISIS').mean() * 100
    ctx['avg_score']  = predictions['crisis_score_100'].mean()

    # Prev month
    try:
        idx = sorted_months.index(sel)
        if idx > 0:
            prev_rows = predictions[predictions['month'] == sorted_months[idx-1]]
            ctx['prev_row'] = prev_rows.iloc[0].to_dict() if len(prev_rows) else {}
        else:
            ctx['prev_row'] = {}
    except Exception:
        ctx['prev_row'] = {}

    # ── Extra context fields (dipakai analisis.py, narasi.py) ────────
    # recovery_pct
    ctx['recovery_pct'] = sf(row_data.get('wisman_recovery_pct', 0))

    # score delta vs bulan sebelumnya
    prev_score = sf(ctx['prev_row'].get('crisis_score_100', ctx['score']))
    score_delta = round(ctx['score'] - prev_score, 1)
    ctx['score_delta'] = score_delta
    ctx['score_trend']  = ('MENINGKAT' if score_delta > 2
                           else 'MENURUN' if score_delta < -2 else 'STABIL')

    # Dominant factor (dari z-score dan volatility)
    zscore   = sf(row_data.get('wisman_zscore', 0))
    usd_vol  = sf(row_data.get('usd_volatility_3m', 0))
    pct_neg  = sf(row_data.get('pct_negative_monthly', 0))
    factors  = {
        'Kunjungan Wisatawan': abs(zscore),
        'Tekanan Kurs':        usd_vol / 500.0 if usd_vol else 0,
        'Sentimen Negatif':    pct_neg / 100.0 if pct_neg else 0,
    }
    ctx['dominant_factor'] = max(factors, key=factors.get)
    # Pre-COVID baseline (rata-rata wisman 2017–2019)
    _pre = predictions[
        pd.to_datetime(predictions['month'].astype(str)).dt.year.isin([2017, 2018, 2019])
    ]['wisman'] if 'wisman' in predictions.columns else pd.Series(dtype=float)
    ctx['precovid_mean'] = float(_pre.mean()) if len(_pre) > 0 else 0.0

    # Anomaly explanation
    if zscore <= -3:
        ctx['anomaly_exp'] = (f'Z-score {zscore:.1f} — kunjungan {abs(zscore):.1f}σ '
                               'di bawah rata-rata (kejadian ekstrem <0.1%)')
    elif zscore <= -2:
        ctx['anomaly_exp'] = f'Z-score {zscore:.1f} — anomali signifikan'
    else:
        ctx['anomaly_exp'] = f'Z-score {zscore:.1f} — dalam rentang normal'

    # Alias tambahan untuk kompatibilitas file lama
    ctx['_pct_aman']   = ctx['pct_aman']
    ctx['_pct_krisis'] = ctx['pct_krisis']
    ctx['_avg_score']  = ctx['avg_score']

    return ctx
