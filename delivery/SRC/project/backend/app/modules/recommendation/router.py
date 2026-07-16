from __future__ import annotations

from fastapi import APIRouter

from app.contracts.models import RecommendRequest, RecommendationResponse

from .service import RecommendationService


def create_recommendation_router(service: RecommendationService) -> APIRouter:
    router = APIRouter(tags=["recommendation"])

    @router.post("/api/recommend", response_model=RecommendationResponse)
    def recommend(request: RecommendRequest) -> RecommendationResponse:
        return service.recommend(request.student)

    return router
