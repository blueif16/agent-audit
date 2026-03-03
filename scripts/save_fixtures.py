"""Save real capture fixtures for testing (Tier 2 - run after merge)."""

import asyncio
import json
from pathlib import Path

from accessvision.capture.scraper import scrape_page
from accessvision.capture.browser import capture_page
from accessvision.capture.pipeline import capture_pages


FIXTURES_DIR = Path(__file__).parent.parent / 'tests' / 'fixtures'
DEFAULT_URL = 'https://example.com'


async def main():
    """Capture one real URL and save all outputs."""
    url = DEFAULT_URL
    print(f"Capturing {url}...")

    # Run scraper and browser in parallel
    scrape_result = await scrape_page(url)
    browser_result = await capture_page(url)

    # Save individual outputs
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Screenshot
    screenshot_path = FIXTURES_DIR / 'sample_screenshot.png'
    screenshot_path.write_bytes(browser_result['screenshot'])
    print(f"✓ Saved {screenshot_path}")

    # Axe results
    axe_path = FIXTURES_DIR / 'sample_axe_results.json'
    axe_path.write_text(json.dumps(browser_result['axe_results'], indent=2))
    print(f"✓ Saved {axe_path}")

    # Element map
    elem_path = FIXTURES_DIR / 'sample_element_map.json'
    elem_path.write_text(json.dumps(browser_result['element_map'], indent=2))
    print(f"✓ Saved {elem_path}")

    # A11y tree
    a11y_path = FIXTURES_DIR / 'sample_a11y_tree.json'
    a11y_path.write_text(json.dumps(browser_result['accessibility_tree'], indent=2))
    print(f"✓ Saved {a11y_path}")

    # Firecrawl scrape
    scrape_path = FIXTURES_DIR / 'sample_firecrawl_scrape.json'
    scrape_path.write_text(json.dumps(scrape_result, indent=2))
    print(f"✓ Saved {scrape_path}")

    # Full PageCapture
    page_capture_data = {
        'url': url,
        'title': scrape_result['metadata'].get('title', 'Example'),
        'priority_score': 8,
        'reason': 'Test fixture',
        'markdown_description': scrape_result['markdown'],
        'axe_results': browser_result['axe_results'],
        'element_map': browser_result['element_map'],
        'accessibility_tree': browser_result['accessibility_tree']
    }
    capture_path = FIXTURES_DIR / 'sample_page_capture.json'
    capture_path.write_text(json.dumps(page_capture_data, indent=2))
    print(f"✓ Saved {capture_path}")

    print("\nAll fixtures saved successfully!")


if __name__ == '__main__':
    asyncio.run(main())
