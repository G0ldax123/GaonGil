from typing import Any

from backend.data_loader import load_ai_results


def analyze_route(route: dict[str, Any], user_type: str) -> dict[str, Any] | None:
    """MVP mock: return a prepared AI result for this route and user type."""
    ai_results = load_ai_results()

    for result in ai_results:
        if result.get("routeId") == route.get("routeId") and result.get("userType") == user_type:
            return result

    return None
