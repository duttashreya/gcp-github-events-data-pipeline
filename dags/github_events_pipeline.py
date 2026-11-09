from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


PROJECT_ROOT = "/home/shreya/gcp-github-events-data-pipeline"

PYTHON = f"{PROJECT_ROOT}/venv/bin/python"
DBT = f"{PROJECT_ROOT}/venv/bin/dbt"


with DAG(
    dag_id="github_events_daily_pipeline",
    start_date=datetime(2026, 11, 9),
    schedule="0 6 * * *",
    catchup=False,
    tags=["github", "api", "duckdb", "dbt"],
) as dag:

    extract_github_events = BashOperator(
        task_id="extract_github_events",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"{PYTHON} ingestion/github_events_api.py"
        ),
    )

    load_raw_events = BashOperator(
        task_id="load_raw_events",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            f"{PYTHON} ingestion/load_raw_events.py"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {PROJECT_ROOT}/dbt/github_events && "
            f"{DBT} run"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {PROJECT_ROOT}/dbt/github_events && "
            f"{DBT} test"
        ),
    )

    extract_github_events >> load_raw_events >> dbt_run >> dbt_test