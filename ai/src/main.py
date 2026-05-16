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
DATA_AI_RESULTS_PATH = PROJECT_ROOT / "data" / "ai_results_runtime.json"


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
    parser.add_argument("--output", default="", help="Optional JSON output path. Defaults to stdout only.")
    return parser


def load_front_request(path: Path = DATA_FRONT_REQUEST_PATH) -> dict | None:
    """Load the backend-style front request example when CLI args are omitted."""

    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
    )
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif DATA_AI_RESULTS_PATH.parent.exists():
        # Keep a runtime artifact in data/ so backend developers can inspect the latest AI output.
        DATA_AI_RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
