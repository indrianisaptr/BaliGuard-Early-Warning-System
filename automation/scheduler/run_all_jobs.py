"""
automation/scheduler/run_all_jobs.py — BaliGuard Automation: Monthly Orchestrator

Orchestrator utama automation BaliGuard. File ini TIDAK melakukan fetch,
validation, cleaning, feature engineering, prediction, maupun upload
Supabase apa pun secara langsung — semua logic itu tetap sepenuhnya
menjadi tanggung jawab run_job.py (per-source automation) dan
update_pipeline.py (rebuild feature + prediction + upload). File ini
hanya memanggil keduanya sebagai subprocess terpisah, dalam urutan
tetap, dan menentukan exit code akhir.

Alur:
    START
      -> loop JOBS -> jalankan run_job.py <job> satu per satu
         (job gagal -> warning, tetap lanjut ke job berikutnya
          maupun ke update_pipeline.py)
      -> jalankan update_pipeline.py
         (gagal -> error, exception di-raise ulang, exit code non-zero)
    SELESAI

Cara pakai:
    python -m automation.scheduler.run_all_jobs
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Path config ──────────────────────────────────────────────
# File ini ada di automation/scheduler/run_all_jobs.py, jadi:
#   parents[0] = automation/scheduler
#   parents[1] = automation
#   parents[2] = project root (tempat update_pipeline.py berada)
# Dipakai sebagai cwd untuk kedua subprocess supaya script tetap
# jalan benar dari folder mana pun script ini dipanggil.
THIS_FILE     = Path(__file__).resolve()
PROJECT_ROOT  = THIS_FILE.parents[2]
UPDATE_PIPELINE_PATH = PROJECT_ROOT / "update_pipeline.py"

# ── Daftar job automation (per-source) ───────────────────────
# Tambah job baru di sini saja — loop di run_all_jobs() otomatis
# menjalankan semuanya tanpa perlu ubah logika utama.
JOBS = [
    "usd_idr",
]

# Total step = semua job automation + 1 step Update Pipeline.
# Dihitung sekali di sini (bukan `len(JOBS)` di dalam loop, bukan
# `total + 1` manual di step Update Pipeline) supaya progress counter
# `[i/TOTAL_STEPS]` selalu konsisten walau JOBS bertambah nanti.
TOTAL_STEPS = len(JOBS) + 1


def _print_header(title: str) -> None:
    print("=" * 40)
    print(f" {title}")
    print("=" * 40)


def run_single_job(job_name: str) -> bool:
    """
    Jalankan satu automation job lewat run_job.py sebagai subprocess.

    run_job.py TIDAK diubah dan TIDAK diimport langsung — dipanggil
    sebagai module terpisah (`python -m automation.scheduler.run_job`)
    supaya proses fetch/validate/clean/staging job ini terisolasi dari
    proses orchestrator (kalau job ini crash, orchestrator tetap hidup).

    Return:
        True  -> job sukses (exit code 0)
        False -> job gagal (exit code != 0) — TIDAK melempar exception,
                 karena kegagalan satu job tidak boleh menghentikan
                 job lain maupun update_pipeline.py.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "automation.scheduler.run_job", job_name],
            cwd=PROJECT_ROOT,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ gagal (exit code {e.returncode})")
        print("  pipeline tetap dilanjutkan")
        return False


def run_update_pipeline() -> None:
    """
    Jalankan update_pipeline.py sebagai subprocess.

    update_pipeline.py TIDAK diubah dan TIDAK diimport langsung —
    dipanggil sebagai script terpisah supaya proses rebuild feature +
    prediction + upload Supabase-nya berjalan di process sendiri,
    konsisten dengan run_single_job().

    check=True membuat subprocess.run melempar CalledProcessError kalau
    exit code != 0. Exception ini SENGAJA tidak ditangkap di sini —
    dibiarkan naik ke caller (run_all_jobs) supaya scheduler ini juga
    gagal (exit code non-zero), sesuai requirement.
    """
    subprocess.run(
        [sys.executable, str(UPDATE_PIPELINE_PATH)],
        cwd=PROJECT_ROOT,
        check=True,
    )


def _print_summary(
    jobs_success: int,
    jobs_failed: int,
    pipeline_status: str,
    started_at: datetime,
    finished_at: datetime,
) -> None:
    """
    Cetak ringkasan akhir run: jumlah job automation berhasil/gagal,
    status Update Pipeline, serta waktu mulai/selesai dan total durasi.

    "Automation jobs" SENGAJA hanya menghitung job di JOBS (usd_idr,
    dst) — bukan gabungan job + Update Pipeline — karena Update
    Pipeline statusnya sudah ditampilkan terpisah lewat baris
    "Pipeline". Label ini murni supaya tidak ada yang mengira Update
    Pipeline belum terhitung; jumlahnya sendiri tidak berubah.

    Dipanggil baik saat run_all_jobs() sukses maupun saat
    update_pipeline gagal (sebelum exception di-raise ulang), supaya
    ringkasan tetap muncul di kedua kondisi.
    """
    duration_seconds = (finished_at - started_at).total_seconds()

    print("=" * 40)
    print()
    print(" Automation Finished")
    print()
    print(f" Jobs berhasil    : {jobs_success}")
    print(f" Jobs gagal       : {jobs_failed}")
    print(f" Automation jobs  : {jobs_success + jobs_failed}")
    print()
    print(f" Pipeline         : {pipeline_status}")
    print()
    print(" Started At")
    print(f" {started_at.isoformat()}")
    print()
    print(" Finished At")
    print(f" {finished_at.isoformat()}")
    print()
    print(" Total Duration")
    print(f" {duration_seconds:.2f} seconds")
    print()
    print("=" * 40)


def run_all_jobs() -> None:
    """
    Orchestrate seluruh siklus automation bulanan BaliGuard.

    Urutan:
      1. Jalankan semua job di JOBS satu per satu (loop, bukan hardcode).
         Job gagal -> warning, lanjut ke job berikutnya.
      2. Jalankan update_pipeline.py.
         Gagal -> exception di-raise ulang, tidak ditangkap di sini,
         supaya exit code proses ini non-zero.
    """
    started_at = datetime.now(timezone.utc)

    _print_header("BaliGuard Monthly Automation")
    print()

    jobs_success = 0
    jobs_failed = 0
    for i, job_name in enumerate(JOBS, start=1):
        print(f"[{i}/{TOTAL_STEPS}] {job_name} Automation")
        success = run_single_job(job_name)
        if success:
            print("✓ selesai")
            jobs_success += 1
        else:
            jobs_failed += 1
        print("-" * 40)
        print()

    print(f"[{TOTAL_STEPS}/{TOTAL_STEPS}] Update Pipeline")
    try:
        run_update_pipeline()
        print("✓ selesai")
        pipeline_status = "SUCCESS"
    except subprocess.CalledProcessError as e:
        print(f"✗ gagal (exit code {e.returncode})")
        pipeline_status = "FAILED"
        finished_at = datetime.now(timezone.utc)
        print()
        _print_summary(jobs_success, jobs_failed, pipeline_status, started_at, finished_at)
        raise
    print()

    finished_at = datetime.now(timezone.utc)
    _print_summary(jobs_success, jobs_failed, pipeline_status, started_at, finished_at)


def main() -> None:
    try:
        run_all_jobs()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode or 1)


if __name__ == "__main__":
    main()
