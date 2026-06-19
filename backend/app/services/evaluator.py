import json
import time
import logging
from pathlib import Path

import mlflow
from google import genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.rag_pipeline import search

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.gemini_api_key)

GOLDEN_SET_PATH = (
    Path(__file__).resolve().parents[3] / "evaluation" / "golden_test_set.json"
    )

JUDGE_PROMPT = """You are an expert evaluator for AI question-answering systems. \
    Compare the actual answer to expected answer and return ONLY valid JSON — 
    no markdown, no explanation, no code fences:
    
    {{
        "score": <float between 0.0 and 1.0>,
        "reasoning": "<one sentence explanation>"
    }}
    
    Scoring guide:
      1.0 = completely correct, all key facts present
      0.8 = mostly correct, minor details missing
      0.5 = partially correct, key facts present but incomplete
      0.2 = mostly wrong, some relevant content
      0.0 = completely wrong or made up
      
    Expected answer: {expected_answer}
    Actual answer:   {actual_answer}"""

async def evaluate_question(
    question: str,
    expected_answer: str,
    db: AsyncSession,
) -> dict:
    """Run a question through the RAG pipeline and score it with Gemini as judge.
    
    Returns a dict matching EvaluateResponse schema.
    """
    mlflow.set_experiment("arxiv-rag-eval")

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        start = time.time()

        # STEP 1: call search() from rag_pipeline to get actual_answer + sources
        rag_result = await search(question=question, top_k=settings.top_k, db=db)

        # STEP 2: build the judge prompt
        judge_prompt = JUDGE_PROMPT.format(
            expected_answer=expected_answer, actual_answer=rag_result["answer"]
            )

        # STEP 3: call Gemini to get the judge's response
        response = _client.models.generate_content(
            model = settings.gemini_model,
            contents=judge_prompt,
        )

        # STEP 4: parse response.text as JSON, extract score and reasoning
        judge_result = json.loads(response.text)
        score = judge_result["score"]
        reasoning = judge_result["reasoning"]

        # STEP 5: log params (question) and metric (score, duration_ms) to MLflow
        duration_ms = int((time.time() - start) * 1000)
        mlflow.log_param("question", question)
        mlflow.log_metric("score", score)
        mlflow.log_metric("duration_ms", duration_ms)
        mlflow.log_param("chunk_size", settings.chunk_size)
        mlflow.log_param("chunk_overlap", settings.chunk_overlap)
        mlflow.log_param("embedding_model", settings.embedding_model)
        mlflow.log_param("generation_model", settings.gemini_model)
        mlflow.log_param("top_k", settings.top_k)

        # STEP 6: return the dict matching EvaluateResponse
        return {
            "question": question,
            "expected_answer": expected_answer,
            "actual_answer": rag_result["answer"],
            "score": score,
            "reasoning": reasoning,
            "sources": rag_result["sources"],
            "duration_ms": duration_ms,
            "mlflow_run_id": run_id
        }

async def evaluate_batch(db: AsyncSession) -> dict:
    """Run every question in the golden test set and aggregate scores by difficulty.
    
    Returns a dict matching BatchEvaluateResponse schema.
    """
    # STEP 7: load the golden test set from GOLDEN_SET_PATH (open + json.load)
    with open(GOLDEN_SET_PATH) as f:
        data = json.load(f)

    start = time.time()
    scores_by_difficulty: dict[str, list[float]] = {}
    all_scores: list[float] = []

    # STEP 8: loop over golden set, call evaluate_question for each item
    # append score to all_scores AND scores_by_difficulty[item["difficulty"]]
    for item in data:
        evaluate_result = await evaluate_question(
            question=item["question"],
            expected_answer=item["expected_answer"],
            db=db
            )
        evaluate_score = evaluate_result["score"]
        all_scores.append(evaluate_score)
        scores_by_difficulty.setdefault(item["difficulty"], []).append(evaluate_score)

    # STEP 9: compute average_score (overall) and per-difficulty averages
    average_score = sum(all_scores) / len(all_scores)
    per_difficulty_avg = {k: sum(v) / len(v) for k, v in scores_by_difficulty.items()}

    duration_seconds = time.time() - start

    # STEP 10: return dict matching BatchEvaluateResponse
    # fields: total_questions, average_score, scores_by_difficulty,
    #         mlflow_experiment_id, duration_seconds
    return {
        "total_questions": len(data),
        "average_score": average_score,
        "scores_by_difficulty": per_difficulty_avg,
        "mlflow_experiment_id":
            mlflow.get_experiment_by_name("arxiv-rag-eval").experiment_id,
        "duration_seconds": duration_seconds
    }



