-- ============================================================================
-- BaliGuard — Supabase Migration 001 (REVISI)
-- Scope  : narratives, metadata
-- Source : BALIGUARD_DATA_CONTRACT_SPECIFICATION.md (Bagian 3 & 5), v1.0
--          + revisi konsistensi dashboard existing:
--            - report_type diperluas: + 'predict', + 'swot'
--            - kolom format_style ('paragraf' | 'poin') ditambahkan,
--              bagian dari cache key NarrativeRepository:
--              (month, report_type, model_used, format_style)
-- Catatan: predictions & master_dataset BELUM dibuat di migration ini.
--          FK narratives.month -> predictions.month TIDAK diimplementasikan
--          sekarang (tabel induk belum ada) — akan ditambahkan via migration
--          terpisah (mis. 003_add_predictions_fk.sql) setelah tabel
--          predictions dibuat, supaya tidak ada FK menggantung.
-- PENTING: jika tabel narratives/metadata sudah pernah dibuat dari versi
--          001 sebelumnya (tanpa format_style), jalankan dulu:
--            drop table if exists public.narratives cascade;
--          sebelum menjalankan file ini ulang dari awal — supaya skema
--          final konsisten dengan definisi di bawah.
-- Jalankan di: Supabase SQL Editor, satu kali, berurutan dari atas ke bawah.
-- ============================================================================

-- ── Extensions ──────────────────────────────────────────────────────────────
create extension if not exists "pgcrypto"; -- untuk gen_random_uuid()

-- ============================================================================
-- 1. TABLE: metadata
--    Single source of truth versi model ML (Bagian 5 kontrak).
--    Append-only kecuali kolom is_active.
-- ============================================================================

create table if not exists public.metadata (
    model_version                 text primary key,
    artifact_bucket_path_scaler   text not null,
    artifact_bucket_path_rf       text not null,
    artifact_bucket_path_iso      text not null,
    artifact_bucket_path_le       text not null,
    trained_at                    timestamptz not null,
    training_data_range_start     text not null,
    training_data_range_end       text not null,
    is_active                     boolean not null default false,
    feature_set_version           text,
    notes                         text,

    -- ── Constraint: format month YYYY-MM (Bagian 7 kontrak lintas dataset) ──
    constraint chk_metadata_range_start_format
        check (training_data_range_start ~ '^\d{4}-(0[1-9]|1[0-2])$'),
    constraint chk_metadata_range_end_format
        check (training_data_range_end ~ '^\d{4}-(0[1-9]|1[0-2])$'),

    -- ── Constraint: range_start <= range_end (Bagian 5.6) ──
    constraint chk_metadata_range_order
        check (training_data_range_start <= training_data_range_end)
);

comment on table public.metadata is
    'Single source of truth versi model ML aktif/historis. Append-only kecuali is_active. Lihat Data Contract Bagian 5.';

-- ── Partial unique index: hanya boleh ada SATU baris is_active = true ───────
-- Ini implementasi enforced dari Bagian 5.6: "Hanya boleh ada satu baris
-- dengan is_active=true pada satu waktu". Insert/update kedua baris jadi
-- is_active=true akan ditolak otomatis oleh database.
create unique index if not exists uq_metadata_single_active
    on public.metadata (is_active)
    where is_active = true;

-- ── Index pendukung query umum ───────────────────────────────────────────────
create index if not exists idx_metadata_trained_at
    on public.metadata (trained_at desc);

-- ── Trigger: kolom artifact_bucket_path_* wajib lengkap sebelum is_active=true
--    (Bagian 5.6: "model tidak boleh aktif tanpa artifact lengkap")
create or replace function public.fn_metadata_guard_active()
returns trigger
language plpgsql
as $$
begin
    if new.is_active is true then
        if new.artifact_bucket_path_scaler is null
           or new.artifact_bucket_path_rf is null
           or new.artifact_bucket_path_iso is null
           or new.artifact_bucket_path_le is null
        then
            raise exception
                'metadata.is_active tidak boleh true: artifact_bucket_path_* belum lengkap (model_version=%)',
                new.model_version;
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_metadata_guard_active on public.metadata;
create trigger trg_metadata_guard_active
    before insert or update on public.metadata
    for each row
    execute function public.fn_metadata_guard_active();

-- ── Trigger: kolom selain is_active bersifat append-only (immutable) ────────
-- (Bagian 5.4: "append-only untuk semua kolom kecuali is_active")
create or replace function public.fn_metadata_guard_immutable()
returns trigger
language plpgsql
as $$
begin
    if new.artifact_bucket_path_scaler   is distinct from old.artifact_bucket_path_scaler
       or new.artifact_bucket_path_rf    is distinct from old.artifact_bucket_path_rf
       or new.artifact_bucket_path_iso   is distinct from old.artifact_bucket_path_iso
       or new.artifact_bucket_path_le    is distinct from old.artifact_bucket_path_le
       or new.trained_at                 is distinct from old.trained_at
       or new.training_data_range_start  is distinct from old.training_data_range_start
       or new.training_data_range_end    is distinct from old.training_data_range_end
       or new.feature_set_version        is distinct from old.feature_set_version
       or new.notes                      is distinct from old.notes
    then
        raise exception
            'metadata baris % bersifat append-only: hanya kolom is_active yang boleh diupdate',
            old.model_version;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_metadata_guard_immutable on public.metadata;
create trigger trg_metadata_guard_immutable
    before update on public.metadata
    for each row
    execute function public.fn_metadata_guard_immutable();


-- ============================================================================
-- 2. TABLE: narratives
--    Narasi bahasa natural hasil Groq, immutable per baris (Bagian 3 kontrak).
--    FK ke predictions.month SENGAJA belum ditambahkan (lihat catatan atas).
-- ============================================================================

create table if not exists public.narratives (
    id                      uuid primary key default gen_random_uuid(),
    month                   text not null,
    report_type             text not null,
    format_style            text not null default 'paragraf',
    narrative_text          text not null,
    crisis_level_snapshot   text not null,
    tokens_used             integer,
    model_used              text not null,
    success                 boolean not null,
    error_message           text,
    generated_at            timestamptz not null default now(),
    generated_by            text not null,

    -- ── Constraint: format month YYYY-MM ──
    constraint chk_narratives_month_format
        check (month ~ '^\d{4}-(0[1-9]|1[0-2])$'),

    -- ── Constraint: enum report_type (Bagian 6, diperluas: predict & swot
    --    dipakai dashboard existing) ──
    constraint chk_narratives_report_type
        check (report_type in ('summary', 'alert', 'monthly', 'predict', 'swot')),

    -- ── Constraint: enum format_style (paragraf vs poin, dipakai dashboard
    --    & sebagai bagian cache key NarrativeRepository) ──
    constraint chk_narratives_format_style
        check (format_style in ('paragraf', 'poin')),

    -- ── Constraint: enum crisis_level_snapshot (Bagian 6) ──
    constraint chk_narratives_crisis_level
        check (crisis_level_snapshot in ('AMAN', 'WASPADA', 'SIAGA', 'KRISIS')),

    -- ── Constraint: enum generated_by (Bagian 6) ──
    constraint chk_narratives_generated_by
        check (generated_by in ('user', 'scheduler')),

    -- ── Constraint: tokens_used non-negatif jika diisi ──
    constraint chk_narratives_tokens_nonneg
        check (tokens_used is null or tokens_used >= 0),

    -- ── Constraint: narrative_text tidak boleh kosong jika success=true
    --    (Bagian 3.6) ──
    constraint chk_narratives_text_when_success
        check (success = false or length(trim(narrative_text)) > 0),

    -- ── Constraint: error_message wajib ada jika success=false, wajib null
    --    jika success=true (Bagian 3.6) ──
    constraint chk_narratives_error_consistency
        check (
            (success = false and error_message is not null and length(trim(error_message)) > 0)
            or
            (success = true and error_message is null)
        )
);

comment on table public.narratives is
    'Narasi bahasa natural hasil Groq berdasarkan predictions. Immutable per baris — generate ulang = insert baru. Lihat Data Contract Bagian 3.';

-- ── Index: dashboard mengambil versi terbaru per (month, report_type) ───────
-- (Bagian 8: "Dashboard mengharapkan narratives ... terurut berdasarkan
-- generated_at agar bisa mengambil versi terbaru per (month, report_type)")
create index if not exists idx_narratives_month_reporttype_generatedat
    on public.narratives (month, report_type, generated_at desc);

-- Cache key NarrativeRepository: (month, report_type, model_used, format_style)
create index if not exists idx_narratives_cache_key
    on public.narratives (month, report_type, model_used, format_style, generated_at desc);

create index if not exists idx_narratives_generated_at
    on public.narratives (generated_at desc);

create index if not exists idx_narratives_success
    on public.narratives (success)
    where success = false; -- mempercepat query monitoring error


-- ============================================================================
-- 3. ROW LEVEL SECURITY & POLICIES
--    Pola akses (sesuai SAD): writer = service_role (Pipeline/Narrative
--    Service jalan dari backend dengan service key), reader = authenticated
--    user dashboard (Streamlit pakai anon/authenticated key, read-only).
--    Sesuaikan nama role bila Dashboard memakai skema auth berbeda.
-- ============================================================================

alter table public.metadata   enable row level security;
alter table public.narratives enable row level security;

-- ── metadata: read-only untuk anon & authenticated, full akses service_role ──
drop policy if exists "metadata_select_public" on public.metadata;
create policy "metadata_select_public"
    on public.metadata
    for select
    to anon, authenticated
    using (true);

drop policy if exists "metadata_write_service_role" on public.metadata;
create policy "metadata_write_service_role"
    on public.metadata
    for all
    to service_role
    using (true)
    with check (true);

-- ── narratives: read-only untuk anon & authenticated, full akses service_role ─
drop policy if exists "narratives_select_public" on public.narratives;
create policy "narratives_select_public"
    on public.narratives
    for select
    to anon, authenticated
    using (true);

drop policy if exists "narratives_write_service_role" on public.narratives;
create policy "narratives_write_service_role"
    on public.narratives
    for all
    to service_role
    using (true)
    with check (true);


-- ============================================================================
-- 4. SEED MINIMAL
--    Hanya satu baris metadata placeholder supaya FK model_version di
--    predictions (nanti) punya target valid saat development awal, DAN
--    supaya constraint "harus ada artifact lengkap sebelum is_active=true"
--    bisa diverifikasi manual. is_active sengaja FALSE — aktivasi model
--    sungguhan dilakukan oleh proses retrain, bukan seed.
-- ============================================================================

insert into public.metadata (
    model_version,
    artifact_bucket_path_scaler,
    artifact_bucket_path_rf,
    artifact_bucket_path_iso,
    artifact_bucket_path_le,
    trained_at,
    training_data_range_start,
    training_data_range_end,
    is_active,
    feature_set_version,
    notes
)
values (
    'seed_placeholder_v0',
    'models/seed/scaler.pkl',
    'models/seed/rf.pkl',
    'models/seed/iso.pkl',
    'models/seed/le.pkl',
    now(),
    '2017-01',
    '2017-01',
    false,
    'seed',
    'Baris seed development — bukan model produksi. Ganti setelah retrain pertama selesai.'
)
on conflict (model_version) do nothing;

-- ============================================================================
-- Selesai. Verifikasi cepat (boleh dijalankan manual di SQL Editor):
--   select * from public.metadata;
--   select * from public.narratives;
--   select * from pg_policies where tablename in ('metadata', 'narratives');
-- ============================================================================
