# GitHub Events Analytics Pipeline

An end-to-end data engineering and analytics project that ingests public GitHub Events API data, stores raw events locally, transforms the data using dbt, orchestrates the pipeline with Apache Airflow, and provides an interactive Streamlit analytics dashboard.

## 📌 Project Overview

This project demonstrates a production-style **ELT pipeline** using:

- Python
- GitHub Events API
- DuckDB
- SQL
- dbt
- Apache Airflow
- Streamlit
- Pandas
- Git/GitHub

The pipeline follows this architecture:

```text
GitHub Events API
        ↓
Python API Extractor
        ↓
Raw JSON Files
        ↓
DuckDB Warehouse
        ↓
dbt Transformations
        ↓
┌───────────────┬──────────────────┬─────────────────┐
│   Staging     │   Intermediate   │      Mart       │
└───────────────┴──────────────────┴─────────────────┘
                         ↓
                Streamlit Dashboard

             Apache Airflow
          orchestrates the pipeline
```

---

## 🏗️ Architecture

```text
                    GitHub Events API
                           │
                           ▼
                ┌─────────────────────┐
                │ Python API Extractor│
                └──────────┬──────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Raw JSON      │
                  │   File Storage   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     DuckDB      │
                  │  Raw Warehouse  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │       dbt       │
                  │ Transformations │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────────┐  ┌────────┐
         │Staging │  │Intermediate│  │  Mart  │
         └────────┘  └────────────┘  └───┬────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │    Streamlit     │
                              │    Dashboard     │
                              └──────────────────┘


                 Apache Airflow
                       │
                       ▼
        ┌──────────────────────────────┐
        │     Pipeline Orchestration   │
        └──────────────────────────────┘
```

---

## 🔄 Pipeline Flow

### 1. GitHub API Ingestion

The Python ingestion script connects to the public GitHub Events API.

It supports:

- API pagination
- Configurable page size
- Multiple API pages
- HTTP error handling
- Request timeout
- UTC ingestion timestamps
- Date-partitioned raw storage

Raw events are stored under:

```text
data/raw/github_events/
```

Example:

```text
data/raw/github_events/
└── ingestion_date=2026-11-09/
    └── github_events_20261109_143038.json
```

---

### 2. Raw Data Loading

The raw JSON files are loaded into DuckDB.

The raw table stores:

- Event ID
- Event type
- Actor JSON
- Repository JSON
- Payload JSON
- Public/private flag
- Event timestamp
- Complete raw event
- Ingestion timestamp

A separate ingestion log tracks loaded raw files and prevents the same raw file from being loaded repeatedly.

---

### 3. dbt Staging Layer

The staging model extracts useful fields from the nested GitHub JSON structure.

Examples:

- Actor login
- Actor ID
- Repository name
- Repository ID
- Repository URL
- Event type
- Created timestamp

Duplicate event IDs are handled using a window function, keeping the latest ingested record.

Model:

```text
stg_github_events
```

---

### 4. dbt Intermediate Layer

The intermediate model enriches the staged GitHub events.

It creates:

- Event date
- Event hour
- Repository owner
- Repository name
- Bot/human classification
- Event category

Event categories include:

- `code_activity`
- `pull_request_activity`
- `issue_activity`
- `repository_engagement`
- `release_activity`
- `other`

Model:

```text
int_github_events_enriched
```

---

### 5. dbt Mart Layer

The mart layer produces daily GitHub activity metrics.

Metrics include:

- Total events
- Unique actors
- Unique repositories
- Push events
- Pull request events
- Issue events
- Watch events
- Release events
- Bot events
- Human events

Model:

```text
mart_github_activity_daily
```

---

## 🧪 Data Quality

The project includes automated dbt data-quality tests.

Tests validate:

- Event ID is not null
- Event ID is unique
- Event type is not null
- Actor login is not null
- Repository name is not null
- Created timestamp is not null
- Event date is not null
- Event date is unique in the mart
- Mart metrics are not null

Latest successful dbt test run:

```text
PASS=11
WARN=0
ERROR=0
SKIP=0
```

---

## ⚙️ Apache Airflow

Apache Airflow orchestrates the complete pipeline.

The DAG contains four major tasks:

```text
extract_github_events
        ↓
load_raw_events
        ↓
dbt_run
        ↓
dbt_test
```

DAG name:

```text
github_events_daily_pipeline
```

Schedule:

```text
0 6 * * *
```

The pipeline is designed to run daily.

---

## 📊 Streamlit Dashboard

The project includes an interactive Streamlit dashboard for GitHub activity analytics.

### Dashboard Features

- Total GitHub events
- Unique actors
- Unique repositories
- Push activity
- Pull request activity
- Issue activity
- Watch activity
- Release activity
- Human vs Bot activity
- Daily activity trend
- Top repositories
- Date-range filtering
- Daily activity data table

The dashboard reads analytical data from DuckDB and uses the dbt models as the transformation layer.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | API ingestion and data loading |
| **GitHub Events API** | Source data |
| **DuckDB** | Analytical warehouse |
| **SQL** | Data transformation |
| **dbt** | ELT transformations and data quality |
| **Apache Airflow** | Pipeline orchestration |
| **Streamlit** | Interactive dashboard |
| **Pandas** | Data analysis |
| **Git/GitHub** | Version control |

---

## 📁 Project Structure

```text
gcp-github-events-data-pipeline/
│
├── dags/
│   └── github_events_pipeline.py
│
├── ingestion/
│   ├── github_events_api.py
│   └── load_raw_events.py
│
├── dbt/
│   └── github_events/
│       ├── models/
│       │   ├── staging/
│       │   │   ├── stg_github_events.sql
│       │   │   └── schema.yml
│       │   │
│       │   ├── intermediate/
│       │   │   └── int_github_events_enriched.sql
│       │   │
│       │   └── marts/
│       │       ├── mart_github_activity_daily.sql
│       │       └── schema.yml
│       │
│       ├── dbt_project.yml
│       └── README.md
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── warehouse/
│
├── docs/
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>

cd gcp-github-events-data-pipeline
```

### 2. Create a Python virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Pipeline

### Step 1 — Extract GitHub Events

```bash
python ingestion/github_events_api.py
```

This retrieves events from the GitHub Events API and stores them as raw JSON.

---

### Step 2 — Load Raw Events into DuckDB

```bash
python ingestion/load_raw_events.py
```

This loads the latest raw JSON file into the DuckDB raw layer.

---

### Step 3 — Run dbt

Move into the dbt project:

```bash
cd dbt/github_events
```

Run the connection check:

```bash
dbt debug
```

Run transformations:

```bash
dbt run
```

Run data-quality tests:

```bash
dbt test
```

Expected result:

```text
PASS=11
WARN=0
ERROR=0
```

---

### Step 4 — Run Streamlit Dashboard

Return to the project root:

```bash
cd ../..
```

Run:

```bash
streamlit run dashboard/app.py
```

Open:

```text
http://localhost:8501
```

---

## 🌬️ Run Airflow

Set the Airflow home directory:

```bash
export AIRFLOW_HOME=$PWD/airflow
```

Start Airflow:

```bash
airflow standalone
```

Open:

```text
http://localhost:8080
```

The DAG:

```text
github_events_daily_pipeline
```

orchestrates:

```text
GitHub API
     ↓
Raw JSON
     ↓
DuckDB
     ↓
dbt Run
     ↓
dbt Tests
```

---

## 🔁 Idempotency

The raw ingestion layer includes file-level idempotency.

Before loading a raw JSON file, the pipeline checks whether that exact file has already been processed.

Processed files are recorded in:

```text
raw_ingestion_log
```

This prevents accidental duplicate loading of the same raw file.

The dbt staging layer also performs event-level deduplication using:

```sql
row_number()
over (
    partition by event_id
    order by ingestion_timestamp desc
)
```

---

## 📈 Example Analytics

The dashboard can answer questions such as:

- How many GitHub events occurred during a selected period?
- How many unique contributors generated activity?
- How many repositories were active?
- Which repositories generated the most events?
- What percentage of activity came from bots?
- How much activity came from pushes?
- How much activity came from pull requests?
- How does GitHub activity change over time?

---

## 💰 Cost Considerations

This project uses a local analytical architecture:

```text
GitHub Events API
        ↓
Local JSON
        ↓
DuckDB
        ↓
dbt
        ↓
Airflow
        ↓
Streamlit
```

This allows the complete pipeline to run locally without requiring a paid cloud account or cloud billing setup.

The architecture can later be migrated to cloud services such as:

```text
GitHub API
     ↓
Google Cloud Storage
     ↓
BigQuery
     ↓
dbt
     ↓
Cloud Composer
     ↓
Streamlit / BI Tool
```

---

## 🔮 Future Improvements

Potential production extensions include:

- Google Cloud Storage for raw data
- BigQuery as the analytical warehouse
- Cloud Composer for managed Airflow
- GitHub API authentication
- Incremental dbt models
- GitHub Actions CI/CD
- Automated pipeline monitoring
- Alerting for failed data-quality tests
- Historical event storage
- Repository-level trend analysis
- Contributor-level analytics

---

## 🎯 Engineering Concepts Demonstrated

This project demonstrates practical experience with:

- REST API ingestion
- API pagination
- JSON data processing
- Raw data preservation
- Data warehousing
- DuckDB
- SQL transformations
- ELT architecture
- dbt modeling
- dbt testing
- Data deduplication
- Idempotent ingestion
- Airflow orchestration
- Analytical marts
- Dashboard development
- Git version control

---

## 👩‍💻 Author

**Shreya Dutta**

Data Engineering Portfolio Project