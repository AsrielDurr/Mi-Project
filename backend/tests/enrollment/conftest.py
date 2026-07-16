import pytest
from app.contracts.ports import (
    Schedule, Course, StudentProfile, WaitlistEntry,
)

from .fakes import FakeStatePort, FakeTracePort


@pytest.fixture
def mon_schedule():
    return Schedule(day="MON", start="08:00", end="10:00")


@pytest.fixture
def tue_schedule():
    return Schedule(day="TUE", start="10:00", end="12:00")


@pytest.fixture
def wed_schedule():
    return Schedule(day="WED", start="14:00", end="16:00")


@pytest.fixture
def thu_schedule():
    return Schedule(day="THU", start="14:00", end="16:00")


@pytest.fixture
def course_cs101(mon_schedule):
    return Course(
        course_id="CS101", name="Python程序设计", description="Python基础",
        schedule=mon_schedule, capacity=40, enrolled_count=38,
        prerequisite_ids=[], status="OPEN",
    )


@pytest.fixture
def course_ai201(tue_schedule):
    return Course(
        course_id="AI201", name="人工智能基础", description="AI入门",
        schedule=tue_schedule, capacity=30, enrolled_count=30,
        prerequisite_ids=["CS101"], status="OPEN",
    )


@pytest.fixture
def course_db202(tue_schedule):
    return Course(
        course_id="DB202", name="数据库系统", description="数据库",
        schedule=tue_schedule, capacity=35, enrolled_count=34,
        prerequisite_ids=[], status="OPEN",
    )


@pytest.fixture
def course_ml301(thu_schedule):
    return Course(
        course_id="ML301", name="机器学习", description="ML",
        schedule=thu_schedule, capacity=25, enrolled_count=22,
        prerequisite_ids=["AI201"], status="OPEN",
    )


@pytest.fixture
def course_web201(wed_schedule):
    return Course(
        course_id="WEB201", name="Web开发", description="Web",
        schedule=wed_schedule, capacity=40, enrolled_count=26,
        prerequisite_ids=["CS101"], status="OPEN",
    )


@pytest.fixture
def student_s001():
    return StudentProfile(
        student_id="S001", goal="Learn AI", skills=["Python"],
        available_times=["MON_EVENING"],
        completed_course_ids=["CS101"],
        enrolled_course_ids=[],
    )


@pytest.fixture
def student_s002():
    return StudentProfile(
        student_id="S002", goal="Learn Web", skills=["JavaScript"],
        available_times=["TUE_EVENING"],
        completed_course_ids=["CS101"],
        enrolled_course_ids=["AI201"],
    )
