import json
from typing import Any

from ai.src.main import load_dotenv
from ai.src.route_ranker import rank_routes
from backend.data_loader import AI_RESULTS_PATH, load_ai_results


def load_existing_ai_results() -> list[dict[str, Any]]:
    try:
        return load_ai_results()
    except FileNotFoundError:
        return []


def save_ai_results(results: list[dict[str, Any]]) -> None:
    AI_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AI_RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def merge_ai_results(existing: list[dict[str, Any]], updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    update_keys = {
        (route.get("routeId"), route.get("userType"))
        for route in updates
    }
    merged = [
        route
        for route in existing
        if (route.get("routeId"), route.get("userType")) not in update_keys
    ]
    merged.extend(updates)
    return merged


def generate_ai_results(route_payloads: list[dict[str, Any]], user_type: str) -> list[dict[str, Any]]:
    """Run route-level AI analysis for backend-built route payloads and persist ai_results.json."""

    load_dotenv()
    generated_results = rank_routes(
        routes=route_payloads,
        user_type=user_type,
    )
    save_ai_results(merge_ai_results(load_existing_ai_results(), generated_results))
    return generated_results
