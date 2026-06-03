"""
retrain_model.py — BaliGuard Model Retraining Script
=====================================================
Jalankan setelah update_pipeline.py, atau kapanpun data signifikan bertambah:

    python retrain_model.py

Apa yang dilakukan:
  1. Load master_dataset_clean.parquet (hasil update_pipeline.py)
  2. Rebuild scaler pada seluruh data terbaru
  3. Retrain Isolation Forest (anomaly detection)
  4. Retrain Random Forest (crisis classification)
  5. Simpan model baru (menimpa yang lama)
  6. Regenerate predictions_final.csv
  7. Tampilkan evaluation metrics
"""

import warnings, os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════
# THRESHOLD KRISIS — satu-satunya tempat yang perlu diubah
# kalau range crisis_score berubah lagi di masa depan.
# Berlaku untuk: relabeling CSV/parquet + dashboard level_from_score
# ══════════════════════════════════════════════════════════════
THRESHOLD_KRISIS  = 60   # score >= 60  → KRISIS
THRESHOLD_SIAGA   = 45   # score >= 45  → SIAGA
THRESHOLD_WASPADA = 30   # score >= 30  → WASPADA
                          # score <  30  → AMAN

def level_from_score(s: float) -> str:
    """Konversi crisis_score_100 → level string. Konsisten dengan NB04."""
    if s >= THRESHOLD_KRISIS:  return 'KRISIS'
    if s >= THRESHOLD_SIAGA:   return 'SIAGA'
    if s >= THRESHOLD_WASPADA: return 'WASPADA'
    return 'AMAN'

# ── Path config ──────────────────────────────────────────────
BASE     = Path(__file__).parent
DATA_FIN = BASE / 'data' / 'final'
MDL_DIR  = BASE / 'models'
MDL_DIR.mkdir(parents=True, exist_ok=True)

# ── Model config (sama dengan notebook 05) ──────────────────
FEATURES_CORE = [
    'wisman_growth_mom', 'wisman_growth_yoy', 'wisman_zscore',
    'usd_idr_avg', 'usd_volatility_3m', 'usd_change_mom',
    'tpk_bintang', 'tpk_change_mom',
    'inflasi_processed', 'bali_share_pct',
    'avg_sentiment_monthly',
    'month_num', 'is_peak_season',
]

# Lag features dari NB04 cell 10 — gunakan jika tersedia di parquet
# (jika NB04 FINAL sudah dijalankan → lag features ada; jika belum → skip gracefully)
FEATURES_LAG = [
    'wisman_lag_1',       # wisman 1 bulan lalu (delayed effect)
    'wisman_lag_3',       # wisman 3 bulan lalu
    'wisman_trend_3m',    # arah tren 3 bulan
    'wisman_recovery_pct',# recovery vs baseline 2017-2019
]

# FEATURES akan di-resolve saat runtime (graceful fallback jika lag belum ada)
FEATURES = FEATURES_CORE  # placeholder; di-update di prepare_model_data()


def load_data() -> pd.DataFrame:
    path = DATA_FIN / 'master_dataset_clean.parquet'
    if not path.exists():
        raise FileNotFoundError(
            "master_dataset_clean.parquet tidak ditemukan.\n"
            "Jalankan update_pipeline.py terlebih dahulu."
        )
    df = pd.read_parquet(path)
    df['month'] = df['month'].astype(str).str[:7]
    print(f"✓ Dataset loaded: {len(df)} baris, {df['month'].min()} → {df['month'].max()}")
    return df


TARGET      = 'crisis_level'
LABEL_ORDER = ['AMAN', 'WASPADA', 'SIAGA', 'KRISIS']   # ✓ severity order: 0→3


def prepare_model_data(df: pd.DataFrame):
    """Subset data dengan fitur lengkap. Lag features digunakan jika tersedia."""
    # Resolve fitur final: core + lag jika tersedia
    available_lag = [f for f in FEATURES_LAG if f in df.columns]
    feat_cols     = FEATURES_CORE + available_lag
    feat_cols     = [f for f in feat_cols if f in df.columns]

    missing_core = [f for f in FEATURES_CORE if f not in df.columns]
    if missing_core:
        print(f"  ⚠  Core features tidak tersedia: {missing_core}")
    if available_lag:
        print(f"  ✓ Lag features aktif: {available_lag}")
    else:
        print(f"  Lag features tidak ditemukan — jalankan NB04 FINAL untuk mengaktifkan")

    df_model = df[feat_cols + [TARGET, 'month']].copy()

    # Ganti inf/-inf → NaN, lalu isi dengan median kolom
    df_model[feat_cols] = df_model[feat_cols].replace([np.inf, -np.inf], np.nan)
    for col in feat_cols:
        med = df_model[col].median()
        df_model[col] = df_model[col].fillna(med if not np.isnan(med) else 0)

    # Clip outlier ekstrem (±10 std) supaya scaler tidak meledak
    for col in feat_cols:
        std = df_model[col].std()
        mn  = df_model[col].mean()
        if std > 0:
            df_model[col] = df_model[col].clip(mn - 10*std, mn + 10*std)

    # Drop baris yang masih NaN di TARGET saja
    df_model = df_model.dropna(subset=[TARGET])

    # Sanity check
    n_inf = np.isinf(df_model[feat_cols].values).sum()
    n_nan = np.isnan(df_model[feat_cols].values).sum()
    if n_inf + n_nan > 0:
        print(f"  ⚠  Masih ada {n_inf} inf / {n_nan} NaN — kolom bermasalah:")
        for col in feat_cols:
            bad = np.isinf(df_model[col]).sum() + df_model[col].isna().sum()
            if bad: print(f"       {col}: {bad}")
    else:
        print(f"  ✓ Data bersih — tidak ada inf/NaN")

    print(f"  Baris: {len(df_model)} (dari {len(df)})")
    print(f"  Fitur: {len(feat_cols)} | Distribusi: {df_model[TARGET].value_counts().to_dict()}")

    return df_model, feat_cols


def train_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(X)
    return scaler


def train_isolation_forest(X_scaled: np.ndarray) -> IsolationForest:
    """
    Isolation Forest — deteksi anomali tanpa label.
    Contamination ~5% (proporsi anomali yang diharapkan).
    """
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_features=1.0,
        bootstrap=False,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_scaled)
    n_anom = (iso.predict(X_scaled) == -1).sum()
    print(f"  ✓ Isolation Forest: {n_anom} anomali terdeteksi ({n_anom/len(X_scaled)*100:.1f}%)")
    return iso


def train_random_forest(X_scaled: np.ndarray, y: np.ndarray,
                        le: LabelEncoder) -> RandomForestClassifier:
    """
    Random Forest — klasifikasi krisis.
    TimeSeriesSplit untuk validasi (tidak random shuffle).
    """
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation dengan TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=5)
    try:
        cv_scores = cross_val_score(rf, X_scaled, y, cv=tscv,
                                    scoring='accuracy', n_jobs=-1)
        print(f"  CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    except Exception as e:
        print(f"  ⚠  CV gagal: {e}")

    # Train pada seluruh data
    rf.fit(X_scaled, y)

    # Training metrics
    y_pred = rf.predict(X_scaled)
    # ✓ FIX: pakai label yang benar-benar ada di y
    # Menghindari ValueError "Number of classes X does not match target_names Y"
    # ketika kelas tertentu belum muncul (misal KRISIS sebelum NB04 baru dijalankan)
    present_labels = [LABEL_ORDER[i] for i in sorted(np.unique(y))]
    print(f"\n  Classification Report (train set) — kelas aktif: {present_labels}")
    print(classification_report(
        le.inverse_transform(y),
        le.inverse_transform(y_pred),
        labels=present_labels,
        zero_division=0
    ))

    # Feature importance
    feat_imp = pd.Series(rf.feature_importances_).sort_values(ascending=False)
    print("   Top 5 Feature Importance:")
    # (akan di-print dengan nama kolom di caller)

    return rf


def generate_predictions(df: pd.DataFrame, df_model: pd.DataFrame,
                          feat_cols: list, scaler: StandardScaler,
                          iso: IsolationForest, rf: RandomForestClassifier,
                          le: LabelEncoder) -> pd.DataFrame:
    """Generate predictions untuk seluruh dataset."""
    X = df_model[feat_cols].values
    X_scaled = scaler.transform(X)

    iso_pred = iso.predict(X_scaled)
    rf_pred  = rf.predict(X_scaled)
    rf_proba = rf.predict_proba(X_scaled)

    df_model = df_model.copy()
    df_model['iso_anomaly']        = (iso_pred == -1).astype(int)
    df_model['rf_predicted_level'] = le.inverse_transform(rf_pred)
    df_model['rf_confidence']      = rf_proba.max(axis=1)

    # ✓ FIX: pakai rf.classes_ (kelas yang benar-benar diketahui model)
    # bukan le.classes_ — kalau KRISIS hilang dari data training,
    # le.classes_ tetap 4 entry tapi rf_proba hanya 3 kolom → IndexError
    rf_classes = list(le.inverse_transform(rf.classes_))
    for cls in ['KRISIS', 'SIAGA', 'WASPADA', 'AMAN']:
        col = f'prob_{cls.lower()}'
        if cls in rf_classes:
            idx = rf_classes.index(cls)
            df_model[col] = rf_proba[:, idx]
        else:
            df_model[col] = 0.0

    # Merge predictions ke df utama
    pred_cols = ['month', 'iso_anomaly', 'rf_predicted_level',
                 'rf_confidence', 'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman']

    df_out = df.merge(df_model[pred_cols], on='month', how='left',
                      suffixes=('_old', ''))

    # Drop old columns jika ada
    for col in pred_cols[1:]:
        old = col + '_old'
        if old in df_out.columns:
            df_out.drop(columns=[old], inplace=True)

    # Fallback untuk baris tanpa prediksi
    df_out['rf_predicted_level'] = df_out.get('rf_predicted_level',
        df_out['crisis_level']).fillna(df_out['crisis_level'])
    df_out['rf_confidence']  = df_out.get('rf_confidence', 0.7).fillna(0.7)
    df_out['iso_anomaly']    = df_out.get('iso_anomaly', 0).fillna(0).astype(int)

    return df_out


def save_outputs(df: pd.DataFrame, scaler, iso, rf, le, feat_cols):
    """Simpan model dan predictions."""
    # # ── Re-apply threshold sebelum simpan (aman kalau dipanggil standalone) ──
    # if 'crisis_score_100' in df.columns:
    #     df['crisis_level'] = df['crisis_score_100'].apply(level_from_score)

    # Models
    joblib.dump(scaler, MDL_DIR / 'scaler.pkl')
    joblib.dump(iso,    MDL_DIR / 'model_isolation_forest.pkl')
    joblib.dump(rf,     MDL_DIR / 'model_random_forest.pkl')
    joblib.dump(le,     MDL_DIR / 'label_encoder.pkl')
    print(f"\n  ✓ Models saved → {MDL_DIR}/")

    # Predictions CSV — sertakan wisman_growth jika ada
    pred_cols = [
        'month', 'wisman', 'tpk_bintang', 'inflasi_processed',
        'usd_idr_avg', 'avg_sentiment_monthly', 'bali_share_pct',
        'wisman_zscore', 'wisman_growth_mom', 'wisman_growth_yoy',
        'crisis_score_100', 'crisis_level',
        'rf_predicted_level', 'rf_confidence', 'iso_anomaly',
        'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman',
        'crisis_component_tourism', 'crisis_component_economy', 'crisis_component_sentiment',
    ]
    pred_cols_avail = [c for c in pred_cols if c in df.columns]
    pred_path = DATA_FIN / 'predictions_final.csv'
    df[pred_cols_avail].to_csv(pred_path, index=False)
    print(f"  ✓ predictions_final.csv ({len(df)} baris, {len(pred_cols_avail)} kolom)")

    # Master parquet
    df.to_parquet(DATA_FIN / 'master_dataset_clean.parquet', index=False)
    print(f"  ✓ master_dataset_clean.parquet updated")

    # Feature importance log
    fi = pd.Series(rf.feature_importances_, index=feat_cols).sort_values(ascending=False)
    fi.to_csv(MDL_DIR / 'feature_importance.csv')
    print(f"\n  Top 5 features:")
    for name, val in fi.head(5).items():
        print(f"     {name:35s} {val:.4f}")


def run_retrain(verbose: bool = True):
    print("\n" + "═" * 60)
    print("  BaliGuard — Model Retraining")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

def save_outputs(df: pd.DataFrame, scaler, iso, rf, le, feat_cols):
    """Simpan model dan predictions."""

    # Models
    joblib.dump(scaler, MDL_DIR / 'scaler.pkl')
    joblib.dump(iso,    MDL_DIR / 'model_isolation_forest.pkl')
    joblib.dump(rf,     MDL_DIR / 'model_random_forest.pkl')
    joblib.dump(le,     MDL_DIR / 'label_encoder.pkl')
    print(f"\n  ✓ Models saved → {MDL_DIR}/")

    # Predictions CSV — sertakan wisman_growth jika ada
    pred_cols = [
        'month', 'wisman', 'tpk_bintang', 'inflasi_processed',
        'usd_idr_avg', 'avg_sentiment_monthly', 'bali_share_pct',
        'wisman_zscore', 'wisman_growth_mom', 'wisman_growth_yoy',
        'crisis_score_100', 'crisis_level',
        'rf_predicted_level', 'rf_confidence', 'iso_anomaly',
        'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman',
        'crisis_component_tourism', 'crisis_component_economy', 'crisis_component_sentiment',
    ]
    pred_cols_avail = [c for c in pred_cols if c in df.columns]
    pred_path = DATA_FIN / 'predictions_final.csv'
    df[pred_cols_avail].to_csv(pred_path, index=False)
    print(f"  ✓ predictions_final.csv ({len(df)} baris, {len(pred_cols_avail)} kolom)")

    # Master parquet
    df.to_parquet(DATA_FIN / 'master_dataset_clean.parquet', index=False)
    print(f"  ✓ master_dataset_clean.parquet updated")

    # Feature importance log
    fi = pd.Series(rf.feature_importances_, index=feat_cols).sort_values(ascending=False)
    fi.to_csv(MDL_DIR / 'feature_importance.csv')
    print(f"\n  Top 5 features:")
    for name, val in fi.head(5).items():
        print(f"     {name:35s} {val:.4f}")


def run_retrain(verbose: bool = True):
    print("\n" + "═" * 60)
    print("  BaliGuard — Model Retraining")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # Load
    print("\n[1/5] Loading data...")
    df = load_data()

    # ── Gunakan label dari master dataset ──
    print("\n  Menggunakan crisis_level dari master dataset...")
    print(f"  Distribusi existing: {df['crisis_level'].value_counts().to_dict()}")

    # ── Pastikan wisman_growth_mom & yoy ada di df ─────────
    for col in ['wisman_growth_mom', 'wisman_growth_yoy']:
        if col not in df.columns:
            print(f"  ⚠  '{col}' tidak ditemukan — menghitung ulang dari wisman...")
            df = df.sort_values('month').reset_index(drop=True)
            if col == 'wisman_growth_mom':
                df[col] = df['wisman'].pct_change(1)
            else:
                df[col] = df['wisman'].pct_change(12)
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            print(f"  ✓ '{col}' berhasil ditambahkan")

    # Prepare
    print("\n[2/5] Preparing model data...")
    df_model, feat_cols = prepare_model_data(df)

    X = df_model[feat_cols].values
    y_raw = df_model[TARGET].values

    # Label encoding
    le = LabelEncoder()
    # ✓ FIX: set classes_ langsung — le.fit() akan sort alphabetical (AMAN,KRISIS,SIAGA,WASPADA)
    # padahal kita butuh severity order: AMAN=0, WASPADA=1, SIAGA=2, KRISIS=3
    le.classes_ = np.array(LABEL_ORDER)
    y = le.transform(y_raw)

    # Train scaler
    print("\n[3/5] Training scaler + Isolation Forest...")
    scaler   = train_scaler(X)
    X_scaled = scaler.transform(X)
    iso      = train_isolation_forest(X_scaled)

    # Train RF
    print("\n[4/5] Training Random Forest...")
    rf = train_random_forest(X_scaled, y, le)

    # Generate predictions
    print("\n[5/5] Generating predictions...")
    df_out = generate_predictions(df, df_model, feat_cols, scaler, iso, rf, le)

    # Save
    print("\n Saving outputs...")
    save_outputs(df_out, scaler, iso, rf, le, feat_cols)

    # Summary
    latest = df_out.iloc[-1]
    print("\n" + "═" * 60)
    print("  Retraining selesai!")
    print(f" Bulan terbaru  : {latest['month']}")
    print(f" Crisis Score   : {latest.get('crisis_score_100', 0):.1f}/100")
    print(f" Level          : {latest.get('crisis_level', 'N/A')}")
    print(f" RF Pred        : {latest.get('rf_predicted_level', 'N/A')} "
          f"(conf {latest.get('rf_confidence', 0)*100:.0f}%)")
    print("═" * 60 + "\n")

    return df_out


if __name__ == '__main__':
    run_retrain()
