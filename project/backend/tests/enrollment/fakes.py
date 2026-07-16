"""Fake implementations for M2 testing. Only allowed in tests/ and demo/ directories."""

from app.contracts.ports import (
    StatePort, TracePort, TraceEvent,
    StudentProfile, Course, Schedule, WaitlistEntry,
)


class FakeStatePort(StatePort):
    def __init__(self, students=None, courses=None, enrolled_ids=None, waitlists=None):
        self._students = students or {}
        self._courses = courses or {}
        self._enrolled = enrolled_ids or {}
        self._waitlists = waitlists or {}  # course_id -> list[WaitlistEntry]
        self.enroll_save_calls: list[tuple] = []
        self.waitlist_save_calls: list[tuple] = []

    def get_student(self, student_id: str) -> StudentProfile:
        if student_id not in self._students:
            raise KeyError(f"Student {student_id} not found")
        return self._students[student_id]

    def get_course(self, course_id: str) -> Course:
        if course_id not in self._courses:
            raise KeyError(f"Course {course_id} not found")
        return self._courses[course_id]

    def get_enrolled_course_ids(self, student_id: str) -> list[str]:
        return list(self._enrolled.get(student_id, []))

    def save_enrolled(self, student_id: str, course_id: str) -> None:
        self.enroll_save_calls.append(("enrolled", student_id, course_id))
        if student_id not in self._enrolled:
            self._enrolled[student_id] = []
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


class FakeTracePort(TracePort):
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

    def get(self, trace_id: str) -> list[TraceEvent]:
        return []

    def events_of_type(self, event_type: str) -> list[tuple]:
        return [e for e in self.events if e[2] == event_type]
