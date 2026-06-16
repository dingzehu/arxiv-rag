import time
import logging
import mlflow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Paper, Chunk
from app.services.arxiv_fetcher import fetch_papers
from app.services.pdf_extractor import download_and_extract_text
from app.services.chunker import chunk_text
from app.services.embedder import embed_document

logger = logging.getLogger(__name__)

async def ingest_papers(
    query: str,
    max_papers: int,
    db: AsyncSession,
) -> dict:
    """Fetch arXiv papers and store chunks + embeddings in the database.
    
    Returns a summary dict with counts and the MLFlow run ID.
    """
    mlflow.set_experiment("arxiv-rag-ingestion")   # create/select the notebook

    with mlflow.start_run() as run:                # open one entry
        # STEP 1: log the input params to MLFlow
        run_id = run.info.run_id                   # the unique ID of this run
        mlflow.log_param("query", query)           # record the setting
        mlflow.log_param("max_papers", max_papers)
        
        start = time.time()

        # STEP 2: fetch paper metadata from arXiv
        fetched_papers = await fetch_papers(query=query, max_results=max_papers)

        papers_ingested = 0
        chunks_created = 0

        for paper_data in fetched_papers:
            try:
                # STEP 3: skip if this arxiv_id is already in the database
                result = await db.execute(
                    select(Paper).where(Paper.arxiv_id == paper_data["arxiv_id"])
                )
                existing = result.scalar_one_or_none()  
                # returns the Paper object, or None
                if existing:
                    continue  # paper already in DB — skip to next paper
                
                # STEP 4: create and stage a Paper object, then flush to get paper.id
                paper = Paper(
                    arxiv_id=paper_data["arxiv_id"],
                    title=paper_data["title"],
                    authors=paper_data["authors"],
                    abstract=paper_data["abstract"],
                    pdf_url=paper_data["pdf_url"],
                    published_date=paper_data["published_date"]
                )
                db.add(paper)
                await db.flush()

                # STEP 5: download PDF text
                text = await download_and_extract_text(paper.pdf_url)

                # STEP 6: chunk → embed → stage each Chunk object
                for i, chunk in enumerate(chunk_text(text)):
                    embedded_chunk = embed_document(chunk)

                    db.add(Chunk(
                        paper_id=paper.id,
                        chunk_index=i,
                        chunk_text=chunk,
                        embedding=embedded_chunk
                    ))
                    chunks_created += 1

                # STEP 7: commit everything for this paper, increment counters
                await db.commit()
                papers_ingested += 1
            except Exception as e:
                await db.rollback()
                logger.warning("Failed to ingest %s: %s", paper_data["arxiv_id"], e)
                continue
        duration = time.time() - start
        
        # STEP 9: log result metrics to MLFlow
        mlflow.log_metric("papers_ingested", papers_ingested)   # record the result
        mlflow.log_metric("chunks_created", chunks_created)
        mlflow.log_metric("duration_seconds", round(duration, 2))

        # STEP 10: return the summary dict
        return {
            "papers_ingested": papers_ingested,
            "chunks_created": chunks_created,
            "duration_seconds": round(duration, 2),
            "mlflow_run_id": run_id
        }




