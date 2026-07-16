"""M1推荐模块 - 数据模型（严格遵循契约1.0.0）"""

from dataclasses import dataclass, field
from typing import Optional


# ========== 枚举值（来自enums.json） ==========
WEEKDAY_MAP = {1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT", 7: "SUN"}
RECOMMENDATION_SOURCE = ("MODEL", "FALLBACK")
ERROR_CODES = ("VALIDATION_ERROR", "STUDENT_NOT_FOUND", "COURSE_NOT_FOUND",
               "MODEL_ERROR", "STATE_CONFLICT", "INTERNAL_ERROR")


@dataclass
class Schedule:
    """课程时间表 - 遵循domain.schema.json"""
    day: str  # "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN"
    start: str  # "HH:mm"
    end: str    # "HH:mm"


@dataclass
class StudentProfile:
    """学生画像 - 遵循domain.schema.json"""
    student_id: str
    goal: str
    skills: list = field(default_factory=list)
    available_times: list = field(default_factory=list)
    completed_course_ids: list = field(default_factory=list)
    enrolled_course_ids: list = field(default_factory=list)


@dataclass
class Course:
    """课程 - 遵循domain.schema.json"""
    course_id: str
    name: str
    description: str = ""
    schedule: Optional[Schedule] = None
    capacity: int = 0
    enrolled_count: int = 0
    prerequisite_ids: list = field(default_factory=list)
    status: str = "OPEN"


@dataclass
class Recommendation:
    """推荐项 - 遵循domain.schema.json"""
    course_id: str
    score: int
    reason: str
    uncertainty: str = ""


@dataclass
class RecommendationResponse:
    """推荐响应 - 遵循domain.schema.json"""
    trace_id: str
    source: str  # "MODEL" | "FALLBACK"
    model: Optional[str] = None
    prompt_version: str = "v1"
    fallback_reason: Optional[str] = None
    recommendations: list = field(default_factory=list)


@dataclass
class RecommendRequest:
    """推荐请求"""
    student: StudentProfile


@dataclass
class CourseSelectedEvent:
    """前端事件 - 遵循frontend-events.ts (camelCase)"""
    studentId: str
    courseId: str
    recommendationTraceId: str


def weekday_int_to_str(weekday: int) -> str:
    """将数字星期转为枚举字符串"""
    return WEEKDAY_MAP.get(weekday, "MON")


def load_course_to_contract(raw: dict) -> dict:
    """将数据文件格式转为契约格式"""
    return {
        "course_id": raw["id"],
        "name": raw["name"],
        "description": f"{raw.get('teacher', '')}授课",
        "schedule": {
            "day": weekday_int_to_str(raw["weekday"]),
            "start": raw["start"],
            "end": raw["end"]
        },
        "capacity": raw["capacity"],
        "enrolled_count": raw["enrolled"],
        "prerequisite_ids": raw.get("prerequisites", []),
        "status": "OPEN"
    }


def to_dict(obj) -> dict:
    """将dataclass转为dict（契约格式）"""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for f in obj.__dataclass_fields__:
            val = getattr(obj, f)
            if hasattr(val, "__dataclass_fields__"):
                result[f] = to_dict(val)
            elif isinstance(val, list):
                result[f] = [to_dict(i) if hasattr(i, "__dataclass_fields__") else i for i in val]
            else:
                result[f] = val
        return result
    elif isinstance(obj, list):
        return [to_dict(i) if hasattr(i, "__dataclass_fields__") else i for i in obj]
    return obj
