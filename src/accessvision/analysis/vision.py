"""Vision analysis module - Gemini 3.1 Pro WCAG audit."""

import json
from typing import Any

from google import genai

from accessvision import config
from accessvision.models import PageCapture, SeverityLevel, Violation
from accessvision.prompts.vision_audit import build_vision_audit_prompt
from accessvision.analysis.coordinates import box_2d_to_pixel


async def analyze_page_vision(
    page_capture: PageCapture,
    client: genai.Client,
) -> list[Violation]:
    """Run vision-based WCAG analysis on a page capture.

    Args:
        page_capture: Complete page capture with screenshot, element map, etc.
        client: Gemini client (injected for testability)

    Returns:
        List of Violation objects detected by vision analysis
    """
    # Build the vision audit prompt
    prompt_text = build_vision_audit_prompt(
        page_url=page_capture.url,
        page_title=page_capture.title,
        markdown_description=page_capture.markdown_description,
        element_map=page_capture.element_map,
        axe_results=page_capture.axe_results,
    )

    # Upload screenshot to Gemini
    screenshot_bytes = page_capture.screenshot

    # Call Gemini 3.1 Pro with screenshot + prompt
    response = client.models.generate_content(
        model=config.GEMINI_PRO_MODEL,
        contents=[
            genai.content.Image(
                bytes=screenshot_bytes),
            prompt_text,
        ],
        config={
            "thinking": {"type": "MEDIUM"},
            "response_mime_type": "application/json",
        },
    )

    # Parse the JSON response
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Try to extract JSON from response if wrapped in markdown
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        result = json.loads(text)

    violations = []

    for v in result.get("violations", []):
        severity_str = v.get("severity", "Minor").upper()
        try:
            severity = SeverityLevel[severity_str]
        except KeyError:
            severity = SeverityLevel.MINOR

        box_2d = v.get("box_2d")
        # Convert to pixel coordinates if box_2d provided
        pixel_bbox = None
        if box_2d and len(box_2d) == 4:
            from config import SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT
            bbox = box_2d_to_pixel(box_2d, SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT)
            pixel_bbox = [bbox.y_min, bbox.x_min, bbox.y_max, bbox.x_max]

        violation = Violation(
            id=v.get("id", f"vision-{len(violations)+1}"),
            element_index=v.get("element_index"),
            box_2d=pixel_bbox,
            criterion=v.get("criterion", "unknown"),
            criterion_name=v.get("criterion_name", "Unknown"),
            severity=severity,
            description=v.get("description", ""),
            remediation_hint=v.get("remediation_hint", ""),
            detected_by="vision",
        )
        violations.append(violation)

    return violations


def parse_vision_response(response_text: str) -> dict[str, Any]:
    """Parse Gemini vision response, handling various JSON formats.

    Args:
        response_text: Raw response text from Gemini

    Returns:
        Parsed JSON dict with violations, passes, summary

    Raises:
        ValueError: If JSON cannot be parsed
    """
    # Try direct parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code blocks
    for marker in ["```json", "```"]:
        if marker in response_text:
            parts = response_text.split(marker)
            if len(parts) > 1:
                json_text = parts[1].split("```")[0].strip()
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    continue

    raise ValueError(f"Could not parse vision response as JSON: {response_text[:200]}...")
