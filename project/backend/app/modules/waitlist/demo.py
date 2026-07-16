from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .eligibility import FakeEligibilityPort
from .router import create_waitlist_router
from .service import WaitlistService
from .store import (
    CourseNotFoundError,
    InMemoryStore,
    ScenarioNotFoundError,
    StoreError,
    TraceNotFoundError,
)


def default_data_dir() -> Path:
    configured = os.getenv("COURSE_DATA_DIR")
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[5] / "ai-course-selection-data"


def create_demo_app(data_dir: str | Path | None = None) -> FastAPI:
    store = InMemoryStore.from_data_dir(data_dir or default_data_dir())
    eligibility = FakeEligibilityPort(
        blocked={
            ("S002", "AI201"): "与DB202上课时间冲突",
        }
    )
    service = WaitlistService(state=store, eligibility=eligibility, trace=store)

    app = FastAPI(title="M3 Waitlist and Trace Demo", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(CourseNotFoundError)
    async def course_not_found(_: Request, exc: CourseNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "COURSE_NOT_FOUND",
                    "message": str(exc),
                    "trace_id": None,
                }
            },
        )

    @app.exception_handler(TraceNotFoundError)
    async def trace_not_found(_: Request, exc: TraceNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "STATE_CONFLICT",
                    "message": str(exc),
                    "trace_id": None,
                }
            },
        )

    @app.exception_handler(ScenarioNotFoundError)
    async def scenario_not_found(_: Request, exc: ScenarioNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "STATE_CONFLICT",
                    "message": str(exc),
                    "trace_id": None,
                }
            },
        )

    @app.exception_handler(StoreError)
    async def store_error(_: Request, exc: StoreError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "STATE_CONFLICT",
                    "message": str(exc),
                    "trace_id": None,
                }
            },
        )

    app.include_router(create_waitlist_router(store, service))
    app.state.waitlist_store = store
    app.state.waitlist_service = service
    return app


app = create_demo_app()
