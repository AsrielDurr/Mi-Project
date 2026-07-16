from __future__ import annotations

import os
from pathlib import Path

from app.integration.bootstrap import build_services
from app.contracts.models import RecommendationSource


def main() -> None:
    if not os.getenv("MIMO_API_KEY"):
        raise SystemExit("MIMO_API_KEY is not configured")

    data_dir = Path(__file__).resolve().parents[3] / "ai-course-selection-data"
    services = build_services(data_dir)
    profile = services.store.get_student("S004")
    result = services.recommendation.recommend(profile)

    if result.source != RecommendationSource.MODEL:
        raise SystemExit(f"real MiMo verification failed: {result.fallback_reason}")
    if not result.recommendations:
        raise SystemExit("real MiMo returned no recommendations")

    catalog_ids = {course.course_id for course in services.store.list_courses()}
    invalid = [
        item.course_id
        for item in result.recommendations
        if item.course_id not in catalog_ids
    ]
    if invalid:
        raise SystemExit(f"real MiMo returned out-of-catalog courses: {invalid}")

    print(
        f"REAL_MIMO_OK model={result.model} "
        f"trace_id={result.trace_id} "
        f"courses={','.join(item.course_id for item in result.recommendations)}"
    )


if __name__ == "__main__":
    main()
