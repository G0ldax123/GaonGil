"""Segment analyzers for mock/static MVP execution and LLM provider extensions."""

from __future__ import annotations

from abc import ABC, abstractmethod
import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib import error, request

from .accessibility_schema import SegmentAnalysisSchema, normalize_detected
from .slope import get_slope_level

RISK_LABELS = {
    "stairs": "계단",
    "curb": "단차",
    "narrow_path": "좁은 보도",
    "steep_slope": "급경사",
    "uneven_surface": "노면 불량",
    "obstacle": "장애물",
}

ASSET_MOCK_DETECTIONS = {
    "route_a_1": {
        "stairs": "false",
        "curb": "true",
        "narrowRoad": "false",
        "steepRoad": "true",
        "otherObstacle": "unknown",
    },
    "route_a_2": {
        "stairs": "false",
        "curb": "false",
        "narrowRoad": "true",
        "steepRoad": "true",
        "otherObstacle": "false",
    },
}

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompt.md"
DEFAULT_GOOGLE_MODEL = "gemini-2.0-flash"
GOOGLE_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_OPENAI_MODEL = "gpt-5.4"
OPENAI_RESPONSES_API_URL = "https://api.openai.com/v1/responses"


class BaseAccessibilityAnalyzer(ABC):
    """Abstract provider interface for segment-level accessibility analysis."""

    provider_name = "base"

    @abstractmethod
    def analyze(self, segment: dict, user_type: str) -> SegmentAnalysisSchema:
        raise NotImplementedError

    def analyze_route(self, route: dict, user_type: str) -> dict:
        raise NotImplementedError


def _default_analysis() -> SegmentAnalysisSchema:
    return {
        "detected": normalize_detected(None),
        "severity": "medium",
        "accessibility": "caution",
        "risk_factors": [],
        "one_line_summary": "분석 결과를 확인할 수 없는 구간입니다.",
        "reason": "외부 분석 결과를 가져오지 못해 기본값으로 처리했습니다.",
    }


def _json_schema() -> dict:
    # Keep the model on a fixed JSON contract so downstream scoring never depends on free-form text.
    return {
        "type": "object",
        "properties": {
            "detected": {
                "type": "object",
                "properties": {
                    "stairs": {"type": "string", "enum": ["true", "false", "unknown"]},
                    "curb": {"type": "string", "enum": ["true", "false", "unknown"]},
                    "narrow_path": {"type": "string", "enum": ["true", "false", "unknown"]},
                    "steep_slope": {"type": "string", "enum": ["true", "false", "unknown"]},
                    "uneven_surface": {"type": "string", "enum": ["true", "false", "unknown"]},
                    "obstacle": {"type": "string", "enum": ["true", "false", "unknown"]},
                },
                "required": ["stairs", "curb", "narrow_path", "steep_slope", "uneven_surface", "obstacle"],
            },
            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
            "accessibility": {"type": "string", "enum": ["good", "caution", "bad"]},
            "risk_factors": {"type": "array", "items": {"type": "string"}},
            "one_line_summary": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["detected", "severity", "accessibility", "risk_factors", "one_line_summary", "reason"],
    }


def _route_json_schema() -> dict:
    """Schema for the full ai_results.json-style route object."""

    point_schema = {
        "type": "object",
        "properties": {
            "pointId": {"type": "string"},
            "locationName": {"type": "string"},
            "slopePercent": {"type": ["number", "null"]},
            "slopeLevel": {"type": ["string", "null"]},
            "detectedElements": {
                "type": "object",
                "properties": {
                    "stairs": {"type": "string"},
                    "curb": {"type": "string"},
                    "steepRoad": {"type": "string"},
                    "narrowRoad": {"type": "string"},
                    "otherObstacle": {"type": "string"},
                },
                "required": ["stairs", "curb", "steepRoad", "narrowRoad", "otherObstacle"],
            },
            "riskFactors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "label": {"type": "string"},
                        "severity": {"type": "string"},
                        "displayText": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["type", "label", "severity", "displayText", "description"],
                },
            },
            "accessibilityLevel": {"type": "string"},
            "riskLevel": {"type": "string"},
            "recommendation": {"type": "string"},
            "summaryTitle": {"type": "string"},
            "aiSummary": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": [
            "pointId",
            "locationName",
            "slopePercent",
            "slopeLevel",
            "detectedElements",
            "riskFactors",
            "accessibilityLevel",
            "riskLevel",
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
                    "recommendation": {"type": "string"},
                    "riskLevel": {"type": "string"},
                    "summaryTitle": {"type": "string"},
                    "aiSummary": {"type": "string"},
                    "mainRiskFactors": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["recommendation", "riskLevel", "summaryTitle", "aiSummary", "mainRiskFactors", "reason"],
            },
            "points": {"type": "array", "items": point_schema},
        },
        "required": ["routeId", "userType", "userTypeLabel", "routeSummary", "points"],
    }


def _load_prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "너는 교통약자 이동 경로 분석기다. 이미지를 보고 계단, 단차, 좁은 길, 급경사, "
        "노면 불량, 장애물을 JSON으로 분석해라."
    )


def _render_prompt(template: str, segment: dict, user_type: str) -> str:
    return (
        template.replace("{user_type}", user_type)
        .replace("{location_name}", str(segment.get("locationName", "")))
        .replace("{point_id}", str(segment.get("pointId", segment.get("segmentId", ""))))
        .replace("{image_url}", str(segment.get("imageUrl", "")))
    )


def _render_route_prompt(template: str, route: dict, user_type: str, origin: str = "", destination: str = "") -> str:
    """Render the route-level prompt used for one-shot ai_results generation."""

    point_lines = []
    for point in route.get("points", []):
        point_lines.append(
            f'- {point["pointId"]}: {point["locationName"]} | imageUrl={point.get("imageUrl", "")} | '
            f'roadviewImagePath={point.get("roadviewImagePath", "")}'
        )
    points_context = "\n".join(point_lines)

    return (
        template.replace("{user_type}", user_type)
        .replace("{route_id}", str(route.get("routeId", "")))
        .replace("{route_name}", str(route.get("name", "")))
        .replace("{origin}", origin)
        .replace("{destination}", destination)
        .replace("{duration}", str(route.get("duration", "")))
        .replace("{distance}", str(route.get("distance", "")))
        .replace("{points_context}", points_context)
    )


def _image_data_url(image_path: Path, mime_type: str | None = None) -> str:
    detected_mime_type = mime_type or mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    image_base64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{detected_mime_type};base64,{image_base64}"


def _extract_openai_output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"].strip()

    text_parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                text_parts.append(content["text"])

    return "".join(text_parts).strip()


class MockAccessibilityAnalyzer(BaseAccessibilityAnalyzer):
    """Use seed detections first, then fall back to slope-only conservative logic."""

    provider_name = "mock"

    def analyze(self, segment: dict, user_type: str) -> SegmentAnalysisSchema:
        has_slope_value = segment.get("slopePercent") not in {None, ""}
        slope_percent = float(segment.get("slopePercent", 0.0) or 0.0)
        slope_level = get_slope_level(slope_percent) if has_slope_value else "알 수 없음"
        image_name = Path(segment.get("imageUrl", "")).stem
        # File-name mocks let the team demo the full pipeline even when no API key is available.
        file_mock = ASSET_MOCK_DETECTIONS.get(image_name)
        detected = normalize_detected(segment.get("mockDetected") or file_mock)

        if segment.get("mockDetected") is None and file_mock is None and has_slope_value:
            detected["steep_slope"] = "true" if slope_percent > 8 else "false"

        if has_slope_value and slope_percent > 8:
            detected["steep_slope"] = "true"
        elif has_slope_value and slope_percent <= 6 and detected["steep_slope"] == "unknown":
            detected["steep_slope"] = "false"

        risk_factors: list[str] = [
            label for key, label in RISK_LABELS.items() if detected.get(key) == "true"
        ]
        if 6 < slope_percent <= 8 and "급경사" not in risk_factors:
            risk_factors.append("경사 주의")

        if detected["stairs"] == "true" or detected["steep_slope"] == "true":
            severity = "high"
            accessibility = "bad"
        elif risk_factors:
            severity = "medium"
            accessibility = "caution"
        else:
            severity = "low"
            accessibility = "good"

        if accessibility == "good":
            one_line_summary = "이동에 큰 위험 요소가 적은 구간입니다."
            reason = f"경사 수준이 {slope_level}이고 뚜렷한 위험 요소가 확인되지 않았습니다."
        elif accessibility == "bad":
            one_line_summary = "직접 통과하기 까다로운 위험 구간입니다."
            reason = f"{', '.join(risk_factors)} 요소가 확인되어 우회가 필요할 수 있습니다."
        else:
            one_line_summary = "일부 접근성 위험 요소가 있어 주의가 필요한 구간입니다."
            reason = f"경사 수준은 {slope_level}이며 {', '.join(risk_factors)} 요소를 함께 고려해야 합니다."

        return {
            "detected": detected,
            "severity": severity,
            "accessibility": accessibility,
            "risk_factors": risk_factors,
            "one_line_summary": one_line_summary,
            "reason": reason,
            "provider": self.provider_name,
        }


class GoogleAccessibilityAnalyzer(BaseAccessibilityAnalyzer):
    """Use Gemini REST API with a prompt template and inline roadview image."""

    provider_name = "google"

    def analyze(self, segment: dict, user_type: str) -> SegmentAnalysisSchema:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")

        image_path = segment.get("roadviewImagePath")
        if not image_path:
            raise RuntimeError("roadviewImagePath is required for Google analysis")

        full_image_path = Path(__file__).resolve().parents[2] / image_path
        if not full_image_path.exists():
            raise RuntimeError(f"Roadview image not found: {full_image_path}")

        prompt = _render_prompt(_load_prompt_template(), segment, user_type)
        mime_type = mimetypes.guess_type(full_image_path.name)[0] or "image/png"
        image_base64 = base64.b64encode(full_image_path.read_bytes()).decode("utf-8")
        model = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL)
        request_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                # Keep output deterministic so the same prompt/image pair is less likely to drift.
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": _json_schema(),
            },
        }

        api_url = GOOGLE_API_URL_TEMPLATE.format(model=model)
        req = request.Request(
            url=api_url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            data=json.dumps(request_payload).encode("utf-8"),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Google analysis failed: {exc}") from exc

        candidates = payload.get("candidates", [])
        if not candidates:
            raise RuntimeError("Google analysis returned no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if "text" in part).strip()
        if not text:
            raise RuntimeError("Google analysis returned empty text")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Google analysis returned invalid JSON: {text}") from exc

        # Normalize the provider response so the rest of the pipeline sees one stable shape.
        normalized = _default_analysis()
        normalized["detected"] = normalize_detected(parsed.get("detected"))
        normalized["severity"] = parsed.get("severity", normalized["severity"])
        normalized["accessibility"] = parsed.get("accessibility", normalized["accessibility"])
        normalized["risk_factors"] = parsed.get("risk_factors", normalized["risk_factors"])
        normalized["one_line_summary"] = parsed.get("one_line_summary", normalized["one_line_summary"])
        normalized["reason"] = parsed.get("reason", normalized["reason"])
        normalized["provider"] = self.provider_name
        return normalized

    def analyze_route(self, route: dict, user_type: str) -> dict:
        """Send every route image in one request and expect ai_results-style route JSON back."""

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")

        parts = [
            {
                "text": _render_route_prompt(
                    _load_prompt_template(),
                    route,
                    user_type,
                    route.get("origin", ""),
                    route.get("destination", ""),
                )
            }
        ]

        for point in route.get("points", []):
            image_path = point.get("roadviewImagePath")
            if not image_path:
                continue
            full_image_path = Path(__file__).resolve().parents[2] / image_path
            if not full_image_path.exists():
                continue
            mime_type = mimetypes.guess_type(full_image_path.name)[0] or "image/png"
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(full_image_path.read_bytes()).decode("utf-8"),
                    }
                }
            )

        model = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL)
        request_payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                # Route-level results should also stay deterministic across repeated runs.
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": _route_json_schema(),
            },
        }

        api_url = GOOGLE_API_URL_TEMPLATE.format(model=model)
        req = request.Request(
            url=api_url,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            data=json.dumps(request_payload).encode("utf-8"),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Google route analysis failed: {exc}") from exc

        candidates = payload.get("candidates", [])
        if not candidates:
            raise RuntimeError("Google route analysis returned no candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if "text" in part).strip()
        if not text:
            raise RuntimeError("Google route analysis returned empty text")

        try:
            route_result = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Google route analysis returned invalid JSON: {text}") from exc

        route_result["analysisProviders"] = ["google"]
        for point in route_result.get("points", []):
            point["analysisProvider"] = "google"
        return route_result


class OpenAIAccessibilityAnalyzer(BaseAccessibilityAnalyzer):
    """Use OpenAI Responses API with route-level image inputs."""

    provider_name = "openai"

    def analyze(self, segment: dict, user_type: str) -> SegmentAnalysisSchema:
        raise NotImplementedError("OpenAI provider is implemented for route-level analysis only")

    def analyze_route(self, route: dict, user_type: str) -> dict:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        content = [
            {
                "type": "input_text",
                "text": _render_route_prompt(
                    _load_prompt_template(),
                    route,
                    user_type,
                    route.get("origin", ""),
                    route.get("destination", ""),
                ),
            }
        ]

        for point in route.get("points", []):
            image_path = point.get("roadviewImagePath")
            if not image_path:
                continue
            full_image_path = Path(__file__).resolve().parents[2] / image_path
            if not full_image_path.exists():
                continue
            content.append(
                {
                    "type": "input_image",
                    "image_url": _image_data_url(full_image_path),
                    "detail": os.getenv("OPENAI_IMAGE_DETAIL", "low"),
                }
            )

        model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        request_payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
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
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            data=json.dumps(request_payload).encode("utf-8"),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=120) as response:
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

        route_result["analysisProviders"] = ["openai"]
        for point in route_result.get("points", []):
            point["analysisProvider"] = "openai"
        return route_result


def create_accessibility_analyzer() -> BaseAccessibilityAnalyzer:
    """Choose the runtime analyzer provider, with automatic Google fallback."""

    provider = os.getenv("AI_ANALYZER_PROVIDER", "").lower()
    if provider == "mock":
        return MockAccessibilityAnalyzer()
    if provider == "google":
        return GoogleAccessibilityAnalyzer()
    if provider == "openai":
        return OpenAIAccessibilityAnalyzer()
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL", "").startswith("gpt"):
        return OpenAIAccessibilityAnalyzer()
    if os.getenv("GOOGLE_API_KEY"):
        return ResilientGoogleAccessibilityAnalyzer()
    return MockAccessibilityAnalyzer()


class ResilientGoogleAccessibilityAnalyzer(BaseAccessibilityAnalyzer):
    """Prefer Google analysis, but keep the MVP runnable with mock fallback."""

    provider_name = "google"

    def __init__(self) -> None:
        self.google = GoogleAccessibilityAnalyzer()
        self.mock = MockAccessibilityAnalyzer()

    def analyze(self, segment: dict, user_type: str) -> SegmentAnalysisSchema:
        try:
            return self.google.analyze(segment, user_type)
        except Exception:
            # Any provider failure should degrade gracefully to mock output, not break the demo.
            fallback = self.mock.analyze(segment, user_type)
            fallback["provider"] = self.mock.provider_name
            return fallback

    def analyze_route(self, route: dict, user_type: str) -> dict:
        try:
            return self.google.analyze_route(route, user_type)
        except Exception:
            raise
