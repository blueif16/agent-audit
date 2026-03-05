"""Tests for capture pipeline (Tier 1: mocked)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from accessvision.capture.scraper import scrape_page
from accessvision.capture.browser import capture_page
from accessvision.capture.pipeline import capture_pages
from accessvision.models import PageCapture


@pytest.mark.asyncio
async def test_scrape_page_mock():
    """Test Firecrawl scraping with mock."""
    mock_result = {
        'markdown': '# Test Page\n\nContent here',
        'metadata': {'title': 'Test', 'statusCode': 200}
    }

    with patch('accessvision.capture.scraper.FirecrawlApp') as mock_app:
        mock_instance = MagicMock()
        mock_instance.scrape_url.return_value = mock_result
        mock_app.return_value = mock_instance

        result = await scrape_page('https://example.com')

        assert result['markdown'] == '# Test Page\n\nContent here'
        assert result['metadata']['title'] == 'Test'


@pytest.mark.asyncio
async def test_capture_page_mock():
    """Test browser capture with mock."""
    with patch('accessvision.capture.browser.async_playwright') as mock_pw:
        # Setup mock chain
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.screenshot.return_value = b'fake_png'
        mock_page.evaluate.side_effect = [
            {'violations': [], 'passes': []},  # axe results
            [{'index': 0, 'tag': 'button', 'text': 'Submit', 'bbox': {'x': 100, 'y': 200, 'w': 80, 'h': 40}, 'visible': True, 'focusable': True}]  # element map
        ]
        mock_page.accessibility.snapshot.return_value = {'role': 'WebArea'}
        mock_browser.new_page.return_value = mock_page

        mock_playwright = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_pw.return_value.__aenter__.return_value = mock_playwright

        result = await capture_page('https://example.com')

        assert result['screenshot'] == b'fake_png'
        assert 'violations' in result['axe_results']
        assert len(result['element_map']) == 1
        assert result['element_map'][0]['tag'] == 'button'
        assert result['element_map'][0]['bbox']['x'] == 100


@pytest.mark.asyncio
async def test_pipeline_assembly():
    """Test PageCapture assembly from parallel sources."""
    ranked_pages = [
        {
            'url': 'https://example.com/page1',
            'title': 'Page 1',
            'priority_score': 10,
            'reason': 'Critical page'
        }
    ]

    with patch('accessvision.capture.pipeline.scrape_page', new_callable=AsyncMock) as mock_scrape, \
         patch('accessvision.capture.pipeline.capture_page', new_callable=AsyncMock) as mock_capture:

        mock_scrape.return_value = {
            'markdown': '# Page 1',
            'metadata': {}
        }

        mock_capture.return_value = {
            'screenshot': b'png_data',
            'axe_results': {'violations': []},
            'element_map': [{'index': 0, 'tag': 'div'}],
            'accessibility_tree': {}
        }

        results = await capture_pages(ranked_pages)

        assert len(results) == 1
        assert isinstance(results[0], PageCapture)
        assert results[0].url == 'https://example.com/page1'
        assert results[0].priority_score == 10
        assert results[0].screenshot == b'png_data'
        assert results[0].markdown_description == '# Page 1'


@pytest.mark.asyncio
async def test_element_map_fields():
    """Verify element map contains required fields."""
    with patch('accessvision.capture.browser.async_playwright') as mock_pw:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.screenshot.return_value = b'fake'
        mock_page.evaluate.side_effect = [
            {'violations': []},
            [{
                'index': 0,
                'tag': 'input',
                'role': None,
                'text': '',
                'alt': None,
                'aria_label': 'Email',
                'aria_describedby': None,
                'href': None,
                'type': 'email',
                'name': 'email',
                'placeholder': 'Enter email',
                'bbox': {'x': 50, 'y': 100, 'w': 200, 'h': 30},
                'visible': True,
                'focusable': True
            }]
        ]
        mock_page.accessibility.snapshot.return_value = {}
        mock_browser.new_page.return_value = mock_page

        mock_playwright = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_pw.return_value.__aenter__.return_value = mock_playwright

        result = await capture_page('https://example.com')

        elem = result['element_map'][0]
        assert 'tag' in elem
        assert 'bbox' in elem
        assert 'visible' in elem
        assert 'focusable' in elem
        assert elem['aria_label'] == 'Email'
        assert elem['type'] == 'email'
