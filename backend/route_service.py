from typing import Any

from ai.src.route_ranker import load_route_sets
from backend.ai_service import generate_ai_results


RECOMMENDATION_ORDER = {
    "안전": 0,
    "주의": 1,
    "위험": 2,
}

USER_SPEED_METERS_PER_SECOND = {
    "crutches": 0.94,
    "wheelchair": 0.69,
    "elderly": 0.24,
    "stroller": 0.83,
}

ROUTE_KEY_ORDER = (
    "routeId",
    "name",
    "description",
    "distance",
    "estimatedMinutes",
    "estimatedTimeText",
    "recommendation",
    "summaryTitle",
    "summary",
    "mainRiskFactors",
    "mainRiskPoints",
    "points",
)

POINT_KEY_ORDER = (
    "pointId",
    "locationName",
    "lat",
    "lng",
    "imageUrl",
    "roadviewImagePath",
    "detectedElements",
    "recommendation",
    "summaryTitle",
    "aiSummary",
    "reason",
    "analysisProvider",
    "aiLocationName",
)


def find_route_set(start: str, end: str) -> dict[str, Any] | None:
    route_sets = load_route_sets()

    for route_set in route_sets:
        if route_set.get("start") == start and route_set.get("end") == end:
            return route_set
        if not route_set.get("start") and not route_set.get("end"):
            return {
                **route_set,
                "start": start,
                "end": end,
                "routes": [
                    {
                        **route,
                        "origin": start,
                        "destination": end,
                    }
                    for route in route_set.get("routes", [])
                ],
            }

    return None


def merge_point_analysis(route_points: list[dict[str, Any]], ai_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ai_points_by_id = {point.get("pointId"): point for point in ai_points}
    merged_points = []

    for route_point in route_points:
        point_id = route_point.get("pointId")
        ai_point = ai_points_by_id.get(point_id, {})
        merged_point = {**ai_point, **route_point}

        if ai_point.get("locationName") and ai_point.get("locationName") != route_point.get("locationName"):
            merged_point["aiLocationName"] = ai_point.get("locationName")

        merged_points.append(merged_point)

    route_point_ids = {point.get("pointId") for point in route_points}
    for ai_point in ai_points:
        if ai_point.get("pointId") not in route_point_ids:
            merged_points.append(ai_point)

    return merged_points


def calculate_estimated_minutes(distance: Any, user_type: str) -> int | None:
    """Convert a route distance into whole-minute travel time for the given user type."""

    speed = USER_SPEED_METERS_PER_SECOND.get(user_type)
    if speed is None:
        return None

    try:
        distance_meter = float(distance)
    except (TypeError, ValueError):
        return None

    if distance_meter < 0:
        return None
    if distance_meter == 0:
        return 0

    travel_minutes = distance_meter / speed / 60
    rounded_minutes = int(travel_minutes)
    if travel_minutes > rounded_minutes:
        rounded_minutes += 1
    return max(1, rounded_minutes)


def format_estimated_time(minutes: int | None) -> str:
    """Format the estimated time in a frontend-friendly Korean minute label."""

    if minutes is None:
        return ""
    return f"{minutes}분"


def order_point_payload(point: dict[str, Any]) -> dict[str, Any]:
    """Match the backend example response order for each point payload."""

    ordered_point: dict[str, Any] = {}
    for key in POINT_KEY_ORDER:
        if key in point:
            ordered_point[key] = point[key]
    for key, value in point.items():
        if key not in ordered_point:
            ordered_point[key] = value
    return ordered_point


def order_route_payload(route: dict[str, Any]) -> dict[str, Any]:
    """Match docs/back_responce.json so frontend receives a stable route shape."""

    ordered_route: dict[str, Any] = {}
    for key in ROUTE_KEY_ORDER:
        if key in route:
            ordered_route[key] = route[key]
    for key, value in route.items():
        if key not in ordered_route:
            ordered_route[key] = value
    return ordered_route


def build_recommendation(start: str, end: str, user_type: str) -> dict[str, Any] | None:
    route_set = find_route_set(start, end)
    if route_set is None:
        return None

    route_payloads = route_set.get("routes", [])
    ai_results = generate_ai_results(route_payloads=route_payloads, user_type=user_type)
    ai_results_by_route_id = {
        result.get("routeId"): result
        for result in ai_results
        if result.get("userType") == user_type
    }

    routes = []
    for route in route_payloads:
        ai_result = ai_results_by_route_id.get(route.get("routeId"))
        route_summary = ai_result.get("routeSummary", {}) if ai_result else {}
        ai_points = ai_result.get("points", []) if ai_result else []
        points = [order_point_payload(point) for point in merge_point_analysis(route.get("points", []), ai_points)]
        estimated_minutes = calculate_estimated_minutes(route.get("distance"), user_type)

        routes.append(
            order_route_payload(
                {
                    **route,
                    "estimatedMinutes": estimated_minutes,
                    "estimatedTimeText": format_estimated_time(estimated_minutes),
                    "recommendation": route_summary.get("recommendation", "위험"),
                    "summaryTitle": route_summary.get("summaryTitle", "분석 결과 없음"),
                    "summary": route_summary.get("aiSummary", "아직 분석 결과가 없습니다."),
                    "mainRiskFactors": route_summary.get("mainRiskFactors", []),
                    "mainRiskPoints": route_summary.get("mainRiskPoints", []),
                    "points": points,
                }
            )
        )

    routes.sort(
        key=lambda route: (
            RECOMMENDATION_ORDER.get(route.get("recommendation"), 99),
            route.get("routeId", ""),
        )
    )

    return {
        "routeSetId": route_set.get("routeSetId"),
        "start": {"name": route_set.get("start")},
        "end": {"name": route_set.get("end")},
        "userType": user_type,
        "routes": routes,
    }
