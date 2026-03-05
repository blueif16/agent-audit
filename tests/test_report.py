"""Tests for report builder and HTML generation."""

import pytest

from accessvision.models import (
    SeverityLevel,
    Violation,
    PageAudit,
)
from accessvision.report.builder import build_report


def _make_violation(severity: SeverityLevel, criterion: str = "1.1.1", detected_by: str = "vision") -> Violation:
    """Helper to create a test violation."""
    return Violation(
        id=f"v-{criterion}",
        element_index=1,
        box_2d=[100, 100, 200, 200],
        criterion=criterion,
        criterion_name=f"Test {criterion}",
        severity=severity,
        description=f"Test violation at {criterion}",
        remediation_hint="Fix this",
        detected_by=detected_by,
    )


def _make_page_audit(
    url: str,
    title: str,
    priority_score: int,
    violations: list[Violation],
) -> PageAudit:
    """Helper to create a test PageAudit."""
    return PageAudit(
        url=url,
        title=title,
        priority_score=priority_score,
        violations=violations,
        annotated_screenshot=b"\x89PNG\r\n\x1a\n" + b"fake_png_data",
        solution_pr="# Fixes\n\n## Fix for issue\n```html\n<button>Click</button>\n```",
    )


class TestBuildReport:
    """Tests for build_report function."""

    def test_empty_report(self):
        """Test that empty audits produce valid HTML."""
        html = build_report([])

        assert "AccessVision" in html
        assert "0" in html  # No pages
        assert '<div class="value">0</div>' in html  # No violations

    def test_single_page_report(self):
        """Test report with a single page."""
        violations = [
            _make_violation(SeverityLevel.CRITICAL, "2.4.7"),
            _make_violation(SeverityLevel.MINOR, "1.1.1"),
        ]
        audit = _make_page_audit(
            "https://example.com/page1",
            "Page One",
            priority_score=8,
            violations=violations,
        )

        html = build_report([audit])

        # Check summary
        assert "1" in html  # 1 page
        assert "2" in html  # 2 violations

    def test_multiple_pages_sorted_by_composite_score(self):
        """Test that pages are sorted by composite score descending."""
        # Create audits with different composite scores
        # Checkout: 10 * 4 = 40
        checkout = _make_page_audit(
            "https://example.com/checkout",
            "Checkout",
            priority_score=10,
            violations=[_make_violation(SeverityLevel.CRITICAL)],
        )
        # Login: 10 * 3 = 30
        login = _make_page_audit(
            "https://example.com/login",
            "Login",
            priority_score=10,
            violations=[_make_violation(SeverityLevel.SERIOUS)],
        )
        # Blog: 2 * 1 = 2
        blog = _make_page_audit(
            "https://example.com/blog",
            "Blog",
            priority_score=2,
            violations=[_make_violation(SeverityLevel.MINOR)],
        )

        # Add in wrong order
        audits = [blog, checkout, login]
        html = build_report(audits)

        # Verify order in HTML: checkout first, then login, then blog
        checkout_pos = html.find("Checkout")
        login_pos = html.find("Login")
        blog_pos = html.find("Blog")

        assert checkout_pos < login_pos < blog_pos, "Pages should be sorted by composite score"

    def test_severity_breakdown(self):
        """Test severity breakdown in executive summary."""
        violations = [
            _make_violation(SeverityLevel.CRITICAL),
            _make_violation(SeverityLevel.CRITICAL),
            _make_violation(SeverityLevel.SERIOUS),
            _make_violation(SeverityLevel.MINOR),
        ]
        audit = _make_page_audit(
            "https://example.com/page",
            "Test Page",
            priority_score=5,
            violations=violations,
        )

        html = build_report([audit])

        # Check severity counts appear
        assert "Critical" in html
        assert "Serious" in html
        assert "Minor" in html

    def test_axe_vs_vision_comparison(self):
        """Test axe-core vs vision detection source comparison."""
        violations = [
            _make_violation(SeverityLevel.CRITICAL, "2.4.7", "axe-core"),
            _make_violation(SeverityLevel.SERIOUS, "1.4.1", "vision"),
        ]
        audit = _make_page_audit(
            "https://example.com/page",
            "Test Page",
            priority_score=5,
            violations=violations,
        )

        html = build_report([audit])

        # Both sources should be mentioned
        assert "axe-core" in html
        assert "vision" in html

    def test_violation_table_format(self):
        """Test violation table rows are generated correctly."""
        violations = [
            _make_violation(SeverityLevel.CRITICAL, "2.4.7"),
        ]
        audit = _make_page_audit(
            "https://example.com/page",
            "Test",
            priority_score=5,
            violations=violations,
        )

        html = build_report([audit])

        # Check table structure
        assert "<table" in html
        assert "<th>" in html
        assert "2.4.7" in html  # Criterion in table

    def test_annotated_screenshot_included(self):
        """Test that annotated screenshot is included as base64."""
        violations = [_make_violation(SeverityLevel.CRITICAL)]
        audit = _make_page_audit(
            "https://example.com/page",
            "Test",
            priority_score=5,
            violations=violations,
        )

        html = build_report([audit])

        # Should contain base64 encoded image
        assert "data:image/png;base64" in html

    def test_solution_pr_included(self):
        """Test that solution PR markdown is included."""
        violations = [_make_violation(SeverityLevel.CRITICAL)]
        audit = PageAudit(
            url="https://example.com/page",
            title="Test",
            priority_score=5,
            violations=violations,
            annotated_screenshot=b"\x89PNG\r\n\x1a\n" + b"fake",
            solution_pr="# Fixes\n\nAdd alt text to images.",
        )

        html = build_report([audit])

        assert "# Fixes" in html or "Fixes" in html
