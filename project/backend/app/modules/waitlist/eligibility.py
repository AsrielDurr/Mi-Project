from __future__ import annotations

from app.contracts.models import (
    EligibilityResult,
    RuleCheckResult,
    RuleDecision,
    RuleName,
)


class FakeEligibilityPort:
    """Standalone M3 adapter. Production integration injects M2 RuleEngine."""

    def __init__(self, blocked: dict[tuple[str, str], str] | None = None) -> None:
        self._blocked = blocked or {}

    def evaluate(self, student_id: str, course_id: str) -> EligibilityResult:
        reason = self._blocked.get((student_id, course_id))
        if reason is not None:
            return EligibilityResult(
                rule_decision=RuleDecision.BLOCK,
                checks=[
                    RuleCheckResult(
                        rule=RuleName.TIME_CONFLICT,
                        passed=False,
                        reason=reason,
                        related_course_id="DB202",
                    )
                ],
            )
        return EligibilityResult(
            rule_decision=RuleDecision.PASS,
            checks=[
                RuleCheckResult(
                    rule=RuleName.TIME_CONFLICT,
                    passed=True,
                    reason="资格有效并成功补入",
                    related_course_id=None,
                )
            ],
        )

