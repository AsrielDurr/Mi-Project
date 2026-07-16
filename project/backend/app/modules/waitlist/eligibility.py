from __future__ import annotations

from app.contracts.models import EligibilityResult


class FakeEligibilityPort:
    """Standalone M3 adapter. Production integration injects M2 RuleEngine."""

    def __init__(self, blocked: dict[tuple[str, str], str] | None = None) -> None:
        self._blocked = blocked or {}

    def evaluate(self, student_id: str, course_id: str) -> EligibilityResult:
        reason = self._blocked.get((student_id, course_id))
        if reason is not None:
            return EligibilityResult(allowed=False, reason=reason)
        return EligibilityResult(allowed=True, reason="资格有效并成功补入")

