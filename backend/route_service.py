from typing import Any

from backend.ai_service import analyze_route
from backend.data_loader import load_routes


RECOMMENDATION_ORDER = {
    "안전": 0,
    "주의": 1,
    "위험": 2,
}


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


def build_recommendation(start: str, end: str, user_type: str) -> dict[str, Any] | None:
    route_set = find_route_set(start, end)
    if route_set is None:
        return None

    routes = []
    for route in route_set.get("routes", []):
        ai_result = analyze_route(route, user_type)
        route_summary = ai_result.get("routeSummary", {}) if ai_result else {}
        ai_points = ai_result.get("points", []) if ai_result else []
        points = merge_point_analysis(route.get("points", []), ai_points)

        routes.append(
            {
                **route,
                "points": points,
                "recommendation": route_summary.get("recommendation", "위험"),
                "riskLevel": route_summary.get("riskLevel", "unknown"),
                "summaryTitle": route_summary.get("summaryTitle", "분석 결과 없음"),
                "summary": route_summary.get("aiSummary", "아직 분석 결과가 없습니다."),
                "mainRiskFactors": route_summary.get("mainRiskFactors", []),
            }
        )

    routes.sort(
        key=lambda route: (
            RECOMMENDATION_ORDER.get(route.get("recommendation"), 99),
            route.get("duration", 999999),
        )
    )

    return {
        "routeSetId": route_set.get("routeSetId"),
        "start": route_set.get("start"),
        "end": route_set.get("end"),
        "userType": user_type,
        "routes": routes,
    }
