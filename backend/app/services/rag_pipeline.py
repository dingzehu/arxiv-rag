import time
import logging
import mlflow
from google import genai
from sqlalchemy import select, cast, Float
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db import Paper, Chunk
from app.services.embedder import embed_query

logger = logging.getLogger(__name__)

_client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options={"api_version": "v1"},
)

RAG_PROMPT = """You are a research assistant specialising in machine learning
and AI. \
Answer the question below using ONLY the provided context passages from indexed arXiv
papers.

Rules:
- Answer directly and cite the paper title.
- If the context does not contain enough information, say exactly: \
"The indexed papers do not contain enough information to answer this question."
- Never make up information not in the context.
- Keep the answer under 200 words.

CONTEXT:
{context_passages}

QUESTION: {question}"""


async def search(
    question: str,
    top_k: int,
    db: AsyncSession,
) -> dict:
    """Embed a question, retrieve top_k similar chunks, generate an answer with Gemini.
    
    Return a dict matching SearchResponse schema.
    """
    mlflow.set_experiment("arxiv-rag-search")

    with mlflow.start_run() as run:
        # STEP 1: log params (question, top_k, start timer)
        run_id = run.info.run_id      # the unique ID of this run
        mlflow.log_param("question", question)
        mlflow.log_param("top_k", top_k)
        start = time.time()

        # STEP 2: embed the question
        question_vector = embed_query(question)

        # STEP 3: query pgvector
        distance = Chunk.embedding.op("<=>", return_type=Float)(cast(question_vector, Vector(768)))
        rows = (await db.execute(
            select(Chunk.chunk_text,
            Paper.arxiv_id,
            Paper.title,
            Paper.authors,
            distance.label("distance"))
            .join(Paper, Chunk.paper_id == Paper.id)
            .order_by(distance)
            .limit(top_k)
        )).all()

        # STEP 4: build context string from retrieved chunks
        passages = [f"[{i+1}] {row.chunk_text}" for i, row in enumerate(rows)]
        context_passages = "\n\n".join(passages)

        # STEP 5: build the full prompt
        rag_prompt = RAG_PROMPT.format(context_passages=context_passages, question=question)

        # STEP 6: call Gemini to generate the answer
        response = _client.models.generate_content(
            model = settings.gemini_model,
            contents=rag_prompt,
        )
        answer = response.text

        #STEP 7: build sources list — one dict per row
        sources_list = []
        for row in rows:
            sources_list.append({
                "arxiv_id": row.arxiv_id,
                "title": row.title,
                "authors": row.authors,
                "chunk_text": row.chunk_text,
            "similarity_score": round(1 - row.distance, 4)})

        # STEP 8: compute duration_ms, log metrics (top_k param, num_results +
        # duration_ms metrics
        duration_ms = int((time.time() - start) * 1000)
        mlflow.log_metric("num_results", len(rows))
        mlflow.log_metric("duration_ms", duration_ms)

        # STEP 9: return the dict
        return {
            "answer": answer,
            "sources": sources_list,
            "duration_ms": duration_ms,
            "mlflow_run_id": run_id,
        }

