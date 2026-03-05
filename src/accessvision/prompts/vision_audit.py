"""Vision audit prompt for Gemini 3.1 Pro WCAG analysis."""

from typing import Any

# P0 WCAG criteria to evaluate (from FLOW.md Phase 3 Step A)
P0_CRITERIA = [
    {
        "id": "1.1.1",
        "name": "Non-text Content (Alt Text Quality)",
        "description": "Look at each image, read its alt text from element map, determine if the alt text accurately describes the visual content. Flag generic alt text ('image', 'photo', 'banner', 'logo'), missing alt text on informative images, or alt text that doesn't match what the image actually shows.",
    },
    {
        "id": "1.4.1",
        "name": "Use of Color",
        "description": "Scan for patterns where color alone conveys meaning: red/green for error/success states, colored dots for status, links distinguished from body text only by color (no underline), required fields marked only in red, chart/graph data series differentiated only by color.",
    },
    {
        "id": "1.4.3",
        "name": "Contrast (Minimum) - Images",
        "description": "Find text rendered over background images, gradients, or complex visual backgrounds where axe-core's CSS-based contrast check can't see the actual visual contrast. The screenshot reveals what the user actually sees.",
    },
    {
        "id": "2.4.4",
        "name": "Link Purpose (From Context)",
        "description": "Identify all links. Flag generic/repetitive link text ('Click Here', 'Learn More', 'Read More', 'Here') that appears multiple times without distinguishing context. Evaluate whether each link's purpose is clear.",
    },
    {
        "id": "2.4.7",
        "name": "Focus Visible",
        "description": "Examine interactive elements and assess whether they likely have visible focus indicators. Note: without actually tabbing through (that's Computer Use territory), the model can still check if focus styles are visually defined by examining element styling context.",
    },
    {
        "id": "4.1.2",
        "name": "Name, Role, Value - Label Match",
        "description": "Compare what's visually displayed on interactive elements (from the screenshot) against their programmatic names (from the element map's aria_label, text fields). Flag mismatches where a button shows 'Send' but has aria-label='Submit'.",
    },
    {
        "id": "1.4.5",
        "name": "Images of Text",
        "description": "Use vision to detect text baked into images (banners, buttons with image backgrounds containing text, infographics with embedded text). These should use real text instead.",
    },
    {
        "id": "3.3.1",
        "name": "Error Identification",
        "description": "Based on the page context (is this a form?), assess whether error states are likely communicated via text (not just color) and positioned near their related fields.",
    },
]


def build_vision_audit_prompt(
    page_url: str,
    page_title: str,
    markdown_description: str,
    element_map: list[dict[str, Any]],
    axe_results: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the vision audit prompt for Gemini 3.1 Pro.

    Args:
        page_url: URL of the page being audited
        page_title: Title of the page
        markdown_description: Firecrawl markdown description of the page
        element_map: List of element dicts with bbox, text, aria_label, etc.
        axe_results: Axe-core scan results

    Returns:
        List of content parts for Gemini API (prompt + image)
    """
    # Build criteria evaluation instructions
    criteria_instructions = "\n\n".join(
        f"### {c['id']} - {c['name']}\n{c['description']}"
        for c in P0_CRITERIA
    )

    # Format axe-core results for context
    axe_violations = axe_results.get("violations", [])
    axe_summary = f"Axe-core found {len(axe_violations)} violations: " + ", ".join(
        f"{v.get('id', 'unknown')}: {v.get('description', '')[:50]}..."
        for v in axe_violations[:5]
    ) + ("..." if len(axe_violations) > 5 else "")

    # Build element map summary (truncated for prompt size)
    element_summary = "Element Map (index -> tag, text, aria_label, bbox):\n"
    for i, elem in enumerate(element_map[:20]):  # Limit to first 20 elements
        bbox = elem.get("bbox", {})
        bbox_str = f"bbox=({bbox.get('x', 0)},{bbox.get('y', 0)},{bbox.get('w', 0)}x{bbox.get('h', 0)})" if bbox else "no bbox"
        text = elem.get("text", "")[:30] or "(no text)"
        aria = (elem.get("aria_label") or "")[:20] or "(no aria)"
        element_summary += f"  [{i}] <{elem.get('tag', '?')}> '{text}' aria='{aria}' {bbox_str}\n"
    if len(element_map) > 20:
        element_summary += f"  ... and {len(element_map) - 20} more elements\n"

    prompt = f"""You are an expert accessibility auditor. Analyze this webpage screenshot for WCAG 2.2 AA violations that axe-core cannot detect.

## Page Context
- URL: {page_url}
- Title: {page_title}
- Description: {markdown_description[:500]}...

## Axe-core Results (for cross-reference)
{axe_summary}
Axe-core has already caught these issues. Your job is to find VISUAL issues that axe-core cannot detect from the DOM.

## Element Map
{element_summary}

## P0 Criteria to Evaluate
Evaluate each of these criteria systematically. For each violation found, provide:
- element_index: which element from the element map (if applicable)
- box_2d: [y_min, x_min, y_max, x_max] in 1000x1000 grid (REQUIRED for visual violations)
- criterion: e.g., "2.4.7"
- criterion_name: e.g., "Focus Visible"
- severity: Critical, Serious, Moderate, or Minor
- description: what the violation is
- remediation_hint: how to fix it

{criteria_instructions}

## Output Format
Return a JSON object with:
{{
  "page_url": "{page_url}",
  "violations": [
    {{
      "id": "v1",
      "element_index": 14,
      "box_2d": [y_min, x_min, y_max, x_max],
      "criterion": "2.4.7",
      "criterion_name": "Focus Visible",
      "severity": "Critical",
      "description": "...",
      "remediation_hint": "..."
    }}
  ],
  "passes": ["1.1.1", "1.4.3"],  // criteria that passed
  "summary": "Brief summary of findings"
}}

Important: Only report violations you can identify from the screenshot and element map. Do not duplicate axe-core findings unless you can confirm the visual issue exists.
"""

    return prompt
