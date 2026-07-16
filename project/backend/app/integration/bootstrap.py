from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.modules.enrollment.rule_engine import RuleEngine
from app.modules.enrollment.service import EnrollmentService
from app.modules.recommendation.client import MiMoClient
from app.modules.recommendation.client import LlmPort
from app.modules.recommendation.service import RecommendationService
from app.modules.waitlist.demo import default_data_dir
from app.modules.waitlist.service import WaitlistService
from app.modules.waitlist.store import InMemoryStore


@dataclass(frozen=True)
class ApplicationServices:
    store: InMemoryStore
    rule_engine: RuleEngine
    recommendation: RecommendationService
    enrollment: EnrollmentService
    waitlist: WaitlistService


def build_services(
    data_dir: str | Path | None = None,
    llm: LlmPort | None = None,
) -> ApplicationServices:
    store = InMemoryStore.from_data_dir(data_dir or default_data_dir())
    rule_engine = RuleEngine(state=store)
    configured_llm = llm
    if configured_llm is None and os.getenv("MIMO_API_KEY"):
        configured_llm = MiMoClient.from_env()
    return ApplicationServices(
        store=store,
        rule_engine=rule_engine,
        recommendation=RecommendationService(
            catalog=store,
            trace=store,
            llm=configured_llm,
        ),
        enrollment=EnrollmentService(
            eligibility=rule_engine,
            state=store,
            trace=store,
        ),
        waitlist=WaitlistService(
            eligibility=rule_engine,
            state=store,
            trace=store,
        ),
    )
