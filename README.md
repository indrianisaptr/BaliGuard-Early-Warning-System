# BaliGuard

<!--
Badge GitHub Actions sengaja belum dipasang di sini. Rencana: tambahkan
setelah beberapa kali run sukses di production (daily_update.yml &
monthly_retrain.yml), supaya badge yang tampil di halaman depan repo
selalu hijau — badge merah lebih buruk daripada tidak ada badge.

![Daily Automation](https://github.com/<owner>/<repo>/actions/workflows/daily_update.yml/badge.svg)
![Monthly ML Pipeline](https://github.com/<owner>/<repo>/actions/workflows/monthly_retrain.yml/badge.svg)
-->

**AI-powered Early Warning System for Bali Tourism Crisis Monitoring.**

BaliGuard is a machine learning system that continuously scores the health of Bali's tourism sector — from visitor arrivals and exchange rate pressure to sentiment and external shocks (disasters, global events) — and classifies each month into one of four crisis levels (**AMAN → WASPADA → SIAGA → KRISIS**). Predictions are served through an interactive Streamlit dashboard with AI-generated narrative reports, backed by a production-style pipeline that runs on a schedule via GitHub Actions.

- 🤖 **Machine Learning** — Random Forest classification + Isolation Forest anomaly detection
- ⚙️ **Automation** — scheduled data ingestion, fully decoupled from the ML pipeline
- 📊 **Streamlit Dashboard** — 5-page interactive interface with KPIs, forecasts, and scenario simulation
- 🔁 **GitHub Actions** — production scheduler for daily data fetch and monthly retraining
- ☁️ **Supabase** — persistent storage for predictions, metadata, narratives, and pipeline run logs
- 🚨 **Early Warning System** — four-level crisis classification designed to support decision-making, not just forecasting

---

## Project Status

| Component      | Status              |
| -------------- | ------------------- |
| Dashboard      | ✅ Production Ready |
| ML Pipeline    | ✅ Production Ready |
| Automation     | ✅ Production Ready |
| GitHub Actions | ✅ Active           |
| Supabase       | ✅ Connected        |

---

## Architecture Overview

```
External Data
      │
      ▼
  Automation
      │
      ▼
Feature Engineering
      │
      ▼
Machine Learning
      │
      ▼
  Predictions
      │
      ▼
   Supabase
      │
      ▼
Streamlit Dashboard
```

The system is split into independent layers on purpose: **automation** only fetches and stages external data, the **ML pipeline** only reads that staged data (never calls external APIs itself), and the **dashboard** only reads predictions — each layer can be changed, tested, or re-run without touching the others.

---

## Key Features

| Feature                                | Description                                                                                                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Automated Data Collection**    | `automation/` fetches external data (e.g. USD/IDR exchange rate), validates it, and writes it to a staging layer — independent of the ML pipeline |
| **Feature Engineering**          | Rebuilds growth rates, rolling statistics, z-scores, volatility, seasonality, and external risk indicators from raw sources                          |
| **Crisis Score**                 | A weighted composite score (tourism, economy, sentiment, external risk components) mapped to four severity levels                                    |
| **Random Forest Classification** | Predicts`crisis_level` (AMAN / WASPADA / SIAGA / KRISIS) with per-class probabilities                                                              |
| **Isolation Forest**             | Unsupervised anomaly detection as a supporting signal alongside crisis classification                                                                |
| **Automated Retraining**         | `retrain_model.py` rebuilds the scaler and retrains both models on the latest processed dataset                                                    |
| **GitHub Actions Scheduler**     | Daily automation run + monthly pipeline/retraining run, without manual intervention                                                                  |
| **Streamlit Dashboard**          | Multi-page interface: Overview & Timeline, Detailed Analysis, Sentiment, Prediction & Projection, AI Narrative                                       |
| **LLM Narrative**                | AI-generated situation reports (summary / alert / monthly, paragraph or bullet format) via Groq LLM                                                  |
| **Supabase Integration**         | Predictions, metadata, pipeline run logs, and narrative history are persisted to Supabase                                                            |

---

## Technology Stack

| Category           | Technology                                     |
| ------------------ | ---------------------------------------------- |
| Language           | Python                                         |
| Data Processing    | Pandas, NumPy                                  |
| Machine Learning   | Scikit-Learn (Random Forest, Isolation Forest) |
| Model Persistence  | Joblib, Parquet                                |
| Dashboard          | Streamlit, Plotly                              |
| LLM / Narrative    | Groq API                                       |
| Backend / Storage  | Supabase                                       |
| Automation         | Python (`requests`, `PyYAML`)              |
| CI/CD & Scheduling | GitHub Actions                                 |
| Configuration      | python-dotenv                                  |

---

## Repository Structure

```
notebooks/           # NB01–NB06: EDA → preprocessing → sentiment → feature engineering → modeling → LLM narrative
automation/           # Data ingestion layer: fetch, validate, stage external data (see automation/README.md)
models/               # Trained model artifacts (.pkl): Random Forest, Isolation Forest, scaler, label encoder
data/                 # raw / processed / final datasets produced by the pipeline
dashboard.py          # Streamlit dashboard entry point
update_pipeline.py    # Monthly ML update: reads staging, rebuilds features, computes crisis score, predicts
retrain_model.py      # Retrains Random Forest & Isolation Forest on the latest processed dataset
src/                  # Dashboard source: config, shared context builder, pages, services, components
docs/                 # Additional project documentation
```

---

## Machine Learning Pipeline

```
Raw Data
      │
      ▼
Feature Engineering
      │
      ▼
Crisis Score
      │
      ▼
   Training
      │
      ▼
  Prediction
      │
      ▼
  Dashboard
```

The pipeline builds a monthly time series of tourism, economic, sentiment, and external risk features, computes a weighted crisis score, and feeds those features into a Random Forest classifier (crisis level) and an Isolation Forest (anomaly signal). Results are written to `predictions_final.csv` / `master_dataset_clean.parquet` and consumed by the dashboard.

---

## Automation

The `automation/` folder is a self-contained data ingestion layer, fully decoupled from the ML pipeline — it only fetches, validates, and stages external data; `update_pipeline.py` never calls an external API directly.

| Workflow            | Schedule | Purpose                                          |
| ------------------- | -------- | ------------------------------------------------ |
| Daily Automation    | Daily    | Fetch USD/IDR → Validation → Staging           |
| Monthly ML Pipeline | Monthly  | Update Pipeline → Retraining → Update Supabase |

See [`automation/README.md`](automation/README.md) for complete automation documentation.

---

## GitHub Actions

| Workflow           | Trigger  | Purpose                      |
| ------------------ | -------- | ---------------------------- |
| Daily Automation   | Schedule | Fetch USD/IDR                |
| Monthly Retraining | Schedule | Update Pipeline + Retraining |

Both workflows can also be triggered manually from the GitHub Actions tab.

---

## Getting Started

**Clone the repository**

```bash
git clone <repository-url>
cd MultiMetode
```

**Install dependencies**

```bash
# Automation layer (fetch, validation, staging)
pip install -r requirements.txt

# ML pipeline (feature engineering, crisis score, modeling)
pip install -r requirements-pipeline.txt

# Dashboard
pip install streamlit plotly groq pyarrow joblib python-dotenv
```

**Run the dashboard**

```bash
streamlit run dashboard.py
```

**Run the ML update pipeline**

```bash
python update_pipeline.py
```

**Run model retraining**

```bash
python retrain_model.py
```

---

## Project Workflow

```
External Sources
      │
      ▼
  Automation
      │
      ▼
    Staging
      │
      ▼
Update Pipeline
      │
      ▼
   Retraining
      │
      ▼
  Predictions
      │
      ▼
   Dashboard
```

---

## Future Improvements

- [ ] Additional external data sources beyond USD/IDR
- [ ] Weather API integration for climate-related risk signals
- [ ] Additional ML models for comparison/ensembling
- [ ] Monitoring for automation and pipeline job health
- [ ] Alerting on repeated fetch, validation, or pipeline failures
- [ ] CI/CD enhancements (e.g. automated tests before deployment)

---

## Project Highlights

✓ Automated data ingestion, decoupled from Machine Learning

✓ Feature engineering pipeline consistent with model training

✓ Machine Learning retraining pipeline (Random Forest + Isolation Forest)

✓ GitHub Actions automation for daily fetch and monthly retraining

✓ Multi-page Streamlit dashboard with AI-generated narrative reports

✓ Supabase integration for predictions, metadata, and pipeline history

---

## Documentation

| Document                                            | Description                                                                                                                        |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| [`automation/README.md`](automation/README.md)     | Full documentation of the automation layer: folder structure, components, daily/monthly workflows, design principles               |
| [`docs/`](docs/)                                   | Additional project documentation                                                                                                   |
| [`evaluation_baseline.md`](evaluation_baseline.md) | Baseline model evaluation metrics, recorded before retraining, used as the reference point for measuring future retraining results |
| `README.md`                                       | This document — project overview, architecture, features, and getting started guide                                               |

---

## License

This project is released under the [MIT License]().

See the [LICENSE](LICENSE) file for details.
