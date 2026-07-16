from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


class EligibilityResult(StrictModel):
    allowed: bool
    reason: str


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
