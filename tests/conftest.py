"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_page_capture():
    """Mock PageCapture for testing."""
    from accessvision.models import PageCapture

    return PageCapture(
        url="https://example.com/test",
        title="Test Page",
        priority_score=8,
        reason="High-traffic page",
        screenshot=b"fake_png_data",
        markdown_description="# Test Page\n\nSample content",
        axe_results={"violations": [], "passes": []},
        element_map=[],
        accessibility_tree={}
    )
