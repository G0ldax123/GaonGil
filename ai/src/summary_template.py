"""Template-based summary builders to avoid unstable free-form generation."""

from __future__ import annotations

from typing import Iterable


USER_LABELS = {
    "wheelchair": "휠체어 이용자",
    "stroller": "유모차 이용자",
    "elderly": "노약자",
    "crutches": "목발 이용자",
}


def _join_risk_factors(risk_factors: Iterable[str]) -> str:
    values = [value for value in risk_factors if value]
    return ", ".join(values) if values else "뚜렷한 위험 요소"


def build_segment_summary(segment_analysis: dict, user_type: str) -> str:
    """Create a short card sentence for a segment analysis result."""

    label = USER_LABELS.get(user_type, user_type)
    risk_factors = segment_analysis.get("risk_factors", [])
    accessibility = segment_analysis.get("accessibility", "caution")

    if accessibility == "good":
        return f"{label} 기준, 비교적 이동이 수월한 구간입니다."
    if accessibility == "bad":
        return f"{_join_risk_factors(risk_factors)} 때문에 {label}는 우회가 필요한 구간입니다."
    return f"{_join_risk_factors(risk_factors)} 때문에 {label}는 주의가 필요한 구간입니다."


def build_route_summary(route_result: dict, user_type: str) -> str:
    """Create a fixed-format route summary for frontend/backend consumers."""

    label = USER_LABELS.get(user_type, user_type)
    difficulty = route_result.get("difficulty", "보통")
    risk_factors = route_result.get("riskFactors", [])
    reasons = _join_risk_factors(risk_factors)

    return (
        f"{label} 기준, 이 경로는 {difficulty} 경로입니다. "
        f"주요 위험 요소는 {reasons}입니다. "
        f"계단/단차/급경사 여부를 확인한 결과, {route_result.get('reason', '복합 위험도를 기준으로 판단했습니다.')} "
    )
