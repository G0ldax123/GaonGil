from typing import Any

from backend.ai_service import analyze_route
from backend.data_loader import load_routes


RECOMMENDATION_ORDER = {
    "안전": 0,
    "주의": 1,
    "위험": 2,
}

ROUTE_KEY_ORDER = (
    "routeId",
    "name",
    "description",
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
    route_sets = load_routes()

    for route_set in route_sets:
        if route_set.get("start", {}).get("name") == start and route_set.get("end", {}).get("name") == end:
            return route_set

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

    routes = []
    for route in route_set.get("routes", []):
        ai_result = analyze_route(route, user_type)
        route_summary = ai_result.get("routeSummary", {}) if ai_result else {}
        ai_points = ai_result.get("points", []) if ai_result else []
        points = [order_point_payload(point) for point in merge_point_analysis(route.get("points", []), ai_points)]

        routes.append(
            order_route_payload(
                {
                    **route,
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
        "start": route_set.get("start"),
        "end": route_set.get("end"),
        "userType": user_type,
        "routes": routes,
    }
