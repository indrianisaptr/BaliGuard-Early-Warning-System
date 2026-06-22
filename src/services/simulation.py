"""
src/services/simulation.py — BaliGuard: Scenario Risk Simulator
"""
import numpy as np
from src.config import THRESHOLD


def simulate_score(row: dict,
                   wisman_delta_pct: float = 0.0,
                   usd_delta_pct:    float = 0.0,
                   sent_delta:       float = 0.0) -> float:
    def sf(x):
        try:
            v = float(x)
            return 0.0 if (v != v) else v
        except Exception:
            return 0.0

    ct = sf(row.get('crisis_component_tourism',   0.4))
    ce = sf(row.get('crisis_component_economy',   0.3))
    cx = sf(row.get('external_risk_score',        0.0))
    cs = sf(row.get('crisis_component_sentiment', 0.25))

    ct2 = float(np.clip(ct - (wisman_delta_pct / 100) * 0.5, 0, 1))
    ce2 = float(np.clip(ce + (usd_delta_pct    / 100) * 0.3, 0, 1))
    cx2 = float(np.clip(cx, 0, 1))
    cs2 = float(np.clip(cs - sent_delta               * 0.2, 0, 1))

    return round(
        (
            0.45 * ct2 +
            0.25 * ce2 +
            0.20 * cx2 +
            0.10 * cs2
        ) * 100,
        1
    )


def level_from_score(s: float) -> str:
    if s >= THRESHOLD['KRISIS']:  return 'KRISIS'
    if s >= THRESHOLD['SIAGA']:   return 'SIAGA'
    if s >= THRESHOLD['WASPADA']: return 'WASPADA'
    return 'AMAN'


def compute_scenario_summary(row: dict,
                              wisman_delta_pct: float,
                              usd_delta_pct:    float,
                              sent_delta:       float) -> dict:
    original_score = float(row.get('crisis_score_100', 30.0))
    original_level = str(row.get('crisis_level', 'AMAN'))
    new_score      = simulate_score(row, wisman_delta_pct, usd_delta_pct, sent_delta)
    new_level      = level_from_score(new_score)
    return {
        'original_score': original_score,
        'original_level': original_level,
        'new_score':      new_score,
        'new_level':      new_level,
        'delta':          new_score - original_score,
        'level_changed':  new_level != original_level,
    }