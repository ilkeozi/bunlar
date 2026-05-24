from __future__ import annotations

from dataclasses import dataclass

from material_ingestion.services.web_crawl_decision_service import record_decision
from material_ingestion.services.web_crawl_frontier_service import (
    enqueue_frontier_item,
    ensure_crawl_run,
    transition_frontier_item,
)
from material_ingestion.services.web_crawl_identity_service import ensure_uri_identity
from material_ingestion.services.web_crawler_reason_codes import REASON_DISCOVERED


@dataclass(slots=True)
class CrawlOrchestrationContext:
    crawl_run_id: int
    run_key: str


def ensure_orchestration(run_key: str, *, force_refresh: bool = False) -> CrawlOrchestrationContext:
    crawl_run_id = ensure_crawl_run(run_key=run_key, force_refresh=force_refresh)
    return CrawlOrchestrationContext(crawl_run_id=crawl_run_id, run_key=run_key)


def register_discovered_uri(*, run_key: str, observed_uri: str, reason_code: str = REASON_DISCOVERED) -> int:
    ctx = ensure_orchestration(run_key)
    identity = ensure_uri_identity(observed_uri)
    frontier_id = enqueue_frontier_item(identity.uri_identity_id, ctx.crawl_run_id, reason_code=reason_code)
    record_decision(
        crawl_run_id=ctx.crawl_run_id,
        uri_identity_id=identity.uri_identity_id,
        decision_type="queue",
        reason_code=reason_code,
        detail={"frontier_item_id": frontier_id, "observed_uri": observed_uri},
    )
    return frontier_id


def mark_frontier_in_progress(frontier_item_id: int) -> None:
    transition_frontier_item(frontier_item_id, "in_progress", reason_code="worker_processing")


def mark_frontier_completed(frontier_item_id: int) -> None:
    transition_frontier_item(frontier_item_id, "completed", reason_code="completed")
