from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from app.modules.waitlist.demo import create_demo_app


PROJECT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_DIR.parent / "ai-course-selection-data"
OPENAPI_FILE = PROJECT_DIR / "contracts" / "openapi.yaml"


def _contract() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI_FILE.read_text(encoding="utf-8"))


def _assert_component(payload: Any, component_name: str) -> None:
    contract = _contract()
    schema = {
        **contract,
        "$ref": f"#/components/schemas/{component_name}",
    }
    Draft202012Validator(schema).validate(payload)


def test_all_m3_success_responses_match_frozen_openapi_components() -> None:
    with TestClient(create_demo_app(DATA_DIR)) as client:
        status = client.get(
            "/api/admin/course-status",
            params={"course_id": "AI201"},
        )
        release = client.post(
            "/api/admin/release-seat",
            json={"course_id": "AI201"},
        )
        recompute = client.post(
            "/api/admin/recompute-waitlist",
            json={"course_id": "AI201"},
        )
        trace = client.get(f"/api/trace/{recompute.json()['trace_id']}")
        reset = client.post(
            "/api/demo/reset",
            json={"scenario_id": "waitlist_recompute"},
        )

    responses = [
        (status, "CourseStatusResponse"),
        (release, "ReleaseSeatResponse"),
        (recompute, "RecomputeResult"),
        (trace, "TraceResponse"),
        (reset, "DemoResetResponse"),
    ]
    for response, component in responses:
        assert response.status_code == 200
        _assert_component(response.json(), component)


def test_m3_error_response_matches_frozen_openapi_component() -> None:
    with TestClient(create_demo_app(DATA_DIR)) as client:
        response = client.get(
            "/api/admin/course-status",
            params={"course_id": "UNKNOWN"},
        )

    assert response.status_code == 404
    _assert_component(response.json(), "ErrorResponse")
