"""Tests for route ranking and recommended route selection."""

import json

from ai.src.route_ranker import load_route_sets, rank_routes


def _route_set_payload() -> list[dict]:
    return [
        {
            "routeSetId": "demo_route_1",
            "start": {"name": "출발지"},
            "end": {"name": "도착지"},
            "routes": [
                {
                    "routeId": "route_a",
                    "name": "안전 경로",
                    "description": "위험 요소가 적은 경로",
                    "duration": 14,
                    "distance": 850,
                    "points": [
                        {
                            "pointId": "a_1",
                            "locationName": "지점 A1",
                            "imageUrl": "/images/roadview/route_a_1.jpg",
                            "slopePercent": 2.0,
                            "slopeLevel": "완만",
                            "mockDetected": {
                                "stairs": "false",
                                "curb": "false",
                                "narrow_path": "false",
                                "steep_slope": "false",
                                "uneven_surface": "false",
                                "obstacle": "false"
                            }
                        }
                    ]
                },
                {
                    "routeId": "route_b",
                    "name": "계단 경로",
                    "description": "계단이 있는 경로",
                    "duration": 11,
                    "distance": 700,
                    "points": [
                        {
                            "pointId": "b_1",
                            "locationName": "지점 B1",
                            "imageUrl": "/images/roadview/route_b_1.jpg",
                            "slopePercent": 3.0,
                            "slopeLevel": "완만",
                            "mockDetected": {
                                "stairs": "true",
                                "curb": "true",
                                "narrow_path": "false",
                                "steep_slope": "false",
                                "uneven_surface": "false",
                                "obstacle": "false"
                            }
                        }
                    ]
                },
                {
                    "routeId": "route_c",
                    "name": "급경사 경로",
                    "description": "경사가 큰 경로",
                    "duration": 12,
                    "distance": 760,
                    "points": [
                        {
                            "pointId": "c_1",
                            "locationName": "지점 C1",
                            "imageUrl": "/images/roadview/route_c_1.jpg",
                            "slopePercent": 9.0,
                            "slopeLevel": "급경사",
                            "mockDetected": {
                                "stairs": "false",
                                "curb": "false",
                                "narrow_path": "true",
                                "steep_slope": "true",
                                "uneven_surface": "true",
                                "obstacle": "false"
                            }
                        }
                    ]
                }
            ]
        }
    ]


def test_routes_are_sorted_by_total_risk_score(tmp_path) -> None:
    payload = _route_set_payload()
    seed_path = tmp_path / "routes.json"
    seed_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    route_sets = load_route_sets(seed_path)
    ranked = rank_routes(route_sets[0]["routes"], "wheelchair")
    scores = [route["totalRiskScore"] for route in ranked]
    assert scores == sorted(scores)


def test_recommended_route_matches_lowest_risk_route(tmp_path) -> None:
    payload = _route_set_payload()
    seed_path = tmp_path / "routes.json"
    seed_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    route_sets = load_route_sets(seed_path)
    ranked = rank_routes(route_sets[0]["routes"], "wheelchair")
    lowest_risk_route = min(ranked, key=lambda route: route["totalRiskScore"])
    assert ranked[0]["routeId"] == lowest_risk_route["routeId"]
