"""Report assembly and HTML generation."""

import base64
from pathlib import Path
from typing import List

from accessvision.models import PageAudit, SeverityLevel


# Severity colors for HTML
SEVERITY_COLORS = {
    SeverityLevel.CRITICAL: "#FF0000",
    SeverityLevel.SERIOUS: "#FF8C00",
    SeverityLevel.MODERATE: "#FFD700",
    SeverityLevel.MINOR: "#4169E1",
}

SEVERITY_NAMES = {
    SeverityLevel.CRITICAL: "Critical",
    SeverityLevel.SERIOUS: "Serious",
    SeverityLevel.MODERATE: "Moderate",
    SeverityLevel.MINOR: "Minor",
}


def _load_template() -> str:
    """Load the HTML template."""
    template_path = Path(__file__).parent / "template.html"
    return template_path.read_text()


def _count_by_source(violations: list) -> dict:
    """Count violations by detection source (axe-core vs vision)."""
    axe_count = sum(1 for v in violations if v.detected_by == "axe-core")
    vision_count = sum(1 for v in violations if v.detected_by == "vision")
    return {"axe": axe_count, "vision": vision_count}


def _count_by_severity(violations: list) -> dict:
    """Count violations by severity level."""
    counts = {sev: 0 for sev in SeverityLevel}
    for v in violations:
        counts[v.severity] += 1
    return counts


def _format_violations_table(violations: list) -> str:
    """Generate HTML table rows for violations."""
    if not violations:
        return "<tr><td colspan='6'>No violations detected.</td></tr>"

    rows = []
    for i, v in enumerate(violations, 1):
        color = SEVERITY_COLORS.get(v.severity, "#888888")
        severity_name = SEVERITY_NAMES.get(v.severity, "Unknown")
        row = f"""
        <tr>
            <td>{i}</td>
            <td><span class="severity-badge" style="background:{color}">{severity_name}</span></td>
            <td>{v.criterion}</td>
            <td>{v.criterion_name}</td>
            <td>{v.detected_by}</td>
            <td>{v.description}</td>
        </tr>
        """
        rows.append(row)

    return "".join(rows)


def _format_page_section(audit: PageAudit, idx: int) -> str:
    """Generate HTML for a single page section."""
    # Encode annotated screenshot as base64
    screenshot_b64 = base64.b64encode(audit.annotated_screenshot).decode("utf-8")

    violations_table = _format_violations_table(audit.violations)

    # Escape solution PR markdown for HTML display
    solution_html = audit.solution_pr.replace("&", "&amp;")
    solution_html = solution_html.replace("<", "&lt;").replace(">", "&gt;")
    solution_html = solution_html.replace("```", "&quot;&quot;&quot;")

    return f"""
    <div class="page-section" id="page-{idx}">
        <h2>{idx}. {audit.title}</h2>
        <p class="url"><a href="{audit.url}" target="_blank">{audit.url}</a></p>
        <p class="priority">Priority Score: {audit.priority_score} | Max Severity: {audit.max_severity.name} | Composite: {audit.composite_score}</p>

        <h3>Annotated Screenshot</h3>
        <img src="data:image/png;base64,{screenshot_b64}" alt="Annotated screenshot of {audit.title}" class="screenshot" />

        <h3>Violations ({len(audit.violations)})</h3>
        <table class="violations-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Severity</th>
                    <th>Criterion</th>
                    <th>Name</th>
                    <th>Source</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {violations_table}
            </tbody>
        </table>

        <h3>Fix Suggestions</h3>
        <pre class="solution">{solution_html}</pre>
    </div>
    """


def build_report(audits: List[PageAudit]) -> str:
    """Build HTML report from list of PageAudit objects.

    Args:
        audits: List of completed page audits

    Returns:
        Complete HTML report as string
    """
    if not audits:
        # Return empty report
        template = _load_template()
        return template.format(
            total_pages=0,
            total_violations=0,
            severity_breakdown="",
            axe_vs_vision="",
            pages_section=""
        )

    # Sort by composite score descending
    sorted_audits = sorted(audits, key=lambda a: a.composite_score, reverse=True)

    # Calculate summary statistics
    total_pages = len(sorted_audits)
    total_violations = sum(len(a.violations) for a in sorted_audits)

    # Severity breakdown
    all_violations = []
    for a in sorted_audits:
        all_violations.extend(a.violations)

    severity_counts = _count_by_severity(all_violations)
    severity_breakdown = "".join(
        f"<li>{SEVERITY_NAMES[sev]}: {count}</li>"
        for sev, count in severity_counts.items()
        if count > 0
    )

    # Axe vs Vision comparison
    source_counts = _count_by_source(all_violations)
    axe_vs_vision = f"""
    <div class="source-comparison">
        <div class="source-stat">
            <span class="source-label">axe-core</span>
            <span class="source-count">{source_counts['axe']}</span>
        </div>
        <div class="source-stat">
            <span class="source-label">Vision</span>
            <span class="source-count">{source_counts['vision']}</span>
        </div>
    </div>
    """

    # Generate page sections
    pages_section = "".join(
        _format_page_section(audit, idx + 1)
        for idx, audit in enumerate(sorted_audits)
    )

    # Fill template
    template = _load_template()
    return template.format(
        total_pages=total_pages,
        total_violations=total_violations,
        severity_breakdown=severity_breakdown,
        axe_vs_vision=axe_vs_vision,
        pages_section=pages_section
    )
