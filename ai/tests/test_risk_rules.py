"""Tests for user-type specific risk scoring rules."""

from ai.src.risk_rules import calculate_segment_risk


def test_wheelchair_stairs_segment_has_high_risk() -> None:
    analysis = {
        "detected": {
            "stairs": "true",
            "curb": "false",
            "narrow_path": "false",
            "steep_slope": "false",
            "uneven_surface": "false",
            "obstacle": "false",
        }
    }
    score = calculate_segment_risk(analysis, "wheelchair", {"slopePercent": 1.0, "distanceMeter": 100})
    assert score >= 20


def test_user_types_can_score_same_segment_differently() -> None:
    analysis = {
        "detected": {
            "stairs": "true",
            "curb": "true",
            "narrow_path": "false",
            "steep_slope": "false",
            "uneven_surface": "false",
            "obstacle": "false",
        }
    }
    segment = {"slopePercent": 2.0, "distanceMeter": 100}
    wheelchair_score = calculate_segment_risk(analysis, "wheelchair", segment)
    stroller_score = calculate_segment_risk(analysis, "stroller", segment)
    assert wheelchair_score != stroller_score
