from unittest.mock import patch, MagicMock
from app.services.rag_pipeline import search

async def test_search_returns_answer(mock_db):
    with patch("app.services.rag_pipeline.mlflow") as mock_mlflow:
        with patch("app.services.rag_pipeline.embed_query", return_value=[0.1] * 768):
            with patch("app.services.rag_pipeline._client") as mock_client:
                mock_run = MagicMock()
                mock_run.info.run_id = "test-run-id"
                mock_mlflow.start_run.return_value.__enter__.return_value = mock_run
                
                mock_row = MagicMock()
                mock_row.chunk_text = "some chunk test"
                mock_row.arxiv_id = "1234.5678"
                mock_row.title = "Test Paper"
                mock_row.authors = "Author A"
                mock_row.distance = 0.2
                execute_result = MagicMock()
                execute_result.all.return_value = [mock_row]
                mock_db.execute.return_value = execute_result

                mock_response = MagicMock()
                mock_response.text = "This is the generated answer."
                mock_client.models.generate_content.return_value = mock_response


                result = await search("what is attention?", top_k=1, db=mock_db)
                assert result["answer"] == "This is the generated answer."
                assert len(result["sources"]) == 1
                assert result["sources"][0]["arxiv_id"] == "1234.5678"
                assert "mlflow_run_id" in result
                assert "duration_ms" in result


