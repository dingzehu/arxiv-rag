from unittest.mock import MagicMock, patch, AsyncMock

async def test_search_route_returns_answer(client):
    with patch("app.api.routes.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {
            "answer": "The actual answer.",
            "sources": [],
            "duration_ms": 100,
            "mlflow_run_id": "search-run-id",
        }

        response = await client.post(
            "/search", json={"question": "what is attention?", "top_k": 1})

        assert response.status_code == 200
        assert response.json()["answer"] == "The actual answer."

async def test_search_route_validates_empty_question(client):
    response = await client.post(
        "/search", json={"question": "    ", "top_k": 5}
    )

    assert response.status_code == 422

async def test_health_route_return_ok(client, mock_db):
    execute_result = MagicMock()
    execute_result.scalar.return_value = 0
    mock_db.execute.return_value = execute_result

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


