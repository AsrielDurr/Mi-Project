from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


DATA_DIR = Path(__file__).resolve().parents[4] / "ai-course-selection-data"


class StubMiMo:
    model = "mimo-integration-stub"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return (
            '{"recommendations":[{"course_id":"WEB201","score":91,'
            '"reason":"匹配软件开发目标","uncertainty":"需确认前端基础"}]}'
        )


def student(student_id: str, goal: str) -> dict:
    return {
        "student_id": student_id,
        "goal": goal,
        "skills": ["Python"],
        "available_times": ["上午"],
        "completed_course_ids": ["CS101"],
        "enrolled_course_ids": [],
    }


def test_v1_stub_model_recommendation_drives_successful_enrollment_on_one_trace() -> None:
    with TestClient(create_app(DATA_DIR, llm=StubMiMo())) as client:
        recommendation = client.post(
            "/api/recommend",
            json={"student": student("S002", "软件开发")},
        ).json()
        assert recommendation["source"] == "MODEL"
        assert recommendation["recommendations"][0]["course_id"] == "WEB201"

        enrollment = client.post(
            "/api/enroll",
            json={
                "student_id": "S002",
                "course_id": "WEB201",
                "recommendation_trace_id": recommendation["trace_id"],
            },
        ).json()
        assert enrollment["status"] == "ENROLLED"
        assert enrollment["trace_id"] == recommendation["trace_id"]

        event_types = [
            event["event_type"]
            for event in client.get(f"/api/trace/{enrollment['trace_id']}").json()["events"]
        ]
        assert event_types == [
            "RECOMMENDATION_REQUESTED",
            "MODEL_RECOMMENDED",
            "ENROLLMENT_REQUESTED",
            "RULE_CHECKED",
            "ENROLLMENT_DECIDED",
        ]


def test_v2_time_conflict_is_rejected_without_state_write() -> None:
    with TestClient(create_app(DATA_DIR)) as client:
        result = client.post(
            "/api/enroll",
            json={"student_id": "S001", "course_id": "AI201"},
        ).json()
        assert result["rule_decision"] == "BLOCK"
        assert result["status"] == "REJECTED"
        assert any(
            check["rule"] == "TIME_CONFLICT" and not check["passed"]
            for check in result["checks"]
        )
        status = client.get(
            "/api/student/status", params={"student_id": "S001"}
        ).json()
        assert "AI201" not in [item["course_id"] for item in status["enrollments"]]


def test_v3_full_course_enters_waitlist_visible_to_teacher() -> None:
    with TestClient(create_app(DATA_DIR)) as client:
        result = client.post(
            "/api/enroll",
            json={"student_id": "S004", "course_id": "AI201"},
        ).json()
        assert result["rule_decision"] == "PASS"
        assert result["status"] == "WAITLISTED"
        assert result["waitlist_position"] == 3

        teacher = client.get(
            "/api/admin/course-status", params={"course_id": "AI201"}
        ).json()
        assert teacher["waitlist"][-1]["student_id"] == "S004"


def test_v4_real_rule_engine_skips_invalid_first_and_promotes_second() -> None:
    with TestClient(create_app(DATA_DIR)) as client:
        # The first waiting student changes state while waiting by enrolling in DB202.
        changed = client.post(
            "/api/enroll",
            json={"student_id": "S002", "course_id": "DB202"},
        ).json()
        assert changed["status"] == "ENROLLED"

        release = client.post(
            "/api/admin/release-seat", json={"course_id": "AI201"}
        ).json()
        result = client.post(
            "/api/admin/recompute-waitlist", json={"course_id": "AI201"}
        ).json()

        assert release["trace_id"] == result["trace_id"]
        assert [item["student_id"] for item in result["checked"]] == ["S002", "S005"]
        assert [item["waitlist_status"] for item in result["checked"]] == [
            "SKIPPED", "PROMOTED",
        ]
        assert result["promoted_student_ids"] == ["S005"]

        student_status = client.get(
            "/api/student/status", params={"student_id": "S005"}
        ).json()
        assert "AI201" in [item["course_id"] for item in student_status["enrollments"]]
