"""Test core data models and scoring logic."""

from accessvision.models import SeverityLevel, Violation, composite_score


def test_severity_weights():
    """Verify severity enum values match spec."""
    assert SeverityLevel.CRITICAL == 4
    assert SeverityLevel.SERIOUS == 3
    assert SeverityLevel.MODERATE == 2
    assert SeverityLevel.MINOR == 1


def test_composite_score():
    """Test priority × severity scoring formula."""
    # Critical violation on high-priority page
    assert composite_score(10, SeverityLevel.CRITICAL) == 40

    # Minor violation on medium-priority page
    assert composite_score(6, SeverityLevel.MINOR) == 6

    # Serious violation on low-priority page
    assert composite_score(3, SeverityLevel.SERIOUS) == 9


def test_composite_score_sorting():
    """Verify pages sort correctly by composite score."""
    pages = [
        {"priority": 6, "severity": SeverityLevel.MINOR, "name": "contact"},
        {"priority": 10, "severity": SeverityLevel.CRITICAL, "name": "checkout"},
        {"priority": 8, "severity": SeverityLevel.SERIOUS, "name": "search"},
    ]

    scores = [(p["name"], composite_score(p["priority"], p["severity"])) for p in pages]
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    assert sorted_scores[0][0] == "checkout"  # 40
    assert sorted_scores[1][0] == "search"    # 24
    assert sorted_scores[2][0] == "contact"   # 6


def test_violation_creation(sample_violation_dict):
    """Test Violation dataclass instantiation."""
    v = Violation(
        id=sample_violation_dict["id"],
        element_index=sample_violation_dict["element_index"],
        box_2d=sample_violation_dict["box_2d"],
        criterion=sample_violation_dict["criterion"],
        criterion_name=sample_violation_dict["criterion_name"],
        severity=SeverityLevel.CRITICAL,
        description=sample_violation_dict["description"],
        remediation_hint=sample_violation_dict["remediation_hint"],
        detected_by=sample_violation_dict["detected_by"]
    )

    assert v.criterion == "2.4.7"
    assert v.severity == SeverityLevel.CRITICAL
    assert v.detected_by == "vision"
