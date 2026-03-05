"""Tests for site discovery via Firecrawl."""

import pytest
from unittest.mock import AsyncMock, patch
from accessvision.discovery import discover_pages


@pytest.mark.asyncio
async def test_discover_pages_success():
    """Test successful page discovery with mocked Firecrawl response."""
    mock_response_data = {
        "success": True,
        "links": [
            {"url": "https://example.com/", "title": "Home"},
            {"url": "https://example.com/about", "title": "About Us"},
            {"url": "https://example.com/contact", "title": "Contact"}
        ]
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        # Setup mock
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        # Call function
        result = await discover_pages("https://example.com")

        # Assertions
        assert len(result) == 3
        assert result[0]["url"] == "https://example.com/"
        assert result[0]["title"] == "Home"
        assert result[1]["url"] == "https://example.com/about"
        assert result[2]["url"] == "https://example.com/contact"


@pytest.mark.asyncio
async def test_discover_pages_filters_empty_urls():
    """Test that pages with empty URLs are filtered out."""
    mock_response_data = {
        "success": True,
        "links": [
            {"url": "https://example.com/", "title": "Home"},
            {"url": "", "title": "Invalid"},
            {"url": "https://example.com/about", "title": "About"}
        ]
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await discover_pages("https://example.com")

        # Should only have 2 valid URLs
        assert len(result) == 2
        assert all(page["url"] for page in result)


@pytest.mark.asyncio
async def test_discover_pages_missing_api_key():
    """Test that missing API key raises ValueError."""
    with patch("accessvision.discovery.FIRECRAWL_API_KEY", None):
        with pytest.raises(ValueError, match="FIRECRAWL_API_KEY not set"):
            await discover_pages("https://example.com")


@pytest.mark.asyncio
async def test_discover_pages_api_failure():
    """Test handling of Firecrawl API failure."""
    mock_response_data = {
        "success": False,
        "error": "Rate limit exceeded"
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(ValueError, match="Firecrawl /map failed"):
            await discover_pages("https://example.com")


# ============ Tier 2: Integration tests with real API keys ============

@pytest.mark.integration
@pytest.mark.asyncio
async def test_discover_pages_integration():
    """Integration test: discover pages with real Firecrawl API."""
    # Skip if no API key
    pytest.importorskip("aiohttp")

    from accessvision.config import FIRECRAWL_API_KEY
    if not FIRECRAWL_API_KEY:
        pytest.skip("FIRECRAWL_API_KEY not set")

    # Use a simple test site
    try:
        result = await discover_pages("https://example.com")
    except ValueError as e:
        if "Unauthorized" in str(e) or "Invalid token" in str(e):
            pytest.skip(f"FIRECRAWL_API_KEY invalid: {e}")
        raise

    # Assertions
    assert isinstance(result, list)
    assert len(result) > 0
    # Each should have url and title
    for page in result:
        assert "url" in page
        assert page["url"]
        assert "title" in page
