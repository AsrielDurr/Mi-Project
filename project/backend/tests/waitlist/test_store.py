from __future__ import annotations

from pathlib import Path

import pytest

from app.contracts.ports import CatalogPort, StatePort, TracePort
from app.modules.waitlist.store import CourseNotFoundError, InMemoryStore


DATA_DIR = Path(__file__).resolve().parents[4] / "ai-course-selection-data"


@pytest.fixture()
def store() -> InMemoryStore:
    return InMemoryStore.from_data_dir(DATA_DIR)


def test_loads_existing_course_and_waitlist_data(store: InMemoryStore) -> None:
    status = store.get_course_status("AI201")

    assert status.course.course_id == "AI201"
    assert status.course.capacity == 30
    assert status.course.enrolled_count == 30
    assert status.available_seats == 0
    assert [entry.student_id for entry in status.waitlist] == ["S002", "S005"]
    assert [entry.position for entry in status.waitlist] == [1, 2]


def test_store_implements_frozen_shared_ports(store: InMemoryStore) -> None:
    assert isinstance(store, CatalogPort)
    assert isinstance(store, StatePort)
    assert isinstance(store, TracePort)


def test_reset_restores_seed_state_without_changing_source_files(
    store: InMemoryStore,
) -> None:
    courses_file = DATA_DIR / "courses.json"
    before = courses_file.read_bytes()

    store.release_seat("AI201")
    assert store.get_course_status("AI201").course.capacity == 31

    summary = store.reset("waitlist_recompute")

    assert summary.scenario_id == "waitlist_recompute"
    assert store.get_course_status("AI201").course.capacity == 30
    assert courses_file.read_bytes() == before


def test_unknown_course_is_reported(store: InMemoryStore) -> None:
    with pytest.raises(CourseNotFoundError):
        store.get_course_status("UNKNOWN")
