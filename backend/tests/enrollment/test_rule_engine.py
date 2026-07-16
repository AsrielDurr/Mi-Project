"""M2 RuleEngine tests."""

import pytest

from app.contracts.ports import (
    RuleDecision, RuleName, RuleCheckResult,
    StudentProfile, Course, Schedule,
)
from app.modules.enrollment.rule_engine import RuleEngine
from .fakes import FakeStatePort


class TestRuleEngineDuplicate:
    def test_duplicate_enrollment_returns_block(self):
        """AC-R2-1: 重复选课 → BLOCK."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])  # already enrolled
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": ["CS101"]},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "CS101")

        assert result.rule_decision == RuleDecision.BLOCK
        dup_check = result.checks[0]
        assert dup_check.rule == RuleName.DUPLICATE
        assert dup_check.passed is False

    def test_duplicate_enrollment_not_already_enrolled_passes(self):
        """Not enrolled yet → DUPLICATE passes."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "CS101")

        dup_check = result.checks[0]
        assert dup_check.rule == RuleName.DUPLICATE
        assert dup_check.passed is True


class TestRuleEnginePrerequisite:
    def test_missing_prerequisite_returns_block(self):
        """AC-R2-2: 缺少先修 → BLOCK with missing course."""
        course = Course("AI201", "AI基础", "", Schedule("TUE", "10:00", "12:00"),
                        30, 30, ["CS101"], "OPEN")
        student = StudentProfile("S002", "goal", ["Python"], [],
                                 [], [])
        state = FakeStatePort(
            students={"S002": student},
            courses={"AI201": course},
            enrolled_ids={"S002": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S002", "AI201")

        assert result.rule_decision == RuleDecision.BLOCK
        prereq_check = result.checks[1]
        assert prereq_check.rule == RuleName.PREREQUISITE
        assert prereq_check.passed is False
        assert prereq_check.related_course_id is not None

    def test_satisfied_prerequisite_passes(self):
        """Student has completed prereq → PREREQUISITE passes."""
        course = Course("AI201", "AI基础", "", Schedule("TUE", "10:00", "12:00"),
                        30, 30, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"AI201": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "AI201")

        prereq_check = result.checks[1]
        assert prereq_check.rule == RuleName.PREREQUISITE
        assert prereq_check.passed is True

    def test_no_prerequisites_passes(self):
        """Course with no prerequisites → PREREQUISITE passes."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [], [], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "CS101")

        prereq_check = result.checks[1]
        assert prereq_check.rule == RuleName.PREREQUISITE
        assert prereq_check.passed is True


class TestRuleEngineTimeConflict:
    def test_time_conflict_returns_block(self):
        """AC-R2-3: 时间重叠 → BLOCK with conflicting course."""
        schedule = Schedule("MON", "08:00", "10:00")
        course = Course("WEB201", "Web", "", schedule, 40, 26, ["CS101"], "OPEN")
        # Student already enrolled in CS101 at same time
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])
        cs101 = Course("CS101", "Python", "", schedule, 40, 38, [], "OPEN")
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course, "CS101": cs101},
            enrolled_ids={"S001": ["CS101"]},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "WEB201")

        assert result.rule_decision == RuleDecision.BLOCK
        conflict_check = result.checks[2]
        assert conflict_check.rule == RuleName.TIME_CONFLICT
        assert conflict_check.passed is False
        assert conflict_check.related_course_id == "CS101"

    def test_no_time_conflict_passes(self):
        """Different time slots → TIME_CONFLICT passes."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        cs101 = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                       40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course, "CS101": cs101},
            enrolled_ids={"S001": ["CS101"]},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "WEB201")

        conflict_check = result.checks[2]
        assert conflict_check.rule == RuleName.TIME_CONFLICT
        assert conflict_check.passed is True

    def test_no_enrolled_courses_no_conflict(self):
        """Student with no enrolled courses → TIME_CONFLICT passes."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [], [], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "WEB201")

        conflict_check = result.checks[2]
        assert conflict_check.rule == RuleName.TIME_CONFLICT
        assert conflict_check.passed is True


class TestRuleEngineDeterminism:
    def test_same_input_same_result(self):
        """同一输入 → 相同结果."""
        course = Course("CS101", "Python", "", Schedule("MON", "08:00", "10:00"),
                        40, 38, [], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], ["CS101"])
        state = FakeStatePort(
            students={"S001": student},
            courses={"CS101": course},
            enrolled_ids={"S001": ["CS101"]},
        )
        engine = RuleEngine(state=state)

        r1 = engine.evaluate("S001", "CS101")
        r2 = engine.evaluate("S001", "CS101")

        assert r1.rule_decision == r2.rule_decision
        for c1, c2 in zip(r1.checks, r2.checks):
            assert c1.rule == c2.rule
            assert c1.passed == c2.passed
            assert c1.reason == c2.reason


class TestRuleEngineNoStateMutation:
    def test_rule_engine_does_not_call_save(self):
        """RuleEngine 不修改 StatePort (no save_enrolled/save_waitlisted calls)."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        engine.evaluate("S001", "WEB201")

        assert len(state.enroll_save_calls) == 0
        assert len(state.waitlist_save_calls) == 0


class TestRuleEngineCheckOrder:
    def test_checks_are_in_fixed_order(self):
        """规则检查顺序固定为 DUPLICATE → PREREQUISITE → TIME_CONFLICT."""
        course = Course("WEB201", "Web", "", Schedule("WED", "14:00", "16:00"),
                        40, 26, ["CS101"], "OPEN")
        student = StudentProfile("S001", "goal", ["Python"], [],
                                 ["CS101"], [])
        state = FakeStatePort(
            students={"S001": student},
            courses={"WEB201": course},
            enrolled_ids={"S001": []},
        )
        engine = RuleEngine(state=state)

        result = engine.evaluate("S001", "WEB201")

        rule_names = [c.rule for c in result.checks]
        assert rule_names == [RuleName.DUPLICATE, RuleName.PREREQUISITE, RuleName.TIME_CONFLICT]
