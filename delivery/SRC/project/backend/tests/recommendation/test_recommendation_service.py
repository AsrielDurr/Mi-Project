from __future__ import annotations

from pathlib import Path

import pytest

from app.contracts.models import RecommendationSource, StudentProfile
from app.modules.recommendation.service import RecommendationService
from app.modules.waitlist.store import InMemoryStore


DATA_DIR = Path(__file__).resolve().parents[4] / "ai-course-selection-data"


class StubLlm:
    model = "mimo-test"

    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = responses
        self.calls = 0

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def student(goal: str = "人工智能") -> StudentProfile:
    return StudentProfile(student_id="S001", goal=goal)


def test_valid_mimo_response_is_returned_and_traced() -> None:
    store = InMemoryStore.from_data_dir(DATA_DIR)
    llm = StubLlm([
        '{"recommendations":[{"course_id":"AI201","score":92,'
        '"reason":"匹配AI目标","uncertainty":"需确认数学基础"}]}'
    ])
    service = RecommendationService(store, store, llm)

    result = service.recommend(student())

    assert result.source == RecommendationSource.MODEL
    assert result.model == "mimo-test"
    assert result.recommendations[0].course_id == "AI201"
    assert llm.calls == 1
    assert store.get(result.trace_id)[-1].event_type == "MODEL_RECOMMENDED"


def test_invalid_course_retries_once_then_uses_visible_fallback() -> None:
    store = InMemoryStore.from_data_dir(DATA_DIR)
    invalid = '{"recommendations":[{"course_id":"MADE-UP","score":99,' \
        '"reason":"x","uncertainty":"x"}]}'
    llm = StubLlm([invalid, invalid])
    service = RecommendationService(store, store, llm)

    result = service.recommend(student())

    assert llm.calls == 2
    assert result.source == RecommendationSource.FALLBACK
    assert "目录外课程" in (result.fallback_reason or "")
    assert all(item.course_id != "MADE-UP" for item in result.recommendations)


def test_timeout_retries_once_then_falls_back() -> None:
    store = InMemoryStore.from_data_dir(DATA_DIR)
    llm = StubLlm([TimeoutError("slow"), TimeoutError("slow")])
    result = RecommendationService(store, store, llm).recommend(student())
    assert llm.calls == 2
    assert result.source == RecommendationSource.FALLBACK
    assert "TimeoutError" in (result.fallback_reason or "")


def test_empty_goal_is_rejected_without_calling_model() -> None:
    store = InMemoryStore.from_data_dir(DATA_DIR)
    llm = StubLlm([])
    with pytest.raises(ValueError, match="学习目标不能为空"):
        RecommendationService(store, store, llm).recommend(student("   "))
    assert llm.calls == 0
