"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_violation_dict():
    """Hand-written violation for testing."""
    return {
        "id": "v1",
        "element_index": 14,
        "box_2d": [780, 350, 830, 550],
        "criterion": "2.4.7",
        "criterion_name": "Focus Visible",
        "severity": "Critical",
        "description": "Submit button has no visible focus indicator",
        "remediation_hint": "Add :focus-visible outline style",
        "detected_by": "vision"
    }


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return {
        "url": "https://example.com/checkout",
        "title": "Checkout",
        "priority_score": 10,
        "reason": "Revenue-critical form flow"
    }
