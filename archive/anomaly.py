"""
src/services/anomaly.py — BaliGuard: Anomaly Detection Helpers
"""
import numpy as np
import pandas as pd


def get_anomaly_context(predictions: pd.DataFrame, sel_month: str) -> dict:
    """
    Ambil konteks anomali untuk bulan yang dipilih.
    Return dict: is_anomaly, anomaly_months, pct_anomaly, nearby_events
    """
    anom_col = 'iso_anomaly'
    if anom_col not in predictions.columns:
        return {'is_anomaly': False, 'anomaly_months': [], 'pct_anomaly': 0.0}

    rows = predictions[predictions['month'] == sel_month]
    is_anomaly = bool(rows.iloc[0][anom_col]) if len(rows) else False

    anom_months = predictions[predictions[anom_col] == 1]['month'].tolist()
    pct_anomaly = len(anom_months) / len(predictions) * 100 if len(predictions) else 0

    return {
        'is_anomaly':    is_anomaly,
        'anomaly_months': anom_months,
        'pct_anomaly':   pct_anomaly,
        'total_anomaly': len(anom_months),
    }
