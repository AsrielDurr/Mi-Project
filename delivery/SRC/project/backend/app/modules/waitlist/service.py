from __future__ import annotations

from typing import Any, Protocol

from app.contracts.models import (
    ActorType,
    CourseStatusResponse,
    RecomputeCheck,
    RecomputeResult,
    ReleaseSeatResponse,
    WaitlistStatus,
)
from app.contracts.ports import EligibilityPort, StatePort, TracePort


class WaitlistStatePort(StatePort, Protocol):
    def get_course_status(self, course_id: str) -> CourseStatusResponse: ...

    def mark_waitlist_skipped(
        self,
        student_id: str,
        course_id: str,
        reason: str,
    ) -> None: ...

    def promote_waitlisted(
        self,
        student_id: str,
        course_id: str,
        reason: str,
    ) -> None: ...


class WaitlistTracePort(TracePort, Protocol):
    def create(
        self,
        event_type: str,
        payload: dict[str, Any],
        actor: ActorType = ActorType.SYSTEM,
    ) -> str: ...

    def append(
        self,
        trace_id: str,
        event_type: str,
        payload: dict[str, Any],
        actor: ActorType = ActorType.SYSTEM,
    ) -> None: ...


class WaitlistService:
    def __init__(
        self,
        state: WaitlistStatePort,
        eligibility: EligibilityPort,
        trace: WaitlistTracePort,
    ) -> None:
        self._state = state
        self._eligibility = eligibility
        self._trace = trace
        self._active_trace_by_course: dict[str, str] = {}

    def release_seat(self, course_id: str) -> ReleaseSeatResponse:
        before = self._state.get_course_status(course_id)
        self._state.release_seat(course_id)
        after_course = self._state.get_course_status(course_id).course
        available = max(after_course.capacity - after_course.enrolled_count, 0)
        trace_id = self._trace.create(
            "SEAT_RELEASED",
            {
                "course_id": course_id,
                "capacity_before": before.course.capacity,
                "capacity_after": after_course.capacity,
                "enrolled_count": after_course.enrolled_count,
                "available_seats": available,
            },
            actor=ActorType.TEACHER,
        )
        self._active_trace_by_course[course_id] = trace_id
        return ReleaseSeatResponse(
            trace_id=trace_id,
            course_id=course_id,
            capacity_before=before.course.capacity,
            capacity_after=after_course.capacity,
            enrolled_count=after_course.enrolled_count,
            available_seats=available,
        )

    def recompute(self, course_id: str) -> RecomputeResult:
        status = self._state.get_course_status(course_id)
        available_before = status.available_seats
        trace_id = self._active_trace_by_course.pop(course_id, None)
        if trace_id is None:
            trace_id = self._trace.create(
                "WAITLIST_RECOMPUTED",
                {
                    "course_id": course_id,
                    "available_seats_before": available_before,
                },
                actor=ActorType.SYSTEM,
            )
        else:
            self._trace.append(
                trace_id,
                "WAITLIST_RECOMPUTED",
                {
                    "course_id": course_id,
                    "available_seats_before": available_before,
                },
                actor=ActorType.SYSTEM,
            )
        checked: list[RecomputeCheck] = []
        promoted: list[str] = []
        remaining = available_before

        if remaining > 0:
            for entry in self._state.list_waitlist(course_id):
                if remaining <= 0:
                    break
                if entry.status != WaitlistStatus.WAITING:
                    continue

                eligibility = self._eligibility.evaluate(entry.student_id, course_id)
                self._trace.append(
                    trace_id,
                    "WAITLIST_ELIGIBILITY_CHECKED",
                    {
                        "student_id": entry.student_id,
                        "course_id": course_id,
                        "allowed": eligibility.allowed,
                        "reason": eligibility.reason,
                    },
                    actor=ActorType.SYSTEM,
                )
                if not eligibility.allowed:
                    self._state.mark_waitlist_skipped(
                        entry.student_id,
                        course_id,
                        eligibility.reason,
                    )
                    checked.append(
                        RecomputeCheck(
                            student_id=entry.student_id,
                            waitlist_status=WaitlistStatus.SKIPPED,
                            reason=eligibility.reason,
                        )
                    )
                    self._trace.append(
                        trace_id,
                        "WAITLIST_SKIPPED",
                        {
                            "student_id": entry.student_id,
                            "course_id": course_id,
                            "reason": eligibility.reason,
                        },
                        actor=ActorType.SYSTEM,
                    )
                    continue

                self._state.promote_waitlisted(
                    entry.student_id,
                    course_id,
                    eligibility.reason,
                )
                checked.append(
                    RecomputeCheck(
                        student_id=entry.student_id,
                        waitlist_status=WaitlistStatus.PROMOTED,
                        reason=eligibility.reason,
                    )
                )
                promoted.append(entry.student_id)
                remaining -= 1
                self._trace.append(
                    trace_id,
                    "WAITLIST_PROMOTED",
                    {
                        "student_id": entry.student_id,
                        "course_id": course_id,
                        "reason": eligibility.reason,
                    },
                    actor=ActorType.SYSTEM,
                )

        return RecomputeResult(
            trace_id=trace_id,
            course_id=course_id,
            available_seats_before=available_before,
            checked=checked,
            promoted_student_ids=promoted,
        )
