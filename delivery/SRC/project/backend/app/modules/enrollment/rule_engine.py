"""M2 RuleEngine — deterministic eligibility checks.

Implements EligibilityPort. Pure function: reads state, returns evaluation,
never modifies state, never calls LLM.
"""

from app.contracts.ports import (
    EligibilityPort,
    EligibilityResult,
    RuleCheckResult,
    RuleDecision,
    RuleName,
    StatePort,
)


class RuleEngine(EligibilityPort):
    def __init__(self, state: StatePort):
        self._state = state

    def evaluate(self, student_id: str, course_id: str) -> EligibilityResult:
        state = self._state
        student = state.get_student(student_id)
        target_course = state.get_course(course_id)
        enrolled_ids = state.get_enrolled_course_ids(student_id)

        checks: list[RuleCheckResult] = []

        # 1. DUPLICATE
        if course_id in enrolled_ids:
            checks.append(RuleCheckResult(
                rule=RuleName.DUPLICATE,
                passed=False,
                reason=f"已选过课程 {course_id}",
                related_course_id=course_id,
            ))
        else:
            checks.append(RuleCheckResult(
                rule=RuleName.DUPLICATE,
                passed=True,
                reason="未重复选课",
                related_course_id=None,
            ))

        # 2. PREREQUISITE
        prereqs = target_course.prerequisite_ids
        if prereqs:
            completed = set(student.completed_course_ids)
            missing = [p for p in prereqs if p not in completed]
            if missing:
                checks.append(RuleCheckResult(
                    rule=RuleName.PREREQUISITE,
                    passed=False,
                    reason=f"缺少先修课程: {', '.join(missing)}",
                    related_course_id=missing[0],
                ))
            else:
                checks.append(RuleCheckResult(
                    rule=RuleName.PREREQUISITE,
                    passed=True,
                    reason="已满足先修要求",
                    related_course_id=None,
                ))
        else:
            checks.append(RuleCheckResult(
                rule=RuleName.PREREQUISITE,
                passed=True,
                reason="该课程无先修要求",
                related_course_id=None,
            ))

        # 3. TIME_CONFLICT
        conflict_found = False
        conflict_course_id = None
        target_sched = target_course.schedule

        for eid in enrolled_ids:
            try:
                enrolled_course = state.get_course(eid)
            except KeyError:
                continue
            es = enrolled_course.schedule
            if (es.day == target_sched.day
                    and es.start < target_sched.end
                    and target_sched.start < es.end):
                conflict_found = True
                conflict_course_id = eid
                break

        if conflict_found:
            checks.append(RuleCheckResult(
                rule=RuleName.TIME_CONFLICT,
                passed=False,
                reason=f"与 {conflict_course_id} 上课时间冲突",
                related_course_id=conflict_course_id,
            ))
        else:
            checks.append(RuleCheckResult(
                rule=RuleName.TIME_CONFLICT,
                passed=True,
                reason="无时间冲突",
                related_course_id=None,
            ))

        # Determine overall decision
        any_blocked = any(not c.passed for c in checks)
        rule_decision = RuleDecision.BLOCK if any_blocked else RuleDecision.PASS

        return EligibilityResult(rule_decision=rule_decision, checks=checks)
