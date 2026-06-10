"""
src/services/forecast.py — BaliGuard: Forecast & Projection Service
Semua kalkulasi proyeksi masa depan ada di sini.
"""
import streamlit as st
import pandas as pd
import numpy as np
from src.config import THRESHOLD, WEIGHT_TOURISM, WEIGHT_ECONOMY, WEIGHT_SENTIMENT
# from src.utils import level_from_score
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from src.utils import sf

def level_from_score(s: float) -> str:
    if s >= THRESHOLD["KRISIS"]:
        return "KRISIS"
    if s >= THRESHOLD["SIAGA"]:
        return "SIAGA"
    if s >= THRESHOLD["WASPADA"]:
        return "WASPADA"
    return "AMAN"


def project_future_row(predictions: pd.DataFrame, target_month: str) -> dict:
    """
    Proyeksikan satu baris data untuk bulan di luar data historis.
    Menggunakan tren linear dari 6 bulan terakhir.
    """
    last_rows = predictions.tail(6)
    proj: dict = {}
    num_cols = predictions.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        vals = last_rows[col].dropna()
        if len(vals) >= 3:
            trend = np.polyfit(range(len(vals)), vals.values, 1)
            proj[col] = float(np.polyval(trend, len(vals)))
        elif len(vals):
            proj[col] = float(vals.mean())
        else:
            proj[col] = 0.0
    proj['month']        = target_month
    proj['crisis_level'] = level_from_score(
    proj.get('crisis_score_100', 30.0)
    )
    # Clip ke range yang masuk akal
    proj['crisis_score_100'] = float(np.clip(proj.get('crisis_score_100', 30.0), 0, 100))
    return proj


@st.cache_data(show_spinner=False)
def forecast_months(pred_df: pd.DataFrame, n: int = 6,
                    from_month: str = None) -> tuple:
    """
    Proyeksi n bulan ke depan dari from_month.
    Return: (results: list[dict], trend: float)
    Kompatibel dengan prediksi.py dan narasi.py.
    """
    last_n   = pred_df.tail(12)
    last_val = float(last_n['crisis_score_100'].values[-1])
    trend    = float(np.polyfit(range(len(last_n)), last_n['crisis_score_100'].values, 1)[0])

    data_last_p = pd.Period(pred_df['month'].iloc[-1], freq='M')

    if from_month is None:
        start_p = data_last_p
        base    = last_val
    else:
        start_p = pd.Period(str(from_month)[:7], freq='M')
        offset  = int((start_p - data_last_p).n)
        base    = float(np.clip(last_val + trend * offset, 0, 100))

    results = []
    for i in range(1, n + 1):
        p    = start_p + i
        m    = str(p)
        # Ambil dari historis jika tersedia
        if m in pred_df['month'].values:
            row = pred_df[pred_df['month'] == m].iloc[0].to_dict()
            row.setdefault('score', row.get('crisis_score_100', 0))
            row.setdefault('level', row.get('crisis_level', 'AMAN'))
            row.setdefault('confidence', sf(row.get('rf_confidence', 0.5)) * 100)
            results.append(row)
        else:
            sc   = float(np.clip(base + trend * i, 0, 100))
            conf = max(35.0, 85.0 - (i - 1) * 10.0)
            results.append({
                'month':             m,
                'score':             round(sc, 1),
                'level':             level_from_score(sc),
                'confidence':        conf,
                'crisis_score_100':  round(sc, 1),
                'crisis_level':      level_from_score(sc),
                'rf_predicted_level': level_from_score(sc),
                'rf_confidence':     conf / 100,
            })
    return results, round(trend, 2)


def compute_trend_direction(predictions: pd.DataFrame,
                             col: str = 'crisis_score_100',
                             n: int = 3) -> tuple[str, float]:
    """
    Hitung arah tren n bulan terakhir.
    Return: (direction, delta) — direction ∈ {'up','down','flat'}
    """
    vals = predictions.sort_values('month').tail(n)[col].dropna()
    if len(vals) < 2:
        return 'flat', 0.0
    delta = float(vals.iloc[-1] - vals.iloc[0])
    if abs(delta) < 1.0:
        return 'flat', delta
    return ('up' if delta > 0 else 'down'), delta
