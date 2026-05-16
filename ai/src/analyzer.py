"""Route-level AI clients for generating ai_results.json-compatible output."""

from __future__ import annotations

from abc import ABC, abstractmethod
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "ai" / "prompt.md"

DEFAULT_GOOGLE_MODEL = "gemini-2.0-flash"
GOOGLE_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DEFAULT_OPENAI_MODEL = "gpt-5.4"
OPENAI_RESPONSES_API_URL = "https://api.openai.com/v1/responses"


class RouteAccessibilityAnalyzer(ABC):
    """Provider interface for one route in, one ai_results-style JSON object out."""

    provider_name = "base"

    @abstractmethod
    def analyze_route(self, route: dict, user_type: str) -> dict:
        raise NotImplementedError


def _load_prompt_template() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def _route_input_payload(route: dict, user_type: str) -> dict:
    """Build the exact route metadata block sent with the route images."""

    return {
        "userType": user_type,
        "routeId": route.get("routeId", ""),
        "routeName": route.get("name", ""),
        "origin": route.get("origin", ""),
        "destination": route.get("destination", ""),
        "points": [
            {
                "pointId": point.get("pointId", ""),
                "locationName": point.get("locationName", ""),
                "imageUrl": point.get("imageUrl", ""),
                "roadviewImagePath": point.get("roadviewImagePath", ""),
            }
            for point in route.get("points", [])
        ],
    }


def _render_route_prompt(route: dict, user_type: str) -> str:
    """Append concrete route input to the shared prompt."""

    input_json = json.dumps(_route_input_payload(route, user_type), ensure_ascii=False, indent=2)
    return f"{_load_prompt_template()}\n\n---\n\nInput JSON:\n{input_json}"


def _iter_route_image_paths(route: dict) -> list[Path]:
    """Resolve local route image paths in point order."""

    image_paths: list[Path] = []
    for point in route.get("points", []):
        image_path = point.get("roadviewImagePath")
        if not image_path:
            continue

        full_image_path = PROJECT_ROOT / image_path
        if full_image_path.exists():
            image_paths.append(full_image_path)

    return image_paths


def _image_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    image_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{image_base64}"


def _extract_openai_output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()

    text_parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                text_parts.append(content["text"])

    return "".join(text_parts).strip()


def _route_json_schema() -> dict:
    """Minimal schema for the ai_results.json route object used by the backend."""

    detected_elements_schema = {
        "type": "object",
        "properties": {
            "stairs": {"type": "string", "enum": ["true", "false", "unknown"]},
            "curb": {"type": "string", "enum": ["true", "false", "unknown"]},
            "steepRoad": {"type": "string", "enum": ["true", "false", "unknown"]},
            "narrowRoad": {"type": "string", "enum": ["true", "false", "unknown"]},
        },
        "required": ["stairs", "curb", "steepRoad", "narrowRoad"],
    }

    point_schema = {
        "type": "object",
        "properties": {
            "pointId": {"type": "string"},
            "locationName": {"type": "string"},
            "detectedElements": detected_elements_schema,
            "recommendation": {"type": "string", "enum": ["안전", "주의", "위험"]},
            "summaryTitle": {"type": "string"},
            "aiSummary": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": [
            "pointId",
            "locationName",
            "detectedElements",
            "recommendation",
            "summaryTitle",
            "aiSummary",
            "reason",
        ],
    }

    return {
        "type": "object",
        "properties": {
            "routeId": {"type": "string"},
            "userType": {"type": "string"},
            "userTypeLabel": {"type": "string"},
            "routeSummary": {
                "type": "object",
                "properties": {
                    "recommendation": {"type": "string", "enum": ["안전", "주의", "위험"]},
                    "summaryTitle": {"type": "string"},
                    "aiSummary": {"type": "string"},
                    "mainRiskFactors": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["계단", "단차", "경사로", "좁은 길"]},
                    },
                    "mainRiskPoints": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": [
                    "recommendation",
                    "summaryTitle",
                    "aiSummary",
                    "mainRiskFactors",
                    "mainRiskPoints",
                    "reason",
                ],
            },
            "points": {"type": "array", "items": point_schema},
        },
        "required": ["routeId", "userType", "userTypeLabel", "routeSummary", "points"],
    }


class GoogleRouteAnalyzer(RouteAccessibilityAnalyzer):
    """Send one route prompt and all route images to Gemini."""

    provider_name = "google"

    def analyze_route(self, route: dict, user_type: str) -> dict:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")

        parts = [{"text": _render_route_prompt(route, user_type)}]
        for image_path in _iter_route_image_paths(route):
            mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(image_path.read_bytes()).decode("utf-8"),
                    }
                }
            )

        model = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL)
        request_payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": _route_json_schema(),
            },
        }

        req = request.Request(
            url=GOOGLE_API_URL_TEMPLATE.format(model=model),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            data=json.dumps(request_payload).encode("utf-8"),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Google route analysis failed: HTTP {exc.code}: {error_body}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Google route analysis failed: {exc}") from exc

        candidates = payload.get("candidates", [])
        if not candidates:
            raise RuntimeError("Google route analysis returned no candidates")

        response_parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in response_parts if "text" in part).strip()
        if not text:
            raise RuntimeError("Google route analysis returned empty text")

        try:
            route_result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Google route analysis returned invalid JSON: {text}") from exc

        route_result["analysisProviders"] = [self.provider_name]
        return route_result


class OpenAIRouteAnalyzer(RouteAccessibilityAnalyzer):
    """Send one route prompt and all route images to the OpenAI Responses API."""

    provider_name = "openai"

    def analyze_route(self, route: dict, user_type: str) -> dict:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        content = [{"type": "input_text", "text": _render_route_prompt(route, user_type)}]
        for image_path in _iter_route_image_paths(route):
            content.append(
                {
                    "type": "input_image",
                    "image_url": _image_data_url(image_path),
                    "detail": os.getenv("OPENAI_IMAGE_DETAIL", "low"),
                }
            )

        request_payload = {
            "model": os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            "input": [{"role": "user", "content": content}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "route_accessibility_analysis",
                    "schema": _route_json_schema(),
                    "strict": False,
                }
            },
            "store": False,
        }

        reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "low")
        if reasoning_effort:
            request_payload["reasoning"] = {"effort": reasoning_effort}

        req = request.Request(
            url=OPENAI_RESPONSES_API_URL,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            data=json.dumps(request_payload).encode("utf-8"),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI route analysis failed: HTTP {exc.code}: {error_body}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"OpenAI route analysis failed: {exc}") from exc

        if payload.get("status") not in {None, "completed"}:
            raise RuntimeError(f"OpenAI route analysis returned status {payload.get('status')}: {payload}")

        text = _extract_openai_output_text(payload)
        if not text:
            raise RuntimeError("OpenAI route analysis returned empty text")

        try:
            route_result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI route analysis returned invalid JSON: {text}") from exc

        route_result["analysisProviders"] = [self.provider_name]
        return route_result


def create_route_analyzer() -> RouteAccessibilityAnalyzer:
    """Choose the configured provider and fail clearly when no real API is configured."""

    provider = os.getenv("AI_ANALYZER_PROVIDER", "").lower()
    if provider == "google":
        return GoogleRouteAnalyzer()
    if provider == "openai":
        return OpenAIRouteAnalyzer()
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIRouteAnalyzer()
    if os.getenv("GOOGLE_API_KEY"):
        return GoogleRouteAnalyzer()
    raise RuntimeError("Set OPENAI_API_KEY or GOOGLE_API_KEY before running AI route analysis")
