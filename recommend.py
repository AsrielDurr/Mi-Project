"""M1推荐模块 - 推荐引擎（严格遵循契约1.0.0）"""

import uuid
import json
import os
from datetime import datetime, timezone

from models import (
    StudentProfile, Recommendation, RecommendationResponse,
    load_course_to_contract, weekday_int_to_str
)


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai-course-selection-data")
PROMPT_VERSION = "v1"


def load_raw_courses() -> list[dict]:
    """加载原始课程数据"""
    path = os.path.join(DATA_DIR, "courses.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_contract_courses() -> list[dict]:
    """加载并转换为契约格式的课程数据"""
    raw_courses = load_raw_courses()
    return [load_course_to_contract(c) for c in raw_courses]


def load_recommendation_examples() -> dict[str, dict]:
    """加载推荐示例"""
    path = os.path.join(DATA_DIR, "recommendation_examples.json")
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    return {ex["goal"]: {"courses": ex["recommend"], "reason": ex["reason"]} for ex in examples}


def generate_trace_id(prefix: str = "trace-rec") -> str:
    """生成唯一trace_id"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def time_to_minutes(time_str: str) -> int:
    """将 HH:mm 转为分钟数"""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def check_prerequisites(student: StudentProfile, course: dict) -> tuple[bool, str]:
    """检查先修课程是否满足"""
    prereqs = course.get("prerequisite_ids", [])
    if not prereqs:
        return True, "无先修要求"
    
    completed = set(student.completed_course_ids)
    enrolled = set(student.enrolled_course_ids)
    satisfied = completed | enrolled
    
    missing = [p for p in prereqs if p not in satisfied]
    if missing:
        return False, f"缺少先修课程: {', '.join(missing)}"
    return True, "已满足先修要求"


def check_time_conflict(student: StudentProfile, course: dict, courses: list[dict]) -> tuple[bool, str]:
    """检查时间冲突"""
    enrolled_ids = set(student.enrolled_course_ids)
    enrolled_courses = [c for c in courses if c["course_id"] in enrolled_ids]
    
    schedule = course.get("schedule", {})
    course_day = schedule.get("day", "MON")
    course_start = time_to_minutes(schedule.get("start", "00:00"))
    course_end = time_to_minutes(schedule.get("end", "23:59"))
    
    for ec in enrolled_courses:
        ec_schedule = ec.get("schedule", {})
        ec_day = ec_schedule.get("day", "MON")
        if ec_day == course_day:
            ec_start = time_to_minutes(ec_schedule.get("start", "00:00"))
            ec_end = time_to_minutes(ec_schedule.get("end", "23:59"))
            if course_start < ec_end and course_end > ec_start:
                return False, f"与{ec['name']}上课时间冲突"
    
    return True, "无时间冲突"


def compute_score(student: StudentProfile, course: dict, time_preference: str = "上午") -> tuple[int, str]:
    """计算推荐分数 (0-100)"""
    score = 50
    reasons = []
    
    goal = student.goal.lower()
    course_name = course["name"].lower()
    
    # 课程ID到类别的映射（基于数据）
    category_map = {
        "AI201": "ai", "ML301": "ai", "CV401": "ai",
        "WEB201": "web", "DB202": "database",
        "CS101": "programming", "ALG201": "programming",
        "NET301": "network"
    }
    category = category_map.get(course["course_id"], "")
    
    # 目标匹配 (+30)
    if goal in ["人工智能", "ai"]:
        if category == "ai" or "ai" in course_name or "机器学习" in course_name or "人工智能" in course_name:
            score += 30
            reasons.append("高度匹配AI学习目标")
    elif goal in ["软件开发", "software"]:
        if "web" in course_name or "程序" in course_name or "开发" in course_name:
            score += 30
            reasons.append("高度匹配软件开发目标")
    
    # 先修课程满足 (+10)
    prereqs_ok, _ = check_prerequisites(student, course)
    if prereqs_ok:
        score += 10
    
    # 时间偏好匹配 (+10)
    schedule = course.get("schedule", {})
    start_hour = int(schedule.get("start", "08:00").split(":")[0])
    if time_preference in ["上午", "morning"] and start_hour < 12:
        score += 10
        reasons.append("符合上午偏好")
    elif time_preference in ["下午", "afternoon"] and start_hour >= 12:
        score += 10
        reasons.append("符合下午偏好")
    
    # 名额可用性 (+5~10)
    available = course["capacity"] - course["enrolled_count"]
    if available > 5:
        score += 10
        reasons.append("名额充足")
    elif available > 0:
        score += 5
        reasons.append("名额有限")
    
    reason_str = "；".join(reasons) if reasons else "综合评估"
    return min(score, 100), reason_str


def fallback_recommend(student: StudentProfile, courses: list[dict], time_preference: str = "上午") -> list[Recommendation]:
    """降级推荐：基于规则的本地推荐"""
    examples = load_recommendation_examples()
    example = examples.get(student.goal, {})
    recommended_ids = set(example.get("courses", []))
    example_reason = example.get("reason", "")
    
    recommendations = []
    for course in courses:
        # 跳过已满课程
        if course["enrolled_count"] >= course["capacity"]:
            continue
        # 跳过已选/已修课程
        if course["course_id"] in student.enrolled_course_ids or course["course_id"] in student.completed_course_ids:
            continue
        # 先修课程检查
        prereqs_ok, _ = check_prerequisites(student, course)
        if not prereqs_ok:
            continue
        # 时间冲突检查
        time_ok, _ = check_time_conflict(student, course, courses)
        if not time_ok:
            continue
        
        # 计算分数
        is_recommended = course["course_id"] in recommended_ids
        score, reason = compute_score(student, course, time_preference)
        
        # 目标路线课程加分
        if is_recommended:
            score = min(score + 15, 100)
            if not reason.startswith("高度"):
                reason = example_reason + "；" + reason
        
        uncertainty = "当前结果未经过MiMo生成，推荐质量可能下降"
        if score >= 40:
            recommendations.append(Recommendation(
                course_id=course["course_id"],
                score=score,
                reason=reason,
                uncertainty=uncertainty
            ))
    
    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations[:5]


def recommend(student: StudentProfile, time_preference: str = "上午") -> RecommendationResponse:
    """主推荐流程"""
    trace_id = generate_trace_id()
    courses = load_contract_courses()
    
    # 当前使用降级方案
    model_result = None
    
    if model_result is not None:
        return RecommendationResponse(
            trace_id=trace_id,
            source="MODEL",
            model="mimo-auto",
            prompt_version=PROMPT_VERSION,
            fallback_reason=None,
            recommendations=model_result
        )
    else:
        fallback_results = fallback_recommend(student, courses, time_preference)
        if not fallback_results:
            fallback_results = [Recommendation(
                course_id="N/A",
                score=0,
                reason="暂无合适的课程推荐",
                uncertainty="所有可选课程均不满足条件"
            )]
        
        return RecommendationResponse(
            trace_id=trace_id,
            source="FALLBACK",
            model=None,
            prompt_version=PROMPT_VERSION,
            fallback_reason="MiMo模型暂不可用，使用本地规则推荐",
            recommendations=fallback_results
        )
