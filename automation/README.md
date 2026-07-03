# BaliGuard Automation

## Overview

The `automation/` folder is responsible for **data ingestion** — everything that happens *before* the Machine Learning pipeline runs. It is intentionally kept separate from the ML pipeline (`update_pipeline.py` / `retrain_model.py`) so that each layer has a single, well-defined responsibility.

Automation handles:

- **Fetching** raw data from external sources (e.g. USD/IDR exchange rate)
- **Validation** of incoming data (schema, ranges, duplicates, missing values, dates)
- **Light cleaning** before data is considered trustworthy
- **Staging** — writing validated data to a well-known location the ML pipeline can read from

`update_pipeline.py`, in contrast, **only reads from staging**. It never calls an external API directly. This separation means the ML pipeline can be reasoned about, tested, and rerun without any dependency on network access or third-party API availability.

```
External API
      │
      ▼
 Fetch Module
      │
      ▼
 Validation
      │
      ▼
 Cleaning
      │
      ▼
 Staging JSON
      │
      ▼
 update_pipeline.py
      │
      ▼
 Retrain Model
```

---

## Architecture Philosophy

| Layer | Responsibility |
|--------|----------------|
| Automation | Acquire, validate, clean, and stage external data |
| Pipeline | Feature engineering, crisis scoring, and prediction |
| Retraining | Update ML models using the latest processed dataset |
| Dashboard | Visualize predictions and operational insights |

Each layer is intentionally isolated so that changes in one component do not require modifications in another.

---

## Folder Structure

```
automation/
├── config/
│   ├── settings.py          # Global automation settings
│   └── sources.yaml         # Declarative list of external data sources
├── fetch/
│   └── usd_idr.py           # Fetches USD/IDR exchange rate data
├── scheduler/
│   ├── run_job.py           # Runs a single automation job
│   └── run_all_jobs.py      # Orchestrates all registered jobs in sequence
├── storage/
│   └── staging_writer.py    # Reads/writes staged data (JSON)
├── validation/
│   └── validate_usd_idr.py  # Validation rules for USD/IDR data
├── data/
│   ├── cache/                # Local cache for fetch operations
│   └── staging/               # Validated data, ready for the ML pipeline
└── logs/                      # Automation run logs
```

| Folder | Responsibility |
|---|---|
| `config/` | Central place to declare data sources and automation-wide settings, without touching job logic |
| `fetch/` | Talks to external APIs and pulls raw data |
| `scheduler/` | Orchestrates the fetch → validate → clean → stage sequence, for one job or all jobs |
| `storage/` | Abstracts how staged data is read and written |
| `validation/` | Enforces data quality rules before anything is staged |
| `data/cache/` | Temporary/intermediate storage used during fetch operations |
| `data/staging/` | The **only** interface between automation and the ML pipeline |
| `logs/` | Execution logs for troubleshooting and auditing automation runs |

---

## Components

### `fetch/`

Responsible for retrieving raw data from external sources — currently the USD/IDR exchange rate (`usd_idr.py`). Fetch modules are expected to know nothing about the ML pipeline; their only output is raw data handed off to validation.

### `validation/`

Every dataset fetched by automation is checked before it is trusted. Validation covers:

- **Missing values** — required fields must be present
- **Duplicates** — no duplicate records for the same period
- **Date correctness** — dates must be well-formed and fall within an expected range
- **Value range** — numeric values must fall within sane bounds (e.g. exchange rate cannot be negative or absurdly large)
- **Schema** — the shape of the data must match what downstream staging expects

Data that fails validation is not written to staging.

### `storage/`

Handles writing validated, cleaned data to the staging layer as JSON files, keyed by data type and period. Example location:

```
automation/data/staging/usd_idr/YYYY-MM.json
```

> **Important:** the ML pipeline (`update_pipeline.py`) only ever *reads* from `automation/data/staging/`. It never calls `fetch/` or any external API directly — staging is the sole handoff point between automation and machine learning.

### `scheduler/`

Coordinates the end-to-end automation sequence for a job:

```
Fetch
  ↓
Validate
  ↓
Clean
  ↓
Write Staging
```

`run_job.py` runs a single job through this sequence; `run_all_jobs.py` runs every registered job (as configured in `config/sources.yaml`) in one pass — this is the entry point used by the daily GitHub Actions workflow.

### `config/`

Declares external data sources and their settings (e.g. endpoints, expected schema, validation thresholds) in `sources.yaml`, plus shared automation settings in `settings.py`. This keeps source-specific configuration out of job logic, so adding a new data source does not require modifying scheduler or validation code.

### `logs/`

Stores execution logs produced by automation runs, useful for auditing what was fetched, validated, and staged — and for diagnosing failures without needing to re-run a job.

---

## Failure Handling

If a fetch or validation step fails:

- invalid data is never written into staging;
- downstream ML pipelines continue using the latest valid staged data;
- execution logs are recorded for troubleshooting;
- GitHub Actions reports the failure through workflow status.

This prevents corrupted external data from propagating into the prediction pipeline.

---

## Daily Workflow

Defined in `.github/workflows/daily_update.yml`, this workflow runs automation on a daily schedule to keep staging data fresh.

```
GitHub Actions
      │
      ▼
run_all_jobs.py
      │
      ▼
Fetch USD/IDR
      │
      ▼
Validation
      │
      ▼
Cleaning
      │
      ▼
Write Staging
      │
      ▼
Commit if there are changes
```

---

## Monthly Workflow

Defined in `.github/workflows/monthly_retrain.yml`, this workflow runs the full monthly ML cycle, in sequence.

```
update_pipeline.py
      │
      ▼
Feature Engineering
      │
      ▼
Crisis Score
      │
      ▼
Predictions
      │
      ▼
retrain_model.py
      │
      ▼
Train New Models
      │
      ▼
Update predictions_final.csv
      │
      ▼
Update Models
      │
      ▼
Push Repository
      │
      ▼
Update Supabase
```

---

## Manual Execution

Automation and the ML pipeline can each be run manually from the project root:

```bash
# Run all automation jobs (fetch → validate → clean → stage)
python -m automation.scheduler.run_all_jobs

# Run the monthly ML update pipeline (reads staging, rebuilds features, scores, predicts)
python update_pipeline.py

# Retrain the models on the latest master dataset
python retrain_model.py
```

---

## End-to-End Data Flow

```
External API
      │
      ▼
automation/fetch
      │
      ▼
validation
      │
      ▼
staging
      │
      ▼
update_pipeline.py
      │
      ▼
master_dataset_clean.parquet
      │
      ▼
Random Forest
Isolation Forest
      │
      ▼
predictions_final.csv
      │
      ▼
Supabase
      │
      ▼
Streamlit Dashboard
```

---

## Data Lifecycle

```
External API
        │
        ▼
Raw Data
        │
        ▼
Validated Data
        │
        ▼
Staged Data
        │
        ▼
Processed Dataset
        │
        ▼
Machine Learning
        │
        ▼
Predictions
        │
        ▼
Dashboard
```

While the *End-to-End Data Flow* above maps to concrete files and scripts, this diagram describes the same journey from the perspective of the **data's lifecycle** — the state it moves through, independent of which module happens to touch it.

---

## Scheduler Summary

| Workflow | Frequency | Purpose |
|----------|-----------|----------|
| Daily Automation | Every day | Fetch USD/IDR and update staging |
| Monthly ML Pipeline | Monthly | Update features, retrain models, refresh predictions |

---

> **Important**
>
> Automation never modifies machine learning models.
> The only responsibility of automation is to keep the staging layer up to date.
>
> Model updates are handled exclusively by the monthly ML pipeline.

---

## Design Principles

- **Automation is independent from Machine Learning.** Each layer can be developed, tested, and run without depending on the other's internal implementation.
- **Machine Learning never fetches external APIs directly.** `update_pipeline.py` and `retrain_model.py` only read from local files (staging, processed data, master dataset).
- **Every external dataset must pass through the staging layer.** There is no shortcut from `fetch/` directly into the ML pipeline.
- **Automation jobs can run independently.** Each job in `scheduler/` can be triggered on its own via `run_job.py`, without requiring the full pipeline.
- **Retraining only occurs after the monthly pipeline finishes.** `retrain_model.py` is only meaningful once `update_pipeline.py` has produced an updated master dataset.
- **GitHub Actions acts as the production scheduler.** Daily and monthly workflows are the source of truth for when automation and ML jobs run in production — not ad-hoc manual execution.

---

## Future Extensions

The automation layer is designed to grow incrementally without restructuring existing components:

- Additional data sources beyond USD/IDR (e.g. inflation, tourism statistics feeds)
- More automation jobs registered in `scheduler/` and `config/sources.yaml`
- Weather API integration for climate-related risk signals
- Google Trends automation for tourism demand signals
- GDELT automation for event-driven crisis signals
- Monitoring & alerting on automation job failures (e.g. notify on repeated fetch or validation failures)
- Automatic retraining triggers based on data drift or significant new data volume, rather than a fixed monthly schedule

---

*This document describes the automation layer as currently implemented. It is intended to let a new developer understand the full automation workflow by reading this file alone.*
