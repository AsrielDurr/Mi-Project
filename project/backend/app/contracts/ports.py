from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .models import Course, EligibilityResult, StudentProfile, TraceEvent, WaitlistEntry


@runtime_checkable
class CatalogPort(Protocol):
    def list_courses(self) -> list[Course]: ...

    def get_course(self, course_id: str) -> Course: ...


@runtime_checkable
class StatePort(Protocol):
    def get_student(self, student_id: str) -> StudentProfile: ...

    def get_enrolled_course_ids(self, student_id: str) -> list[str]: ...

    def save_enrolled(self, student_id: str, course_id: str) -> None: ...

    def save_waitlisted(self, student_id: str, course_id: str) -> int: ...

    def list_waitlist(self, course_id: str) -> list[WaitlistEntry]: ...

    def release_seat(self, course_id: str) -> None: ...


@runtime_checkable
class EligibilityPort(Protocol):
    """M2 implements this port; M3 injects it during integration."""

    def evaluate(self, student_id: str, course_id: str) -> EligibilityResult: ...


@runtime_checkable
class TracePort(Protocol):
    def create(self, event_type: str, payload: dict[str, Any]) -> str: ...

    def append(self, trace_id: str, event_type: str, payload: dict[str, Any]) -> None: ...

    def get(self, trace_id: str) -> list[TraceEvent]: ...
