from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.waitlist.eligibility import FakeEligibilityPort
from app.modules.waitlist.service import WaitlistService
from app.modules.waitlist.store import InMemoryStore


DATA_DIR = Path(__file__).resolve().parents[4] / "ai-course-selection-data"


@pytest.fixture()
def store() -> InMemoryStore:
    return InMemoryStore.from_data_dir(DATA_DIR)


@pytest.fixture()
def service(store: InMemoryStore) -> WaitlistService:
    eligibility = FakeEligibilityPort(
        blocked={
            ("S002", "AI201"): "与DB202上课时间冲突",
        }
    )
    return WaitlistService(state=store, eligibility=eligibility, trace=store)


def test_release_seat_increases_capacity_by_one(
    service: WaitlistService,
    store: InMemoryStore,
) -> None:
    result = service.release_seat("AI201")

    assert result.capacity_before == 30
    assert result.capacity_after == 31
    assert result.enrolled_count == 30
    assert result.available_seats == 1
    assert store.get_course_status("AI201").available_seats == 1


def test_recompute_skips_first_candidate_and_promotes_second(
    service: WaitlistService,
    store: InMemoryStore,
) -> None:
    service.release_seat("AI201")

    result = service.recompute("AI201")

    assert result.available_seats_before == 1
    assert [item.student_id for item in result.checked] == ["S002", "S005"]
    assert [item.waitlist_status for item in result.checked] == [
        "SKIPPED",
        "PROMOTED",
    ]
    assert result.promoted_student_ids == ["S005"]

    status = store.get_course_status("AI201")
    assert status.course.enrolled_count == 31
    assert "S005" in status.enrolled_student_ids
    assert status.available_seats == 0


def test_recompute_without_a_seat_does_not_mutate_waitlist(
    service: WaitlistService,
    store: InMemoryStore,
) -> None:
    before = store.get_course_status("AI201")

    result = service.recompute("AI201")

    after = store.get_course_status("AI201")
    assert result.available_seats_before == 0
    assert result.checked == []
    assert result.promoted_student_ids == []
    assert after == before


def test_recompute_trace_contains_release_checks_skip_and_promotion(
    service: WaitlistService,
    store: InMemoryStore,
) -> None:
    service.release_seat("AI201")
    result = service.recompute("AI201")

    trace = store.get_trace(result.trace_id)
    assert [event.event_type for event in trace.events] == [
        "SEAT_RELEASED",
        "WAITLIST_RECOMPUTED",
        "WAITLIST_ELIGIBILITY_CHECKED",
        "WAITLIST_SKIPPED",
        "WAITLIST_ELIGIBILITY_CHECKED",
        "WAITLIST_PROMOTED",
    ]
    assert trace.events[2].payload["student_id"] == "S002"
    assert trace.events[4].payload["student_id"] == "S005"
