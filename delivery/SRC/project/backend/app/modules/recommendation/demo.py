from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.waitlist.demo import default_data_dir
from app.modules.waitlist.store import InMemoryStore

from .client import MiMoClient
from .router import create_recommendation_router
from .service import RecommendationService


def create_demo_app() -> FastAPI:
    store = InMemoryStore.from_data_dir(default_data_dir())
    llm = MiMoClient.from_env() if os.getenv("MIMO_API_KEY") else None
    service = RecommendationService(catalog=store, trace=store, llm=llm)
    app = FastAPI(title="M1 Recommendation Demo", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(create_recommendation_router(service))
    return app


app = create_demo_app()
