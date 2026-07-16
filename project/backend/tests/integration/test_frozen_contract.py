from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from app.main import create_app


PROJECT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_DIR.parent / "ai-course-selection-data"
OPENAPI_FILE = PROJECT_DIR / "contracts" / "openapi.yaml"


def assert_component(payload: Any, name: str) -> None:
    contract = yaml.safe_load(OPENAPI_FILE.read_text(encoding="utf-8"))
    Draft202012Validator(
        {**contract, "$ref": f"#/components/schemas/{name}"}
    ).validate(payload)


def test_all_eight_integrated_endpoints_keep_the_frozen_contract() -> None:
    with TestClient(create_app(DATA_DIR)) as client:
        recommend = client.post(
            "/api/recommend",
            json={
                "student": {
                    "student_id": "S004",
                    "goal": "软件开发",
                    "skills": [],
                    "available_times": [],
                    "completed_course_ids": ["CS101"],
                    "enrolled_course_ids": [],
                }
            },
        )
        enroll = client.post(
            "/api/enroll",
            json={"student_id": "S004", "course_id": "AI201"},
        )
        student_status = client.get(
            "/api/student/status", params={"student_id": "S004"}
        )
        course_status = client.get(
            "/api/admin/course-status", params={"course_id": "AI201"}
        )
        release = client.post(
            "/api/admin/release-seat", json={"course_id": "AI201"}
        )
        recompute = client.post(
            "/api/admin/recompute-waitlist", json={"course_id": "AI201"}
        )
        trace = client.get(f"/api/trace/{recompute.json()['trace_id']}")
        reset = client.post(
            "/api/demo/reset", json={"scenario_id": "waitlist_recompute"}
        )

    for response, component in [
        (recommend, "RecommendationResponse"),
        (enroll, "EnrollmentDecision"),
        (student_status, "StudentStatusResponse"),
        (course_status, "CourseStatusResponse"),
        (release, "ReleaseSeatResponse"),
        (recompute, "RecomputeResult"),
        (trace, "TraceResponse"),
        (reset, "DemoResetResponse"),
    ]:
        assert response.status_code == 200
        assert_component(response.json(), component)
