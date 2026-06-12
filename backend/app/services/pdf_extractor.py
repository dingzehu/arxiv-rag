import httpx
import io
import asyncio
import logging
import pdfplumber

logger = logging.getLogger(__name__)

async def download_and_extract_text(pdf_url: str) -> str:
    """The function for download and extract content from the pdf_url"""
    async with httpx.AsyncClient() as client:
        response = await client.get(pdf_url, follow_redirects=True, timeout=30.0)
        # follow_redirects=True is required because arXiv redirects PDF URLs before
        # serving the file. Without this flag, httpx stops at the redirect and
        # returns an empty response 
        response.raise_for_status()  # raises an exception for 4xx/5xx
        pdf_bytes = response.content  # the raw PDF as bytes

    def _extract():
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()  # return None for image-only pages
                if text:
                    pages_text.append(text)
            logger.info("Extracted text from %d pages: %s", len(pdf.pages), pdf_url)
        return "\n".join(pages_text).strip()
    return await asyncio.to_thread(_extract)
