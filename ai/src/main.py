"""CLI entrypoint for generating backend-compatible ai_results JSON."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src.route_ranker import analyze_routes_for_user, load_route_sets
else:
    from .route_ranker import analyze_routes_for_user, load_route_sets


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FRONT_REQUEST_PATH = PROJECT_ROOT / "data" / "front_request.json"
DATA_AI_RESULTS_PATH = PROJECT_ROOT / "data" / "ai_results.json"


def load_dotenv(dotenv_path: Path | None = None) -> None:
    """Load local .env values into the current process without overriding real env vars."""

    env_path = dotenv_path or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for local MVP execution."""

    parser = argparse.ArgumentParser(description="GaonGil AI/data MVP analyzer")
    parser.add_argument("--user-type", choices=["wheelchair", "stroller", "elderly", "crutches"])
    parser.add_argument("--origin", default="")
    parser.add_argument("--destination", default="")
    parser.add_argument("--route-id", default="", help="Analyze only one route, for example route_a.")
    parser.add_argument("--output", default="", help="Optional JSON output path. Defaults to stdout only.")
    return parser


def load_front_request(path: Path = DATA_FRONT_REQUEST_PATH) -> dict | None:
    """Load the backend-style front request example when CLI args are omitted."""

    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _stored_point_result(point: dict) -> dict:
    return {
        "pointId": point.get("pointId", ""),
        "locationName": point.get("locationName", ""),
        "detectedElements": point.get("detectedElements", {}),
        "recommendation": point.get("recommendation", ""),
        "summaryTitle": point.get("summaryTitle", ""),
        "aiSummary": point.get("aiSummary", ""),
        "reason": point.get("reason", ""),
    }


def _stored_route_result(route: dict) -> dict:
    route_summary = route.get("routeSummary", {})
    return {
        "routeId": route.get("routeId", ""),
        "userType": route.get("userType", ""),
        "userTypeLabel": route.get("userTypeLabel", ""),
        "routeSummary": {
            "recommendation": route_summary.get("recommendation", ""),
            "summaryTitle": route_summary.get("summaryTitle", ""),
            "aiSummary": route_summary.get("aiSummary", ""),
            "mainRiskFactors": route_summary.get("mainRiskFactors", []),
            "mainRiskPoints": route_summary.get("mainRiskPoints", []),
            "reason": route_summary.get("reason", ""),
        },
        "points": [_stored_point_result(point) for point in route.get("points", [])],
    }


def build_storage_payload(payload: list[dict]) -> list[dict]:
    """Keep data/ai_results.json aligned with docs/ai_results.json."""

    return [_stored_route_result(route) for route in payload]


def load_existing_ai_results(path: Path = DATA_AI_RESULTS_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def merge_ai_results(existing: list[dict], updates: list[dict]) -> list[dict]:
    merged = list(existing)
    update_keys = {
        (route.get("routeId"), route.get("userType"))
        for route in updates
    }
    merged = [
        route
        for route in merged
        if (route.get("routeId"), route.get("userType")) not in update_keys
    ]
    merged.extend(updates)
    return merged


def main() -> int:
    """Run the analyzer and print fixed JSON to stdout."""

    # Load local secrets from .env for venv-based development without tracking them in Git.
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    route_sets = load_route_sets()
    if not route_sets:
        raise SystemExit("No route sets available")

    front_request = load_front_request()
    if not args.user_type and front_request:
        args.user_type = front_request.get("userType", "")
    if not args.user_type:
        args.user_type = route_sets[0].get("userType", "")
    if not args.origin:
        if front_request:
            args.origin = front_request.get("start", "")
        if not args.origin:
            args.origin = route_sets[0]["start"]
    if not args.destination:
        if front_request:
            args.destination = front_request.get("end", "")
        if not args.destination:
            args.destination = route_sets[0]["end"]
    if not args.user_type:
        raise SystemExit("--user-type is required when data/front_request.json is unavailable")

    payload = analyze_routes_for_user(
        user_type=args.user_type,
        origin=args.origin,
        destination=args.destination,
        route_id=args.route_id,
    )
    if args.route_id and not payload:
        raise SystemExit(f"No analyzable route found for route id: {args.route_id}")
    storage_payload = build_storage_payload(payload)
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(storage_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif DATA_AI_RESULTS_PATH.parent.exists():
        if args.route_id:
            storage_payload = merge_ai_results(load_existing_ai_results(), storage_payload)
        DATA_AI_RESULTS_PATH.write_text(json.dumps(storage_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(storage_payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
