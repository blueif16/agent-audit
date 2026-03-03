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
    box_2d: Optional[list[int]]  # [y_min, x_min, y_max, x_max] in 1000x1000 grid
    criterion: str  # e.g., "2.4.7"
    criterion_name: str
    severity: SeverityLevel
    description: str
    remediation_hint: str
    detected_by: str  # "axe-core" or "vision"


@dataclass
class PageCapture:
    """Complete capture data for a single page."""
    url: str
    title: str
    priority_score: int  # 1-10, assigned during discovery
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
    violations: list[Violation]
    annotated_screenshot: bytes  # PNG with visual markers
    solution_pr: str  # Markdown fix document

    @property
    def max_severity(self) -> SeverityLevel:
        """Return the highest severity level among all violations."""
        if not self.violations:
            return SeverityLevel.MINOR
        return max(v.severity for v in self.violations)

    @property
    def composite_score(self) -> int:
        """Calculate priority × severity weight for report ordering."""
        return self.priority_score * self.max_severity.value


def composite_score(priority_score: int, max_severity: SeverityLevel) -> int:
    """Calculate composite score for page ordering.

    Args:
        priority_score: Page priority (1-10) from discovery phase
        max_severity: Highest severity level among page violations

    Returns:
        Composite score (priority × severity weight)
    """
    return priority_score * max_severity.value
