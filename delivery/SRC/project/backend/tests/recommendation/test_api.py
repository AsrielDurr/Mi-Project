from __future__ import annotations

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.modules.recommendation.demo import create_demo_app


def test_recommend_api_matches_frozen_shape_in_fallback_mode() -> None:
    with patch.dict(os.environ, {}, clear=False) as env:
        env.pop("MIMO_API_KEY", None)
        env.pop("MIMO_BASE_URL", None)
        env.pop("MIMO_MODEL", None)
        app = create_demo_app()
    with TestClient(app) as client:
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
