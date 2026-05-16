"""Route loading, point analysis, ranking, and JSON response assembly."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .analyzer import BaseAccessibilityAnalyzer, create_accessibility_analyzer
from .risk_rules import calculate_segment_risk

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
DATA_ROUTES_PATH = PROJECT_ROOT / "data" / "routes.json"
DOCS_ROUTES_PATH = PROJECT_ROOT / "docs" / "routes.json"
FALLBACK_SEED_PATH = BASE_DIR / "data" / "routes_seed.json"

USER_LABELS = {
    "wheelchair": "휠체어 이용자",
    "stroller": "유모차 이용자",
    "elderly": "노약자",
    "crutches": "목발 이용자",
}

ROUTE_RECOMMENDATION_MAP = {
    "good": "안전",
    "caution": "주의",
    "bad": "위험",
}

ROUTE_SUMMARY_TITLE_MAP = {
    "good": "이동 가능성이 높은 경로",
    "caution": "일부 주의 구간이 있는 경로",
    "bad": "위험 구간이 많은 경로",
}

POINT_SUMMARY_TITLE_MAP = {
    "good": "안전한 구간",
    "caution": "주의가 필요한 구간",
    "bad": "위험한 구간",
}

RISK_ELEMENT_META = {
    "stairs": {
        "label": "계단",
        "displayText": "계단 확인",
        "description": "계단이 확인되어 이동 보조나 우회가 필요할 수 있습니다.",
    },
    "curb": {
        "label": "단차",
        "displayText": "보도 단차 있음",
        "description": "보도 진입부 단차가 있어 이동 시 주의가 필요합니다.",
    },
    "steepRoad": {
        "label": "가파른 길",
        "displayText": "주의 경사 구간",
        "description": "경사도가 높아 이동 시 보조가 필요할 수 있습니다.",
    },
    "narrowRoad": {
        "label": "좁은 길",
        "displayText": "보도 폭 좁음",
        "description": "보도 폭이 좁아 회피 공간이 부족할 수 있습니다.",
    },
    "otherObstacle": {
        "label": "기타 장애물",
        "displayText": "장애물 가능성",
        "description": "시야상 장애물 가능성이 있어 주의가 필요합니다.",
    },
}


def _natural_sort_key(value: str) -> list[int | str]:
    """Sort route asset names like route_a_2, route_a_10 in numeric order."""

    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def _load_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Route data not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {path}") from exc


def _route_data_path(custom_path: Path | str | None = None) -> Path:
    # Runtime should prefer data/routes.json because backend already reads from data/.
    if custom_path:
        return Path(custom_path)
    if DATA_ROUTES_PATH.exists():
        return DATA_ROUTES_PATH
    if DOCS_ROUTES_PATH.exists():
        return DOCS_ROUTES_PATH
    return FALLBACK_SEED_PATH


def _normalize_route_set_payload(payload: dict | list) -> list[dict]:
    """Support either docs/routes.json route-set arrays or simple fallback route lists."""

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("routes"), list):
        return [payload]
    raise ValueError("Route JSON must be a route-set array or an object with 'routes'")


def _resolve_asset_path(image_url: str) -> str:
    """Match JSON imageUrl to the local roadview asset path."""

    if not image_url:
        return ""
    image_name = Path(image_url).stem
    # Group images by route id so roadview captures stay organized as more demo routes are added.
    route_folder = "_".join(image_name.split("_")[:2]) if "_" in image_name else ""
    route_dir = BASE_DIR.parent / "assets" / "roadview" / route_folder
    for extension in (".jpg", ".jpeg", ".png"):
        asset_path = route_dir / f"{image_name}{extension}"
        if asset_path.exists():
            return f"assets/roadview/{route_folder}/{asset_path.name}"
    return image_url.lstrip("/")


def _normalize_point(point: dict) -> dict:
    """Convert docs/routes point objects into the internal analysis shape."""

    return {
        "pointId": point["pointId"],
        "locationName": point.get("locationName", point["pointId"]),
        "imageUrl": point.get("imageUrl", ""),
        # Keep the original imageUrl for clients, but resolve a local asset path for analysis.
        "roadviewImagePath": _resolve_asset_path(point.get("imageUrl", "")),
        "slopePercent": float(point["slopePercent"]) if point.get("slopePercent") not in {None, ""} else None,
        "slopeLevel": point.get("slopeLevel"),
        "distanceMeter": int(point.get("distanceMeter", 0)),
        "mockDetected": point.get("mockDetected"),
    }


def _infer_image_url_from_asset(route_id: str, asset_name: str) -> str:
    """Mirror frontend/backend asset URLs from a local roadview file name."""

    stem = Path(asset_name).stem
    return f"/assets/roadview/{route_id}/{asset_name}"


def _augment_points_with_assets(route: dict) -> list[dict]:
    """Add synthetic points for route images that exist locally but are missing in docs/routes.json.

    routes.json may list only a subset of point metadata. For the hackathon demo,
    every captured roadview image should still be analyzed, so this function backfills missing
    point entries from assets/roadview/<route_id>/.
    """

    normalized_points = [_normalize_point(point) for point in route.get("points", [])]
    known_point_ids = {point["pointId"] for point in normalized_points}

    route_asset_dir = BASE_DIR.parent / "assets" / "roadview" / route["routeId"]
    if not route_asset_dir.exists():
        return normalized_points

    route_assets = sorted(
        [path for path in route_asset_dir.iterdir() if path.is_file()],
        key=lambda path: _natural_sort_key(path.stem),
    )

    for asset_path in route_assets:
        stem = asset_path.stem
        suffix = stem.split("_")[-1]
        point_id = f"{route['routeId'].split('_')[-1]}_{suffix}"
        if point_id in known_point_ids:
            continue

        normalized_points.append(
            {
                "pointId": point_id,
                "locationName": f"{route['name']} 추가 지점 {suffix}",
                "imageUrl": _infer_image_url_from_asset(route["routeId"], asset_path.name),
                "roadviewImagePath": f"assets/roadview/{route['routeId']}/{asset_path.name}",
                "slopePercent": None,
                "slopeLevel": None,
                "distanceMeter": 0,
                "mockDetected": None,
            }
        )
        known_point_ids.add(point_id)

    return normalized_points


def _normalize_route_set(route_set: dict) -> dict:
    # Convert the shared route-set payload into the exact structure the analyzer expects.
    routes = []
    for route in route_set.get("routes", []):
        # Merge shared point metadata with any extra local captures saved under assets/roadview/<route_id>/.
        routes.append(
            {
                "routeId": route["routeId"],
                "name": route.get("name", route["routeId"]),
                "description": route.get("description", ""),
                "duration": int(route.get("duration", 0)),
                "distance": int(route.get("distance", 0)),
                "points": _augment_points_with_assets(route),
            }
        )

    return {
        "routeSetId": route_set.get("routeSetId", "default_route_set"),
        "start": route_set.get("start", {}).get("name", route_set.get("origin", "")),
        "end": route_set.get("end", {}).get("name", route_set.get("destination", "")),
        "routes": routes,
    }


def load_seed_routes(seed_path: Path | str | None = None) -> list[dict]:
    """Load the first matching route set and return its normalized routes."""

    route_sets = load_route_sets(seed_path)
    if not route_sets:
        raise ValueError("No route sets available")
    return route_sets[0]["routes"]


def load_route_sets(seed_path: Path | str | None = None) -> list[dict]:
    """Load and normalize route sets from docs/routes.json or fallback seed."""

    path = _route_data_path(seed_path)
    payload = _load_json(path)
    return [_normalize_route_set(route_set) for route_set in _normalize_route_set_payload(payload)]


def _choose_route_set(route_sets: list[dict], origin: str, destination: str) -> dict:
    """Pick the route set matching the requested start/end, or fall back to the first."""

    if origin and destination:
        for route_set in route_sets:
            if route_set["start"] == origin and route_set["end"] == destination:
                return route_set
    return route_sets[0]


def _route_risk_level(score: int) -> str:
    """Collapse numeric point/route score into the 3-level low/medium/high bucket."""

    if score <= 8:
        return "low"
    if score <= 18:
        return "medium"
    return "high"


def _route_accessibility(score: int) -> str:
    """Translate numeric score into the fixed good/caution/bad accessibility label."""

    if score <= 8:
        return "good"
    if score <= 18:
        return "caution"
    return "bad"


def _build_point_detected_elements(analysis: dict) -> dict:
    """Map internal detection keys to the exact keys used by docs/ai_results.json."""

    detected = analysis["detected"]
    return {
        "stairs": detected["stairs"],
        "curb": detected["curb"],
        "steepRoad": detected["steep_slope"],
        "narrowRoad": detected["narrow_path"],
        "otherObstacle": "true" if detected["uneven_surface"] == "true" or detected["obstacle"] == "true" else (
            "unknown" if detected["uneven_surface"] == "unknown" or detected["obstacle"] == "unknown" else "false"
        ),
    }


def _analysis_from_point_result(point_result: dict) -> dict:
    """Map ai_results-style point detections back into the scoring input shape."""

    detected_elements = point_result.get("detectedElements", {})
    return {
        "detected": {
            "stairs": detected_elements.get("stairs", "unknown"),
            "curb": detected_elements.get("curb", "unknown"),
            "steep_slope": detected_elements.get("steepRoad", "unknown"),
            "narrow_path": detected_elements.get("narrowRoad", "unknown"),
            "uneven_surface": detected_elements.get("otherObstacle", "unknown"),
            "obstacle": detected_elements.get("otherObstacle", "unknown"),
        }
    }


def _build_point_risk_factors(point_analysis: dict) -> list[dict]:
    risk_factors = []
    detected_elements = point_analysis["detectedElements"]

    for risk_type, value in detected_elements.items():
        if value != "true":
            continue
        # Expand bare detections into frontend-ready cards with labels and descriptions.
        meta = RISK_ELEMENT_META[risk_type]
        risk_factors.append(
            {
                "type": risk_type,
                "label": meta["label"],
                "severity": point_analysis["riskLevel"],
                "displayText": meta["displayText"],
                "description": meta["description"],
            }
        )
    return risk_factors


def _build_point_summary(point_analysis: dict, user_type: str) -> tuple[str, str, str]:
    user_label = USER_LABELS.get(user_type, user_type)
    risk_labels = [factor["label"] for factor in point_analysis["riskFactors"]]
    accessibility_level = point_analysis["accessibilityLevel"]
    joined = ", ".join(risk_labels) if risk_labels else "일부 위험 요소"

    if accessibility_level == "good":
        summary = f"{user_label} 기준으로 특별한 위험 요소가 적어 이동 가능성이 높은 구간입니다."
        reason = "계단, 단차, 가파른 길, 좁은 길이 확인되지 않았고 경사도도 완만합니다."
    elif accessibility_level == "bad":
        summary = f"{user_label} 기준으로 {joined} 때문에 위험도가 높은 구간입니다."
        reason = f"{', '.join(risk_labels)} 요소가 확인되어 직접 통과가 어렵습니다."
    else:
        summary = f"{user_label} 기준으로 {joined}로 인해 주의가 필요한 구간입니다."
        reason = f"{', '.join(risk_labels)} 요소가 있어 이동 시 보조가 필요할 수 있습니다."

    summary_title = POINT_SUMMARY_TITLE_MAP[accessibility_level]
    return summary_title, summary, reason


def _build_route_summary(route_result: dict, user_type: str) -> dict:
    """Build the final routeSummary block expected by the sample AI output contract."""

    user_label = USER_LABELS.get(user_type, user_type)
    main_risk_factors = route_result["routeSummary"]["mainRiskFactors"]
    accessibility_level = route_result["routeSummary"]["accessibilityLevel"]
    risk_text = ", ".join(main_risk_factors) if main_risk_factors else "특별한 위험 요소"

    if accessibility_level == "good":
        ai_summary = f"{route_result['routeId']}는 {user_label} 기준으로 비교적 이동하기 좋은 경로입니다."
        reason = "주요 지점 분석 결과 계단, 단차, 급경사 위험이 상대적으로 낮습니다."
    elif accessibility_level == "bad":
        ai_summary = f"{route_result['routeId']}는 {user_label} 기준으로 {risk_text} 때문에 위험도가 높은 경로입니다."
        reason = f"주요 지점 분석 결과 {risk_text} 요소 비중이 높아 직접 통과가 어렵습니다."
    else:
        ai_summary = f"{route_result['routeId']}는 {user_label} 기준으로 {risk_text} 요소가 있어 주의가 필요한 경로입니다."
        reason = f"주요 지점 분석 결과 {risk_text} 요소가 포함되어 있습니다."

    return {
        "recommendation": ROUTE_RECOMMENDATION_MAP[accessibility_level],
        "riskLevel": route_result["routeSummary"]["riskLevel"],
        "summaryTitle": ROUTE_SUMMARY_TITLE_MAP[accessibility_level],
        "aiSummary": ai_summary,
        "mainRiskFactors": main_risk_factors,
        "reason": reason,
        "accessibilityLevel": accessibility_level,
    }


def analyze_point(point: dict, user_type: str, analyzer: BaseAccessibilityAnalyzer | None = None) -> tuple[dict, int]:
    """Analyze one route point and return docs/ai_results-compatible JSON."""

    provider = analyzer or create_accessibility_analyzer()
    analysis = provider.analyze(point, user_type)
    point_risk_score = calculate_segment_risk(analysis, user_type, point)
    accessibility_level = analysis["accessibility"]
    risk_level = _route_risk_level(point_risk_score)

    point_result = {
        "pointId": point["pointId"],
        "locationName": point["locationName"],
        "imageUrl": point.get("imageUrl", ""),
        "roadviewImagePath": point.get("roadviewImagePath", ""),
        "slopePercent": point.get("slopePercent"),
        "slopeLevel": point.get("slopeLevel"),
        "detectedElements": _build_point_detected_elements(analysis),
        "riskFactors": [],
        "accessibilityLevel": accessibility_level,
        "riskLevel": risk_level,
        "recommendation": ROUTE_RECOMMENDATION_MAP[accessibility_level],
        "analysisProvider": analysis.get("provider", "unknown"),
    }
    # Build the exact point payload the backend and frontend sample files already expect.
    point_result["riskFactors"] = _build_point_risk_factors(point_result)
    summary_title, ai_summary, reason = _build_point_summary(point_result, user_type)
    point_result["summaryTitle"] = summary_title
    point_result["aiSummary"] = ai_summary
    point_result["reason"] = reason
    point_result["segmentRiskScore"] = point_risk_score
    return point_result, point_risk_score


def analyze_route(route: dict, user_type: str, analyzer: BaseAccessibilityAnalyzer | None = None) -> dict:
    """Analyze a route and build a docs/ai_results-compatible object."""

    provider = analyzer or create_accessibility_analyzer()

    # In google mode, ask the model for the full ai_results-style route object in one shot.
    if hasattr(provider, "analyze_route") and provider.provider_name == "google":
        route_payload = dict(route)
        route_payload["origin"] = route.get("origin", "")
        route_payload["destination"] = route.get("destination", "")
        route_result = provider.analyze_route(route_payload, user_type)
        route_result.setdefault("routeId", route["routeId"])
        route_result.setdefault("userType", user_type)
        route_result.setdefault("userTypeLabel", USER_LABELS.get(user_type, user_type))
        route_result.setdefault("name", route["name"])
        route_result.setdefault("duration", route["duration"])
        route_result.setdefault("distance", route["distance"])
        route_points_by_id = {point["pointId"]: point for point in route.get("points", [])}
        for point_result in route_result.get("points", []):
            route_point = route_points_by_id.get(point_result.get("pointId"), {})
            point_result.setdefault("imageUrl", route_point.get("imageUrl", ""))
            point_result.setdefault("roadviewImagePath", route_point.get("roadviewImagePath", ""))
            point_result.setdefault("analysisProvider", "google")
            if "segmentRiskScore" not in point_result:
                point_result["segmentRiskScore"] = calculate_segment_risk(
                    _analysis_from_point_result(point_result),
                    user_type,
                    route_point,
                )
        route_result["totalRiskScore"] = sum(point.get("segmentRiskScore", 0) for point in route_result.get("points", []))
        return route_result

    analyzed_points = []
    total_risk_score = 0
    main_risk_factors: list[str] = []

    # Analyze every point, including synthetic points derived from locally captured roadview assets.
    for point in route.get("points", []):
        point_result, point_risk_score = analyze_point(point, user_type, provider)
        analyzed_points.append(point_result)
        total_risk_score += point_risk_score
        for factor in point_result["riskFactors"]:
            if factor["label"] not in main_risk_factors:
                main_risk_factors.append(factor["label"])

    accessibility_level = _route_accessibility(total_risk_score)
    route_result = {
        "routeId": route["routeId"],
        "userType": user_type,
        "userTypeLabel": USER_LABELS.get(user_type, user_type),
        "name": route["name"],
        "duration": route["duration"],
        "distance": route["distance"],
        "points": analyzed_points,
        "totalRiskScore": total_risk_score,
        "analysisProviders": sorted({point["analysisProvider"] for point in analyzed_points}),
        "routeSummary": {
            "riskLevel": _route_risk_level(total_risk_score),
            "mainRiskFactors": main_risk_factors,
            "accessibilityLevel": accessibility_level,
        },
    }
    route_result["routeSummary"] = _build_route_summary(route_result, user_type)
    return route_result


def rank_routes(
    routes: Iterable[dict],
    user_type: str,
    analyzer: BaseAccessibilityAnalyzer | None = None,
    route_id: str = "",
) -> list[dict]:
    """Analyze and sort candidate routes by total risk score."""

    # Ignore placeholder routes that have no captured points yet.
    analyzable_routes = [
        route
        for route in routes
        if route.get("points") and (not route_id or route.get("routeId") == route_id)
    ]
    route_results = [analyze_route(route, user_type, analyzer) for route in analyzable_routes]
    return sorted(route_results, key=lambda item: (item["totalRiskScore"], item["distance"]))


def analyze_routes_for_user(
    user_type: str,
    origin: str,
    destination: str,
    analyzer: BaseAccessibilityAnalyzer | None = None,
    route_id: str = "",
) -> list[dict]:
    """Return the ai_results-style route array consumed by backend/data_loader.py."""

    route_sets = load_route_sets()
    route_set = _choose_route_set(route_sets, origin, destination)
    return rank_routes(route_set["routes"], user_type, analyzer, route_id)
