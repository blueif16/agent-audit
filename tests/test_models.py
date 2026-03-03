"""Tests for core data models and scoring logic."""

from accessvision.models import (
    SeverityLevel,
    Violation,
    PageCapture,
    PageAudit,
    composite_score
)


def test_severity_weights():
    """Verify severity level numeric values."""
    assert SeverityLevel.CRITICAL == 4
    assert SeverityLevel.SERIOUS == 3
    assert SeverityLevel.MODERATE == 2
    assert SeverityLevel.MINOR == 1


def test_composite_score_function():
    """Test composite score calculation."""
    assert composite_score(10, SeverityLevel.CRITICAL) == 40
    assert composite_score(10, SeverityLevel.SERIOUS) == 30
    assert composite_score(8, SeverityLevel.MODERATE) == 16
    assert composite_score(6, SeverityLevel.MINOR) == 6


def test_page_audit_composite_score():
    """Test PageAudit composite score property."""
    capture = PageCapture(
        url="https://example.com",
        title="Test",
        priority_score=10,
        reason="Critical page",
        screenshot=b"",
        markdown_description="",
        axe_results={},
        element_map=[],
        accessibility_tree={}
    )

    violations = [
        Violation(
            id="v1",
            element_index=1,
            box_2d=[100, 100, 200, 200],
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.CRITICAL,
            description="Missing focus indicator",
            remediation_hint="Add :focus-visible style"
        ),
        Violation(
            id="v2",
            element_index=2,
            box_2d=[300, 300, 400, 400],
            criterion="1.4.1",
            criterion_name="Use of Color",
            severity=SeverityLevel.SERIOUS,
            description="Color-only indicator",
            remediation_hint="Add text label"
        )
    ]

    audit = PageAudit(
        page_capture=capture,
        violations=violations,
        annotated_screenshot=b"",
        solution_pr=""
    )

    # Max severity is CRITICAL (4), priority is 10
    assert audit.max_severity == SeverityLevel.CRITICAL
    assert audit.composite_score == 40


def test_violation_sorting():
    """Test that violations can be sorted by severity."""
    violations = [
        Violation("v1", None, None, "1.1.1", "Alt Text", SeverityLevel.MINOR, "", ""),
        Violation("v2", None, None, "2.4.7", "Focus", SeverityLevel.CRITICAL, "", ""),
        Violation("v3", None, None, "1.4.1", "Color", SeverityLevel.SERIOUS, "", ""),
        Violation("v4", None, None, "1.4.3", "Contrast", SeverityLevel.MODERATE, "", ""),
    ]

    sorted_violations = sorted(violations, key=lambda v: v.severity, reverse=True)

    assert sorted_violations[0].severity == SeverityLevel.CRITICAL
    assert sorted_violations[1].severity == SeverityLevel.SERIOUS
    assert sorted_violations[2].severity == SeverityLevel.MODERATE
    assert sorted_violations[3].severity == SeverityLevel.MINOR
