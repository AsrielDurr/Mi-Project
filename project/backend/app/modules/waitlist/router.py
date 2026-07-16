from __future__ import annotations

from fastapi import APIRouter

from app.contracts.models import (
    CourseCommandRequest,
    CourseStatusResponse,
    DemoResetRequest,
    DemoResetResponse,
    RecomputeResult,
    ReleaseSeatResponse,
    TraceResponse,
)


def create_waitlist_router(store, service) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/api/admin/course-status",
        response_model=CourseStatusResponse,
        tags=["waitlist"],
    )
    def get_course_status(course_id: str) -> CourseStatusResponse:
        return store.get_course_status(course_id)

    @router.post(
        "/api/admin/release-seat",
        response_model=ReleaseSeatResponse,
        tags=["waitlist"],
    )
    def release_seat(command: CourseCommandRequest) -> ReleaseSeatResponse:
        return service.release_seat(command.course_id)

    @router.post(
        "/api/admin/recompute-waitlist",
        response_model=RecomputeResult,
        tags=["waitlist"],
    )
    def recompute_waitlist(command: CourseCommandRequest) -> RecomputeResult:
        return service.recompute(command.course_id)

    @router.get(
        "/api/trace/{trace_id}",
        response_model=TraceResponse,
        tags=["trace"],
    )
    def get_trace(trace_id: str) -> TraceResponse:
        return store.get_trace(trace_id)

    @router.post(
        "/api/demo/reset",
        response_model=DemoResetResponse,
        tags=["demo"],
    )
    def reset_demo(command: DemoResetRequest) -> DemoResetResponse:
        return store.reset(command.scenario_id)

    return router

