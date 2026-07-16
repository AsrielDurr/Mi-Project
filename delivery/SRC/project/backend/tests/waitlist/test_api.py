from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.waitlist.demo import create_demo_app


DATA_DIR = Path(__file__).resolve().parents[4] / "ai-course-selection-data"


def create_client() -> TestClient:
    return TestClient(create_demo_app(DATA_DIR))


def test_course_status_matches_shared_contract() -> None:
    with create_client() as client:
        response = client.get(
            "/api/admin/course-status",
            params={"course_id": "AI201"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["course"]["course_id"] == "AI201"
    assert body["available_seats"] == 0
    assert [item["student_id"] for item in body["waitlist"]] == ["S002", "S005"]


def test_full_waitlist_flow_and_trace() -> None:
    with create_client() as client:
        release = client.post(
            "/api/admin/release-seat",
            json={"course_id": "AI201"},
        )
        assert release.status_code == 200
        assert release.json()["available_seats"] == 1

        recompute = client.post(
            "/api/admin/recompute-waitlist",
            json={"course_id": "AI201"},
        )
        assert recompute.status_code == 200
        result = recompute.json()
        assert result["promoted_student_ids"] == ["S005"]
        assert [item["waitlist_status"] for item in result["checked"]] == [
            "SKIPPED",
            "PROMOTED",
        ]

        trace = client.get(f"/api/trace/{result['trace_id']}")
        assert trace.status_code == 200
        assert [item["event_type"] for item in trace.json()["events"]] == [
            "SEAT_RELEASED",
            "WAITLIST_RECOMPUTED",
            "WAITLIST_ELIGIBILITY_CHECKED",
            "WAITLIST_SKIPPED",
            "WAITLIST_ELIGIBILITY_CHECKED",
            "WAITLIST_PROMOTED",
        ]

        status = client.get(
            "/api/admin/course-status",
            params={"course_id": "AI201"},
        ).json()
        assert status["course"]["enrolled_count"] == 31
        assert status["available_seats"] == 0
        assert "S005" in status["enrolled_student_ids"]


def test_reset_restores_initial_state() -> None:
    with create_client() as client:
        client.post("/api/admin/release-seat", json={"course_id": "AI201"})
        client.post("/api/admin/recompute-waitlist", json={"course_id": "AI201"})

        reset = client.post(
            "/api/demo/reset",
            json={"scenario_id": "waitlist_recompute"},
        )
        assert reset.status_code == 200

        status = client.get(
            "/api/admin/course-status",
            params={"course_id": "AI201"},
        ).json()
        assert status["course"]["capacity"] == 30
        assert status["course"]["enrolled_count"] == 30
        assert [item["status"] for item in status["waitlist"]] == [
            "WAITING",
            "WAITING",
        ]


def test_unknown_course_uses_contract_error_envelope() -> None:
    with create_client() as client:
        response = client.get(
            "/api/admin/course-status",
            params={"course_id": "UNKNOWN"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "COURSE_NOT_FOUND",
            "message": "课程不存在: UNKNOWN",
            "trace_id": None,
        }
    }
