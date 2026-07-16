from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.contracts.models import (
    ActorType,
    Course,
    Recommendation,
    RecommendationResponse,
    RecommendationSource,
    StudentProfile,
)
from app.contracts.ports import CatalogPort, TracePort

from .client import LlmPort, compact_json


PROMPT_VERSION = "v1"
RECOMMENDATION_LIST = TypeAdapter(list[Recommendation])


class RecommendationService:
    def __init__(
        self,
        catalog: CatalogPort,
        trace: TracePort,
        llm: LlmPort | None,
    ) -> None:
        self._catalog = catalog
        self._trace = trace
        self._llm = llm

    def recommend(self, student: StudentProfile) -> RecommendationResponse:
        if not student.goal.strip():
            raise ValueError("学习目标不能为空")

        courses = self._catalog.list_courses()
        course_ids = {course.course_id for course in courses}
        trace_id = self._trace.create(
            "RECOMMENDATION_REQUESTED",
            {
                "student_id": student.student_id,
                "goal": student.goal,
                "prompt_version": PROMPT_VERSION,
            },
            actor=ActorType.STUDENT,
        )

        failure_reason: str | None = None
        if self._llm is not None:
            for attempt in (1, 2):
                try:
                    recommendations = self._enrich_names(
                        self._call_model(student, courses, course_ids), courses
                    )
                    self._trace.append(
                        trace_id,
                        "MODEL_RECOMMENDED",
                        {
                            "model": self._llm.model,
                            "source": RecommendationSource.MODEL,
                            "prompt_version": PROMPT_VERSION,
                            "course_ids": [item.course_id for item in recommendations],
                            "attempt": attempt,
                        },
                        actor=ActorType.MODEL,
                    )
                    return RecommendationResponse(
                        trace_id=trace_id,
                        source=RecommendationSource.MODEL,
                        model=self._llm.model,
                        prompt_version=PROMPT_VERSION,
                        fallback_reason=None,
                        recommendations=recommendations,
                    )
                except Exception as exc:
                    failure_reason = f"{type(exc).__name__}: {exc}"
                    self._trace.append(
                        trace_id,
                        "MODEL_ATTEMPT_FAILED",
                        {"attempt": attempt, "reason": failure_reason},
                        actor=ActorType.MODEL,
                    )
        else:
            failure_reason = "MiMo未配置"

        recommendations = self._fallback(student, courses)
        self._trace.append(
            trace_id,
            "FALLBACK_RECOMMENDED",
            {
                "source": RecommendationSource.FALLBACK,
                "reason": failure_reason,
                "course_ids": [item.course_id for item in recommendations],
            },
            actor=ActorType.SYSTEM,
        )
        return RecommendationResponse(
            trace_id=trace_id,
            source=RecommendationSource.FALLBACK,
            model=None,
            prompt_version=PROMPT_VERSION,
            fallback_reason=failure_reason,
            recommendations=recommendations,
        )

    def _call_model(
        self,
        student: StudentProfile,
        courses: list[Course],
        course_ids: set[str],
    ) -> list[Recommendation]:
        assert self._llm is not None
        system_prompt = (
            "你是课程推荐助手。只推荐给定目录中的课程，不判断选课资格、容量或候补顺序。"
            "只返回JSON对象，格式为{\"recommendations\":[{\"course_id\":string,"
            "\"score\":0到100整数,\"reason\":string,\"uncertainty\":string}]}。"
        )
        user_prompt = compact_json(
            {
                "student": student.model_dump(mode="json"),
                "catalog": [course.model_dump(mode="json") for course in courses],
            }
        )
        raw = self._llm.complete(system_prompt, user_prompt)
        parsed: Any = json.loads(raw)
        items = parsed.get("recommendations") if isinstance(parsed, dict) else None
        try:
            recommendations = RECOMMENDATION_LIST.validate_python(items)
        except ValidationError as exc:
            raise ValueError("MiMo返回结构无效") from exc
        if not recommendations:
            raise ValueError("MiMo没有返回推荐课程")
        invalid = [item.course_id for item in recommendations if item.course_id not in course_ids]
        if invalid:
            raise ValueError(f"MiMo返回目录外课程: {', '.join(invalid)}")
        return recommendations

    @staticmethod
    def _enrich_names(
        recommendations: list[Recommendation], courses: list[Course]
    ) -> list[Recommendation]:
        name_map = {c.course_id: c.name for c in courses}
        for r in recommendations:
            r.course_name = name_map.get(r.course_id, r.course_id)
        return recommendations

    @staticmethod
    def _fallback(student: StudentProfile, courses: list[Course]) -> list[Recommendation]:
        keywords = {
            "人工智能": ["人工智能", "机器学习", "计算机视觉"],
            "ai": ["人工智能", "机器学习", "计算机视觉"],
            "软件开发": ["程序", "Web", "数据库"],
        }
        preferred = keywords.get(student.goal.strip().lower(), [student.goal.strip()])

        def score(course: Course) -> tuple[int, str]:
            matched = any(word.lower() in course.name.lower() for word in preferred)
            return (80 if matched else 50, "匹配学习目标" if matched else "课程目录基础推荐")

        already_taken = set(student.completed_course_ids) | set(student.enrolled_course_ids)
        candidates = [course for course in courses if course.course_id not in already_taken]
        ranked = sorted(candidates, key=lambda course: score(course)[0], reverse=True)[:3]
        return [
            Recommendation(
                course_id=course.course_id,
                course_name=course.name,
                score=score(course)[0],
                reason=score(course)[1],
                uncertainty="降级推荐未经过MiMo生成，最终资格由规则模块判断",
            )
            for course in ranked
        ]
