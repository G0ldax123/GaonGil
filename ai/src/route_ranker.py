"""Route loading, asset mapping, AI execution, and result normalization."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .analyzer import RouteAccessibilityAnalyzer, create_route_analyzer


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
DATA_ROUTES_PATH = PROJECT_ROOT / "data" / "routes.json"
DOCS_ROUTES_PATH = PROJECT_ROOT / "docs" / "routes.json"

USER_LABELS = {
    "wheelchair": "휠체어 이용자",
    "stroller": "유모차 이용자",
    "elderly": "노약자",
    "crutches": "목발 이용자",
}

RECOMMENDATION_ORDER = {
    "안전": 0,
    "주의": 1,
    "위험": 2,
}

DEFAULT_DETECTED_ELEMENTS = {
    "stairs": "unknown",
    "curb": "unknown",
    "steepRoad": "unknown",
    "narrowRoad": "unknown",
}

ALLOWED_MAIN_RISK_FACTORS = {"계단", "단차", "경사로", "좁은 길"}


def _natural_sort_key(value: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def _load_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Route data not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {path}") from exc


def _route_data_path(custom_path: Path | str | None = None) -> Path:
    if custom_path:
        return Path(custom_path)
    if DATA_ROUTES_PATH.exists():
        return DATA_ROUTES_PATH
    if DOCS_ROUTES_PATH.exists():
        return DOCS_ROUTES_PATH
    return DATA_ROUTES_PATH


def _normalize_route_set_payload(payload: dict | list) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("routes"), list):
        return [payload]
    raise ValueError("Route JSON must be a route-set array or an object with 'routes'")


def _resolve_asset_path(image_url: str) -> str:
    if not image_url:
        return ""

    image_path = Path(image_url)
    image_name = image_path.stem
    route_folder = image_path.parent.name if image_path.parent.name else ""
    if not route_folder and "_" in image_name:
        route_folder = "_".join(image_name.split("_")[:2])

    route_dir = PROJECT_ROOT / "assets" / "roadview" / route_folder
    for extension in (image_path.suffix, ".jpg", ".jpeg", ".png"):
        if not extension:
            continue
        asset_path = route_dir / f"{image_name}{extension}"
        if asset_path.exists():
            return f"assets/roadview/{route_folder}/{asset_path.name}"

    return image_url.lstrip("/")


def _normalize_point(point: dict) -> dict:
    return {
        "pointId": point["pointId"],
        "locationName": point.get("locationName", point["pointId"]),
        "imageUrl": point.get("imageUrl", ""),
        "roadviewImagePath": _resolve_asset_path(point.get("imageUrl", "")),
    }


def _image_url_from_asset(route_id: str, asset_name: str) -> str:
    return f"/assets/roadview/{route_id}/{asset_name}"


def _point_id_from_asset(route_id: str, asset_name: str) -> str:
    suffix = Path(asset_name).stem.split("_")[-1]
    route_suffix = route_id.split("_")[-1]
    return f"{route_suffix}_{suffix}"


def _default_route_name(route_id: str) -> str:
    suffix = route_id.split("_")[-1].upper()
    return f"경로 {suffix}" if suffix else route_id


def _augment_points_with_assets(route: dict) -> list[dict]:
    points = [_normalize_point(point) for point in route.get("points", [])]
    known_point_ids = {point["pointId"] for point in points}

    route_asset_dir = PROJECT_ROOT / "assets" / "roadview" / route["routeId"]
    if not route_asset_dir.exists():
        return points

    route_assets = sorted(
        [path for path in route_asset_dir.iterdir() if path.is_file()],
        key=lambda path: _natural_sort_key(path.stem),
    )
    for asset_path in route_assets:
        point_id = _point_id_from_asset(route["routeId"], asset_path.name)
        if point_id in known_point_ids:
            continue

        points.append(
            {
                "pointId": point_id,
                "locationName": f"{route.get('name', _default_route_name(route['routeId']))} 주요 지점 {asset_path.stem.split('_')[-1]}",
                "imageUrl": _image_url_from_asset(route["routeId"], asset_path.name),
                "roadviewImagePath": f"assets/roadview/{route['routeId']}/{asset_path.name}",
            }
        )
        known_point_ids.add(point_id)

    return points


def _normalize_route_set(route_set: dict) -> dict:
    start = route_set.get("start", {}).get("name", route_set.get("origin", ""))
    end = route_set.get("end", {}).get("name", route_set.get("destination", ""))
    routes = []

    for route in route_set.get("routes", []):
        routes.append(
            {
                "routeId": route["routeId"],
                "name": route.get("name", _default_route_name(route["routeId"])),
                "description": route.get("description", ""),
                "origin": start,
                "destination": end,
                "points": _augment_points_with_assets(route),
            }
        )

    return {
        "routeSetId": route_set.get("routeSetId", "default_route_set"),
        "userType": route_set.get("userType", ""),
        "start": start,
        "end": end,
        "routes": routes,
    }


def load_route_sets(seed_path: Path | str | None = None) -> list[dict]:
    path = _route_data_path(seed_path)
    payload = _load_json(path)
    return [_normalize_route_set(route_set) for route_set in _normalize_route_set_payload(payload)]


def load_seed_routes(seed_path: Path | str | None = None) -> list[dict]:
    route_sets = load_route_sets(seed_path)
    if not route_sets:
        raise ValueError("No route sets available")
    return route_sets[0]["routes"]


def _choose_route_set(route_sets: list[dict], origin: str, destination: str) -> dict:
    if origin and destination:
        for route_set in route_sets:
            if route_set["start"] == origin and route_set["end"] == destination:
                return route_set
            if not route_set["start"] and not route_set["end"]:
                return {
                    **route_set,
                    "start": origin,
                    "end": destination,
                    "routes": [
                        {
                            **route,
                            "origin": origin,
                            "destination": destination,
                        }
                        for route in route_set.get("routes", [])
                    ],
                }
    return route_sets[0]


def _normalize_detected_elements(raw_detected: dict | None) -> dict:
    detected = dict(DEFAULT_DETECTED_ELEMENTS)
    if not raw_detected:
        return detected

    for key in detected:
        value = raw_detected.get(key, "unknown")
        detected[key] = value if value in {"true", "false", "unknown"} else "unknown"
    return detected


def _normalize_point_result(raw_point: dict, route_point: dict) -> dict:
    recommendation = raw_point.get("recommendation", "주의")
    return {
        "pointId": route_point["pointId"],
        "locationName": raw_point.get("locationName") or route_point.get("locationName", route_point["pointId"]),
        "detectedElements": _normalize_detected_elements(raw_point.get("detectedElements")),
        "recommendation": recommendation,
        "summaryTitle": raw_point.get("summaryTitle", "분석 확인 필요"),
        "aiSummary": raw_point.get("aiSummary", "AI 분석 결과에서 해당 지점 요약을 확인해야 합니다."),
        "reason": raw_point.get("reason", "AI 분석 결과에서 해당 지점 판단 근거가 누락되었습니다."),
        "analysisProvider": raw_point.get("analysisProvider", ""),
    }


def _normalize_route_result(raw_result: dict, route: dict, user_type: str, provider_name: str) -> dict:
    raw_summary = raw_result.get("routeSummary", {})
    route_recommendation = raw_summary.get("recommendation", "주의")
    raw_points_by_id = {point.get("pointId"): point for point in raw_result.get("points", [])}
    points = [
        _normalize_point_result(raw_points_by_id.get(route_point["pointId"], {}), route_point)
        for route_point in route.get("points", [])
    ]
    for point in points:
        if not point["analysisProvider"]:
            point["analysisProvider"] = provider_name

    return {
        "routeId": route["routeId"],
        "userType": raw_result.get("userType", user_type),
        "userTypeLabel": raw_result.get("userTypeLabel", USER_LABELS.get(user_type, "교통약자")),
        "name": route.get("name", route["routeId"]),
        "analysisProviders": raw_result.get("analysisProviders", [provider_name]),
        "routeSummary": {
            "recommendation": route_recommendation,
            "summaryTitle": raw_summary.get("summaryTitle", "분석 결과"),
            "aiSummary": raw_summary.get("aiSummary", "AI가 생성한 경로 분석 결과입니다."),
            "mainRiskFactors": [
                factor
                for factor in raw_summary.get("mainRiskFactors", [])
                if factor in ALLOWED_MAIN_RISK_FACTORS
            ],
            "mainRiskPoints": raw_summary.get("mainRiskPoints", []),
            "reason": raw_summary.get("reason", "AI 분석 결과를 기준으로 판단했습니다."),
        },
        "points": points,
    }


def analyze_route(route: dict, user_type: str, analyzer: RouteAccessibilityAnalyzer | None = None) -> dict:
    provider = analyzer or create_route_analyzer()
    raw_result = provider.analyze_route(route, user_type)
    return _normalize_route_result(raw_result, route, user_type, provider.provider_name)


def rank_routes(
    routes: Iterable[dict],
    user_type: str,
    analyzer: RouteAccessibilityAnalyzer | None = None,
    route_id: str = "",
) -> list[dict]:
    analyzable_routes = [
        route
        for route in routes
        if route.get("points") and (not route_id or route.get("routeId") == route_id)
    ]
    route_results = [analyze_route(route, user_type, analyzer) for route in analyzable_routes]
    return sorted(
        route_results,
        key=lambda item: (
            RECOMMENDATION_ORDER.get(item.get("routeSummary", {}).get("recommendation"), 99),
            item["routeId"],
        ),
    )


def analyze_routes_for_user(
    user_type: str,
    origin: str,
    destination: str,
    analyzer: RouteAccessibilityAnalyzer | None = None,
    route_id: str = "",
) -> list[dict]:
    route_sets = load_route_sets()
    route_set = _choose_route_set(route_sets, origin, destination)
    return rank_routes(route_set["routes"], user_type, analyzer, route_id)
