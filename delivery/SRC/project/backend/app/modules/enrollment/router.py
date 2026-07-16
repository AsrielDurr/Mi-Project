"""M2 API routes — POST /api/enroll and GET /api/student/status."""

from fastapi import APIRouter, HTTPException, Query

from app.contracts.models import (
    EnrollmentDecision,
    EnrollmentRequest,
    StudentStatusResponse,
)

from .service import EnrollmentService


def create_router(service: EnrollmentService, course_ids: list[str]) -> APIRouter:
    router = APIRouter(tags=["enrollment"])

    @router.post("/api/enroll", response_model=EnrollmentDecision)
    def enroll(body: EnrollmentRequest) -> EnrollmentDecision:
        try:
            return EnrollmentDecision.model_validate(
                service.enroll(
                    body.student_id,
                    body.course_id,
                    body.recommendation_trace_id,
                )
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/student/status", response_model=StudentStatusResponse)
    def student_status(student_id: str = Query(...)) -> StudentStatusResponse:
        try:
            return StudentStatusResponse.model_validate(
                service.get_student_status(student_id, course_ids)
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
