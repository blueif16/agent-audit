"""Tests for vision analysis module."""

import json
import pytest
from unittest.mock import MagicMock, patch

from accessvision.models import PageCapture, SeverityLevel, Violation
from accessvision.analysis.vision import parse_vision_response


class TestParseVisionResponse:
    """Tests for parsing Gemini vision responses."""

    def test_parse_clean_json(self):
        """Test parsing clean JSON response."""
        response = json.dumps({
            "violations": [
                {
                    "id": "v1",
                    "element_index": 14,
                    "box_2d": [780, 350, 830, 550],
                    "criterion": "2.4.7",
                    "criterion_name": "Focus Visible",
                    "severity": "Critical",
                    "description": "No focus indicator",
                    "remediation_hint": "Add outline",
                }
            ],
            "passes": ["1.1.1", "1.4.3"],
            "summary": "Found 1 violation"
        })

        result = parse_vision_response(response)

        assert len(result["violations"]) == 1
        assert result["violations"][0]["criterion"] == "2.4.7"

    def test_parse_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown code block."""
        response = '''Here is the analysis:

```json
{
  "violations": [
    {
      "id": "v1",
      "criterion": "2.4.7",
      "severity": "Serious"
    }
  ],
  "passes": ["1.1.1"],
  "summary": "Test"
}
```

Let me know if you need anything else.'''

        result = parse_vision_response(response)

        assert len(result["violations"]) == 1
        assert result["violations"][0]["criterion"] == "2.4.7"

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_vision_response("This is not JSON at all")

        assert "Could not parse" in str(exc_info.value)


class TestVisionPromptStructure:
    """Tests that verify prompt contains all P0 criteria."""

    def test_prompt_contains_all_p0_criteria(self):
        """Verify the prompt evaluates all 8 P0 criteria."""
        from accessvision.prompts.vision_audit import build_vision_audit_prompt

        prompt = build_vision_audit_prompt(
            page_url="https://example.com",
            page_title="Test Page",
            markdown_description="A test page",
            element_map=[{"index": 0, "tag": "div", "text": "test"}],
            axe_results={"violations": []},
        )

        # Check all 8 P0 criteria are mentioned
        p0_ids = ["1.1.1", "1.4.1", "1.4.3", "2.4.4", "2.4.7", "4.1.2", "1.4.5", "3.3.1"]
        for criterion_id in p0_ids:
            assert criterion_id in prompt, f"Missing criterion {criterion_id}"

    def test_prompt_mentions_criterion_names(self):
        """Verify the prompt contains criterion names."""
        from accessvision.prompts.vision_audit import build_vision_audit_prompt

        prompt = build_vision_audit_prompt(
            page_url="https://example.com",
            page_title="Test Page",
            markdown_description="A test page",
            element_map=[],
            axe_results={"violations": []},
        )

        # Check criterion names
        assert "Alt Text" in prompt or "Non-text Content" in prompt
        assert "Focus Visible" in prompt
        assert "Use of Color" in prompt

    def test_prompt_includes_axe_summary(self):
        """Verify the prompt includes axe-core results for cross-reference."""
        from accessvision.prompts.vision_audit import build_vision_audit_prompt

        axe_results = {
            "violations": [
                {"id": "img-alt", "description": "Image must have alt text"}
            ]
        }

        prompt = build_vision_audit_prompt(
            page_url="https://example.com",
            page_title="Test Page",
            markdown_description="A test page",
            element_map=[],
            axe_results=axe_results,
        )

        assert "axe-core" in prompt.lower()
        assert "img-alt" in prompt


class TestViolationCreation:
    """Tests for Violation model with vision data."""

    def test_violation_from_vision(self):
        """Test creating a Violation from vision analysis."""
        violation = Violation(
            id="v1",
            element_index=14,
            box_2d=[780, 350, 830, 550],
            criterion="2.4.7",
            criterion_name="Focus Visible",
            severity=SeverityLevel.CRITICAL,
            description="The submit button has no visible focus indicator",
            remediation_hint="Add :focus-visible { outline: 2px solid blue; }",
            detected_by="vision",
        )

        assert violation.id == "v1"
        assert violation.element_index == 14
        assert violation.box_2d == [780, 350, 830, 550]
        assert violation.severity == SeverityLevel.CRITICAL
        assert violation.detected_by == "vision"

    def test_violation_severity_ordering(self):
        """Test that severity ordering works correctly."""
        violations = [
            Violation(id="v1", element_index=None, box_2d=None, criterion="1", criterion_name="C1",
                     severity=SeverityLevel.MINOR, description="", remediation_hint="", detected_by="vision"),
            Violation(id="v2", element_index=None, box_2d=None, criterion="2", criterion_name="C2",
                     severity=SeverityLevel.CRITICAL, description="", remediation_hint="", detected_by="vision"),
            Violation(id="v3", element_index=None, box_2d=None, criterion="3", criterion_name="C3",
                     severity=SeverityLevel.MODERATE, description="", remediation_hint="", detected_by="vision"),
        ]

        # Sort by severity descending
        violations.sort(key=lambda v: -v.severity.value)

        assert violations[0].severity == SeverityLevel.CRITICAL
        assert violations[1].severity == SeverityLevel.MODERATE
        assert violations[2].severity == SeverityLevel.MINOR
