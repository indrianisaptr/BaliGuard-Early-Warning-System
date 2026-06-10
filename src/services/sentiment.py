"""
src/services/sentiment.py — BaliGuard: Sentiment Analysis Helpers
"""
import pandas as pd
import numpy as np


def get_sentiment_summary(predictions: pd.DataFrame) -> dict:
    """Ringkasan statistik sentimen dari seluruh dataset."""
    col = 'avg_sentiment_monthly'
    if col not in predictions.columns:
        return {}
    s = predictions[col].dropna()
    return {
        'mean':       float(s.mean()),
        'std':        float(s.std()),
        'min':        float(s.min()),
        'max':        float(s.max()),
        'pct_positive': (s > 0).mean() * 100,
        'pct_negative': (s < 0).mean() * 100,
        'trend_3m':    float(s.tail(3).mean() - s.tail(6).head(3).mean()),
    }


def classify_sentiment(score: float) -> tuple[str, str]:
    """Return (label, color) untuk satu nilai sentimen."""
    if score > 0.3:  return 'Sangat Positif', '#22c55e'
    if score > 0:    return 'Positif',         '#86efac'
    if score > -0.3: return 'Negatif',         '#fca5a5'
    return 'Sangat Negatif', '#ef4444'


def compute_sentiment_correlation(predictions: pd.DataFrame) -> float:
    """Korelasi Pearson antara sentimen dan crisis_score_100."""
    cols = ['avg_sentiment_monthly', 'crisis_score_100']
    df = predictions[cols].dropna()
    if len(df) < 5:
        return 0.0
    return float(df.corr().iloc[0, 1])
