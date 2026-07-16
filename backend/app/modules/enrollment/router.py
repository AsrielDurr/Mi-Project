"""M2 API routes — POST /api/enroll and GET /api/student/status."""

from fastapi import APIRouter, HTTPException, Query

from .service import EnrollmentService


def create_router(service: EnrollmentService, course_ids: list[str]) -> APIRouter:
    router = APIRouter(tags=["enrollment"])

    @router.post("/api/enroll")
    async def enroll(body: dict):
        student_id = body.get("student_id")
        course_id = body.get("course_id")
        recommendation_trace_id = body.get("recommendation_trace_id")

        if not student_id or not course_id:
            raise HTTPException(status_code=422, detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "student_id and course_id are required",
                    "trace_id": None,
                }
            })

        try:
            decision = service.enroll(student_id, course_id, recommendation_trace_id)
        except KeyError as e:
            msg = str(e)
            if "Student" in msg:
                raise HTTPException(status_code=404, detail={
                    "error": {
                        "code": "STUDENT_NOT_FOUND",
                        "message": msg,
                        "trace_id": None,
                    }
                })
            elif "Course" in msg:
                raise HTTPException(status_code=404, detail={
                    "error": {
                        "code": "COURSE_NOT_FOUND",
                        "message": msg,
                        "trace_id": None,
                    }
                })
            raise HTTPException(status_code=500, detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": msg,
                    "trace_id": None,
                }
            })

        return decision

    @router.get("/api/student/status")
    async def student_status(student_id: str = Query(...)):
        try:
            status = service.get_student_status(student_id, course_ids)
        except KeyError as e:
            raise HTTPException(status_code=404, detail={
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": str(e),
                    "trace_id": None,
                }
            })

        return status

    return router
