"""M2 standalone demo — uses FakeStatePort and FakeTracePort.

Run: python -m uvicorn app.modules.enrollment.demo:app --port 8102

Demo scenarios:
1. POST /api/enroll {student_id: "S001", course_id: "CS101"} → duplicate → REJECTED
2. POST /api/enroll {student_id: "S002", course_id: "ML301"} → missing prereq → REJECTED
3. POST /api/enroll {student_id: "S001", course_id: "DB202"} → time conflict → REJECTED
4. POST /api/enroll {student_id: "S001", course_id: "WEB201"} → capacity ✓ → ENROLLED
5. POST /api/enroll {student_id: "S001", course_id: "AI201"} → full → WAITLISTED
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.contracts.ports import (
    Schedule, Course, StudentProfile, WaitlistEntry,
)

from .service import EnrollmentService
from .router import create_router


class DemoFakeStatePort:
    """FakeStatePort with fixed demo data covering all M2 scenarios."""

    def __init__(self):
        self._students = {
            "S001": StudentProfile(
                student_id="S001", goal="Learn AI", skills=["Python"],
                available_times=["MON_EVENING"],
                completed_course_ids=["CS101"],
                enrolled_course_ids=["CS101"],
            ),
            "S002": StudentProfile(
                student_id="S002", goal="Learn Web", skills=["JavaScript"],
                available_times=["TUE_EVENING"],
                completed_course_ids=["CS101"],
                enrolled_course_ids=[],
            ),
            "S003": StudentProfile(
                student_id="S003", goal="Learn AI", skills=["Python"],
                available_times=["MON_EVENING"],
                completed_course_ids=["CS101"],
                enrolled_course_ids=[],
            ),
        }

        self._courses = {
            "CS101": Course(
                course_id="CS101", name="Python程序设计", description="Python基础",
                schedule=Schedule(day="MON", start="08:00", end="10:00"),
                capacity=40, enrolled_count=38, prerequisite_ids=[], status="OPEN",
            ),
            "AI201": Course(
                course_id="AI201", name="人工智能基础", description="AI入门",
                schedule=Schedule(day="TUE", start="10:00", end="12:00"),
                capacity=30, enrolled_count=30, prerequisite_ids=["CS101"], status="OPEN",
            ),
            "DB202": Course(
                course_id="DB202", name="数据库系统", description="数据库",
                schedule=Schedule(day="MON", start="08:00", end="10:00"),
                capacity=35, enrolled_count=34, prerequisite_ids=[], status="OPEN",
            ),
            "ML301": Course(
                course_id="ML301", name="机器学习", description="ML",
                schedule=Schedule(day="THU", start="14:00", end="16:00"),
                capacity=25, enrolled_count=22, prerequisite_ids=["AI201"], status="OPEN",
            ),
            "WEB201": Course(
                course_id="WEB201", name="Web开发", description="Web开发",
                schedule=Schedule(day="WED", start="14:00", end="16:00"),
                capacity=40, enrolled_count=26, prerequisite_ids=["CS101"], status="OPEN",
            ),
        }

        self._enrolled: dict[str, list[str]] = {
            "S001": ["CS101"],
            "S002": [],
            "S003": [],
        }

        self._waitlists: dict[str, list[WaitlistEntry]] = {
            "AI201": [
                WaitlistEntry("S002", "AI201", 1, "2026-07-16T09:00:00", "WAITING", None),
                WaitlistEntry("S005", "AI201", 2, "2026-07-16T09:05:00", "WAITING", None),
            ],
        }

        self.enroll_save_calls: list[tuple] = []
        self.waitlist_save_calls: list[tuple] = []

    @property
    def course_ids(self) -> list[str]:
        return list(self._courses.keys())

    def get_student(self, student_id: str) -> StudentProfile:
        if student_id not in self._students:
            raise KeyError(f"Student {student_id} not found")
        return self._students[student_id]

    def get_course(self, course_id: str) -> Course:
        if course_id not in self._courses:
            raise KeyError(f"Course {course_id} not found")
        return self._courses[course_id]

    def get_enrolled_course_ids(self, student_id: str) -> list[str]:
        self.get_student(student_id)
        return list(self._enrolled.get(student_id, []))

    def save_enrolled(self, student_id: str, course_id: str) -> None:
        self.enroll_save_calls.append(("enrolled", student_id, course_id))
        if student_id not in self._enrolled:
            self._enrolled[student_id] = []
        if course_id not in self._enrolled[student_id]:
            self._enrolled[student_id].append(course_id)

    def save_waitlisted(self, student_id: str, course_id: str) -> int:
        self.waitlist_save_calls.append(("waitlisted", student_id, course_id))
        if course_id not in self._waitlists:
            self._waitlists[course_id] = []
        position = len(self._waitlists[course_id]) + 1
        entry = WaitlistEntry(
            student_id=student_id, course_id=course_id,
            position=position, applied_at="2026-07-16T10:00:00",
            status="WAITING", last_check_reason=None,
        )
        self._waitlists[course_id].append(entry)
        return position

    def list_waitlist(self, course_id: str) -> list[WaitlistEntry]:
        return list(self._waitlists.get(course_id, []))

    def is_waitlisted(self, student_id: str, course_id: str) -> bool:
        entries = self._waitlists.get(course_id, [])
        return any(e.student_id == student_id for e in entries)


class DemoFakeTracePort:
    def __init__(self):
        self.events: list[tuple] = []
        self._next_id = 0

    def create(self, event_type: str, actor: str, payload: dict) -> str:
        self._next_id += 1
        trace_id = f"trace-{self._next_id:03d}"
        self.events.append(("create", trace_id, event_type, actor, payload))
        return trace_id

    def append(self, trace_id: str, event_type: str, actor: str, payload: dict) -> None:
        self.events.append(("append", trace_id, event_type, actor, payload))

    def get(self, trace_id: str) -> list:
        return []


def create_app() -> FastAPI:
    state = DemoFakeStatePort()
    trace = DemoFakeTracePort()
    service = EnrollmentService(state=state, trace=trace)
    router = create_router(service, course_ids=state.course_ids)

    app = FastAPI(title="M2 Enrollment Module Demo", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
