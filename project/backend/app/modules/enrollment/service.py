"""M2 EnrollmentService — orchestrates eligibility check and state transitions.

Capacity is NOT part of eligibility; it's handled here:
- PASS + capacity → ENROLLED
- PASS + full    → WAITLISTED
- BLOCK          → REJECTED
"""

from __future__ import annotations

from app.contracts.ports import (
    EligibilityPort,
    RuleDecision,
    EnrollmentStatus,
    StatePort,
    TracePort,
)
from .rule_engine import RuleEngine


class EnrollmentService:
    def __init__(self, state: StatePort, trace: TracePort, eligibility: EligibilityPort | None = None):
        self._state = state
        self._trace = trace
        self._engine = eligibility if eligibility is not None else RuleEngine(state=state)

    def enroll(self, student_id: str, course_id: str, recommendation_trace_id: str | None = None) -> dict:
        request_payload = {
            "student_id": student_id,
            "course_id": course_id,
            "recommendation_trace_id": recommendation_trace_id,
        }
        if recommendation_trace_id:
            trace_id = recommendation_trace_id
            self._trace.append(
                trace_id=trace_id,
                event_type="ENROLLMENT_REQUESTED",
                actor="STUDENT",
                payload=request_payload,
            )
        else:
            trace_id = self._trace.create(
                event_type="ENROLLMENT_REQUESTED",
                actor="STUDENT",
                payload=request_payload,
            )

        eligibility = self._engine.evaluate(student_id, course_id)
        course = self._state.get_course(course_id)

        self._trace.append(
            trace_id=trace_id,
            event_type="RULE_CHECKED",
            actor="SYSTEM",
            payload={
                "student_id": student_id,
                "course_id": course_id,
                "rule_decision": eligibility.rule_decision,
                "checks": [
                    {
                        "rule": c.rule,
                        "passed": c.passed,
                        "reason": c.reason,
                        "related_course_id": c.related_course_id,
                    }
                    for c in eligibility.checks
                ],
            },
        )

        checks = [
            {
                "rule": c.rule,
                "passed": c.passed,
                "reason": c.reason,
                "related_course_id": c.related_course_id,
            }
            for c in eligibility.checks
        ]

        if eligibility.rule_decision == RuleDecision.BLOCK:
            status = EnrollmentStatus.REJECTED
            capacity_available = course.enrolled_count < course.capacity
            waitlist_position = None

        elif course.enrolled_count < course.capacity:
            self._state.save_enrolled(student_id, course_id)
            status = EnrollmentStatus.ENROLLED
            capacity_available = True
            waitlist_position = None

        else:
            if self._state.is_waitlisted(student_id, course_id):
                entries = self._state.list_waitlist(course_id)
                existing = [e for e in entries if e.student_id == student_id]
                waitlist_position = existing[0].position if existing else None
            else:
                waitlist_position = self._state.save_waitlisted(student_id, course_id)
            status = EnrollmentStatus.WAITLISTED
            capacity_available = False

        self._trace.append(
            trace_id=trace_id,
            event_type="ENROLLMENT_DECIDED",
            actor="SYSTEM",
            payload={
                "student_id": student_id,
                "course_id": course_id,
                "rule_decision": eligibility.rule_decision,
                "capacity_available": capacity_available,
                "status": status,
                "waitlist_position": waitlist_position,
                "checks": checks,
            },
        )

        return {
            "trace_id": trace_id,
            "student_id": student_id,
            "course_id": course_id,
            "course_name": course.name,
            "rule_decision": eligibility.rule_decision,
            "capacity_available": capacity_available,
            "status": status,
            "waitlist_position": waitlist_position,
            "checks": checks,
        }

    def get_student_status(self, student_id: str, all_course_ids: list[str] | None = None) -> dict:
        student = self._state.get_student(student_id)
        enrolled_ids = self._state.get_enrolled_course_ids(student_id)

        enrollments = [
            {"course_id": cid, "status": EnrollmentStatus.ENROLLED}
            for cid in enrolled_ids
        ]

        waitlist_entries = []
        seen_courses = set()
        course_ids_to_check = all_course_ids if all_course_ids is not None else enrolled_ids
        for cid in course_ids_to_check:
            entries = self._state.list_waitlist(cid)
            for e in entries:
                if e.student_id == student_id and e.course_id not in seen_courses:
                    seen_courses.add(e.course_id)
                    waitlist_entries.append({
                        "student_id": e.student_id,
                        "course_id": e.course_id,
                        "position": e.position,
                        "applied_at": e.applied_at,
                        "status": e.status,
                        "last_check_reason": e.last_check_reason,
                    })

        return {
            "student_id": student_id,
            "enrollments": enrollments,
            "waitlist_entries": waitlist_entries,
        }
