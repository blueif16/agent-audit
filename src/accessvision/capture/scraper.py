"""Firecrawl-based page scraping for clean markdown extraction."""

import asyncio
from typing import Dict, Any
from firecrawl import FirecrawlApp

from accessvision.config import FIRECRAWL_API_KEY


async def scrape_page(url: str) -> Dict[str, Any]:
    """Scrape a page using Firecrawl /scrape endpoint.

    Args:
        url: Page URL to scrape

    Returns:
        Dict with 'markdown' and 'metadata' keys
    """
    # Firecrawl SDK is synchronous, run in executor with timeout
    loop = asyncio.get_event_loop()

    def _scrape():
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        result = app.scrape(url, formats=['markdown'])
        return result

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _scrape),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        raise RuntimeError(f"Firecrawl scrape timed out for {url}") from None

    # Handle different Firecrawl response formats
    markdown = ''
    metadata = {}
    if hasattr(result, 'markdown'):
        markdown = result.markdown or ''
    elif hasattr(result, 'data') and isinstance(result.data, dict):
        markdown = result.data.get('markdown', '')

    if hasattr(result, 'metadata'):
        meta = result.metadata
        if hasattr(meta, '__dict__'):
            metadata = vars(meta)
        elif isinstance(meta, dict):
            metadata = meta
    elif hasattr(result, 'data') and isinstance(result.data, dict):
        metadata = result.data.get('metadata', {})

    return {
        'markdown': markdown,
        'metadata': metadata
    }
