"""Core data models for AccessVision."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class SeverityLevel(IntEnum):
    """WCAG violation severity levels with numeric weights for scoring."""
    CRITICAL = 4
    SERIOUS = 3
    MODERATE = 2
    MINOR = 1


@dataclass
class Violation:
    """A single WCAG violation detected on a page."""
    id: str
    element_index: Optional[int]
    box_2d: list[int]  # [y_min, x_min, y_max, x_max] in 1000x1000 grid
    criterion: str  # e.g. "2.4.7"
    criterion_name: str
    severity: SeverityLevel
    description: str
    remediation_hint: str
    detected_by: str = "vision"  # "vision" or "axe"


@dataclass
class PageCapture:
    """Complete capture data for a single page."""
    url: str
    title: str
    priority_score: int  # 1-10, assigned in Phase 1
    reason: str  # Why this page was prioritized
    screenshot: bytes  # PNG from Playwright
    markdown_description: str  # from Firecrawl
    axe_results: dict  # from axe-core
    element_map: list[dict]  # from Playwright
    accessibility_tree: dict  # from Playwright


@dataclass
class PageAudit:
    """Complete audit results for a single page."""
    url: str
    title: str
    priority_score: int
    max_severity: SeverityLevel
    violations: list[Violation]
    annotated_screenshot: bytes  # PNG with colored overlays
    solution_pr_markdown: str
    passes: list[str]  # WCAG criteria that passed
    summary: str


def composite_score(priority_score: int, max_severity: SeverityLevel) -> int:
    """
    Calculate composite score for sorting pages in final report.

    Higher scores = more urgent to fix.
    Formula: priority_score × severity_weight
    """
    return priority_score * max_severity.value
