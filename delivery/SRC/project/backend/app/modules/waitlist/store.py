from __future__ import annotations

import copy
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.contracts.models import (
    ActorType,
    Course,
    CourseStatus,
    CourseStatusResponse,
    DemoResetResponse,
    Schedule,
    StudentProfile,
    TraceEvent,
    TraceResponse,
    WaitlistEntry,
    WaitlistStatus,
    Weekday,
)


CHINA_TZ = timezone(timedelta(hours=8))
WEEKDAYS = {
    1: Weekday.MON,
    2: Weekday.TUE,
    3: Weekday.WED,
    4: Weekday.THU,
    5: Weekday.FRI,
    6: Weekday.SAT,
    7: Weekday.SUN,
}


class StoreError(RuntimeError):
    pass


class CourseNotFoundError(StoreError):
    pass


class StudentNotFoundError(StoreError):
    pass


class TraceNotFoundError(StoreError):
    pass


class ScenarioNotFoundError(StoreError):
    pass


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalise_time(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CHINA_TZ)
    return parsed.isoformat()


class InMemoryStore:
    """Single-process state store backed by read-only JSON seed files."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._courses: dict[str, Course] = {}
        self._students: dict[str, StudentProfile] = {}
        self._enrolled_by_course: dict[str, set[str]] = defaultdict(set)
        self._waitlists: dict[str, list[WaitlistEntry]] = defaultdict(list)
        self._traces: dict[str, list[TraceEvent]] = defaultdict(list)
        self._load_seed()

    @classmethod
    def from_data_dir(cls, data_dir: str | Path) -> "InMemoryStore":
        resolved = Path(data_dir).resolve()
        required = ["courses.json", "students.json", "enrollments.json", "waitlist.json"]
        missing = [name for name in required if not (resolved / name).is_file()]
        if missing:
            raise FileNotFoundError(f"数据目录缺少文件: {', '.join(missing)}")
        return cls(resolved)

    def _load_seed(self) -> None:
        raw_courses = _read_json(self._data_dir / "courses.json")
        raw_students = _read_json(self._data_dir / "students.json")
        raw_enrollments = _read_json(self._data_dir / "enrollments.json")
        raw_waitlists = _read_json(self._data_dir / "waitlist.json")

        self._courses = {}
        for raw in raw_courses:
            day = WEEKDAYS.get(int(raw["weekday"]))
            if day is None:
                raise ValueError(f"课程{raw['id']}的weekday无效")
            self._courses[raw["id"]] = Course(
                course_id=raw["id"],
                name=raw["name"],
                description=f"{raw.get('category', '')} · {raw.get('teacher', '')}".strip(" ·"),
                schedule=Schedule(day=day, start=raw["start"], end=raw["end"]),
                capacity=raw["capacity"],
                enrolled_count=raw["enrolled"],
                prerequisite_ids=raw.get("prerequisites", []),
                status=CourseStatus.OPEN,
            )

        self._students = {}
        for raw in raw_students:
            selected = list(dict.fromkeys(raw.get("selectedCourses", [])))
            self._students[raw["id"]] = StudentProfile(
                student_id=raw["id"],
                name=raw.get("name", raw["id"]),
                goal=raw.get("goal", ""),
                skills=[],
                available_times=[raw.get("timePreference", "")]
                if raw.get("timePreference")
                else [],
                completed_course_ids=raw.get("completedCourses", []),
                enrolled_course_ids=selected,
            )

        self._enrolled_by_course = defaultdict(set)
        for raw in raw_enrollments:
            if raw.get("status") == "ENROLLED":
                student_id = raw["studentId"]
                course_id = raw["courseId"]
                self._enrolled_by_course[course_id].add(student_id)
                student = self._students.get(student_id)
                if student and course_id not in student.enrolled_course_ids:
                    student.enrolled_course_ids.append(course_id)

        self._waitlists = defaultdict(list)
        for course_waitlist in raw_waitlists:
            course_id = course_waitlist["courseId"]
            entries = sorted(
                course_waitlist.get("queue", []),
                key=lambda item: (item.get("priority", 0), item.get("applyTime", "")),
            )
            self._waitlists[course_id] = [
                WaitlistEntry(
                    student_id=item["studentId"],
                    course_id=course_id,
                    position=index,
                    applied_at=_normalise_time(item["applyTime"]),
                    status=WaitlistStatus.WAITING,
                    last_check_reason=None,
                )
                for index, item in enumerate(entries, start=1)
            ]

        self._traces = defaultdict(list)

    def list_courses(self) -> list[Course]:
        return [course.model_copy(deep=True) for course in self._courses.values()]

    def list_students(self) -> list[dict]:
        return [
            {"student_id": sid, "name": s.name}
            for sid, s in sorted(self._students.items())
        ]

    def get_course(self, course_id: str) -> Course:
        course = self._courses.get(course_id)
        if course is None:
            raise CourseNotFoundError(f"课程不存在: {course_id}")
        return course.model_copy(deep=True)

    def get_student(self, student_id: str) -> StudentProfile:
        student = self._students.get(student_id)
        if student is None:
            raise StudentNotFoundError(f"学生不存在: {student_id}")
        return student.model_copy(deep=True)

    def get_enrolled_course_ids(self, student_id: str) -> list[str]:
        return list(self.get_student(student_id).enrolled_course_ids)

    def get_course_status(self, course_id: str) -> CourseStatusResponse:
        course = self.get_course(course_id)
        waitlist = sorted(
            self._waitlists.get(course_id, []),
            key=lambda entry: entry.position,
        )
        return CourseStatusResponse(
            course=course,
            available_seats=max(course.capacity - course.enrolled_count, 0),
            enrolled_student_ids=sorted(self._enrolled_by_course.get(course_id, set())),
            waitlist=[entry.model_copy(deep=True) for entry in waitlist],
        )

    def list_waitlist(self, course_id: str) -> list[WaitlistEntry]:
        self.get_course(course_id)
        return [
            entry.model_copy(deep=True)
            for entry in sorted(
                self._waitlists.get(course_id, []),
                key=lambda item: item.position,
            )
        ]

    def is_waitlisted(self, student_id: str, course_id: str) -> bool:
        return any(
            entry.student_id == student_id
            and entry.status == WaitlistStatus.WAITING
            for entry in self._waitlists.get(course_id, [])
        )

    def release_seat(self, course_id: str) -> None:
        course = self._courses.get(course_id)
        if course is None:
            raise CourseNotFoundError(f"课程不存在: {course_id}")
        course.capacity += 1

    def save_enrolled(self, student_id: str, course_id: str) -> None:
        student = self._students.get(student_id)
        course = self._courses.get(course_id)
        if student is None:
            raise StudentNotFoundError(f"学生不存在: {student_id}")
        if course is None:
            raise CourseNotFoundError(f"课程不存在: {course_id}")
        if course_id in student.enrolled_course_ids:
            return
        if course.enrolled_count >= course.capacity:
            raise StoreError(f"课程没有可用名额: {course_id}")
        student.enrolled_course_ids.append(course_id)
        self._enrolled_by_course[course_id].add(student_id)
        course.enrolled_count += 1

    def save_waitlisted(self, student_id: str, course_id: str) -> int:
        self.get_student(student_id)
        self.get_course(course_id)
        queue = self._waitlists[course_id]
        existing = next((entry for entry in queue if entry.student_id == student_id), None)
        if existing is not None:
            return existing.position
        position = len(queue) + 1
        queue.append(
            WaitlistEntry(
                student_id=student_id,
                course_id=course_id,
                position=position,
                applied_at=datetime.now(CHINA_TZ).isoformat(),
                status=WaitlistStatus.WAITING,
                last_check_reason=None,
            )
        )
        return position

    def mark_waitlist_skipped(self, student_id: str, course_id: str, reason: str) -> None:
        entry = self._find_waitlist_entry(student_id, course_id)
        entry.status = WaitlistStatus.SKIPPED
        entry.last_check_reason = reason

    def promote_waitlisted(self, student_id: str, course_id: str, reason: str) -> None:
        entry = self._find_waitlist_entry(student_id, course_id)
        self.save_enrolled(student_id, course_id)
        entry.status = WaitlistStatus.PROMOTED
        entry.last_check_reason = reason

    def _find_waitlist_entry(self, student_id: str, course_id: str) -> WaitlistEntry:
        self.get_course(course_id)
        for entry in self._waitlists.get(course_id, []):
            if entry.student_id == student_id:
                return entry
        raise StoreError(f"候补记录不存在: {student_id}/{course_id}")

    def create(
        self,
        event_type: str,
        payload: dict[str, Any],
        actor: ActorType = ActorType.SYSTEM,
    ) -> str:
        trace_id = f"trace-{uuid4().hex}"
        self.append(trace_id, event_type, payload, actor=actor)
        return trace_id

    def append(
        self,
        trace_id: str,
        event_type: str,
        payload: dict[str, Any],
        actor: ActorType = ActorType.SYSTEM,
    ) -> None:
        event = TraceEvent(
            event_id=f"event-{uuid4().hex}",
            trace_id=trace_id,
            event_type=event_type,
            actor=actor,
            payload=copy.deepcopy(payload),
            created_at=datetime.now(CHINA_TZ).isoformat(),
        )
        self._traces[trace_id].append(event)

    def get_trace(self, trace_id: str) -> TraceResponse:
        if trace_id not in self._traces:
            raise TraceNotFoundError(f"追溯记录不存在: {trace_id}")
        events = sorted(self._traces[trace_id], key=lambda event: event.created_at)
        return TraceResponse(
            trace_id=trace_id,
            events=[event.model_copy(deep=True) for event in events],
        )

    def get(self, trace_id: str) -> list[TraceEvent]:
        """Frozen TracePort adapter used by M1/M2 during integration."""
        return self.get_trace(trace_id).events

    def reset(self, scenario_id: str) -> DemoResetResponse:
        if scenario_id not in {"default", "waitlist_recompute"}:
            raise ScenarioNotFoundError(f"演示场景不存在: {scenario_id}")
        self._load_seed()
        trace_id = self.create(
            "SCENARIO_RESET",
            {"scenario_id": scenario_id},
            actor=ActorType.SYSTEM,
        )
        return DemoResetResponse(
            trace_id=trace_id,
            scenario_id=scenario_id,
            course_ids=sorted(self._courses),
            student_ids=sorted(self._students),
        )
