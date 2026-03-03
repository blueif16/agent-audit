"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return {
        "url": "https://example.com/checkout",
        "title": "Checkout",
        "priority_score": 10,
        "reason": "Revenue-critical form flow"
    }
