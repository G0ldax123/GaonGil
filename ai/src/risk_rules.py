"""Rule-based risk scoring for route accessibility ranking."""

from __future__ import annotations

from .accessibility_schema import DifficultyValue

RISK_WEIGHTS: dict[str, dict[str, int]] = {
    "wheelchair": {
        "stairs": 14,
        "curb": 9,
        "narrow_path": 8,
        "steep_slope": 10,
        "uneven_surface": 4,
        "obstacle": 8,
    },
    "stroller": {
        "stairs": 10,
        "curb": 8,
        "narrow_path": 4,
        "steep_slope": 5,
        "uneven_surface": 4,
        "obstacle": 4,
    },
    "elderly": {
        "stairs": 9,
        "curb": 3,
        "narrow_path": 2,
        "steep_slope": 10,
        "uneven_surface": 8,
        "obstacle": 3,
    },
    "crutches": {
        "stairs": 4,
        "curb": 9,
        "narrow_path": 3,
        "steep_slope": 9,
        "uneven_surface": 8,
        "obstacle": 3,
    },
}

UNKNOWN_WEIGHTS = {
    "wheelchair": 1.5,
    "stroller": 1.0,
    "elderly": 1.0,
    "crutches": 1.0,
}


def calculate_segment_risk(analysis: dict, user_type: str, segment: dict) -> int:
    """Score a segment using fixed rules, not free-form model text."""

    weights = RISK_WEIGHTS.get(user_type, RISK_WEIGHTS["wheelchair"])
    unknown_penalty = UNKNOWN_WEIGHTS.get(user_type, 1.0)
    detected = analysis.get("detected", {})
    risk_score = 0.0

    for key, weight in weights.items():
        value = detected.get(key, "unknown")
        if value == "true":
            risk_score += weight
        elif value == "unknown":
            risk_score += unknown_penalty

    if user_type == "elderly":
        if float(segment.get("distanceMeter", 0)) > 260:
            risk_score += 2
    elif user_type == "wheelchair":
        if detected.get("stairs") == "true":
            risk_score += 6

    return int(round(risk_score))


def route_accessibility_from_score(total_risk_score: int) -> str:
    """Map route score to the fixed accessibility label."""

    if total_risk_score <= 15:
        return "good"
    if total_risk_score <= 30:
        return "caution"
    return "bad"


def difficulty_from_score(total_risk_score: int) -> DifficultyValue:
    """Map route score to the fixed Korean difficulty label."""

    if total_risk_score <= 15:
        return "쉬움"
    if total_risk_score <= 30:
        return "보통"
    return "어려움"
