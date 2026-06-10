"""
src/utils.py — BaliGuard: Core Constants & Base Helpers
Setelah refactoring, file ini hanya berisi:
- Constants (LABEL_ORDER, FEATURES, THRESHOLD)
- sf() helper
- load_data(), load_models(), load_nav_icons() dengan @st.cache
- get_current_usd_idr() — live USD/IDR fetch
- compute_delta_context() — MoM delta

Logika berat sudah dipindah ke:
  src/services/forecast.py
  src/services/simulation.py
  src/services/llm_service.py
"""
import streamlit as st
from src.config import (
    LABEL_ORDER, FEATURES_CORE, FEATURES_LAG,
    THRESHOLD, DATA_DIR, MODEL_DIR,
)
import pandas as pd
import numpy as np
import requests, json, os
from src.config import LEVEL_COLORS
from pathlib import Path

from src.components.cards import (
    kpi_card,
    alert_card,
)

from src.components.badges import (
    status_dot,
)

import time

_t_start = time.perf_counter()
_t = {}

def _tick(label):
    _t[label] = time.perf_counter() - _t_start

# Compatibility aliases
kpi_html = kpi_card
alert_html = alert_card

# ── Path config ───────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / 'data' / 'final'
MODEL_DIR = BASE_DIR / 'models'



# ── Micro helpers ─────────────────────────────────────────────────────
def sf(val, default: float = 0.0) -> float:
    """Safe float — return default jika None/NaN/error."""
    try:
        v = float(val)
        return default if (v != v) else v
    except Exception:
        return default


def level_from_score(s: float) -> str:
    if s >= THRESHOLD["KRISIS"]:  return 'KRISIS'
    if s >= THRESHOLD["SIAGA"]:   return 'SIAGA'
    if s >= THRESHOLD["WASPADA"]: return 'WASPADA'
    return 'AMAN'


# ── Data loaders (cached) ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> tuple:
    master = pd.read_parquet(DATA_DIR / 'master_dataset_clean.parquet')
    pred   = pd.read_csv(DATA_DIR / 'predictions_final.csv')
    cache  = {}
    p = DATA_DIR / 'narratives_cache.json'
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    return master, pred, cache


@st.cache_resource(show_spinner=False)
def load_models() -> tuple:
    import joblib
    rf     = joblib.load(MODEL_DIR / 'model_random_forest.pkl')
    iso_f  = joblib.load(MODEL_DIR / 'model_isolation_forest.pkl')
    scaler = joblib.load(MODEL_DIR / 'scaler.pkl')
    le     = joblib.load(MODEL_DIR / 'label_encoder.pkl')
    return rf, iso_f, scaler, le


@st.cache_resource(show_spinner=False)
def load_nav_icons() -> dict:
    """Base64 icon dari images/ — dibuat sekali, tidak dibuat ulang setiap rerun."""
    import base64
    # Nama file di images/ folder sesuai struktur project asli
    mapping = {
        'Gambaran Umum & Garis Waktu': BASE_DIR / 'images' / 'overview&timeline.png',
        'Analisis Detail':             BASE_DIR / 'images' / 'analisis_detail.png',
        'Sentimen':                    BASE_DIR / 'images' / 'sentimen.png',
        'Prediksi & Proyeksi':         BASE_DIR / 'images' / 'prediksi&proyeksi.png',
        'Narasi AI':                   BASE_DIR / 'images' / 'narasi_ai.png',
    }
    result = {}
    for label, path in mapping.items():
        if path.exists():
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            result[label] = f'data:image/png;base64,{b64}'
        # Kalau file tidak ada, key tidak dimasukkan
        # → sidebar.py akan pakai emoji fallback (NAV_ICONS_FALLBACK)
    return result


# ── Live USD/IDR ──────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_usd_idr() -> float | None:
    for url in [
        'https://api.exchangerate-api.com/v4/latest/USD',
        'https://open.er-api.com/v6/latest/USD',
    ]:
        try:
            r = requests.get(url, timeout=5)
            return float(r.json()['rates']['IDR'])
        except Exception:
            continue
    return None


def get_current_usd_idr(predictions: pd.DataFrame,
                         month: str) -> tuple[float | None, bool]:
    """Return (rate, is_live). Live jika bulan >= data terakhir."""
    last_m = predictions['month'].max()
    if month >= last_m:
        live = fetch_live_usd_idr()
        if live:
            return live, True
    rows = predictions[predictions['month'] == month]
    if len(rows) and 'usd_idr_avg' in rows.columns:
        return float(rows.iloc[0]['usd_idr_avg']), False
    return None, False


# ── Delta context ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_delta_context(row_data_dict: dict,
                           pred_df: pd.DataFrame,
                           sel_month: str) -> dict:
    """Hitung delta MoM untuk semua KPI utama."""
    months = list(pred_df['month'].values)
    if sel_month not in months:
        return {}
    idx = months.index(sel_month)
    if idx <= 0:
        return {}
    prev = pred_df.iloc[idx - 1].to_dict()
    result = {}
    for key in ['wisman', 'tpk_bintang', 'inflasi_processed', 'usd_idr_avg',
                'avg_sentiment_monthly', 'crisis_score_100', 'bali_share_pct']:
        c, p = sf(row_data_dict.get(key)), sf(prev.get(key))
        result[key] = {
            'curr': c, 'prev': p,
            'delta': c - p,
            'delta_pct': (c - p) / p * 100 if p != 0 else 0,
        }
    return result
