from unittest.mock import MagicMock, AsyncMock, patch

from app.services.ingestion import ingest_paper_list

async def test_ingest_paper_list_ingests_new_paper():
    db = AsyncMock()
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_query_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()

    with patch("app.services.ingestion.download_and_extract_text",
        new_callable=AsyncMock) as mock_download:
        mock_download.return_value = "Some extract text"
        with patch("app.services.ingestion.chunk_text") as mock_chunk:
            mock_chunk.return_value = [
                "chunk one owth enought words to pass", "chunk two also fine"]
            with patch("app.services.ingestion.embed_document") as mock_embed:
                mock_embed.return_value = [0.1] * 768
                with patch("app.services.ingestion.mlflow") as mock_mlflow:
                    with patch("app.services.ingestion._check_ingestion_regression"):

                        mock_run = MagicMock()
                        mock_run.info.run_id = "test_run_id"
                        mock_mlflow.start_run.return_value.__enter__.return_value = mock_run

                        result = await ingest_paper_list(papers=[
                            {
                                "arxiv_id": "1706.03762",
                                "title": "Attention is all you need",
                                "authors": "Vaswani",
                                "abstract": "A new attention-based architecture.",
                                "pdf_url": "https://arxiv.org/abs/1706.03762",
                                "published_date": "2026-01-01"
                            }
                        ], db=db)

                        assert result["papers_ingested"] == 1
                        assert result["chunks_created"] > 0
                        assert result["papers_skipped"] == 0

async def test_ingest_paper_list_skips_existing_paper():
    db = AsyncMock()
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = MagicMock()
    db.execute = AsyncMock(return_value=mock_query_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()

    with patch("app.services.ingestion.mlflow") as mock_mlflow:
        with patch("app.services.ingestion._check_ingestion_regression"):

            mock_run = MagicMock()
            mock_run.info.run_id = "test_run_id"
            mock_mlflow.start_run.return_value.__enter__.return_value = mock_run

            result = await ingest_paper_list(papers=[
                {
                    "arxiv_id": "1706.03762",
                    "title": "Attention is all you need",
                    "authors": "Vaswani",
                    "abstract": "A new attention-based architecture.",
                    "pdf_url": "https://arxiv.org/abs/1706.03762",
                    "published_date": "2026-01-01"
                }
            ], db=db)

            assert result["papers_ingested"] == 0
            assert result["chunks_created"] == 0
            assert result["papers_skipped"] == 1

async def test_ingest_paper_list_handles_download_failure():
    db = AsyncMock()
    mock_query_result = MagicMock()
    mock_query_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_query_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()

    
    with patch("app.services.ingestion.mlflow"):
        with patch("app.services.ingestion._check_ingestion_regression"):
            with patch("app.services.ingestion.download_and_extract_text",
                new_callable=AsyncMock) as mock_download:
                mock_download.side_effect = Exception("network timeout")

                result = await ingest_paper_list(papers=[
                    {
                        "arxiv_id": "1706.03762",
                        "title": "Attention is all you need",
                        "authors": "Vaswani",
                        "abstract": "A new attention-based architecture.",
                        "pdf_url": "https://arxiv.org/abs/1706.03762",
                        "published_date": "2026-01-01"
                    }
                ], db=db)

                db.rollback.assert_called_once()

                assert result["papers_ingested"] == 0
                assert result["chunks_created"] == 0
                assert result["papers_skipped"] == 0


        