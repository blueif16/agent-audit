"""Tests for LLM-based page ranking."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from accessvision.ranking import rank_pages


@pytest.mark.asyncio
async def test_rank_pages_success():
    """Test successful page ranking with mocked Gemini response."""
    input_pages = [
        {"url": "https://example.com/", "title": "Home"},
        {"url": "https://example.com/blog", "title": "Blog"},
        {"url": "https://example.com/checkout", "title": "Checkout"}
    ]

    mock_ranked_response = [
        {
            "url": "https://example.com/checkout",
            "title": "Checkout",
            "priority_score": 10,
            "reason": "Revenue-critical form flow"
        },
        {
            "url": "https://example.com/",
            "title": "Home",
            "priority_score": 9,
            "reason": "Landing page, highest traffic"
        }
    ]

    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_ranked_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        # Call function
        result = await rank_pages(input_pages, n=2)

        # Assertions
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com/checkout"
        assert result[0]["priority_score"] == 10
        assert "reason" in result[0]
        assert result[1]["priority_score"] == 9


@pytest.mark.asyncio
async def test_rank_pages_validates_scores():
    """Test that invalid priority scores raise ValueError."""
    input_pages = [{"url": "https://example.com/", "title": "Home"}]

    mock_invalid_response = [
        {
            "url": "https://example.com/",
            "title": "Home",
            "priority_score": 15,  # Invalid: > 10
            "reason": "Test"
        }
    ]

    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_invalid_response)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        with pytest.raises(ValueError, match="Invalid priority_score"):
            await rank_pages(input_pages, n=1)


@pytest.mark.asyncio
async def test_rank_pages_missing_api_key():
    """Test that missing API key raises ValueError."""
    with patch("accessvision.ranking.GOOGLE_API_KEY", None):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY not set"):
            await rank_pages([], n=5)


@pytest.mark.asyncio
async def test_rank_pages_malformed_json():
    """Test handling of malformed JSON response."""
    input_pages = [{"url": "https://example.com/", "title": "Home"}]

    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        with pytest.raises(ValueError, match="Failed to parse ranking response"):
            await rank_pages(input_pages, n=1)


@pytest.mark.asyncio
async def test_rank_pages_returns_at_most_n():
    """Test that rank_pages returns at most N pages even if response has more."""
    input_pages = [{"url": f"https://example.com/{i}", "title": f"Page {i}"} for i in range(10)]

    mock_response_data = [
        {
            "url": f"https://example.com/{i}",
            "title": f"Page {i}",
            "priority_score": 10 - i,
            "reason": "Test"
        }
        for i in range(10)
    ]

    with patch("google.generativeai.GenerativeModel") as mock_model_class:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_data)
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        result = await rank_pages(input_pages, n=5)

        # Should return exactly 5 pages
        assert len(result) == 5
