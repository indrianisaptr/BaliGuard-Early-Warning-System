"""
update_pipeline.py — BaliGuard Semi-Automatic Monthly Update Pipeline
======================================================================
Jalankan tiap bulan setelah data BPS baru tersedia:

    python update_pipeline.py

Apa yang dilakukan:
  1. Fetch USD/IDR terbaru dari API live (Frankfurter / Open ER)
  2. Load data existing dari data/processed/
  3. Append baris bulan baru (jika ada data BPS baru)
  4. Rebuild semua fitur (growth, zscore, rolling, lag, dll)
  5. Hitung ulang crisis_score
  6. Jalankan model (Isolation Forest + Random Forest)
  7. Simpan predictions_final.csv + master_dataset_clean.parquet terbaru

Untuk data BPS (wisman, TPK, inflasi):
  - Letakkan file update di data/raw/updates/
  - Format: CSV dengan kolom [month, value]
  - Contoh: data/raw/updates/wisman_update.csv
"""

import os, sys, json, warnings, urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings('ignore')

# ── Path config ──────────────────────────────────────────────
BASE     = Path(__file__).parent
DATA_RAW = BASE / 'data' / 'raw'
DATA_PRO = BASE / 'data' / 'processed'
DATA_FIN = BASE / 'data' / 'final'
MDL_DIR  = BASE / 'data' / 'models'

for d in [DATA_RAW / 'updates', DATA_PRO, DATA_FIN, MDL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Crisis score weights (HARUS sama persis dengan NB04 FINAL) ──
# NB04 cell 16: 0.45 tourism · 0.30 economy · 0.25 sentiment
W_TOURISM   = 0.45
W_ECONOMY   = 0.30
W_SENTIMENT = 0.25

# ── Level thresholds (HARUS sama persis dengan NB04 FINAL) ──
# NB04: >= 70 KRISIS · >= 50 SIAGA · >= 30 WASPADA
def level_from_score(s: float) -> str:
    if s >= 70: return 'KRISIS'
    if s >= 50: return 'SIAGA'
    if s >= 30: return 'WASPADA'
    return 'AMAN'


# ════════════════════════════════════════════════════════════
# 1. FETCH LIVE USD/IDR
# ════════════════════════════════════════════════════════════

def fetch_usd_idr_monthly(start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Ambil data kurs USD/IDR dari API live.
    Fallback: Frankfurter → Open ER → file cache lokal.

    Returns DataFrame: [month (str YYYY-MM), usd_idr_avg (float)]
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"  📡 Fetching USD/IDR: {start_date} → {end_date}")

    # ── Option 1: Frankfurter (gratis, no key) ────────────────
    try:
        url = (f"https://api.frankfurter.app/{start_date}..{end_date}"
               f"?from=USD&to=IDR")
        req  = urllib.request.Request(url, headers={"User-Agent": "BaliGuard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        rows = [
            {'date': pd.to_datetime(d), 'usd_idr': float(v['IDR'])}
            for d, v in data['rates'].items()
        ]
        df = pd.DataFrame(rows)
        df['month'] = df['date'].dt.to_period('M').astype(str)
        result = df.groupby('month')['usd_idr'].mean().reset_index()
        result.columns = ['month', 'usd_idr_avg']
        print(f"  ✅ Frankfurter: {len(result)} bulan")
        return result
    except Exception as e:
        print(f"  ⚠️  Frankfurter gagal: {e}")

    # ── Option 2: Open Exchange Rates (free tier, no key) ─────
    try:
        # Open ER API free: hanya latest, tapi kita bisa iterasi per bulan
        url  = "https://open.er-api.com/v6/latest/USD"
        req  = urllib.request.Request(url, headers={"User-Agent": "BaliGuard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        rate = float(data['rates']['IDR'])
        now_m = datetime.now().strftime('%Y-%m')
        result = pd.DataFrame([{'month': now_m, 'usd_idr_avg': rate}])
        print(f"  ✅ Open ER (latest only): {rate:,.0f}")
        return result
    except Exception as e:
        print(f"  ⚠️  Open ER gagal: {e}")

    # ── Fallback: cache lokal ─────────────────────────────────
    cache_path = DATA_PRO / 'usd_idr_cache.csv'
    if cache_path.exists():
        print(f"  ⚠️  Menggunakan cache lokal: {cache_path}")
        return pd.read_csv(cache_path)

    print("  ❌ Semua sumber USD/IDR gagal. Skip update kurs.")
    return pd.DataFrame(columns=['month', 'usd_idr_avg'])


def update_usd_idr() -> pd.DataFrame:
    """Load existing USD data, fetch terbaru, append, simpan."""
    usd_path = DATA_PRO / 'monthly_usd.csv'

    if usd_path.exists():
        existing = pd.read_csv(usd_path)
        existing['month'] = existing['month'].astype(str).str[:7]   # YYYY-MM
        last_month = existing['month'].max()
        # Mulai fetch dari bulan setelah data terakhir
        next_start = (pd.Period(last_month, freq='M') + 1).strftime('%Y-%m-01')
    else:
        existing   = pd.DataFrame(columns=['month', 'usd_idr_avg'])
        next_start = '2009-01-01'

    today    = datetime.now()
    end_date = f"{today.year}-{today.month:02d}-{today.day:02d}"

    if next_start[:7] > end_date[:7]:
        print("  ℹ️  USD/IDR sudah up-to-date.")
        return existing

    new_data = fetch_usd_idr_monthly(next_start, end_date)

    if new_data.empty:
        return existing

    combined = pd.concat([existing, new_data], ignore_index=True)
    combined = combined.drop_duplicates(subset='month', keep='last')
    combined = combined.sort_values('month').reset_index(drop=True)

    # Simpan cache dan file utama
    combined.to_csv(usd_path, index=False)
    combined.to_csv(DATA_PRO / 'usd_idr_cache.csv', index=False)
    print(f"  ✅ USD/IDR updated: {len(combined)} bulan, terakhir {combined['month'].max()}")
    return combined


# ════════════════════════════════════════════════════════════
# 2. LOAD & APPEND DATA BPS (MANUAL UPDATE)
# ════════════════════════════════════════════════════════════

def load_bps_updates():
    """
    Cek folder data/raw/updates/ untuk file update BPS.
    Format tiap file:
      - wisman_update.csv    : month (YYYY-MM), wisman
      - tpk_update.csv       : month (YYYY-MM), tpk_bintang
      - inflasi_update.csv   : month (YYYY-MM), inflasi_processed
      - sentimen_update.csv  : month (YYYY-MM), avg_sentiment_monthly
    """
    updates = {}
    update_dir = DATA_RAW / 'updates'

    for fname, col in [
        ('wisman_update.csv',   'wisman'),
        ('tpk_update.csv',      'tpk_bintang'),
        ('inflasi_update.csv',  'inflasi_processed'),
        ('sentimen_update.csv', 'avg_sentiment_monthly'),
    ]:
        fpath = update_dir / fname
        if fpath.exists():
            df = pd.read_csv(fpath)
            df['month'] = df['month'].astype(str).str[:7]
            updates[col] = df
            print(f"  📂 Update ditemukan: {fname} ({len(df)} baris)")

    return updates


def merge_bps_updates(master: pd.DataFrame, updates: dict) -> pd.DataFrame:
    """Append/update baris baru dari data BPS ke master dataset."""
    if not updates:
        return master

    # Buat set bulan baru yang perlu ditambahkan
    all_new_months = set()
    for col, df in updates.items():
        all_new_months.update(df['month'].tolist())

    existing_months = set(master['month'].astype(str))
    new_months = sorted(all_new_months - existing_months)

    if not new_months:
        print("  ℹ️  Tidak ada bulan baru dari BPS updates.")
        # Update existing rows
        for col, df in updates.items():
            df = df.set_index('month')
            for m in df.index:
                if m in existing_months:
                    master.loc[master['month'].astype(str) == m, col] = df.loc[m, col]
        return master

    print(f"  ➕ Bulan baru dari BPS: {new_months}")
    last_row = dict(master.iloc[-1])

    new_rows = []
    for m in new_months:
        row = dict(last_row)   # template dari bulan terakhir
        row['month'] = m
        for col, df in updates.items():
            df_m = df[df['month'] == m]
            if not df_m.empty:
                row[col] = float(df_m[col].iloc[0])
        new_rows.append(row)

    master = pd.concat([master, pd.DataFrame(new_rows)], ignore_index=True)
    master = master.sort_values('month').reset_index(drop=True)
    return master


# ════════════════════════════════════════════════════════════
# 3. FEATURE ENGINEERING (sama persis dengan notebook 04)
# ════════════════════════════════════════════════════════════

def rolling_slope(series: pd.Series, window: int = 3) -> pd.Series:
    """Slope dari rolling window menggunakan polyfit."""
    def _slope(arr):
        if len(arr) < 2 or np.isnan(arr).all():
            return np.nan
        x = np.arange(len(arr))
        valid = ~np.isnan(arr)
        if valid.sum() < 2:
            return np.nan
        return np.polyfit(x[valid], arr[valid], 1)[0]
    return series.rolling(window).apply(_slope, raw=True)


def rebuild_features(df: pd.DataFrame, usd_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rebuild seluruh fitur engineering dari raw columns.
    Ini adalah versi fungsi dari notebook 04.
    """
    df = df.copy().sort_values('month').reset_index(drop=True)

    # ── Update USD/IDR dari data live ────────────────────────
    if not usd_df.empty:
        usd_map = usd_df.set_index('month')['usd_idr_avg'].to_dict()
        df['usd_idr_avg'] = df['month'].astype(str).map(usd_map).fillna(df.get('usd_idr_avg', np.nan))
        df['usd_idr_avg'] = df['usd_idr_avg'].ffill()

    # ── Fitur growth rate ────────────────────────────────────
    df['wisman_growth_mom'] = df['wisman'].pct_change()
    df['wisman_growth_yoy'] = df['wisman'].pct_change(periods=12)

    if 'wisnus' in df.columns:
        df['wisnus_growth_mom'] = df['wisnus'].pct_change()

    # ── Rolling averages ─────────────────────────────────────
    df['wisman_ma3'] = df['wisman'].rolling(3).mean()
    df['wisman_ma6'] = df['wisman'].rolling(6).mean()

    # ── USD volatilitas ──────────────────────────────────────
    df['usd_volatility_3m'] = df['usd_idr_avg'].rolling(3).std()
    df['usd_change_mom']    = df['usd_idr_avg'].pct_change()

    # ── Z-score wisman (anomali) ─────────────────────────────
    roll_mean = df['wisman'].rolling(12).mean()
    roll_std  = df['wisman'].rolling(12).std()
    df['wisman_zscore'] = (df['wisman'] - roll_mean) / roll_std.replace(0, np.nan)
    df['is_anomaly']    = (df['wisman_zscore'] < -2).astype(int)

    # ── Bali market share ────────────────────────────────────
    if 'bali_share_pct' in df.columns:
        df['bali_share_change'] = df['bali_share_pct'].diff()

    # ── TPK features ─────────────────────────────────────────
    if 'tpk_bintang' in df.columns:
        df['tpk_change_mom'] = df['tpk_bintang'].diff()
        df['tpk_ma3']        = df['tpk_bintang'].rolling(3).mean()
        df['tpk_lag_1']      = df['tpk_bintang'].shift(1)

    # ── Trend slopes ─────────────────────────────────────────
    df['wisman_trend_3m'] = rolling_slope(df['wisman'], 3)
    if 'avg_sentiment_monthly' in df.columns:
        df['sentiment_trend_3m'] = rolling_slope(df['avg_sentiment_monthly'], 3)
    if 'usd_idr_avg' in df.columns:
        df['usd_trend_3m'] = rolling_slope(df['usd_idr_avg'], 3)

    # ── Seasonality ──────────────────────────────────────────
    df['month_num']      = df['month'].astype(str).str[5:7].astype(int)
    df['is_peak_season'] = df['month_num'].isin([7, 8, 12, 1]).astype(int)

    return df


# ════════════════════════════════════════════════════════════
# 4. CRISIS SCORE (sama dengan notebook 04)
# ════════════════════════════════════════════════════════════

def compute_crisis_score(df: pd.DataFrame) -> pd.DataFrame:
    """Hitung ulang crisis_score_100 dan crisis_level."""
    df = df.copy()

    scores = pd.Series(np.zeros(len(df)), index=df.index)
    weights_used = pd.Series(np.zeros(len(df)), index=df.index)

    # ── Tourism component (75%) ──────────────────────────────
    tourism_score = pd.Series(np.zeros(len(df)), index=df.index)
    t_parts = 0

    if 'wisman_zscore' in df.columns:
        z = df['wisman_zscore'].fillna(0)
        zscore_score = np.clip(-z, 0, 4) / 4
        tourism_score += zscore_score * 0.5
        t_parts += 0.5

    if 'wisman_growth_mom' in df.columns:
        g = df['wisman_growth_mom'].fillna(0)
        growth_score = np.clip(-g, 0, 1)
        tourism_score += growth_score * 0.3
        t_parts += 0.3

    if 'tpk_bintang' in df.columns:
        tpk_norm = 1 - (df['tpk_bintang'].fillna(50) / 100)
        tourism_score += tpk_norm * 0.2
        t_parts += 0.2

    if t_parts > 0:
        tourism_score = tourism_score / t_parts
    df['crisis_component_tourism'] = tourism_score.clip(0, 1)

    # ── Economy component (20%) ──────────────────────────────
    economy_score = pd.Series(np.zeros(len(df)), index=df.index)
    e_parts = 0

    if 'usd_change_mom' in df.columns:
        usd_ch = df['usd_change_mom'].fillna(0)
        usd_score = np.clip(usd_ch * 5, 0, 1)
        economy_score += usd_score * 0.5
        e_parts += 0.5

    if 'inflasi_processed' in df.columns:
        inf_score = np.clip(df['inflasi_processed'].fillna(3) / 10, 0, 1)
        economy_score += inf_score * 0.5
        e_parts += 0.5

    if e_parts > 0:
        economy_score = economy_score / e_parts
    df['crisis_component_economy'] = economy_score.clip(0, 1)

    # ── Sentiment component (5%) ─────────────────────────────
    sent_score = pd.Series(np.zeros(len(df)), index=df.index)
    if 'avg_sentiment_monthly' in df.columns:
        # Sentimen -1..1 → dibalik (negatif = buruk = score tinggi)
        s = df['avg_sentiment_monthly'].fillna(0)
        sent_score = np.clip((-s + 1) / 2, 0, 1)
    df['crisis_component_sentiment'] = sent_score

    # ── Combined score ───────────────────────────────────────
    df['crisis_score'] = (
        W_TOURISM   * df['crisis_component_tourism'] +
        W_ECONOMY   * df['crisis_component_economy'] +
        W_SENTIMENT * df['crisis_component_sentiment']
    )
    df['crisis_score_100'] = (df['crisis_score'] * 100).clip(0, 100)
    df['crisis_level']     = df['crisis_score_100'].apply(level_from_score)

    return df


# ════════════════════════════════════════════════════════════
# 5. RUN MODEL PREDICTIONS
# ════════════════════════════════════════════════════════════

FEATURES = [
    'wisman_growth_mom', 'wisman_growth_yoy', 'wisman_zscore',
    'usd_idr_avg', 'usd_volatility_3m', 'usd_change_mom',
    'tpk_bintang', 'tpk_change_mom',
    'inflasi_processed', 'bali_share_pct',
    'avg_sentiment_monthly',
    'month_num', 'is_peak_season',
]

def run_model_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Load scaler + model dari disk, run prediction pada seluruh dataset.
    Kalau model belum ada → skip dan gunakan rule-based dari crisis_score.
    """
    scaler_path = MDL_DIR / 'scaler.pkl'
    rf_path     = MDL_DIR / 'model_random_forest.pkl'
    iso_path    = MDL_DIR / 'model_isolation_forest.pkl'
    le_path     = MDL_DIR / 'label_encoder.pkl'

    if not all(p.exists() for p in [scaler_path, rf_path, iso_path, le_path]):
        print("  ⚠️  Model files tidak ditemukan. Menggunakan rule-based predictions.")
        df['rf_predicted_level'] = df['crisis_level']
        df['rf_confidence']      = 0.70
        df['iso_anomaly']        = df.get('is_anomaly', 0)
        df['prob_krisis']        = (df['crisis_score_100'] / 100).clip(0, 1)
        df['prob_siaga']         = 0.3
        df['prob_waspada']       = 0.3
        df['prob_aman']          = 0.1
        return df

    scaler   = joblib.load(scaler_path)
    rf_model = joblib.load(rf_path)
    iso      = joblib.load(iso_path)
    le       = joblib.load(le_path)

    # Subset dengan fitur lengkap
    feat_cols = [f for f in FEATURES if f in df.columns]
    df_model  = df[feat_cols + ['month', 'crisis_level']].dropna().copy()

    X = df_model[feat_cols].values
    try:
        X_scaled = scaler.transform(X)
    except Exception:
        X_scaled = scaler.fit_transform(X)

    # Isolation Forest
    iso_pred = iso.predict(X_scaled)
    df_model['iso_anomaly'] = (iso_pred == -1).astype(int)

    # Random Forest
    rf_pred  = rf_model.predict(X_scaled)
    rf_proba = rf_model.predict_proba(X_scaled)

    df_model['rf_predicted_level'] = le.inverse_transform(rf_pred)
    df_model['rf_confidence']      = rf_proba.max(axis=1)

    # Probabilitas per kelas
    classes = list(le.classes_)
    for cls in ['KRISIS', 'SIAGA', 'WASPADA', 'AMAN']:
        col = f'prob_{cls.lower()}'
        if cls in classes:
            df_model[col] = rf_proba[:, classes.index(cls)]
        else:
            df_model[col] = 0.0

    # Merge back ke df utama
    pred_cols = ['month', 'iso_anomaly', 'rf_predicted_level', 'rf_confidence',
                 'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman']
    df = df.merge(df_model[pred_cols], on='month', how='left', suffixes=('', '_new'))

    # Update existing columns
    for col in pred_cols[1:]:
        if col + '_new' in df.columns:
            df[col] = df[col + '_new'].fillna(df.get(col, 0))
            df.drop(columns=[col + '_new'], inplace=True)

    # Fill missing (baris yang tidak punya fitur lengkap)
    df['rf_predicted_level'] = df.get('rf_predicted_level', df['crisis_level']).fillna(df['crisis_level'])
    df['rf_confidence']      = df.get('rf_confidence', 0.7).fillna(0.7)
    df['iso_anomaly']        = df.get('iso_anomaly', 0).fillna(0).astype(int)

    print(f"  ✅ Model predictions: {len(df_model)} baris diprediksi")
    return df


# ════════════════════════════════════════════════════════════
# 6. MAIN PIPELINE
# ════════════════════════════════════════════════════════════

def run_pipeline(verbose: bool = True):
    print("\n" + "═" * 60)
    print("  🛡️  BaliGuard — Update Pipeline")
    print(f"  📅  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # ── Load master dataset ──────────────────────────────────
    master_path = DATA_FIN / 'master_dataset_clean.parquet'
    pred_path   = DATA_FIN / 'predictions_final.csv'

    if not master_path.exists():
        print("❌ master_dataset_clean.parquet tidak ditemukan.")
        print("   Jalankan notebook 01-04 terlebih dahulu.")
        sys.exit(1)

    df = pd.read_parquet(master_path)
    df['month'] = df['month'].astype(str).str[:7]
    print(f"\n✅ Master dataset: {len(df)} baris, {df['month'].min()} → {df['month'].max()}")

    # ── Step 1: Update USD/IDR live ──────────────────────────
    print("\n[1/5] Mengambil data USD/IDR terbaru...")
    usd_df = update_usd_idr()

    # ── Step 2: Load BPS manual updates ─────────────────────
    print("\n[2/5] Mengecek update data BPS...")
    bps_updates = load_bps_updates()
    df = merge_bps_updates(df, bps_updates)

    # ── Step 3: Rebuild features ─────────────────────────────
    print("\n[3/5] Rebuild fitur engineering...")
    df = rebuild_features(df, usd_df)

    # ── Step 4: Recompute crisis score ───────────────────────
    print("\n[4/5] Menghitung ulang crisis score...")
    df = compute_crisis_score(df)
    score_summary = df.groupby('crisis_level').size()
    print(f"  Distribusi level: {score_summary.to_dict()}")
    print(f"  Periode: {df['month'].min()} → {df['month'].max()}")

    # ── Step 5: Run model predictions ────────────────────────
    print("\n[5/5] Menjalankan model predictions...")
    df = run_model_predictions(df)

    # ── Save outputs ─────────────────────────────────────────
    print("\n💾 Menyimpan output...")

    # Simpan master dataset (parquet)
    df.to_parquet(master_path, index=False)
    print(f"  ✅ master_dataset_clean.parquet ({len(df)} baris)")

    # Simpan predictions CSV
    pred_cols = [
        'month', 'wisman', 'tpk_bintang', 'inflasi_processed',
        'usd_idr_avg', 'avg_sentiment_monthly', 'bali_share_pct',
        'wisman_zscore', 'crisis_score_100', 'crisis_level',
        'rf_predicted_level', 'rf_confidence', 'iso_anomaly',
        'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman',
        'crisis_component_tourism', 'crisis_component_economy', 'crisis_component_sentiment',
    ]
    pred_cols_avail = [c for c in pred_cols if c in df.columns]
    df[pred_cols_avail].to_csv(pred_path, index=False)
    print(f"  ✅ predictions_final.csv ({len(df)} baris)")

    # ── Summary ──────────────────────────────────────────────
    latest = df.iloc[-1]
    print("\n" + "═" * 60)
    print(f"  🏁 Pipeline selesai!")
    print(f"  📊 Bulan terbaru  : {latest['month']}")
    print(f"  🎯 Crisis Score   : {latest['crisis_score_100']:.1f}/100")
    print(f"  📍 Level          : {latest['crisis_level']}")
    print(f"  💱 USD/IDR        : Rp {latest.get('usd_idr_avg', 0):,.0f}")
    print("═" * 60 + "\n")

    return df


if __name__ == '__main__':
    run_pipeline()
