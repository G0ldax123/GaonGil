import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ROUTES_PATH = DATA_DIR / "routes.json"
AI_RESULTS_PATH = DATA_DIR / "ai_results.json"
FRONT_REQUEST_PATH = DATA_DIR / "front_request.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_routes() -> list[dict[str, Any]]:
    return load_json(ROUTES_PATH)


def load_ai_results() -> list[dict[str, Any]]:
    return load_json(AI_RESULTS_PATH)


def load_front_request() -> dict[str, Any]:
    return load_json(FRONT_REQUEST_PATH)
