"""Tests for solution_pr module."""

import json
import pytest
from unittest.mock import MagicMock, patch

from accessvision.models import PageCapture, SeverityLevel, Violation
from accessvision.output.solution_pr import generate_solution_pr
from accessvision.prompts.solution_pr import build_solution_pr_prompt


class TestBuildSolutionPrPrompt:
    """Tests for the prompt builder function."""

    def test_prompt_contains_all_required_sections(self):
        """Verify prompt contains all required sections."""
        violations = [
            Violation(
                id="v1",
                element_index=0,
                box_2d=[100, 100, 200, 200],
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Image missing alt text",
                remediation_hint="Add alt attribute",
                detected_by="vision",
            ),
            Violation(
                id="v2",
                element_index=1,
                box_2d=[200, 200, 300, 300],
                criterion="2.4.7",
                criterion_name="Focus Visible",
                severity=SeverityLevel.MINOR,
                description="Focus indicator not visible",
                remediation_hint="Add outline style",
                detected_by="axe-core",
            ),
        ]

        prompt = build_solution_pr_prompt(
            page_url="https://example.com",
            page_title="Test Page",
            priority_score=8,
            violations=violations,
            axe_results={"violations": []},
            markdown_description="# Test Page\nThis is a test.",
            element_map=[
                {
                    "index": 0,
                    "tag": "img",
                    "text": "",
                    "aria_label": None,
                    "placeholder": None,
                    "name": None,
                    "type": None,
                    "href": None,
                    "bbox": {"x": 100, "y": 100, "w": 100, "h": 100},
                },
                {
                    "index": 1,
                    "tag": "button",
                    "text": "Submit",
                    "aria_label": None,
                    "placeholder": None,
                    "name": None,
                    "type": None,
                    "href": None,
                    "bbox": {"x": 200, "y": 200, "w": 100, "h": 50},
                },
            ],
        )

        # Check required sections
        assert "https://example.com" in prompt
        assert "Test Page" in prompt
        assert "Priority Score: 8" in prompt
        assert "Page Context" in prompt or "##" in prompt
        assert "Violations Detected" in prompt
        assert "1.1.1" in prompt  # Critical criterion
        assert "2.4.7" in prompt  # Minor criterion
        assert "Critical" in prompt
        assert "Minor" in prompt

    def test_prompt_sorts_violations_by_severity(self):
        """Verify violations are sorted by severity (Critical first)."""
        violations = [
            Violation(
                id="v1",
                element_index=0,
                box_2d=None,
                criterion="2.4.7",
                criterion_name="Focus Visible",
                severity=SeverityLevel.MINOR,
                description="Minor issue",
                remediation_hint="Fix it",
                detected_by="vision",
            ),
            Violation(
                id="v2",
                element_index=1,
                box_2d=None,
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Critical issue",
                remediation_hint="Fix it",
                detected_by="axe-core",
            ),
        ]

        prompt = build_solution_pr_prompt(
            page_url="https://example.com",
            page_title="Test",
            priority_score=5,
            violations=violations,
            axe_results={"violations": []},
            markdown_description="Test",
            element_map=[],
        )

        # Critical should appear before Minor
        critical_pos = prompt.find("Critical")
        minor_pos = prompt.find("Minor")
        assert critical_pos < minor_pos, "Critical should appear before Minor in prompt"

    def test_prompt_contains_before_after_instructions(self):
        """Verify prompt asks for before/after code blocks."""
        violations = [
            Violation(
                id="v1",
                element_index=0,
                box_2d=None,
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Test",
                remediation_hint="Test",
                detected_by="vision",
            ),
        ]

        prompt = build_solution_pr_prompt(
            page_url="https://example.com",
            page_title="Test",
            priority_score=5,
            violations=violations,
            axe_results={"violations": []},
            markdown_description="Test",
            element_map=[],
        )

        assert "BEFORE" in prompt or "before" in prompt.lower()
        assert "AFTER" in prompt or "after" in prompt.lower()


class TestGenerateSolutionPr:
    """Tests for the solution PR generation function."""

    @pytest.mark.asyncio
    async def test_generate_solution_pr_returns_markdown(self):
        """Test that generate_solution_pr returns markdown string."""
        # Create mock PageCapture (without actual screenshot bytes for test)
        page_capture = PageCapture(
            url="https://example.com",
            title="Example Domain",
            priority_score=8,
            reason="Test page",
            screenshot=b"fake-png-bytes",  # Required field but mocked
            markdown_description="# Example Domain\n\nTest content",
            axe_results={"violations": []},
            element_map=[
                {
                    "index": 0,
                    "tag": "img",
                    "text": "logo",
                    "aria_label": None,
                    "placeholder": None,
                    "name": None,
                    "type": None,
                    "href": None,
                    "bbox": {"x": 0, "y": 0, "w": 100, "h": 100},
                },
            ],
            accessibility_tree={},
        )

        violations = [
            Violation(
                id="v1",
                element_index=0,
                box_2d=[100, 100, 200, 200],
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Image missing alt text",
                remediation_hint="Add alt attribute",
                detected_by="vision",
            ),
            Violation(
                id="v2",
                element_index=1,
                box_2d=[200, 200, 300, 300],
                criterion="2.4.7",
                criterion_name="Focus Visible",
                severity=SeverityLevel.MINOR,
                description="Focus indicator not visible",
                remediation_hint="Add outline style",
                detected_by="axe-core",
            ),
        ]

        # Mock Gemini client response
        mock_response_text = """# Accessibility Fix PR

## Critical: Non-text Content (1.1.1)

**Description:** Image missing alt text

**Before:**
```html
<img src="logo.png">
```

**After:**
```html
<img src="logo.png" alt="Company Logo">
```

## Minor: Focus Visible (2.4.7)

**Description:** Focus indicator not visible

**Before:**
```css
button { outline: none; }
```

**After:**
```css
button:focus { outline: 2px solid blue; }
```
"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_response_text
            mock_client.models.generate_content = MagicMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await generate_solution_pr(page_capture, violations)

            # Verify result is a string
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_solution_pr_severity_ordering(self):
        """Test that output contains severity-ordered sections."""
        page_capture = PageCapture(
            url="https://example.com",
            title="Test",
            priority_score=5,
            reason="Test",
            screenshot=b"fake",
            markdown_description="Test",
            axe_results={"violations": []},
            element_map=[],
            accessibility_tree={},
        )

        violations = [
            Violation(
                id="v-minor",
                element_index=0,
                box_2d=None,
                criterion="2.4.7",
                criterion_name="Focus Visible",
                severity=SeverityLevel.MINOR,
                description="Minor issue",
                remediation_hint="Fix it",
                detected_by="vision",
            ),
            Violation(
                id="v-critical",
                element_index=1,
                box_2d=None,
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Critical issue",
                remediation_hint="Fix it",
                detected_by="axe-core",
            ),
        ]

        mock_response_text = """# Fixes

## Critical: Non-text Content (1.1.1)
Critical content here

## Minor: Focus Visible (2.4.7)
Minor content here
"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_response_text
            mock_client.models.generate_content = MagicMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await generate_solution_pr(page_capture, violations)

            # Check severity ordering - Critical should appear before Minor
            critical_section = result.find("Critical:")
            minor_section = result.find("Minor:")
            assert critical_section < minor_section, "Critical should appear before Minor in output"

    @pytest.mark.asyncio
    async def test_generate_solution_pr_contains_code_blocks(self):
        """Test that output contains code blocks (css or html)."""
        page_capture = PageCapture(
            url="https://example.com",
            title="Test",
            priority_score=5,
            reason="Test",
            screenshot=b"fake",
            markdown_description="Test",
            axe_results={"violations": []},
            element_map=[],
            accessibility_tree={},
        )

        violations = [
            Violation(
                id="v1",
                element_index=0,
                box_2d=None,
                criterion="1.1.1",
                criterion_name="Non-text Content",
                severity=SeverityLevel.CRITICAL,
                description="Test",
                remediation_hint="Test",
                detected_by="vision",
            ),
        ]

        mock_response_text = """# Fixes

## Critical: Non-text Content

**Before:**
```html
<img src="test.png">
```

**After:**
```html
<img src="test.png" alt="Test image">
```

Some CSS:
```css
.element { color: red; }
```
"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = mock_response_text
            mock_client.models.generate_content = MagicMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            result = await generate_solution_pr(page_capture, violations)

            # Check for code blocks
            assert "```html" in result or "```css" in result, "Output should contain code blocks"

    @pytest.mark.asyncio
    async def test_generate_solution_pr_missing_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        page_capture = PageCapture(
            url="https://example.com",
            title="Test",
            priority_score=5,
            reason="Test",
            screenshot=b"fake",
            markdown_description="Test",
            axe_results={},
            element_map=[],
            accessibility_tree={},
        )

        with patch("accessvision.output.solution_pr.config") as mock_config:
            mock_config.GOOGLE_API_KEY = None

            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                await generate_solution_pr(page_capture, [])
