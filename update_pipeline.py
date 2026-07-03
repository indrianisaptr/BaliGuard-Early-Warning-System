"""
update_pipeline.py — BaliGuard Semi-Automatic Monthly Update Pipeline
======================================================================
Jalankan tiap bulan setelah data BPS baru tersedia:

    python update_pipeline.py

Apa yang dilakukan:
  1. Baca USD/IDR terbaru dari automation staging
     (automation/data/staging/usd_idr/) — TIDAK fetch API apapun di sini.
     Fetch live sepenuhnya jadi tanggung jawab automation/fetch/usd_idr.py
     (dijalankan terpisah via automation/scheduler/run_job.py).
     Kalau staging kosong, fallback ke dataset historis lokal apa adanya.
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

import os, sys, uuid, warnings, json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings('ignore')

# ── Path config ──────────────────────────────────────────────
BASE     = Path(__file__).parent
DATA_RAW = BASE / 'data' / 'raw'
DATA_PRO = BASE / 'data' / 'processed'
DATA_FIN = BASE / 'data' / 'final'
MDL_DIR  = BASE / 'models'

for d in [DATA_RAW / 'updates', DATA_PRO, DATA_FIN, MDL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Automation staging bridge ────────────────────────────────
# update_pipeline.py TIDAK BOLEH melakukan fetch API apapun.
# Satu-satunya sumber data baru untuk usd_idr adalah staging yang
# ditulis oleh automation/fetch/usd_idr.py + storage/staging_writer.py.
# Kalau staging tidak bisa diimport (mis. dijalankan tanpa folder
# automation/ di sebelahnya), kita treat sebagai "staging kosong"
# dan jatuh ke dataset historis lokal — bukan fetch live.
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

try:
    from automation.storage.staging_writer import list_staging_keys, read_staging
    _STAGING_AVAILABLE = True
except ImportError:
    _STAGING_AVAILABLE = False

# ── Prediction Storage (Supabase) bridge ─────────────────────
# Storage layer baru: setelah predictions_final.csv ditulis, kirim juga
# isinya ke Supabase via batch upsert. Kalau modul/kredensial tidak
# tersedia, pipeline tetap jalan seperti biasa (CSV tetap jadi sumber
# kebenaran untuk dashboard lama) — upsert hanya di-skip dengan warning.
# Import struktur target project adalah src/repositories/ (lihat docstring
# metadata_repository.py & prediction_repository.py). Dicoba dulu supaya
# konsisten dengan arsitektur; fallback ke flat import untuk kondisi saat
# ini di mana update_pipeline.py masih dijalankan dari root dan kedua
# repository berada satu folder dengannya. Sebelum deploy, sebaiknya
# repository dipindah ke src/repositories/ dan fallback ini dihapus.
try:
    from src.repositories.prediction_repository import PredictionRepository
    _PREDICTION_REPO_AVAILABLE = True
except ImportError:
    try:
        from prediction_repository import PredictionRepository
        _PREDICTION_REPO_AVAILABLE = True
    except ImportError:
        _PREDICTION_REPO_AVAILABLE = False

# ── Metadata Storage (Supabase) bridge ────────────────────────
# Sama seperti PredictionRepository di atas: kalau modul/kredensial tidak
# tersedia, pipeline tetap jalan seperti biasa — upsert metadata hanya
# di-skip dengan warning, tidak menggagalkan pipeline.
try:
    from src.repositories.metadata_repository import MetadataRepository
    _METADATA_REPO_AVAILABLE = True
except ImportError:
    try:
        from metadata_repository import MetadataRepository
        _METADATA_REPO_AVAILABLE = True
    except ImportError:
        _METADATA_REPO_AVAILABLE = False

# ── Pipeline Log Storage (Supabase) bridge ────────────────────
# Sama seperti PredictionRepository/MetadataRepository di atas: kalau
# modul/kredensial tidak tersedia, pipeline tetap jalan seperti biasa —
# insert log hanya di-skip dengan warning, tidak menggagalkan pipeline.
try:
    from src.repositories.pipeline_log_repository import PipelineLogRepository
    _PIPELINE_LOG_REPO_AVAILABLE = True
except ImportError:
    try:
        from pipeline_log_repository import PipelineLogRepository
        _PIPELINE_LOG_REPO_AVAILABLE = True
    except ImportError:
        _PIPELINE_LOG_REPO_AVAILABLE = False

# Versi pipeline saat ini. Tidak ada mekanisme versioning otomatis di
# repo ini (bukan hasil kalkulasi). Update manual setiap ada perubahan
# besar pipeline — mis. perubahan step/urutan run_pipeline(), perubahan
# skema PREDICTION_OUTPUT_COLUMNS, atau perubahan logic crisis score.
# Perubahan kecil/kosmetik di luar pipeline (mis. tampilan Dashboard)
# TIDAK perlu menaikkan versi ini — versi ini murni menandai versi
# update_pipeline.py, bukan versi Dashboard (lihat field terpisah
# `dashboard_version` di metadata).
PIPELINE_VERSION = "1.0.0"

# ── Kolom output final predictions_final.csv ─────────────────
# Single source of truth: dipakai baik untuk to_csv() maupun untuk data
# yang dikirim ke PredictionRepository.upsert_predictions(), supaya CSV
# dan Supabase selalu identik. Daftar ini HARUS sama persis dengan
# PREDICTIONS_COLUMNS di prediction_repository.py (31 kolom, sesuai
# output final NB05 — TIDAK termasuk crisis_component_tourism/economy/
# sentiment, karena NB05 sudah tidak lagi mengirim itu ke predictions_final.csv).
PREDICTION_OUTPUT_COLUMNS = [
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

# ── Crisis score weights — DARI NB04 Cell[17] ACTUAL CODE ──────────────────
# CATATAN: NB04 Cell[16] COMMENT bilang "45/30/25" tapi CODE Cell[17] = 0.75/0.20/0.05
# update_pipeline versi lama ikut comment → SALAH → sudah diperbaiki
# (konstanta ini tidak dipakai langsung oleh compute_crisis_score() lagi,
#  tapi disimpan di sini sebagai dokumentasi)
W_TOURISM   = 0.75   # ← 0.75 sesuai NB04 Cell[17]
W_ECONOMY   = 0.20
W_SENTIMENT = 0.05

# ── Level thresholds (HARUS sama persis dengan NB04 FINAL) ──
THRESHOLD_KRISIS  = 60
THRESHOLD_SIAGA   = 45
THRESHOLD_WASPADA = 30

def level_from_score(s: float) -> str:
    if s >= THRESHOLD_KRISIS:
        return 'KRISIS'
    if s >= THRESHOLD_SIAGA:
        return 'SIAGA'
    if s >= THRESHOLD_WASPADA:
        return 'WASPADA'
    return 'AMAN'


# ════════════════════════════════════════════════════════════
# 1. FETCH LIVE USD/IDR
# ════════════════════════════════════════════════════════════

def load_usd_idr_from_staging() -> pd.DataFrame:
    """
    Baca seluruh record usd_idr dari automation staging.
    TIDAK melakukan fetch API apapun — staging adalah satu-satunya
    titik kontak update_pipeline.py dengan dunia automation
    (sesuai BALIGUARD_AUTOMATION_ARCHITECTURE.md: "automation berhenti
    di staging, pipeline ML tidak pernah tahu soal fetch/API").

    Return: DataFrame [month, usd_idr_avg] — kosong jika staging
    tidak tersedia atau belum berisi data.
    """
    if not _STAGING_AVAILABLE:
        print("  ⚠  Modul automation.storage.staging_writer tidak terimport — "
              "anggap staging kosong, lanjut ke fallback historis lokal.")
        return pd.DataFrame(columns=['month', 'usd_idr_avg'])

    try:
        keys = list_staging_keys('usd_idr')
    except Exception as e:
        print(f"  ⚠  Gagal membaca daftar staging usd_idr: {e}")
        return pd.DataFrame(columns=['month', 'usd_idr_avg'])

    if not keys:
        return pd.DataFrame(columns=['month', 'usd_idr_avg'])

    rows = []
    for key in keys:
        try:
            record = read_staging('usd_idr', key)
        except Exception as e:
            print(f"  ⚠  Gagal membaca staging usd_idr key={key}: {e}")
            continue
        if record and record.get('usd_idr_avg') is not None:
            rows.append({'month': record['month'], 'usd_idr_avg': record['usd_idr_avg']})

    if not rows:
        return pd.DataFrame(columns=['month', 'usd_idr_avg'])

    result = pd.DataFrame(rows).drop_duplicates(subset='month', keep='last')
    result = result.sort_values('month').reset_index(drop=True)
    print(f"  ✓ Staging usd_idr: {len(result)} bulan ditemukan "
          f"({result['month'].min()} → {result['month'].max()})")
    return result


def update_usd_idr() -> pd.DataFrame:
    """
    Sumber data usd_idr untuk pipeline, TANPA fetch API apapun:
      1. Prioritas: data dari automation staging (read-only).
      2. Fallback: dataset historis lokal (data/processed/monthly_usd.csv)
         apa adanya — tidak di-fetch ulang, hanya dibaca.

    Hasil akhir tetap digabung & ditulis ke monthly_usd.csv +
    usd_idr_cache.csv supaya kompatibel dengan rebuild_features()
    dan output pipeline yang sudah ada (tidak berubah).
    """
    usd_path = DATA_PRO / 'monthly_usd.csv'

    if usd_path.exists():
        existing = pd.read_csv(usd_path)
        existing['month'] = existing['month'].astype(str).str[:7]
    else:
        existing = pd.DataFrame(columns=['month', 'usd_idr_avg'])

    staging_data = load_usd_idr_from_staging()

    if staging_data.empty:
        print("  ⚠  Staging usd_idr kosong — pakai dataset historis lokal "
              "apa adanya (tidak fetch live).")
        if existing.empty:
            print("  ✗ Dataset historis lokal juga kosong/tidak ditemukan.")
        return existing

    combined = pd.concat([existing, staging_data], ignore_index=True)
    combined = combined.drop_duplicates(subset='month', keep='last')
    combined = combined.sort_values('month').reset_index(drop=True)

    combined.to_csv(usd_path, index=False)
    combined.to_csv(DATA_PRO / 'usd_idr_cache.csv', index=False)
    print(f"  ✓ USD/IDR updated dari staging: {len(combined)} bulan, "
          f"terakhir {combined['month'].max()}")
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
            print(f"   Update ditemukan: {fname} ({len(df)} baris)")

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
        print("    Tidak ada bulan baru dari BPS updates.")
        # Update existing rows
        for col, df in updates.items():
            df = df.set_index('month')
            for m in df.index:
                if m in existing_months:
                    master.loc[master['month'].astype(str) == m, col] = df.loc[m, col]
        return master

    print(f"  Bulan baru dari BPS: {new_months}")
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
# 2b. LOAD & MERGE EXTERNAL FEATURES (sama persis dengan notebook 05
#     Cell[4] — combined_additional_features_engineered_new.csv)
# ════════════════════════════════════════════════════════════
# AUDIT FINDING: update_pipeline.py sebelumnya TIDAK PERNAH membaca file
# ini, sehingga 2 fitur training (gdelt_crisis_score_zscore,
# disaster_risk_score_zscore) tidak pernah tersedia saat inference.
# Fungsi-fungsi di bawah mereplikasi NB05 Cell[4] baris-per-baris.
EXTERNAL_FEATURES_PATH = DATA_PRO / 'combined_additional_features_engineered_new.csv'


def load_external_features() -> pd.DataFrame:
    """
    Baca & pra-proses combined_additional_features_engineered_new.csv.
    IDENTIK dengan NB05 Cell[4]:
      - date → month (period YYYY-MM)
      - drop kolom 'date'
      - groupby('month').mean(numeric_only=True) — hilangkan duplikasi month
    Return df_ext kosong (hanya kolom 'month') kalau file tidak ditemukan,
    supaya pipeline tetap jalan (fallback graceful, bukan crash) — TIDAK
    ada di notebook (notebook asumsi file selalu ada), ditambahkan khusus
    di sini karena update_pipeline.py harus tahan terhadap file hilang
    di server produksi.
    """
    if not EXTERNAL_FEATURES_PATH.exists():
        print(f"  ⚠  {EXTERNAL_FEATURES_PATH.name} tidak ditemukan di "
              f"{EXTERNAL_FEATURES_PATH.parent} — fitur eksternal CSV dilewati "
              f"(gdelt_crisis_score_zscore & disaster_risk_score_zscore TIDAK akan tersedia).")
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
    Merge left df_ext ke df utama — IDENTIK dengan NB05 Cell[4]:
      - df (master) sebagai anchor: df.merge(df_ext, on='month', how='left')
        → jumlah baris df TIDAK BOLEH berubah
      - fillna(0) untuk seluruh kolom yang berasal dari df_ext

    CATATAN PERILAKU MERGE (sama seperti notebook, TIDAK diubah):
    df sudah punya beberapa kolom dengan nama sama seperti df_ext
    (gdelt_crisis_score, economic_risk_score, disaster_risk_score,
    external_risk_avg, external_risk_max, external_risk_range — sudah ada
    dari master_dataset_clean.parquet/NB04). Karena merge() di notebook
    TIDAK diberi parameter suffixes, pandas otomatis me-rename kolom yang
    bentrok menjadi <kolom>_x (versi df/master) dan <kolom>_y (versi
    df_ext/CSV) — inilah sebabnya di notebook hanya 2 dari 8 kandidat
    FEATURES_EXTERNAL yang lolos filter `f in df.columns`
    (gdelt_crisis_score_zscore, disaster_risk_score_zscore — nama unik,
    tidak bentrok). Direplikasi apa adanya di sini.

    Supaya kolom master yang SUDAH ADA sebelumnya (dipakai
    PREDICTION_OUTPUT_COLUMNS untuk predictions_final.csv & Supabase)
    tidak hilang gara-gara suffix _x/_y ini, versi "_x" (nilai asli
    master — sumber kebenaran yang sudah dipakai output selama ini)
    dikembalikan ke nama semula, dan versi "_y" (duplikat mentah dari
    CSV, tidak dipakai FEATURES maupun output) dibuang. Langkah reconcile
    ini TIDAK mengubah nilai fitur model sama sekali — 19 fitur training
    tidak termasuk kolom-kolom yang bentrok ini (lihat FEATURES di bawah).
    """
    if df_ext.empty or list(df_ext.columns) == ['month']:
        return df

    df = df.copy()
    df['month'] = df['month'].astype(str)

    n_before = len(df)
    df = df.merge(df_ext, on='month', how='left')
    assert len(df) == n_before, (
        "Merge left mengubah jumlah baris master — seharusnya tidak mungkin "
        "(cek duplikasi 'month' di df_ext)"
    )

    # Kolom CSV eksternal yang benar-benar ada di df hasil merge (kolom
    # yang bentrok nama tidak match di sini karena sudah jadi _x/_y —
    # identik dengan notebook Cell[4]).
    ext_cols = [c for c in df_ext.columns if c != 'month' and c in df.columns]
    if ext_cols:
        n_na = df[ext_cols].isna().sum().sum()
        df[ext_cols] = df[ext_cols].fillna(0)
        print(f"  ✓ External features merged: {ext_cols}")
        print(f"  ✓ fillna(0) pada external features: {int(n_na)} NaN diisi 0")

    # Reconcile kolom bentrok — pertahankan versi master (_x) dengan nama
    # semula, buang versi CSV (_y). Tidak memengaruhi fitur model.
    overlap_cols = [c for c in df_ext.columns
                    if c != 'month' and f'{c}_x' in df.columns and f'{c}_y' in df.columns]
    for c in overlap_cols:
        df[c] = df[f'{c}_x']
        df.drop(columns=[f'{c}_x', f'{c}_y'], inplace=True)
    if overlap_cols:
        print(f"  ℹ  Kolom bentrok dgn master (nilai master dipertahankan, "
              f"versi CSV dibuang, TIDAK dipakai sbg fitur model): {overlap_cols}")

    return df


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
    """
    Hitung ulang crisis_score_100 — formula sama persis dengan NB04.

    PERBEDAAN DARI VERSI LAMA (bug yang diperbaiki):
    1. WEIGHTS: 0.75/0.20/0.05 (bukan 0.45/0.30/0.25)
       → NB04 Cell[17] actual code, bukan comment-nya
    2. NORMALISASI: MinMax pada wisman_growth_mom & usd sebelum dipakai
       → NB04 Cell[14]: fit MinMax, clip outlier 5-95pct, normalize ke 0-1
    3. SPECIAL RULE: wisman < 5% baseline → force SIAGA/KRISIS
       → NB04 Cell[18] label_crisis()
    """
    from sklearn.preprocessing import MinMaxScaler
    df = df.copy()

    # ── Step 1: MinMax normalisasi (NB04 Cell[14]) ──────────────────────────
    # Kolom yang perlu dinormalisasi sebelum masuk ke komponen
    cols_to_norm = ['wisman_growth_mom', 'wisman_growth_yoy',
                    'usd_volatility_3m', 'usd_change_mom']
    cols_avail   = [c for c in cols_to_norm if c in df.columns]

    if cols_avail:
        temp_norm = df[cols_avail].copy()
        for col in cols_avail:
            q05 = temp_norm[col].quantile(0.05)
            q95 = temp_norm[col].quantile(0.95)
            temp_norm[col] = temp_norm[col].clip(q05, q95)
        normalized = MinMaxScaler().fit_transform(temp_norm.fillna(0))
        for i, col in enumerate(cols_avail):
            df[f'{col}_norm'] = normalized[:, i]

    # ── Step 2: Tourism component (NB04 Cell[16]) ───────────────────────────
    # growth_score = 1 - wisman_growth_mom_norm  (inverted: rendah = krisis)
    # zscore_score = clip(-zscore, 0, 4) / 4
    # tourism = 0.6 * growth_score + 0.4 * zscore_score
    tourism_score = pd.Series(np.zeros(len(df)), index=df.index)
    if 'wisman_growth_mom_norm' in df.columns:
        tourism_score += (1 - df['wisman_growth_mom_norm'].fillna(0)) * 0.6
    if 'wisman_zscore' in df.columns:
        z = df['wisman_zscore'].fillna(0)
        tourism_score += (np.clip(-z, 0, 4) / 4) * 0.4
    df['crisis_component_tourism'] = tourism_score.clip(0, 1)

    # ── Step 3: Economy component (NB04 Cell[16]) ───────────────────────────
    # 0.4*usd_volatility_norm + 0.3*usd_change_norm + 0.3*tpk_score
    economy_score = pd.Series(np.zeros(len(df)), index=df.index)
    if 'usd_volatility_3m_norm' in df.columns:
        economy_score += df['usd_volatility_3m_norm'].fillna(0) * 0.4
    if 'usd_change_mom_norm' in df.columns:
        economy_score += df['usd_change_mom_norm'].fillna(0) * 0.3
    if 'tpk_bintang' in df.columns:
        tpk_score = np.maximum(0, (60 - df['tpk_bintang'].fillna(50)) / 60)
        economy_score += tpk_score * 0.3
    df['crisis_component_economy'] = economy_score.clip(0, 1)

    # ── Step 4: Sentiment component (NB04 Cell[16]) ─────────────────────────
    # Sentimen -1..1 → inverted → 0-1 (negatif = skor tinggi = krisis)
    sent_score = pd.Series(np.zeros(len(df)), index=df.index)
    if 'avg_sentiment_monthly' in df.columns:
        s = df['avg_sentiment_monthly'].fillna(0)
        sent_score = np.clip((-s + 1) / 2, 0, 1)
    df['crisis_component_sentiment'] = sent_score

    # ── Step 5: Combined score — bobot BENAR dari NB04 Cell[17] ─────────────
    # PERHATIAN: comment Cell[16] bilang "45/30/25" tapi CODE-nya "75/20/5"
    # update_pipeline lama salah ikut comment, bukan code → bug!
    WEIGHT_TOURISM   = 0.75   # ← 0.75 (bukan 0.45)
    WEIGHT_ECONOMY   = 0.20   # ← 0.20 (bukan 0.30)
    WEIGHT_SENTIMENT = 0.05   # ← 0.05 (bukan 0.25)

    df['crisis_score'] = (
        WEIGHT_TOURISM   * df['crisis_component_tourism'] +
        WEIGHT_ECONOMY   * df['crisis_component_economy'] +
        WEIGHT_SENTIMENT * df['crisis_component_sentiment']
    )
    df['crisis_score_100'] = (df['crisis_score'] * 100).clip(0, 100)

    # ── Step 6: Label dengan special rule NB04 Cell[18] ─────────────────────
    # Jika wisman < 5% baseline pre-COVID → force minimal SIAGA/KRISIS
    PRECOVID_MEAN = 501206   # avg wisman Bali 2017-2019
    baselines = df.get('wisman_precovid_mean', pd.Series(PRECOVID_MEAN, index=df.index))

    def _label(row):
        score  = row['crisis_score_100']
        wisman = row.get('wisman', PRECOVID_MEAN)
        base   = baselines.loc[row.name] if hasattr(baselines, 'loc') else PRECOVID_MEAN
        if wisman < base * 0.05:
            return 'KRISIS' if score >= THRESHOLD_KRISIS else 'SIAGA'
        return level_from_score(score)

    df['crisis_level'] = df.apply(_label, axis=1)

    return df


# ════════════════════════════════════════════════════════════
# 5. RUN MODEL PREDICTIONS
# ════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════
# 5. RUN MODEL PREDICTIONS
# ════════════════════════════════════════════════════════════

# ── Fitur training — IDENTIK dengan NB05 Cell[12]/Cell[16] ──────────────
# AUDIT FINDING (sudah diperbaiki): FEATURES_BASE/FEATURES_EXTENDED versi
# lama adalah TEBAKAN ("fitur yang umum dipakai"), BUKAN hasil replikasi
# notebook — jumlah (13/20) dan isinya tidak cocok dengan training
# (19 fitur, urutan berbeda, 2 fitur terakhir gdelt_crisis_score_zscore &
# disaster_risk_score_zscore malah tidak ada sama sekali). Daftar di
# bawah menggantikan keduanya dan disusun PERSIS seperti notebook:
#   FEATURES_CORE (13) + FEATURES_LAG (4) + FEATURES_EXTERNAL (2)
# lihat NB05 Cell[12] untuk definisi asli.

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

# Kandidat fitur eksternal — sama seperti NB05 Cell[12] FEATURES_EXTERNAL.
# Di notebook, 6 dari 8 kandidat ini bentrok nama dengan kolom yang sudah
# ada di master_dataset_clean.parquet, sehingga ke-6-nya berubah nama jadi
# <kolom>_x/_y saat merge (lihat merge_external_features() di atas) dan
# GAGAL lolos filter `f in df.columns` — hanya 2 nama unik yang lolos:
# gdelt_crisis_score_zscore & disaster_risk_score_zscore. Filter di bawah
# mereplikasi hasil yang SAMA (bukan hardcode individual), supaya kalau
# suatu saat reconcile kolom di merge_external_features() diubah, daftar
# fitur ini tetap otomatis konsisten dengan apa yang benar-benar tersedia.
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

# Kolom yang SENGAJA di-reconcile balik ke nama master di
# merge_external_features() (lihat overlap_cols di sana) — bukan fitur
# CSV eksternal yang unik, jadi TIDAK boleh ikut FEATURES walau namanya
# match df.columns setelah reconcile. Harus expliсit karena reconcile
# mengembalikan nama-nama ini ke df.columns (lihat catatan di atas).
_EXTERNAL_RECONCILED_ALIASES = [
    'gdelt_crisis_score', 'economic_risk_score', 'disaster_risk_score',
    'external_risk_avg', 'external_risk_max', 'external_risk_range',
]


def build_features_list(df_columns) -> list:
    """
    Bangun daftar FEATURES final dari kolom df yang tersedia — replikasi
    NB05 Cell[12]: FEATURES_CORE + FEATURES_LAG + FEATURES_EXTERNAL,
    difilter hanya yang benar-benar ada di df, urutan dipertahankan.
    Hasilnya HARUS 19 fitur & 2 terakhir HARUS gdelt_crisis_score_zscore,
    disaster_risk_score_zscore (sesuai fakta audit) selama
    merge_external_features() sudah dipanggil sebelumnya di df.
    """
    cols = set(df_columns)
    features_external = [
        f for f in FEATURES_EXTERNAL_CANDIDATES
        if f in cols and f not in _EXTERNAL_RECONCILED_ALIASES
    ]
    return [f for f in FEATURES_CORE + FEATURES_LAG + features_external if f in cols]


def _build_feature_matrix(df_model: pd.DataFrame,
                           feat_cols: list,
                           expected_n: int) -> tuple:
    """
    Bangun X dengan shape (n_samples, expected_n).
    - Ganti inf → NaN, lalu impute median per kolom.
    - Return (X, feat_cols_used).
    """
    # Pastikan hanya pakai kolom yang ada, sesuai urutan
    available = [f for f in feat_cols if f in df_model.columns]
    if len(available) < expected_n:
        return None, available   # tidak cukup fitur

    # Ambil tepat expected_n kolom pertama (pertahankan urutan)
    cols_used = available[:expected_n]
    X = df_model[cols_used].values.astype(float)

    # Bersihkan inf/NaN
    X = np.where(np.isinf(X), np.nan, X)
    col_medians = np.nanmedian(X, axis=0)
    nan_mask = np.isnan(X)
    if nan_mask.any():
        bad = [(cols_used[i], int(nan_mask[:, i].sum()))
               for i in range(len(cols_used)) if nan_mask[:, i].any()]
        if bad:
            print(f"  ⚠  NaN/inf diimputasi: {bad}")
        X[nan_mask] = np.take(col_medians, np.where(nan_mask)[1])

    return X, cols_used


def run_model_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Load scaler + model dari disk, run prediction pada seluruh dataset.
    Auto-detect jumlah fitur yang diexpect model (base=13 atau extended=17+).
    Kalau model tidak ditemukan atau fitur tidak cocok → rule-based fallback.
    """
    scaler_path = MDL_DIR / 'scaler.pkl'
    rf_path     = MDL_DIR / 'model_random_forest.pkl'
    iso_path    = MDL_DIR / 'model_isolation_forest.pkl'
    le_path     = MDL_DIR / 'label_encoder.pkl'

    def _rule_based(df):
        df['rf_predicted_level'] = df['crisis_level']
        df['rf_confidence']      = 0.70
        df['iso_anomaly']        = df.get('is_anomaly', 0)
        df['prob_krisis']        = (df['crisis_score_100'] / 100).clip(0, 1)
        df['prob_siaga']         = 0.3
        df['prob_waspada']       = 0.3
        df['prob_aman']          = 0.1
        df["iso_score"]          = 0.0
        return df

    if not all(p.exists() for p in [scaler_path, rf_path, iso_path, le_path]):
        print("  ⚠  Model files tidak ditemukan. Menggunakan rule-based predictions.")
        return _rule_based(df)

    scaler   = joblib.load(scaler_path)
    rf_model = joblib.load(rf_path)
    iso      = joblib.load(iso_path)
    le       = joblib.load(le_path)

    expected_n = scaler.n_features_in_
    print(f"  Model expects {expected_n} features "
          f"(scaler={scaler.n_features_in_}, iso={iso.n_features_in_}, "
          f"rf={rf_model.n_features_in_})")

    # Bangun daftar fitur final (urutan persis notebook), difilter ke
    # kolom yang benar-benar tersedia di df. _build_feature_matrix()
    # sendiri yang menangani kasus model lama dengan expected_n lebih
    # kecil (ambil N kolom pertama sesuai urutan) — jadi tidak perlu
    # branching base/extended manual di sini.
    feat_list = build_features_list(df.columns)

    df_model = df[feat_list + ["month", "crisis_level"]].copy()

    X, cols_used = _build_feature_matrix(df_model, feat_list, expected_n)

    if X is None:
        print(f"  ⚠  Fitur tidak cukup ({len(cols_used)}/{expected_n}). "
              "Menggunakan rule-based predictions.")
        return _rule_based(df)

    print(f"  ✓ Feature matrix: {X.shape} — {cols_used}")

    # Scale
    try:
        X_scaled = scaler.transform(X)
    except ValueError as e:
        print(f"  ⚠  scaler.transform gagal ({e}). Refitting scaler pada data ini.")
        X_scaled = scaler.fit_transform(X)

    # Isolation Forest
    try:
        iso_pred = iso.predict(X_scaled)
        df_model['iso_anomaly'] = (iso_pred == -1).astype(int)
        df_model["iso_score"] = iso.decision_function(X_scaled)
    except Exception as e:
        print(f"  ⚠  IsolationForest predict gagal: {e}")
        df_model['iso_anomaly'] = 0

    # Random Forest
    try:
        rf_pred  = rf_model.predict(X_scaled)
        rf_proba = rf_model.predict_proba(X_scaled)
        df_model['rf_predicted_level'] = le.inverse_transform(rf_pred)
        df_model['rf_confidence']      = rf_proba.max(axis=1)
        # ✓ FIX: pakai rf_model.classes_ (kelas yang benar-benar diketahui model)
        # bukan le.classes_ — kalau suatu saat KRISIS hilang dari data,
        # le.classes_ tetap punya 4 entry tapi rf_proba hanya punya 3 kolom → IndexError
        rf_classes = list(le.inverse_transform(rf_model.classes_))
        for cls in ['KRISIS', 'SIAGA', 'WASPADA', 'AMAN']:
            col = f'prob_{cls.lower()}'
            if cls in rf_classes:
                df_model[col] = rf_proba[:, rf_classes.index(cls)]
            else:
                df_model[col] = 0.0
    except Exception as e:
        print(f"  ⚠  RandomForest predict gagal: {e}. Fallback rule-based.")
        return _rule_based(df)

    # Merge back ke df utama
    pred_cols = ['month', 'iso_anomaly', 'iso_score', 'rf_predicted_level', 'rf_confidence',
                 'prob_krisis', 'prob_siaga', 'prob_waspada', 'prob_aman']
    df = df.merge(df_model[pred_cols], on='month', how='left', suffixes=('', '_new'))
    for col in pred_cols[1:]:
        if col + '_new' in df.columns:
            df[col] = df[col + '_new'].fillna(df.get(col, 0))
            df.drop(columns=[col + '_new'], inplace=True)

    df['rf_predicted_level'] = df.get('rf_predicted_level', df['crisis_level']).fillna(df['crisis_level'])
    df['rf_confidence']      = df.get('rf_confidence', 0.7).fillna(0.7)
    df['iso_anomaly']        = df.get('iso_anomaly', 0).fillna(0).astype(int)

    print(f"  ✓ Model predictions selesai: {len(df_model)} baris diprediksi")
    return df


# ════════════════════════════════════════════════════════════
# 5b. MISSING VALUE HANDLING (post-processing, sebelum output disimpan)
# ════════════════════════════════════════════════════════════
# Dijalankan SETELAH seluruh feature engineering (rebuild_features),
# crisis score (compute_crisis_score), dan model prediction
# (run_model_predictions) selesai — TIDAK mengubah rumus/logic apa pun
# di fungsi-fungsi tersebut. Ini murni post-processing pembersihan NaN
# yang memang secara natural muncul dari pct_change()/rolling() (baris
# awal deret waktu) dan dari kolom risk score eksternal yang datang
# apa adanya dari sumber lain (mis. baris baru hasil merge_bps_updates
# yang belum kebagian nilai risk score terbaru).
#
# Dipanggil SATU KALI di run_pipeline(), tepat sebelum df dipakai untuk
# to_parquet() / to_csv() / upsert ke Supabase — supaya master parquet,
# predictions_final.csv, dan data yang dikirim ke PredictionRepository
# semuanya konsisten menerima versi df yang sama-sama sudah bersih.
FILL_ZERO_COLS   = ['wisman_growth_mom', 'wisman_growth_yoy',
                     'wisman_zscore', 'usd_volatility_3m']
FFILL_COLS       = ['gdelt_crisis_score', 'economic_risk_score',
                     'disaster_risk_score']


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Isi nilai NaN pada kolom-kolom tertentu sebelum output disimpan.
    - FILL_ZERO_COLS : NaN → 0
    - FFILL_COLS     : forward fill (nilai bulan sebelumnya)
    Tidak mengubah kolom lain maupun rumus feature engineering yang sudah ada.
    """
    df = df.copy()

    zero_cols_avail = [c for c in FILL_ZERO_COLS if c in df.columns]
    if zero_cols_avail:
        # Normalisasi inf/-inf → 0 DULU, sebelum fillna(0). pct_change()
        # bisa menghasilkan inf/-inf kalau nilai bulan sebelumnya 0 (mis.
        # wisman/usd_idr_avg = 0 di suatu bulan) — bukan NaN, jadi tidak
        # akan tertangkap oleh fillna() saja. Rumus pct_change() sendiri
        # TIDAK diubah; ini murni pembersihan hasil akhirnya di post-processing.
        n_inf = np.isinf(df[zero_cols_avail]).sum().sum()
        if n_inf:
            df[zero_cols_avail] = df[zero_cols_avail].replace([np.inf, -np.inf], 0)
            print(f"  ✓ Missing value handling: {int(n_inf)} nilai inf/-inf "
                  f"dinormalisasi jadi 0 pada kolom {zero_cols_avail}")

        n_before = df[zero_cols_avail].isna().sum().sum()
        df[zero_cols_avail] = df[zero_cols_avail].fillna(0)
        if n_before:
            print(f"  ✓ Missing value handling: {int(n_before)} NaN diisi 0 "
                  f"pada kolom {zero_cols_avail}")

    ffill_cols_avail = [c for c in FFILL_COLS if c in df.columns]
    if ffill_cols_avail:
        n_before = df[ffill_cols_avail].isna().sum().sum()
        df[ffill_cols_avail] = df[ffill_cols_avail].ffill()
        n_after = df[ffill_cols_avail].isna().sum().sum()
        if n_before:
            print(f"  ✓ Missing value handling: forward fill pada kolom "
                  f"{ffill_cols_avail} ({int(n_before)} NaN sebelum, "
                  f"{int(n_after)} NaN tersisa setelah ffill)")
        if n_after:
            # ffill tidak bisa mengisi NaN di baris paling awal (tidak ada
            # nilai sebelumnya untuk di-forward-fill). Dicetak sebagai
            # warning eksplisit supaya tidak diam-diam lolos ke output.
            print(f"  ⚠  Masih ada {int(n_after)} NaN di {ffill_cols_avail} "
                  f"setelah ffill (kemungkinan di baris paling awal dataset, "
                  f"tidak ada nilai sebelumnya untuk di-forward-fill).")

    return df


# ════════════════════════════════════════════════════════════
# 6. MAIN PIPELINE
# ════════════════════════════════════════════════════════════

def run_pipeline(verbose: bool = True):
    # ── Pipeline Log: init state histori run ini ─────────────
    # run_id & started_at dicatat SEBELUM step apa pun dijalankan, supaya
    # log tetap bisa ditulis walau pipeline gagal di step paling awal.
    # status default "FAILED" (pesimis) — baru diubah eksplisit jadi
    # "SUCCESS" tepat sebelum return df di akhir try. Ini supaya SEMUA
    # jalur keluar non-normal (exception ataupun sys.exit di bawah) tetap
    # tercatat sebagai FAILED, bukan salah tercatat SUCCESS.
    # started_at pakai UTC (timezone-aware), bukan datetime.now() lokal —
    # supaya konsisten kalau server pindah VPS/Railway/Docker dengan
    # timezone berbeda. Ini KHUSUS untuk field log started_at/finished_at
    # yang dikirim ke Supabase; print header/notes di bawah tetap pakai
    # datetime.now() lokal apa adanya (hanya tampilan konsol, tidak
    # disimpan sebagai kolom timestamp).
    run_id               = str(uuid.uuid4())
    started_at            = datetime.now(timezone.utc)
    status                = "FAILED"
    error_message         = None
    prediction_uploaded   = False
    metadata_uploaded     = False
    latest_month          = None
    prediction_rows       = None

    try:
        print("\n" + "═" * 60)
        print("   BaliGuard — Update Pipeline")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 60)

        # ── Load master dataset ──────────────────────────────
        master_path = DATA_FIN / 'master_dataset_clean.parquet'
        pred_path   = DATA_FIN / 'predictions_final.csv'

        if not master_path.exists():
            print("✗ master_dataset_clean.parquet tidak ditemukan.")
            print("   Jalankan notebook 01-04 terlebih dahulu.")
            sys.exit(1)

        df = pd.read_parquet(master_path)
        df['month'] = df['month'].astype(str).str[:7]
        print(f"\n ✓ Master dataset: {len(df)} baris, {df['month'].min()} → {df['month'].max()}")

        # ── Step 1: Baca USD/IDR dari staging (tanpa fetch) ──
        print("\n[1/5] Membaca data USD/IDR dari automation staging...")
        usd_df = update_usd_idr()

        # ── Step 2: Load BPS manual updates ─────────────────
        print("\n[2/5] Mengecek update data BPS...")
        bps_updates = load_bps_updates()
        df = merge_bps_updates(df, bps_updates)

        # ── Step 3: Rebuild features ──────────────────────────
        print("\n[3/5] Rebuild fitur engineering...")
        df = rebuild_features(df, usd_df)

        # ── Step 4: Recompute crisis score ───────────────────
        print("\n[4/5] Menghitung ulang crisis score...")
        df = compute_crisis_score(df)
        score_summary = df.groupby('crisis_level').size()
        print(f"  Distribusi level: {score_summary.to_dict()}")
        print(f" Periode: {df['month'].min()} → {df['month'].max()}") 
        df_ext = load_external_features() 
        df = merge_external_features(df, df_ext) 
        
        # ── Step 5: Run model predictions ──────────────────── 
        print("\n[5/5] Menjalankan model predictions...") 
        df = run_model_predictions(df)

        # ── Step 5b: Missing value handling ──────────────────
        # SATU lokasi, dijalankan setelah seluruh feature engineering +
        # model prediction selesai dan SEBELUM df dipakai untuk output
        # apa pun (parquet, CSV, upsert Supabase) — supaya ketiganya
        # menerima persis df yang sama, sudah bersih dari NaN target.
        print("\n Membersihkan missing values sebelum output...")
        df = handle_missing_values(df)

        # ── Save outputs ──────────────────────────────────────
        print("\n Menyimpan output...")

        # Simpan master dataset (parquet)
        df.to_parquet(master_path, index=False)
        print(f"  ✓ master_dataset_clean.parquet ({len(df)} baris)")

        # Simpan predictions CSV
        # PREDICTION_OUTPUT_COLUMNS adalah single source of truth — dipakai sama
        # persis untuk CSV maupun untuk data yang dikirim ke Supabase, supaya
        # keduanya selalu identik.
        missing_pred_cols = [c for c in PREDICTION_OUTPUT_COLUMNS if c not in df.columns]
        if missing_pred_cols:
            print(f"  ⚠  Kolom hilang dari df, tidak akan ada di predictions_final.csv: "
                  f"{missing_pred_cols}")

        pred_cols_avail = [c for c in PREDICTION_OUTPUT_COLUMNS if c in df.columns]
        df[pred_cols_avail].to_csv(pred_path, index=False)
        print(f"  ✓ predictions_final.csv ({len(df)} baris)")

        # ── Kirim predictions ke Supabase (Prediction Storage) ─
        # CSV tetap ditulis seperti sebelumnya (kompatibilitas dashboard lama).
        # Setelah CSV berhasil dibuat, data yang sama (pred_cols_avail — identik
        # dengan yang ditulis ke CSV) di-upsert (batch) ke Supabase tabel
        # public.predictions. Kegagalan di sini TIDAK menggagalkan pipeline —
        # hanya dicetak sebagai warning. Hasilnya disimpan ke prediction_uploaded
        # untuk dicatat di pipeline log di bawah.
        if _PREDICTION_REPO_AVAILABLE:
            repo = PredictionRepository()
            result = repo.upsert_predictions(df[pred_cols_avail])
            prediction_uploaded = bool(result["ok"])
            if result["ok"]:
                print(f"  ✓ Supabase predictions upsert: {result['sent']} baris "
                      f"({result['batches']} batch)")
            else:
                print(f"  ⚠  Supabase predictions upsert dilewati/gagal: {result['error']}")
        else:
            print("  ⚠  Modul prediction_repository tidak terimport — "
                  "upsert Supabase dilewati.")

        # ── Kirim metadata ke Supabase (Metadata Storage) ─────
        # Dijalankan LANGSUNG SETELAH upsert_predictions di atas selesai
        # (berhasil ataupun gagal/skip — metadata tetap dicoba dikirim supaya
        # summary run selalu tercatat). Seluruh nilai diambil dari variabel
        # yang sudah ada di run_pipeline() ini, bukan hasil kalkulasi baru.
        # Field yang memang tidak tersedia di update_pipeline.py (training
        # terjadi di notebook, bukan di sini) diisi None apa adanya.
        # CATATAN: pipeline ini tidak membedakan "bulan data terakhir" vs
        # "bulan prediksi terakhir" sebagai dua nilai terpisah — df sudah
        # merge data + prediksi jadi satu, jadi keduanya bersumber dari
        # df['month'].max() yang sama (bulan terakhir di master dataset
        # setelah rebuild_features + predictions). Nilai ini juga disimpan
        # ke latest_month/prediction_rows untuk dipakai ulang di pipeline
        # log di bawah — bukan dihitung ulang.
        latest_month    = str(df['month'].max())
        prediction_rows = len(df)

        if _METADATA_REPO_AVAILABLE:
            metadata_repo = MetadataRepository()

            # Read latest trained model metadata
            model_version = None
            training_date = None
            model_meta_path = MDL_DIR / 'model_metadata.json'
            if model_meta_path.exists():
                try:
                    with open(model_meta_path) as f:
                        model_meta = json.load(f)
                    model_version = model_meta.get("model_version")
                    training_date = model_meta.get("training_date")
                except Exception as e:
                    print(f"  ⚠  Gagal membaca model_metadata.json: {e}")

            metadata = {
                "model_version": model_version,
                "training_date": training_date,
                "latest_prediction_month": latest_month,
                "latest_data_month": latest_month,
                "prediction_rows": prediction_rows,
                "pipeline_version": PIPELINE_VERSION,
                "dashboard_version": None,
                "notes": f"Auto-updated by update_pipeline.py pada "
                         f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            }
            meta_result = metadata_repo.upsert_metadata(metadata)
            metadata_uploaded = bool(meta_result["ok"])
            if meta_result["ok"]:
                print("  ✓ Supabase metadata upsert: berhasil")
            else:
                print(f"  ⚠  Supabase metadata upsert dilewati/gagal: {meta_result['error']}")
        else:
            print("  ⚠  Modul metadata_repository tidak terimport — "
                  "upsert metadata Supabase dilewati.")

        # ── Summary ────────────────────────────────────────────
        latest = df.iloc[-1]
        print("\n" + "═" * 60)
        print(f"  Pipeline selesai!")
        print(f"  Bulan terbaru  : {latest['month']}")
        print(f"  Crisis Score   : {latest['crisis_score_100']:.1f}/100")
        print(f"  Level          : {latest['crisis_level']}")
        print(f"  USD/IDR        : Rp {latest.get('usd_idr_avg', 0):,.0f}")
        print("═" * 60 + "\n")

        status = "SUCCESS"
        return df

    except SystemExit as e:
        # sys.exit(1) di guard "master_dataset_clean.parquet tidak
        # ditemukan" adalah SystemExit, BUKAN subclass Exception — kalau
        # tidak ditangkap terpisah, error_message akan tetap None
        # walaupun status sudah "FAILED" (default pesimis di atas).
        # Ditangkap eksplisit terpisah dari except Exception di bawah
        # supaya jelas dua jenis kegagalan ini dibedakan.
        # str(e) dari SystemExit hanya berupa exit code (mis. "1") —
        # tidak informatif di tabel pipeline_logs. Dibungkus dengan label
        # supaya histori log langsung terbaca tanpa perlu menebak artinya.
        error_message = f"Pipeline dihentikan (SystemExit: {e.code})"
        raise

    except Exception as e:
        error_message = str(e)
        raise

    finally:
        # ── Pipeline Log: catat histori run ini ke Supabase ──
        # Dijalankan di finally supaya SELALU tercoba, baik pipeline
        # sukses (status="SUCCESS") maupun gagal (status="FAILED",
        # error_message terisi). Kegagalan insert_log sendiri TIDAK
        # menggagalkan/menutupi exception asli pipeline (exception asli
        # tetap di-raise ulang di blok except di atas) — hanya dicetak
        # sebagai warning, konsisten dengan pola Prediction/Metadata di atas.
        # finished_at juga pakai UTC, konsisten dengan started_at, supaya
        # duration_seconds tetap benar terlepas timezone server.
        finished_at       = datetime.now(timezone.utc)
        duration_seconds  = (finished_at - started_at).total_seconds()

        if _PIPELINE_LOG_REPO_AVAILABLE:
            log_repo = PipelineLogRepository()
            log_data = {
                "run_id": run_id,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_seconds": duration_seconds,
                "status": status,
                "latest_month": latest_month,
                "prediction_rows": prediction_rows,
                "prediction_uploaded": prediction_uploaded,
                "metadata_uploaded": metadata_uploaded,
                "pipeline_version": PIPELINE_VERSION,
                "error_message": error_message,
            }
            log_result = log_repo.insert_log(log_data)
            if log_result["ok"]:
                print("  ✓ Supabase pipeline log insert: berhasil")
            else:
                print(f"  ⚠  Supabase pipeline log insert dilewati/gagal: {log_result['error']}")
        else:
            print("  ⚠  Modul pipeline_log_repository tidak terimport — "
                  "insert log Supabase dilewati.")


if __name__ == '__main__':
    run_pipeline()
