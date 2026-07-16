from __future__ import annotations

import sys
from typing import Any, Literal

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return self.value

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def __init__(self, *args: Any, **data: Any) -> None:
        """Accept legacy positional construction while keeping API validation strict."""
        if args:
            field_names = list(type(self).model_fields)
            if len(args) > len(field_names):
                raise TypeError(f"too many positional arguments for {type(self).__name__}")
            for name, value in zip(field_names, args):
                if name in data:
                    raise TypeError(f"multiple values for field {name}")
                data[name] = value
        super().__init__(**data)


class Weekday(StrEnum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class CourseStatus(StrEnum):
    OPEN = "OPEN"
    CANCELLED = "CANCELLED"


class WaitlistStatus(StrEnum):
    WAITING = "WAITING"
    PROMOTED = "PROMOTED"
    SKIPPED = "SKIPPED"


class RuleDecision(StrEnum):
    PASS = "PASS"
    BLOCK = "BLOCK"


class EnrollmentStatus(StrEnum):
    ENROLLED = "ENROLLED"
    WAITLISTED = "WAITLISTED"
    REJECTED = "REJECTED"


class RuleName(StrEnum):
    DUPLICATE = "DUPLICATE"
    PREREQUISITE = "PREREQUISITE"
    TIME_CONFLICT = "TIME_CONFLICT"


class ActorType(StrEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    SYSTEM = "SYSTEM"
    MODEL = "MODEL"


class Schedule(StrictModel):
    day: Weekday
    start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class Course(StrictModel):
    course_id: str
    name: str
    description: str = ""
    schedule: Schedule
    capacity: int = Field(ge=0)
    enrolled_count: int = Field(ge=0)
    prerequisite_ids: list[str] = Field(default_factory=list)
    status: CourseStatus = CourseStatus.OPEN


class StudentProfile(StrictModel):
    student_id: str
    goal: str
    skills: list[str] = Field(default_factory=list)
    available_times: list[str] = Field(default_factory=list)
    completed_course_ids: list[str] = Field(default_factory=list)
    enrolled_course_ids: list[str] = Field(default_factory=list)
    name: str = ""


class RecommendationSource(StrEnum):
    MODEL = "MODEL"
    FALLBACK = "FALLBACK"


class Recommendation(StrictModel):
    course_id: str
    course_name: str = ""
    score: int = Field(ge=0, le=100)
    reason: str
    uncertainty: str


class RecommendRequest(StrictModel):
    student: StudentProfile


class RecommendationResponse(StrictModel):
    trace_id: str
    source: RecommendationSource
    model: str | None
    prompt_version: str
    fallback_reason: str | None
    recommendations: list[Recommendation] = Field(min_length=1)


class WaitlistEntry(StrictModel):
    student_id: str
    course_id: str
    position: int = Field(ge=1)
    applied_at: str
    status: WaitlistStatus = WaitlistStatus.WAITING
    last_check_reason: str | None = None


class CourseStatusResponse(StrictModel):
    course: Course
    available_seats: int = Field(ge=0)
    enrolled_student_ids: list[str]
    waitlist: list[WaitlistEntry]


class RuleCheckResult(StrictModel):
    rule: RuleName
    passed: bool
    reason: str
    related_course_id: str | None = None


class EligibilityResult(StrictModel):
    rule_decision: RuleDecision
    checks: list[RuleCheckResult]

    @property
    def allowed(self) -> bool:
        return self.rule_decision == RuleDecision.PASS

    @property
    def reason(self) -> str:
        failed = next((check for check in self.checks if not check.passed), None)
        return failed.reason if failed else "资格有效并成功补入"


class EnrollmentRequest(StrictModel):
    student_id: str
    course_id: str
    recommendation_trace_id: str | None = None


class EnrollmentDecision(StrictModel):
    trace_id: str
    student_id: str
    course_id: str
    course_name: str = ""
    rule_decision: RuleDecision
    capacity_available: bool
    status: EnrollmentStatus
    waitlist_position: int | None = Field(default=None, ge=1)
    checks: list[RuleCheckResult]


class EnrollmentSummary(StrictModel):
    course_id: str
    status: EnrollmentStatus


class StudentStatusResponse(StrictModel):
    student_id: str
    enrollments: list[EnrollmentSummary]
    waitlist_entries: list[WaitlistEntry]


class ReleaseSeatResponse(StrictModel):
    trace_id: str
    course_id: str
    capacity_before: int = Field(ge=0)
    capacity_after: int = Field(ge=0)
    enrolled_count: int = Field(ge=0)
    available_seats: int = Field(ge=0)


class RecomputeCheck(StrictModel):
    student_id: str
    waitlist_status: Literal["PROMOTED", "SKIPPED"]
    reason: str


class RecomputeResult(StrictModel):
    trace_id: str
    course_id: str
    available_seats_before: int = Field(ge=0)
    checked: list[RecomputeCheck]
    promoted_student_ids: list[str]


class TraceEvent(StrictModel):
    event_id: str
    trace_id: str
    event_type: str
    actor: ActorType
    payload: dict[str, Any]
    created_at: str


class TraceResponse(StrictModel):
    trace_id: str
    events: list[TraceEvent]


class DemoResetResponse(StrictModel):
    trace_id: str
    scenario_id: str
    course_ids: list[str]
    student_ids: list[str]


class CourseCommandRequest(StrictModel):
    course_id: str


class DemoResetRequest(StrictModel):
    scenario_id: str
