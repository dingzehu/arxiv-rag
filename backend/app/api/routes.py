from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import Paper, Chunk
from app.models.schemas import (
    IngestRequest, IngestResponse,
    SearchRequest, SearchResponse,
    EvaluateRequest, EvaluateResponse,
    BatchEvaluateResponse
)
from app.services.ingestion import ingest_papers, ingest_document_bytes
from app.services.rag_pipeline import search
from app.services.evaluator import evaluate_question, evaluate_batch

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_route(
    body: IngestRequest, db: AsyncSession = Depends(get_db)
    ) -> IngestResponse:
    """Trigger arXiv ingestion for the given query; returns counts and MLflow run ID."""
    result = await ingest_papers(query=body.query, max_papers=body.max_papers, db=db)
    return IngestResponse(**result)

@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document_route(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    ) -> IngestResponse:
    """Accept a PDF upload and index it into pgvector — no arXiv fetch."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Upload file must be a PDF.")
    pdf_bytes = await file.read()
    result = await ingest_document_bytes(
        pdf_bytes=pdf_bytes,
        filename=file.filename or "unknown.pdf",
        db=db,
    )
    return IngestResponse(**result)

@router.post("/search", response_model=SearchResponse)
async def search_route(
    body: SearchRequest, db: AsyncSession = Depends(get_db)
    ) -> SearchResponse:
    """Trigger search for the given question;
    returns answer, sources list and MLflow run ID."""
    result = await search(question=body.question, top_k=body.top_k, db=db)
    return SearchResponse(**result)

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_route(
    body: EvaluateRequest, db: AsyncSession = Depends(get_db)
    ) -> EvaluateResponse:
    """Trigger evaluation for the generated answer and expected answer input;
    return expected answer, actual answer and evaluate score"""
    result = await evaluate_question(
        question=body.question, expected_answer=body.expected_answer, db=db
        )
    return EvaluateResponse(**result)

@router.post("/evaluate/batch", response_model=BatchEvaluateResponse)
async def batch_evaluate_route(
    db: AsyncSession = Depends(get_db)
    ) -> BatchEvaluateResponse:
    """Trigger batch evaluation with the give golden test set;
    return average score and score per difficulty."""
    result = await evaluate_batch(db=db)
    return BatchEvaluateResponse(**result)

@router.get("/papers")
async def list_papers_route(
    page: int = 1, size: int = 20, db: AsyncSession = Depends(get_db)
    ) -> list:
    """Return a paginated list of papers."""
    offset = (page - 1) * size
    result = await db.execute(select(Paper).offset(offset).limit(size))
    papers = result.scalars().all()
    return [{"arxiv_id": p.arxiv_id, "title": p.title, "authors": p.authors,
            "published_date": str(p.published_date)} for p in papers]

@router.get("/papers/{arxiv_id}")
async def get_paper_route(arxiv_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Return the paper fields and chunk count."""
    paper = (
        await db.execute(
            select(Paper).where(Paper.arxiv_id == arxiv_id)
            )).scalar_one_or_none()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    chunk_count = (await db.execute(
        select(func.count(Chunk.id)).where(Chunk.paper_id == paper.id)
    )).scalar()
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "pdf_url": paper.pdf_url,
        "published_date": str(paper.published_date),
        "chunk_count": chunk_count,
    }

@router.get("/health")
async def get_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Return connection status, paper and chunk count for health check."""
    paper_count = (await db.execute(select(func.count(Paper.id)))).scalar()
    chunk_count = (await db.execute(select(func.count(Chunk.id)))).scalar()

    return {
        "status": "ok",
        "db": "connected",
        "vector_extension": "enabled",
        "papers_indexed": paper_count,
        "chunks_indexed": chunk_count,
        "mlflow": "connected",
    }
        