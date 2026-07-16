from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.integration.bootstrap import build_services
from app.modules.enrollment.router import create_router as create_enrollment_router
from app.modules.recommendation.router import create_recommendation_router
from app.modules.recommendation.client import LlmPort
from app.modules.waitlist.router import create_waitlist_router
from app.modules.waitlist.store import (
    CourseNotFoundError,
    ScenarioNotFoundError,
    StoreError,
    StudentNotFoundError,
    TraceNotFoundError,
)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "trace_id": None}},
    )


def create_app(
    data_dir: str | Path | None = None,
    llm: LlmPort | None = None,
) -> FastAPI:
    services = build_services(data_dir, llm=llm)
    app = FastAPI(title="AI Course Selection System", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(422, "VALIDATION_ERROR", str(exc.errors()[0]["msg"]))

    @app.exception_handler(StudentNotFoundError)
    async def student_not_found(_: Request, exc: StudentNotFoundError) -> JSONResponse:
        return _error(404, "STUDENT_NOT_FOUND", str(exc))

    @app.exception_handler(CourseNotFoundError)
    async def course_not_found(_: Request, exc: CourseNotFoundError) -> JSONResponse:
        return _error(404, "COURSE_NOT_FOUND", str(exc))

    @app.exception_handler(TraceNotFoundError)
    async def trace_not_found(_: Request, exc: TraceNotFoundError) -> JSONResponse:
        return _error(404, "STATE_CONFLICT", str(exc))

    @app.exception_handler(ScenarioNotFoundError)
    async def scenario_not_found(_: Request, exc: ScenarioNotFoundError) -> JSONResponse:
        return _error(404, "STATE_CONFLICT", str(exc))

    @app.exception_handler(ValueError)
    async def value_error(_: Request, exc: ValueError) -> JSONResponse:
        return _error(422, "VALIDATION_ERROR", str(exc))

    @app.exception_handler(StoreError)
    async def store_error(_: Request, exc: StoreError) -> JSONResponse:
        return _error(409, "STATE_CONFLICT", str(exc))

    course_ids = [course.course_id for course in services.store.list_courses()]
    app.include_router(create_recommendation_router(services.recommendation))
    app.include_router(create_enrollment_router(services.enrollment, course_ids))
    app.include_router(create_waitlist_router(services.store, services.waitlist))
    app.state.services = services

    @app.get("/api/courses")
    def list_courses():
        return [
            {"course_id": c.course_id, "name": c.name}
            for c in services.store.list_courses()
        ]

    @app.get("/api/students")
    def list_students():
        return services.store.list_students()

    return app


app = create_app()
