"""M2 EnrollmentService tests."""

import pytest

from app.contracts.ports import (
    RuleDecision, RuleName, EnrollmentStatus,
    StudentProfile, Course, Schedule,
)
from app.modules.enrollment.service import EnrollmentService
from .fakes import FakeStatePort, FakeTracePort


class TestEnrollmentServiceRejected:
    def test_block_returns_rejected(self):
        """BLOCK → REJECTED, no state writes."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": ["CS101"]},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "CS101")

        assert decision["status"] == EnrollmentStatus.REJECTED
        assert decision["rule_decision"] == RuleDecision.BLOCK
        assert decision["waitlist_position"] is None
        assert len(state.enroll_save_calls) == 0
        assert len(state.waitlist_save_calls) == 0

    def test_block_does_not_call_save_enrolled(self):
        """BLOCK 时不调用 save_enrolled 或 save_waitlisted."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": ["CS101"]},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        svc.enroll("S001", "CS101")

        assert len(state.enroll_save_calls) == 0
        assert len(state.waitlist_save_calls) == 0


class TestEnrollmentServiceEnrolled:
    def test_pass_with_capacity_returns_enrolled(self):
        """PASS + 有容量 → ENROLLED."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "WEB201")

        assert decision["status"] == EnrollmentStatus.ENROLLED
        assert decision["rule_decision"] == RuleDecision.PASS
        assert decision["capacity_available"] is True
        assert decision["waitlist_position"] is None

    def test_pass_with_capacity_calls_save_enrolled(self):
        """PASS + 有容量 → 调用 save_enrolled."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        svc.enroll("S001", "WEB201")

        assert len(state.enroll_save_calls) == 1
        assert state.enroll_save_calls[0][1] == "S001"
        assert state.enroll_save_calls[0][2] == "WEB201"


class TestEnrollmentServiceWaitlisted:
    def test_pass_with_full_capacity_returns_waitlisted(self):
        """PASS + 满员 → WAITLISTED with rank."""
        course = Course("AI201", "AI基础", "", Schedule("TUE", "10:00", "12:00"),
                        30, 30, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"AI201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "AI201")

        assert decision["status"] == EnrollmentStatus.WAITLISTED
        assert decision["rule_decision"] == RuleDecision.PASS
        assert decision["capacity_available"] is False
        assert decision["waitlist_position"] == 1

    def test_pass_with_full_capacity_calls_save_waitlisted(self):
        """PASS + 满员 → 调用 save_waitlisted."""
        course = Course("AI201", "AI基础", "", Schedule("TUE", "10:00", "12:00"),
                        30, 30, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"AI201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        svc.enroll("S001", "AI201")

        assert len(state.waitlist_save_calls) == 1


class TestEnrollmentServiceDuplicateWaitlist:
    def test_duplicate_waitlist_no_second_record(self):
        """重复候补不创建第二条记录."""
        course = Course("AI201", "AI基础", "", Schedule("TUE", "10:00", "12:00"),
                        30, 30, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"AI201": course},
            enrolled_ids={"S001": []},
        )
        # Pre-populate waitlist with S001 already on it
        from app.contracts.ports import WaitlistEntry
        state._waitlists["AI201"] = [
            WaitlistEntry("S001", "AI201", 1, "2026-07-16T09:00:00", "WAITING", None)
        ]
        state.waitlist_save_calls.clear()

        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "AI201")

        # Should return existing waitlist position, not create new entry
        assert decision["status"] == EnrollmentStatus.WAITLISTED
        assert decision["waitlist_position"] == 1
        assert len(state.waitlist_save_calls) == 0


class TestEnrollmentServiceTrace:
    def test_trace_saves_checks_and_final_status(self):
        """TracePort 保存规则检查和最终状态."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "WEB201")

        assert "trace_id" in decision
        assert len(trace.events) >= 1
        # At least one event should be ENROLLMENT_DECIDED or RULE_CHECKED
        event_types = [e[2] for e in trace.events]
        assert "ENROLLMENT_DECIDED" in event_types or "RULE_CHECKED" in event_types


class TestEnrollmentServiceResponseShape:
    def test_response_matches_enrollment_decision_schema(self):
        """响应结构与 EnrollmentDecision schema 一致."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        trace = FakeTracePort()
        svc = EnrollmentService(state=state, trace=trace)

        decision = svc.enroll("S001", "WEB201")

        required_keys = {"trace_id", "student_id", "course_id", "rule_decision",
                         "capacity_available", "status", "waitlist_position", "checks"}
        assert required_keys.issubset(set(decision.keys()))
        assert isinstance(decision["checks"], list)
        assert len(decision["checks"]) == 3
        for check in decision["checks"]:
            assert "rule" in check
            assert "passed" in check
            assert "reason" in check
            assert "related_course_id" in check
