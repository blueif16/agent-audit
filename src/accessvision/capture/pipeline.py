"""Parallel capture pipeline orchestrating scraper and browser."""

import asyncio
from typing import List, Dict, Any

from accessvision.models import PageCapture
from accessvision.capture.scraper import scrape_page
from accessvision.capture.browser import capture_page


async def capture_pages(ranked_pages: List[Dict[str, Any]]) -> List[PageCapture]:
    """Capture all pages in parallel using asyncio.gather.

    Args:
        ranked_pages: List of dicts with 'url', 'title', 'priority_score', 'reason'

    Returns:
        List of PageCapture objects
    """
    # Limit concurrency to avoid resource/rate-limit spikes
    semaphore = asyncio.Semaphore(5)

    async def _bounded_capture(page_info: Dict[str, Any]) -> PageCapture:
        async with semaphore:
            return await _capture_single_page(page_info)

    tasks = [_bounded_capture(page_info) for page_info in ranked_pages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and return successful captures
    captures = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            url = ranked_pages[i].get('url', '<unknown>')
            print(f"Error capturing {url}: {result}")
        else:
            captures.append(result)

    return captures


async def _capture_single_page(page_info: Dict[str, Any]) -> PageCapture:
    """Capture a single page with parallel scraper + browser."""
    url = page_info['url']

    # Run scraper and browser capture in parallel
    scrape_task = scrape_page(url)
    browser_task = capture_page(url)

    scrape_result, browser_result = await asyncio.gather(scrape_task, browser_task)

    # Assemble PageCapture
    return PageCapture(
        url=url,
        title=page_info['title'],
        priority_score=page_info['priority_score'],
        reason=page_info['reason'],
        screenshot=browser_result['screenshot'],
        markdown_description=scrape_result['markdown'],
        axe_results=browser_result['axe_results'],
        element_map=browser_result['element_map'],
        accessibility_tree=browser_result['accessibility_tree']
    )
