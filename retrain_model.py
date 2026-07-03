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

import warnings, os, json
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
DATA_PRO = BASE / 'data' / 'processed'
DATA_FIN = BASE / 'data' / 'final'
MDL_DIR  = BASE / 'models'
MDL_DIR.mkdir(parents=True, exist_ok=True)

# ── Model config — IDENTIK dengan NB05 Cell[12] ──────────────
# AUDIT FINDING A (diperbaiki): FEATURES_LAG versi lama
# (wisman_lag_1/3, wisman_recovery_pct) adalah nama kolom deprecated —
# NB05 sendiri sudah punya komentar "DIPERBAIKI: ... bukan
# wisman_lag_1/3". Daftar di bawah disamakan persis dengan NB05 Cell[12]
# / update_pipeline.py.
FEATURES_CORE = [
    'wisman_growth_mom', 'wisman_growth_yoy', 'wisman_zscore',
    'usd_idr_avg', 'usd_volatility_3m', 'usd_change_mom',
    'tpk_bintang', 'tpk_change_mom',
    'inflasi_processed', 'bali_share_pct',
    'avg_sentiment_monthly',
    'month_num', 'is_peak_season',
]

FEATURES_LAG = [
    'wisman_ma3',
    'wisman_trend_3m',
    'bali_share_change',
    'sentiment_trend_3m',
]

# Kandidat fitur eksternal — sama seperti NB05 Cell[12] FEATURES_EXTERNAL
# / update_pipeline.py FEATURES_EXTERNAL_CANDIDATES. Di notebook, 6 dari
# 8 kandidat ini bentrok nama dengan kolom yang sudah ada di
# master_dataset_clean.parquet sehingga berubah jadi _x/_y saat merge
# dan gagal lolos filter `f in df.columns` — hanya 2 nama unik yang
# lolos: gdelt_crisis_score_zscore & disaster_risk_score_zscore.
FEATURES_EXTERNAL_CANDIDATES = [
    'gdelt_crisis_score',
    'economic_risk_score',
    'disaster_risk_score',
    'external_risk_avg',
    'external_risk_max',
    'external_risk_range',
    'gdelt_crisis_score_zscore',
    'disaster_risk_score_zscore',
]

# Kolom yang direconcile balik ke nama master di merge_external_features()
# — bukan fitur CSV eksternal yang unik, jadi tidak boleh ikut FEATURES.
_EXTERNAL_RECONCILED_ALIASES = [
    'gdelt_crisis_score', 'economic_risk_score', 'disaster_risk_score',
    'external_risk_avg', 'external_risk_max', 'external_risk_range',
]

EXTERNAL_FEATURES_PATH = DATA_PRO / 'combined_additional_features_engineered_new.csv'


def load_external_features() -> pd.DataFrame:
    """
    Baca & pra-proses combined_additional_features_engineered_new.csv.
    IDENTIK dengan NB05 Cell[4] / update_pipeline.py::load_external_features().
    """
    if not EXTERNAL_FEATURES_PATH.exists():
        print(f"  ⚠  {EXTERNAL_FEATURES_PATH.name} tidak ditemukan — fitur "
              f"eksternal CSV dilewati (gdelt_crisis_score_zscore & "
              f"disaster_risk_score_zscore TIDAK akan tersedia).")
        return pd.DataFrame(columns=['month'])

    df_ext = pd.read_csv(EXTERNAL_FEATURES_PATH)
    df_ext['month'] = pd.to_datetime(df_ext['date']).dt.to_period('M').astype(str)
    df_ext = df_ext.drop(columns=['date'])
    df_ext = df_ext.groupby('month').mean(numeric_only=True).reset_index()
    print(f"  ✓ External features CSV: {len(df_ext)} bulan "
          f"({df_ext['month'].min()} → {df_ext['month'].max()})")
    return df_ext


def merge_external_features(df: pd.DataFrame, df_ext: pd.DataFrame) -> pd.DataFrame:
    """
    Merge left df_ext ke df utama — IDENTIK dengan NB05 Cell[4] /
    update_pipeline.py::merge_external_features(). Kolom yang bentrok
    nama dengan master (sudah ada dari NB04) di-reconcile: versi master
    (_x) dipertahankan dengan nama semula, versi CSV (_y) dibuang.
    """
    if df_ext.empty or list(df_ext.columns) == ['month']:
        return df

    df = df.copy()
    df['month'] = df['month'].astype(str)

    n_before = len(df)
    df = df.merge(df_ext, on='month', how='left')
    assert len(df) == n_before, (
        "Merge left mengubah jumlah baris master — cek duplikasi 'month' di df_ext"
    )

    ext_cols = [c for c in df_ext.columns if c != 'month' and c in df.columns]
    if ext_cols:
        n_na = df[ext_cols].isna().sum().sum()
        df[ext_cols] = df[ext_cols].fillna(0)
        print(f"  ✓ External features merged: {ext_cols}")
        print(f"  ✓ fillna(0) pada external features: {int(n_na)} NaN diisi 0")

    overlap_cols = [c for c in df_ext.columns
                    if c != 'month' and f'{c}_x' in df.columns and f'{c}_y' in df.columns]
    for c in overlap_cols:
        df[c] = df[f'{c}_x']
        df.drop(columns=[f'{c}_x', f'{c}_y'], inplace=True)
    if overlap_cols:
        print(f"  ℹ  Kolom bentrok dgn master (nilai master dipertahankan): {overlap_cols}")

    return df


def build_features_list(df_columns) -> list:
    """
    Bangun daftar FEATURES final — replikasi NB05 Cell[12]:
    FEATURES_CORE + FEATURES_LAG + FEATURES_EXTERNAL, difilter hanya
    yang benar-benar ada di df, urutan dipertahankan.
    """
    cols = set(df_columns)
    features_external = [
        f for f in FEATURES_EXTERNAL_CANDIDATES
        if f in cols and f not in _EXTERNAL_RECONCILED_ALIASES
    ]
    return [f for f in FEATURES_CORE + FEATURES_LAG + features_external if f in cols]


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


# Kolom lag/rolling yang wajar NaN di awal periode — IDENTIK dengan
# NB05 Cell[10] fill_zero_cols.
FILL_ZERO_COLS = [
    'wisman_growth_yoy', 'wisman_ma3', 'wisman_trend_3m',
    'sentiment_trend_3m', 'usd_volatility_3m', 'bali_share_change',
    'wisman_growth_mom', 'usd_change_mom', 'tpk_change_mom',
]


def impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    IDENTIK dengan NB05 Cell[10]: fill_zero_cols → 0, lalu comprehensive
    ffill → bfill → median untuk SEMUA kolom numerik (sebelum feature
    selection / dropna), supaya baris awal/akhir tidak hilang.
    """
    df = df.copy()
    for col in FILL_ZERO_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    nan_before = df[numeric_cols].isnull().sum().sum()
    df[numeric_cols] = df[numeric_cols].ffill()
    df[numeric_cols] = df[numeric_cols].bfill()
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    nan_after = df[numeric_cols].isnull().sum().sum()
    print(f"  ✓ Imputation: {nan_before} NaN → {nan_after} NaN (ffill→bfill→median)")

    return df


def prepare_model_data(df: pd.DataFrame):
    """
    Subset data dengan fitur lengkap — urutan operasi IDENTIK dengan
    NB05 Cell[13] (dropna TARGET) → Cell[14] (clip quantile 1-99%) →
    Cell[16] (replace inf→nan→median, lalu scaling di caller).
    df yang masuk ke sini HARUS sudah melalui impute_missing() +
    merge_external_features() (lihat run_retrain()).
    """
    feat_cols = build_features_list(df.columns)

    missing_core = [f for f in FEATURES_CORE if f not in df.columns]
    if missing_core:
        print(f"  ⚠  Core features tidak tersedia: {missing_core}")
    available_lag = [f for f in FEATURES_LAG if f in df.columns]
    if available_lag:
        print(f"  ✓ Lag features aktif: {available_lag}")
    available_ext = [f for f in feat_cols if f in FEATURES_EXTERNAL_CANDIDATES]
    if available_ext:
        print(f"  ✓ External features aktif: {available_ext}")

    # Cell[13]: hanya drop baris yang TARGET-nya NaN (NaN fitur sudah
    # diimputasi di impute_missing())
    df_model = df.dropna(subset=[TARGET]).copy().reset_index(drop=True)
    df_model = df_model[feat_cols + [TARGET, 'month']].copy()

    # Cell[14]: clip quantile 1%-99% per fitur (mencegah recovery COVID
    # mendominasi model secara tidak proporsional)
    df_model[feat_cols] = df_model[feat_cols].clip(
        lower=df_model[feat_cols].quantile(0.01),
        upper=df_model[feat_cols].quantile(0.99),
        axis=1
    )

    # Cell[16]: ganti inf → NaN, lalu isi dengan median kolom
    df_model[feat_cols] = df_model[feat_cols].replace([np.inf, -np.inf], np.nan)
    df_model[feat_cols] = df_model[feat_cols].fillna(df_model[feat_cols].median())

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
    Hyperparameter IDENTIK dengan NB05 Cell[18] (per konfirmasi user —
    disamakan, bukan dibiarkan berbeda by design).
    """
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.15,
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
    Hyperparameter IDENTIK dengan NB05 Cell[26] (per konfirmasi user).
    TimeSeriesSplit untuk validasi (tidak random shuffle) tetap
    dipertahankan sebagai tambahan CV di retrain_model.py (NB05 pakai
    walk-forward CV custom di Cell[24], tapi model FINAL yang disimpan
    NB05 tetap dilatih pada seluruh data — sama seperti di sini).
    """
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=3,
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
    # AUDIT FINDING D (diperbaiki): iso_score sebelumnya tidak pernah
    # dihitung. Dipakai iso.decision_function() — konsisten dengan
    # update_pipeline.py::run_model_predictions() (bukan
    # iso.score_samples() seperti NB05 Cell[18]; keduanya BUKAN nilai
    # identik di scikit-learn — lihat Temuan G di laporan audit).
    df_model['iso_score']          = iso.decision_function(X_scaled)
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
    pred_cols = ['month', 'iso_anomaly', 'iso_score', 'rf_predicted_level',
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
    df_out['iso_score']      = df_out.get('iso_score', 0.0).fillna(0.0)

    return df_out


def save_outputs(df: pd.DataFrame, scaler, iso, rf, le, feat_cols):
    """Simpan model dan predictions."""

    # Models
    joblib.dump(scaler, MDL_DIR / 'scaler.pkl')
    joblib.dump(iso,    MDL_DIR / 'model_isolation_forest.pkl')
    joblib.dump(rf,     MDL_DIR / 'model_random_forest.pkl')
    joblib.dump(le,     MDL_DIR / 'label_encoder.pkl')
    print(f"\n  ✓ Models saved → {MDL_DIR}/")

    # Write latest trained model metadata (version + training timestamp)
    # supaya update_pipeline.py bisa membacanya saat mengisi kolom
    # model_version/training_date di Supabase pipeline_metadata.
    training_dt = datetime.now()
    with open(MDL_DIR / 'model_metadata.json', 'w') as f:
        json.dump({
            "model_version": training_dt.strftime('rf_%Y-%m-%d_%H%M%S'),
            "training_date": training_dt.isoformat(),
        }, f)

    # Predictions CSV — skema IDENTIK dengan PREDICTION_OUTPUT_COLUMNS
    # di update_pipeline.py (31 kolom, single source of truth untuk CSV
    # & Supabase). AUDIT FINDING E/F (diperbaiki): sebelumnya memakai
    # daftar kolom lama dengan crisis_component_* yang tidak ada di
    # skema resmi, dan kehilangan iso_score/wisman_recovery_pct/
    # pct_negative_monthly/usd_volatility_3m yang seharusnya ada.
    pred_cols = [
        'month', 'wisman', 'tpk_bintang', 'inflasi_processed',
        'usd_idr_avg', 'avg_sentiment_monthly', 'bali_share_pct',
        'wisman_zscore', 'wisman_growth_mom', 'wisman_growth_yoy',
        'crisis_score_100', 'crisis_level',
        'rf_predicted_level', 'rf_confidence',
        'prob_aman', 'prob_waspada', 'prob_siaga', 'prob_krisis',
        'iso_anomaly', 'iso_score',
        'gdelt_crisis_score', 'economic_risk_score', 'disaster_risk_score',
        'external_risk_avg', 'physical_risk_score', 'media_risk_score',
        'tourist_perception_score', 'external_risk_score',
        'wisman_recovery_pct', 'pct_negative_monthly', 'usd_volatility_3m',
    ]
    pred_cols_avail = [c for c in pred_cols if c in df.columns]
    missing_pred_cols = [c for c in pred_cols if c not in df.columns]
    if missing_pred_cols:
        print(f"  ⚠  Kolom PREDICTION_OUTPUT_COLUMNS tidak tersedia di df: {missing_pred_cols}")
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

    # ── Merge external CSV features — IDENTIK NB05 Cell[4] (audit finding B) ──
    print("\n  Merging external features (CSV)...")
    df = merge_external_features(df, load_external_features())

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

    # ── Comprehensive imputation — IDENTIK NB05 Cell[10] (audit finding C) ──
    print("\n  Imputing missing values (ffill→bfill→median)...")
    df = impute_missing(df)

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
