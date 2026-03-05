"""Prompt for generating solution PR markdown."""

from accessvision.models import SeverityLevel, Violation


def build_solution_pr_prompt(
    page_url: str,
    page_title: str,
    priority_score: int,
    violations: list[Violation],
    axe_results: dict,
    markdown_description: str,
    element_map: list[dict],
) -> str:
    """Build prompt for generating solution PR markdown.

    Args:
        page_url: URL of the audited page
        page_title: Title of the page
        priority_score: Priority score (1-10) from discovery
        violations: List of violations detected
        axe_results: Raw axe-core results
        markdown_description: Firecrawl markdown description
        element_map: Element map from Playwright

    Returns:
        Prompt string for Gemini
    """
    # Count violations by source
    vision_violations = [v for v in violations if v.detected_by == "vision"]
    axe_violations = [v for v in violations if v.detected_by == "axe-core"]

    # Format violations for the prompt
    violations_text = _format_violations(violations)

    # Format axe results summary
    axe_summary = _format_axe_results(axe_results)

    # Format element map (limited to relevant interactive elements)
    elements_text = _format_element_map(element_map)

    prompt = f"""You are generating an accessibility fix PR for the page: {page_title} ({page_url})
Priority Score: {priority_score}/10

## Page Context (from Firecrawl)
```
{markdown_description[:2000]}
```

## Element Map (interactive elements)
{elements_text}

## Violations Detected
**Total: {len(violations)} violations**
- Vision analysis: {len(vision_violations)} violations
- axe-core: {len(axe_violations)} violations

{violations_text}

## axe-core Raw Results Summary
{axe_summary}

---

Generate a remediation document structured like a pull request. Each violation should have:
1. Severity level (Critical/Serious/Moderate/Minor)
2. WCAG criterion reference
3. Description of the problem
4. The affected element (from element map)
5. Concrete code fix with BEFORE and AFTER code blocks

Order violations by severity (Critical first).

For each fix:
- Identify the CSS selector or HTML element from the element map
- Provide specific CSS properties or HTML changes
- Show the exact before/after code

Format the output as markdown that could be directly used in a PR description."""
    return prompt


def _format_violations(violations: list[Violation]) -> str:
    """Format violations for the prompt."""
    if not violations:
        return "No violations detected."

    # Sort by severity
    sorted_violations = sorted(violations, key=lambda v: -v.severity.value)

    lines = []
    for v in sorted_violations:
        severity_name = v.severity.name
        lines.append(f"""
### {severity_name}: {v.criterion_name} ({v.criterion})
**Detected by:** {v.detected_by}
**Element index:** {v.element_index}

**Description:** {v.description}

**Remediation hint:** {v.remediation_hint}
""")
    return "\n".join(lines)


def _format_axe_results(axe_results: dict) -> str:
    """Format axe-core results summary."""
    violations = axe_results.get("violations", [])
    if not violations:
        return "No axe-core violations."

    lines = []
    for v in violations:
        impact = v.get("impact", "unknown")
        description = v.get("description", "")[:100]
        lines.append(f"- {v.get('id', 'unknown')}: {impact} - {description}")

    return f"{len(violations)} violations:\n" + "\n".join(lines)


def _format_element_map(element_map: list[dict], limit: int = 30) -> str:
    """Format element map for the prompt."""
    if not element_map:
        return "No element map available."

    lines = []
    for i, el in enumerate(element_map[:limit]):
        tag = el.get("tag", "unknown")
        text = el.get("text", "")[:50]
        role = el.get("role") or ""
        bbox = el.get("bbox", {})

        # Get identifying attributes
        attrs = []
        for attr in ["aria_label", "placeholder", "name", "type", "href"]:
            val = el.get(attr)
            if val:
                attrs.append(f"{attr}={val[:30]}")

        identifier = f"#{i} <{tag}>"
        if attrs:
            identifier += f" [{', '.join(attrs)}]"
        if text:
            identifier += f' "{text}"'

        lines.append(f"  {identifier}")

    if len(element_map) > limit:
        lines.append(f"  ... and {len(element_map) - limit} more elements")

    return "\n".join(lines)
