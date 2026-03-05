"""Merge vision and axe-core violations, deduplicating where appropriate."""

from typing import Optional, Tuple

from accessvision.models import SeverityLevel, Violation


def merge_violations(
    vision_violations: list[Violation],
    axe_violations: list[Violation],
) -> list[Violation]:
    """Merge vision and axe-core violations, deduplicating by element + criterion.

    When the same issue is detected by both vision and axe-core, keep the
    higher severity one and mark it as detected_by "both".

    Args:
        vision_violations: Violations from vision analysis
        axe_violations: Violations from axe-core

    Returns:
        Deduplicated, merged list of violations
    """
    # Create a map for deduplication: (element_index, criterion) -> violation
    merged: dict[Tuple[Optional[int], str], Violation] = {}

    # Process all violations
    all_violations = vision_violations + axe_violations

    for v in all_violations:
        key = (v.element_index, v.criterion)

        if key not in merged:
            merged[key] = v
        else:
            existing = merged[key]
            # Check if different sources detected the same issue
            different_sources = existing.detected_by != v.detected_by

            # Keep the higher severity
            if v.severity.value > existing.severity.value:
                # If we had one from each, mark as "both"
                if different_sources:
                    merged[key] = Violation(
                        id=existing.id,
                        element_index=v.element_index,
                        box_2d=v.box_2d or existing.box_2d,
                        criterion=v.criterion,
                        criterion_name=v.criterion_name,
                        severity=v.severity,
                        description=v.description,
                        remediation_hint=v.remediation_hint,
                        detected_by="both",
                    )
                else:
                    merged[key] = v
            elif v.severity.value == existing.severity.value:
                # Same severity, prefer the one with more detail or mark as both
                if different_sources:
                    merged[key] = Violation(
                        id=existing.id,
                        element_index=v.element_index,
                        box_2d=v.box_2d or existing.box_2d,
                        criterion=v.criterion,
                        criterion_name=v.criterion_name,
                        severity=v.severity,
                        description=v.description,
                        remediation_hint=v.remediation_hint,
                        detected_by="both",
                    )
                elif len(v.description) > len(existing.description):
                    merged[key] = v
            elif different_sources:
                # Lower severity but from different source - mark as both
                merged[key] = Violation(
                    id=existing.id,
                    element_index=v.element_index,
                    box_2d=v.box_2d or existing.box_2d,
                    criterion=v.criterion,
                    criterion_name=v.criterion_name,
                    severity=existing.severity,  # Keep higher severity
                    description=existing.description,
                    remediation_hint=existing.remediation_hint,
                    detected_by="both",
                )

    # Return sorted by severity (Critical first)
    result = list(merged.values())
    result.sort(key=lambda v: (-v.severity.value, v.criterion))

    return result


def categorize_by_severity(violations: list[Violation]) -> dict[SeverityLevel, list[Violation]]:
    """Group violations by severity level.

    Args:
        violations: List of violations

    Returns:
        Dict mapping severity to list of violations
    """
    categorized: dict[SeverityLevel, list[Violation]] = {
        SeverityLevel.CRITICAL: [],
        SeverityLevel.SERIOUS: [],
        SeverityLevel.MODERATE: [],
        SeverityLevel.MINOR: [],
    }

    for v in violations:
        categorized[v.severity].append(v)

    return categorized
