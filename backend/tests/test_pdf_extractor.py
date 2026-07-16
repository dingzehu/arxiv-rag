from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pdf_extractor import download_and_extract_text, extract_text_from_bytes


async def test_download_and_extract_text_returns_page_text():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample text from page"

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    mock_response = MagicMock()
    mock_response.content = b"%PDF-fake"
    mock_response.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.pdf_extractor.httpx.AsyncClient", return_value=mock_http):
        with patch("app.services.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
            result = await download_and_extract_text("https://example.com/paper.pdf")

    assert result == "Sample text from page"


async def test_extract_text_from_bytes_joins_multiple_pages():
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page one"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page two"

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("app.services.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
        result = await extract_text_from_bytes(b"%PDF-fake")

    assert result == "Page one\nPage two"


async def test_extract_text_from_bytes_skips_image_only_pages():
    # pdfplumber returns None for pages that contain only images (no text layer)
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page one"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = None

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page1, mock_page2]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("app.services.pdf_extractor.pdfplumber.open", return_value=mock_pdf):
        result = await extract_text_from_bytes(b"%PDF-fake")

    assert result == "Page one"
