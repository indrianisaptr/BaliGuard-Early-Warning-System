-- ============================================================================
-- BaliGuard — Supabase Migration 002
-- Scope  : predictions (Prediction Storage)
-- Source : predictions_final.csv (audit: 208 baris, 31 kolom, month unik,
--          tanpa NaN, month range 2009-01 → 2026-04, crisis_level &
--          rf_predicted_level enum {AMAN, WASPADA, SIAGA, KRISIS}).
-- Catatan:
--   - predictions BUKAN append-only seperti narratives — setiap run
--     pipeline melakukan recompute fitur & ulang prediksi untuk SELURUH
--     histori (rebuild_features dipanggil atas seluruh df), sehingga nilai
--     untuk bulan yang sama bisa berubah antar run (mis. zscore, growth,
--     rolling window bergeser kalau ada revisi data BPS). Maka tabel ini
--     pakai UPSERT per month (PK = month), bukan insert-only.
--   - FK predictions.month <- narratives.month, dan FK predictions.model_version
--     -> metadata.model_version SENGAJA TIDAK ditambahkan di sini (scope chat
--     ini hanya Prediction Storage). Lihat catatan migration 001 — akan
--     ditambahkan terpisah jika diperlukan (mis. 003_add_predictions_fk.sql).
-- Jalankan di: Supabase SQL Editor, satu kali, setelah 001.
-- ============================================================================

-- ============================================================================
-- 1. TABLE: predictions
-- ============================================================================

create table if not exists public.predictions (
    month                       text primary key,

    -- ── Input features (BPS, kurs, sentimen) ──
    wisman                      bigint not null,
    tpk_bintang                 double precision not null,
    inflasi_processed           double precision not null,
    usd_idr_avg                 double precision not null,
    avg_sentiment_monthly       double precision not null,
    bali_share_pct              double precision not null,
    wisman_zscore                double precision not null,
    wisman_growth_mom           double precision not null,
    wisman_growth_yoy           double precision not null,

    -- ── Crisis score (rule-based, NB04) ──
    crisis_score_100            double precision not null,
    crisis_level                text not null,

    -- ── Random Forest output ──
    rf_predicted_level          text not null,
    rf_confidence                double precision not null,
    prob_aman                   double precision not null,
    prob_waspada                double precision not null,
    prob_siaga                  double precision not null,
    prob_krisis                 double precision not null,

    -- ── Isolation Forest output ──
    iso_anomaly                 integer not null,
    iso_score                   double precision not null,

    -- ── External / risk component scores ──
    gdelt_crisis_score           double precision not null,
    economic_risk_score          double precision not null,
    disaster_risk_score          double precision not null,
    external_risk_avg            double precision not null,
    physical_risk_score          double precision not null,
    media_risk_score             double precision not null,
    tourist_perception_score     double precision not null,
    external_risk_score          double precision not null,

    -- ── Tambahan / turunan ──
    wisman_recovery_pct         double precision not null,
    pct_negative_monthly        double precision not null,
    usd_volatility_3m           double precision not null,

    -- ── Audit kolom (bukan bagian predictions_final.csv, ditambahkan
    --    untuk kebutuhan storage — tidak mengubah skema CSV) ──
    model_version                text,
    upserted_at                  timestamptz not null default now(),

    -- ── Constraint: format month YYYY-MM (Bagian 7 kontrak, konsisten 001) ──
    constraint chk_predictions_month_format
        check (month ~ '^\d{4}-(0[1-9]|1[0-2])$'),

    -- ── Constraint: enum crisis_level & rf_predicted_level ──
    constraint chk_predictions_crisis_level
        check (crisis_level in ('AMAN', 'WASPADA', 'SIAGA', 'KRISIS')),
    constraint chk_predictions_rf_predicted_level
        check (rf_predicted_level in ('AMAN', 'WASPADA', 'SIAGA', 'KRISIS')),

    -- ── Constraint: iso_anomaly binary (0/1) ──
    constraint chk_predictions_iso_anomaly
        check (iso_anomaly in (0, 1)),

    -- ── Constraint: probabilitas dalam rentang [0, 1] ──
    constraint chk_predictions_probs_range
        check (
            prob_aman    between 0 and 1 and
            prob_waspada between 0 and 1 and
            prob_siaga   between 0 and 1 and
            prob_krisis  between 0 and 1
        ),

    -- ── Constraint: rf_confidence dalam rentang [0, 1] ──
    constraint chk_predictions_confidence_range
        check (rf_confidence between 0 and 1)
);

comment on table public.predictions is
    'Output prediksi pipeline ML per bulan (predictions_final.csv mirror). Mutable per month — di-upsert tiap run pipeline karena seluruh histori di-rebuild ulang. Lihat update_pipeline.py.';

-- ── Index pendukung query umum ───────────────────────────────────────────────
create index if not exists idx_predictions_crisis_level
    on public.predictions (crisis_level);

create index if not exists idx_predictions_month_desc
    on public.predictions (month desc);

create index if not exists idx_predictions_upserted_at
    on public.predictions (upserted_at desc);


-- ============================================================================
-- 2. ROW LEVEL SECURITY & POLICIES
--    Pola sama dengan 001: writer = service_role (pipeline), reader =
--    anon/authenticated (dashboard, read-only).
-- ============================================================================

alter table public.predictions enable row level security;

drop policy if exists "predictions_select_public" on public.predictions;
create policy "predictions_select_public"
    on public.predictions
    for select
    to anon, authenticated
    using (true);

drop policy if exists "predictions_write_service_role" on public.predictions;
create policy "predictions_write_service_role"
    on public.predictions
    for all
    to service_role
    using (true)
    with check (true);

-- ============================================================================
-- Selesai. Verifikasi cepat:
--   select count(*) from public.predictions;
--   select * from public.predictions order by month desc limit 5;
-- ============================================================================
