from __future__ import annotations

from fastapi.testclient import TestClient

from app.modules.recommendation.demo import create_demo_app


def test_recommend_api_matches_frozen_shape_in_fallback_mode() -> None:
    with TestClient(create_demo_app()) as client:
        response = client.post(
            "/api/recommend",
            json={
                "student": {
                    "student_id": "S001",
                    "goal": "人工智能",
                    "skills": ["Python"],
                    "available_times": ["上午"],
                    "completed_course_ids": ["CS101"],
                    "enrolled_course_ids": ["DB202"],
                }
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "trace_id", "source", "model", "prompt_version",
        "fallback_reason", "recommendations",
    }
    assert body["source"] == "FALLBACK"
    assert body["fallback_reason"] == "MiMo未配置"
    assert body["recommendations"]
