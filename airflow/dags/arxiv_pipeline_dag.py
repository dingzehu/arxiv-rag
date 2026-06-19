import asyncio
import logging

import mlflow

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from app.services.arxiv_fetcher import fetch_papers
from app.services.ingestion import ingest_paper_list
from app.services.evaluator import evaluate_batch
from app.database import AsyncSessionLocal

QUERIES = ["transformer", "attention mechanism",
                "large language model", "neural network",
                "reinforcement learning"]

def fetch(**context):
    async def _fetch_all():

        all_papers = []
        for query in QUERIES:
            papers_per_query = await fetch_papers(query=query, max_results=10)
            all_papers.extend(papers_per_query)
        for paper in all_papers:
            paper["published_date"] = paper["published_date"].date().isoformat()
        return all_papers        # automatically pushed to XCom

    return asyncio.run(_fetch_all())



def ingest(ti, **context):
    all_papers = ti.xcom_pull(task_ids="fetch_papers")   # pulled from XCom

    async def _ingest_async():
        mlflow.set_experiment("arxiv-rag-ingestion")
        with mlflow.start_run():
            mlflow.log_param("source", "airflow_daily")
            mlflow.log_param("queries", ",".join(QUERIES))
            mlflow.log_param("papers_fetched", len(all_papers))
            async with AsyncSessionLocal() as db:
                await ingest_paper_list(papers=all_papers, db=db)

    asyncio.run(_ingest_async())

def evaluate(**context):
    async def _evaluate_async():
        async with AsyncSessionLocal() as db:
            result = await evaluate_batch(db=db)
        if result["average_score"] < 0.70:
            logging.warning("Evaluation score below threshold: %s",
            result["average_score"])

    asyncio.run(_evaluate_async())

with DAG(
    dag_id="arxiv_daily_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:

    # ~50 papers across 5 ML topics; datetime → isoformat() so XCom JSON
    # serialisation works
    fetch_task = PythonOperator(
        task_id="fetch_papers",
        python_callable=fetch,
    )

    # Pull XCom list and ingest the papers;
    # arxiv_id UNIQUE constraint ensures re-runs skip duplicates (idempotent)
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

    fetch_task >> ingest_task >> evaluate_task