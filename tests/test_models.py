"""Tests for core data models and scoring logic."""

from accessvision.models import (
    SeverityLevel,
    Violation,
    PageAudit,
    composite_score
)


def test_severity_weights():
    """Verify severity level numeric weights."""
    assert SeverityLevel.CRITICAL == 4
    assert SeverityLevel.SERIOUS == 3
    assert SeverityLevel.MODERATE == 2
    assert SeverityLevel.MINOR == 1


def test_composite_score_function():
    """Test composite score calculation."""
    # Critical violation on high-priority page
    assert composite_score(10, SeverityLevel.CRITICAL) == 40

    # Minor violations on low-priority page
    assert composite_score(2, SeverityLevel.MINOR) == 2

    # Serious violation on medium-priority page
    assert composite_score(6, SeverityLevel.SERIOUS) == 18


def test_page_audit_composite_score():
    """Test PageAudit composite score property."""
    violations = [
        Violation(
            id="v1",
            element_index=1,
            box_2d=[100, 100, 200, 200],
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.CRITICAL,
            description="No focus indicator",
            remediation_hint="Add :focus-visible style",
            detected_by="vision"
        ),
        Violation(
            id="v2",
            element_index=2,
            box_2d=[300, 300, 400, 400],
            criterion="1.4.1",
            criterion_name="Use of Color",
            severity=SeverityLevel.SERIOUS,
            description="Color-only indicators",
            remediation_hint="Add text labels",
            detected_by="vision"
        )
    ]

    audit = PageAudit(
        url="https://example.com/checkout",
        title="Checkout",
        priority_score=10,
        violations=violations,
        annotated_screenshot=b"fake_png_data",
        solution_pr="# Fixes\n..."
    )

    # Max severity is CRITICAL (4), priority is 10
    assert audit.max_severity == SeverityLevel.CRITICAL
    assert audit.composite_score == 40


def test_page_audit_sort_order():
    """Test that pages sort correctly by composite score."""
    audits = [
        PageAudit(
            url="https://example.com/blog",
            title="Blog",
            priority_score=2,
            violations=[
                Violation(
                    id="v1", element_index=1, box_2d=None,
                    criterion="1.1.1", criterion_name="Alt Text",
                    severity=SeverityLevel.MINOR,
                    description="Minor issue",
                    remediation_hint="Fix it",
                    detected_by="axe-core"
                )
            ],
            annotated_screenshot=b"",
            solution_pr=""
        ),
        PageAudit(
            url="https://example.com/checkout",
            title="Checkout",
            priority_score=10,
            violations=[
                Violation(
                    id="v2", element_index=2, box_2d=None,
                    criterion="2.4.7", criterion_name="Focus Visible",
                    severity=SeverityLevel.CRITICAL,
                    description="Critical issue",
                    remediation_hint="Fix it",
                    detected_by="vision"
                )
            ],
            annotated_screenshot=b"",
            solution_pr=""
        ),
        PageAudit(
            url="https://example.com/login",
            title="Login",
            priority_score=10,
            violations=[
                Violation(
                    id="v3", element_index=3, box_2d=None,
                    criterion="1.4.1", criterion_name="Use of Color",
                    severity=SeverityLevel.SERIOUS,
                    description="Serious issue",
                    remediation_hint="Fix it",
                    detected_by="vision"
                )
            ],
            annotated_screenshot=b"",
            solution_pr=""
        )
    ]

    # Sort by composite score descending
    sorted_audits = sorted(audits, key=lambda a: a.composite_score, reverse=True)

    # Expected order: checkout (40), login (30), blog (2)
    assert sorted_audits[0].url == "https://example.com/checkout"
    assert sorted_audits[0].composite_score == 40
    assert sorted_audits[1].url == "https://example.com/login"
    assert sorted_audits[1].composite_score == 30
    assert sorted_audits[2].url == "https://example.com/blog"
    assert sorted_audits[2].composite_score == 2
