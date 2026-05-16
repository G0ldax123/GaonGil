"""Shared schema helpers for fixed AI/data JSON output."""

from __future__ import annotations

from typing import Dict, Final, Literal, TypedDict

DetectionValue = Literal["true", "false", "unknown"]
SeverityValue = Literal["low", "medium", "high"]
AccessibilityValue = Literal["good", "caution", "bad"]
DifficultyValue = Literal["쉬움", "보통", "어려움"]
UserType = Literal["wheelchair", "stroller", "elderly", "crutches"]

DETECTION_KEYS: Final[tuple[str, ...]] = (
    "stairs",
    "curb",
    "narrow_path",
    "steep_slope",
    "uneven_surface",
    "obstacle",
)

DETECTION_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "stairs": ("stairs",),
    "curb": ("curb",),
    "narrow_path": ("narrow_path", "narrowRoad"),
    "steep_slope": ("steep_slope", "steepRoad"),
    "uneven_surface": ("uneven_surface",),
    "obstacle": ("obstacle", "otherObstacle"),
}


class DetectedSchema(TypedDict):
    stairs: DetectionValue
    curb: DetectionValue
    narrow_path: DetectionValue
    steep_slope: DetectionValue
    uneven_surface: DetectionValue
    obstacle: DetectionValue


class SegmentAnalysisSchema(TypedDict):
    detected: DetectedSchema
    severity: SeverityValue
    accessibility: AccessibilityValue
    risk_factors: list[str]
    one_line_summary: str
    reason: str


def empty_detected() -> DetectedSchema:
    """Return the default detection payload for a segment."""

    return {
        "stairs": "unknown",
        "curb": "unknown",
        "narrow_path": "unknown",
        "steep_slope": "unknown",
        "uneven_surface": "unknown",
        "obstacle": "unknown",
    }


def normalize_detected(raw_detected: Dict[str, str] | None) -> DetectedSchema:
    """Clamp detection values to the supported true/false/unknown set."""

    detected = empty_detected()
    if not raw_detected:
        return detected

    for key in DETECTION_KEYS:
        value = "unknown"
        for alias in DETECTION_ALIASES[key]:
            if alias in raw_detected:
                value = raw_detected.get(alias, "unknown")
                break
        detected[key] = value if value in {"true", "false", "unknown"} else "unknown"
    return detected
