"""Tests for merging vision and axe-core violations."""

import pytest
from accessvision.models import SeverityLevel, Violation
from accessvision.analysis.merge import merge_violations, categorize_by_severity


class TestMergeViolations:
    """Tests for merge_violations function."""

    def test_empty_lists(self):
        """Test merging empty lists."""
        result = merge_violations([], [])

        assert result == []

    def test_only_vision_violations(self):
        """Test when only vision violations exist."""
        vision = [
            Violation(
                id="v1",
                element_index=1,
                box_2d=[100, 200, 300, 400],
                criterion="2.4.7",
                criterion_name="Focus Visible",
                severity=SeverityLevel.CRITICAL,
                description="No focus indicator",
                remediation_hint="Add outline",
                detected_by="vision",
            )
        ]

        result = merge_violations(vision, [])

        assert len(result) == 1
        assert result[0].id == "v1"

    def test_only_axe_violations(self):
        """Test when only axe violations exist."""
        axe = [
            Violation(
                id="a1",
                element_index=2,
                box_2d=None,
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.SERIOUS,
                description="Missing alt text",
                remediation_hint="Add alt",
                detected_by="axe-core",
            )
        ]

        result = merge_violations([], axe)

        assert len(result) == 1
        assert result[0].id == "a1"

    def test_deduplicate_same_element_and_criterion(self):
        """Test deduplication when same element + criterion detected by both."""
        vision = Violation(
            id="v1",
            element_index=1,
            box_2d=[100, 200, 300, 400],
            criterion="1.1.1",
            criterion_name="Alt Text",
            severity=SeverityLevel.SERIOUS,
            description="Generic alt text",
            remediation_hint="Use specific text",
            detected_by="vision",
        )
        axe = Violation(
            id="a1",
            element_index=1,
            box_2d=None,
            criterion="1.1.1",
            criterion_name="Non-text Content",
            severity=SeverityLevel.MODERATE,
            description="Missing alt",
            remediation_hint="Add alt",
            detected_by="axe-core",
        )

        result = merge_violations([vision], [axe])

        assert len(result) == 1
        assert result[0].severity == SeverityLevel.SERIOUS
        assert result[0].detected_by == "both"

    def test_keep_higher_severity(self):
        """Test that higher severity is kept when duplicate."""
        vision = Violation(
            id="v1",
            element_index=1,
            box_2d=[100, 200, 300, 400],
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.CRITICAL,
            description="No focus",
            remediation_hint="Add outline",
            detected_by="vision",
        )
        axe = Violation(
            id="a1",
            element_index=1,
            box_2d=None,
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.MINOR,
            description="Poor focus",
            remediation_hint="Improve",
            detected_by="axe-core",
        )

        result = merge_violations([vision], [axe])

        assert len(result) == 1
        assert result[0].severity == SeverityLevel.CRITICAL
        assert result[0].id == "v1"

    def test_different_criteria_not_deduplicated(self):
        """Test that different criteria are not deduplicated."""
        vision = Violation(
            id="v1",
            element_index=1,
            box_2d=[100, 200, 300, 400],
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.CRITICAL,
            description="No focus",
            remediation_hint="Add outline",
            detected_by="vision",
        )
        axe = Violation(
            id="a1",
            element_index=1,
            box_2d=None,
            criterion="1.1.1",
            criterion_name="Alt Text",
            severity=SeverityLevel.SERIOUS,
            description="Missing alt",
            remediation_hint="Add alt",
            detected_by="axe-core",
        )

        result = merge_violations([vision], [axe])

        assert len(result) == 2

    def test_sorted_by_severity(self):
        """Test that result is sorted by severity descending."""
        violations = [
            Violation(
                id="v1",
                element_index=None,
                box_2d=None,
                criterion="1",
                criterion_name="Minor",
                severity=SeverityLevel.MINOR,
                description="Minor issue",
                remediation_hint="Fix",
                detected_by="vision",
            ),
            Violation(
                id="v2",
                element_index=None,
                box_2d=None,
                criterion="2",
                criterion_name="Critical",
                severity=SeverityLevel.CRITICAL,
                description="Critical issue",
                remediation_hint="Fix",
                detected_by="vision",
            ),
            Violation(
                id="v3",
                element_index=None,
                box_2d=None,
                criterion="3",
                criterion_name="Serious",
                severity=SeverityLevel.SERIOUS,
                description="Serious issue",
                remediation_hint="Fix",
                detected_by="vision",
            ),
        ]

        result = merge_violations(violations, [])

        assert result[0].severity == SeverityLevel.CRITICAL
        assert result[1].severity == SeverityLevel.SERIOUS
        assert result[2].severity == SeverityLevel.MINOR


class TestCategorizeBySeverity:
    """Tests for categorize_by_severity function."""

    def test_categorize_mixed_violations(self):
        """Test categorizing violations with mixed severities."""
        violations = [
            Violation(id="v1", element_index=None, box_2d=None, criterion="1", criterion_name="C1",
                     severity=SeverityLevel.CRITICAL, description="", remediation_hint="", detected_by="vision"),
            Violation(id="v2", element_index=None, box_2d=None, criterion="2", criterion_name="C2",
                     severity=SeverityLevel.MINOR, description="", remediation_hint="", detected_by="vision"),
            Violation(id="v3", element_index=None, box_2d=None, criterion="3", criterion_name="C3",
                     severity=SeverityLevel.SERIOUS, description="", remediation_hint="", detected_by="vision"),
        ]

        result = categorize_by_severity(violations)

        assert len(result[SeverityLevel.CRITICAL]) == 1
        assert len(result[SeverityLevel.SERIOUS]) == 1
        assert len(result[SeverityLevel.MINOR]) == 1
        assert len(result[SeverityLevel.MODERATE]) == 0

    def test_categorize_empty(self):
        """Test categorizing empty list."""
        result = categorize_by_severity([])

        for level in SeverityLevel:
            assert len(result[level]) == 0
