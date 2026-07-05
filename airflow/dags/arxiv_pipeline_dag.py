import logging, requests

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


BACKEND_URL = "http://backend:8000"

QUERIES = ["transformer", "attention mechanism",
                "large language model", "neural network",
                "reinforcement learning"]

def ingest(**context):
    for query in QUERIES:
        response = requests.post(
            f"{BACKEND_URL}/ingest", json={"query": query, "max_papers": 10},
            timeout=300
            )
        response.raise_for_status()
        result = response.json()
        logging.info("query=%r ingested=%s skipped=%s",
                    query, result.get("papers_ingested"),
                    result.get("papers_skipped"))

def evaluate(**context):
    response = requests.post(f"{BACKEND_URL}/evaluate/batch", timeout=600)
    response.raise_for_status()
    result = response.json()

    if result["average_score"] < 0.70:
        logging.warning("Evaluation score below threshold: %s",
        result["average_score"]
        )

with DAG(
    dag_id="arxiv_daily_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_papers",
        python_callable=ingest,
    )

    # Canary check: score < 0.70 means ingestion may have
    # corrupted retrieval quality
    evaluate_task = PythonOperator(
        task_id="evaluation",
        python_callable=evaluate,
    )

    ingest_task >> evaluate_task