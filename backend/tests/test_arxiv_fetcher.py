from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.arxiv_fetcher import fetch_papers


async def test_fetch_papers_returns_paper_list():
    mock_result = MagicMock()
    mock_result.entry_id = "https://arxiv.org/abs/2301.07041v2"
    mock_result.title = "Attention Is All You Need"
    mock_author = MagicMock()
    mock_author.name = "Vaswani"
    mock_result.authors = [mock_author]
    mock_result.summary = "We propose a new architecture."
    mock_result.pdf_url = "https://arxiv.org/pdf/2301.07041"
    mock_result.published = datetime(2023, 1, 1)

    with patch("app.services.arxiv_fetcher.arxiv.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.results.return_value = [mock_result]
        mock_client_cls.return_value = mock_client

        papers = await fetch_papers("transformer", max_results=1)

    assert len(papers) == 1
    assert papers[0]["arxiv_id"] == "2301.07041"
    assert papers[0]["title"] == "Attention Is All You Need"
    assert papers[0]["authors"] == "Vaswani"


async def test_fetch_papers_strips_version_suffix_from_arxiv_id():
    # arXiv entry_id ends in "v2", "v5", etc — the version must be stripped
    # so the same paper ingested twice is recognised as a duplicate
    mock_result = MagicMock()
    mock_result.entry_id = "https://arxiv.org/abs/2301.07041v5"
    mock_result.title = "Test Paper"
    mock_result.authors = []
    mock_result.summary = ""
    mock_result.pdf_url = ""
    mock_result.published = datetime(2023, 1, 1)

    with patch("app.services.arxiv_fetcher.arxiv.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.results.return_value = [mock_result]
        mock_client_cls.return_value = mock_client

        papers = await fetch_papers("test", max_results=1)

    assert papers[0]["arxiv_id"] == "2301.07041"


async def test_fetch_papers_returns_empty_list_when_no_results():
    with patch("app.services.arxiv_fetcher.arxiv.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.results.return_value = []
        mock_client_cls.return_value = mock_client

        papers = await fetch_papers("xyzzy nonexistent topic", max_results=5)

    assert papers == []
