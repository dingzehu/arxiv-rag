import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.evaluator import evaluate_batch, evaluate_question

fake_data = [
    {"question": "q1", "expected_answer": "a1", "difficulty": "medium"},
    {"question": "q2", "expected_answer": "a2", "difficulty": "easy"},
]
fake_json = json.dumps(fake_data)

async def test_evaluate_question_returns_score(mock_db):
    with patch("app.services.evaluator.mlflow") as mock_flow, patch(
        "app.services.evaluator.search", new_callable=AsyncMock
        ) as mock_search, patch("app.services.evaluator._client") as mock_client:
        mock_run = MagicMock()
        mock_run.info.run_id = "test-run-id"
        mock_flow.start_run.return_value.__enter__.return_value = mock_run

        mock_search.return_value = {
            "answer": "The actual answer.",
            "sources": [],
            "duration_ms": 100,
            "mlflow_run_id": "search-run-id",
        }

        mock_judge_response = MagicMock()
        mock_judge_response.text = '{"score": 0.9, "reasoning": "Correct answer."}'
        mock_client.models.generate_content.return_value = mock_judge_response

        result = await evaluate_question(
            "what is attention?", expected_answer="some expected answer", db=mock_db
            )

        assert result["score"] == 0.9
        assert result["question"] == "what is attention?"
        assert "reasoning" in result
        assert "mlflow_run_id" in result

async def test_evaluate_batch_aggregates_scores(mock_db):
    with (
        patch("pathlib.Path.read_bytes", return_value=fake_json.encode()),
        patch("app.services.evaluator.mlflow"),
        patch(
            "app.services.evaluator.evaluate_question", new_callable=AsyncMock
        ) as mock_evaluate_question,
    ):
        mock_evaluate_question.return_value = {"score": 0.8}

        result = await evaluate_batch(db=mock_db)

        assert result["total_questions"] == 2
        assert result["average_score"] == 0.8
        assert "medium" in result["scores_by_difficulty"]
        assert "easy" in result["scores_by_difficulty"]



                

                

