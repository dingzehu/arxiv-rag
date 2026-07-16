import arxiv
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

async def fetch_papers(query: str, max_results: int = 20) -> list[dict[str, Any]]:
    """Fetch paper metadata from the arXiv API for a given query."""
    def _sync_fetch():        # inner function — does the blocking work
        
        results = []
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results)

        for result in client.results(search):
            paper = {"arxiv_id": result.entry_id.split("/")[-1].split("v")[0],
                    "title": result.title,
                    "authors": ", ".join(str(a) for a in result.authors),
                    "abstract": result.summary, "pdf_url": result.pdf_url,
                    "published_date": result.published}

            results.append(paper)
        logger.info("Fetched %d papers for query: '%s'", len(results), query)
        return results

    return await asyncio.to_thread(_sync_fetch)  # run blocking code off the async thread
