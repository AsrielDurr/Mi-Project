"""Frozen Ports from Step 0 shared contract (dev-workflow.md section 4.4).

M2 implements EligibilityPort via RuleEngine.
M2 consumes StatePort and TracePort (provided by M3 InMemoryStore in integration,
or by FakeStatePort/FakeTracePort in standalone demo/tests).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


# ── Frozen enums (from contracts/enums.json) ──────────────────────────

class RuleDecision:
    PASS = "PASS"
    BLOCK = "BLOCK"


class EnrollmentStatus:
    ENROLLED = "ENROLLED"
    WAITLISTED = "WAITLISTED"
    REJECTED = "REJECTED"


class RuleName:
    DUPLICATE = "DUPLICATE"
    PREREQUISITE = "PREREQUISITE"
    TIME_CONFLICT = "TIME_CONFLICT"


class WaitlistStatus:
    WAITING = "WAITING"
    PROMOTED = "PROMOTED"
    SKIPPED = "SKIPPED"


# ── Domain value objects (from contracts/domain.schema.json) ──────────

@dataclass(frozen=True)
class RuleCheckResult:
    rule: str          # RuleName: DUPLICATE | PREREQUISITE | TIME_CONFLICT
    passed: bool
    reason: str
    related_course_id: str | None = None


@dataclass(frozen=True)
class EligibilityResult:
    """Returned by EligibilityPort.evaluate().

    Maps to EnrollmentDecision's rule_decision + checks fields.
    RuleEngine only decides PASS/BLOCK — it does NOT decide ENROLLED/WAITLISTED/REJECTED.
    """
    rule_decision: str   # RuleDecision: PASS | BLOCK
    checks: list[RuleCheckResult]


@dataclass(frozen=True)
class Schedule:
    day: str   # MON | TUE | WED | THU | FRI | SAT | SUN
    start: str  # HH:MM
    end: str    # HH:MM


@dataclass(frozen=True)
class Course:
    course_id: str
    name: str
    description: str
    schedule: Schedule
    capacity: int
    enrolled_count: int
    prerequisite_ids: list[str]
    status: str  # OPEN | CANCELLED


@dataclass(frozen=True)
class StudentProfile:
    student_id: str
    goal: str
    skills: list[str]
    available_times: list[str]
    completed_course_ids: list[str]
    enrolled_course_ids: list[str]


@dataclass(frozen=True)
class WaitlistEntry:
    student_id: str
    course_id: str
    position: int
    applied_at: str
    status: str           # WaitlistStatus
    last_check_reason: str | None = None


@dataclass
class TraceEvent:
    event_id: str
    trace_id: str
    event_type: str
    actor: str
    payload: dict
    created_at: str


# ── Frozen Ports (from dev-workflow.md section 4.4) ────────────────────

class EligibilityPort(Protocol):
    """M2's RuleEngine implements this. M3 calls it during waitlist recompute."""

    def evaluate(self, student_id: str, course_id: str) -> EligibilityResult: ...


class StatePort(Protocol):
    """M3's InMemoryStore implements this. M2 consumes it for enrollment operations."""

    def get_student(self, student_id: str) -> StudentProfile: ...
    def get_course(self, course_id: str) -> Course: ...
    def get_enrolled_course_ids(self, student_id: str) -> list[str]: ...
    def save_enrolled(self, student_id: str, course_id: str) -> None: ...
    def save_waitlisted(self, student_id: str, course_id: str) -> int: ...
    def list_waitlist(self, course_id: str) -> list[WaitlistEntry]: ...
    def is_waitlisted(self, student_id: str, course_id: str) -> bool: ...


class TracePort(Protocol):
    """M3's InMemoryStore implements this. M2 writes trace events through it."""

    def create(self, event_type: str, actor: str, payload: dict) -> str: ...
    def append(self, trace_id: str, event_type: str, actor: str, payload: dict) -> None: ...
    def get(self, trace_id: str) -> list[TraceEvent]: ...
