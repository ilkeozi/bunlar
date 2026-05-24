from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from material_ingestion.services.web_crawl_decision_service import record_decision
from material_ingestion.services.web_crawl_frontier_service import (
    enqueue_frontier_item,
    ensure_crawl_run,
    transition_frontier_item,
)
from material_ingestion.services.web_crawl_host_scope_service import is_url_host_allowlisted, register_discovered_host
from material_ingestion.services.web_crawl_identity_service import ensure_uri_identity
from material_ingestion.services.web_crawl_robots_service import evaluate_and_persist_robots
from material_ingestion.services.web_crawler_reason_codes import REASON_DISCOVERED


@dataclass(slots=True)
class CrawlOrchestrationContext:
    crawl_run_id: int
    run_key: str


def ensure_orchestration(run_key: str, *, force_refresh: bool = False) -> CrawlOrchestrationContext:
    crawl_run_id = ensure_crawl_run(run_key=run_key, force_refresh=force_refresh)
    return CrawlOrchestrationContext(crawl_run_id=crawl_run_id, run_key=run_key)


def register_discovered_uri(
    *,
    run_key: str,
    observed_uri: str,
    reason_code: str = REASON_DISCOVERED,
    robots_txt: str | None = None,
    robots_fetch_status: str = "success",
    user_agent: str = "*",
) -> int:
    ctx = ensure_orchestration(run_key)
    identity = ensure_uri_identity(observed_uri)
    hostname = urlsplit(identity.canonical_uri).netloc
    host_id = register_discovered_host(hostname, discovery_source=f"link:{run_key}")

    if not is_url_host_allowlisted(observed_uri):
        record_decision(
            crawl_run_id=ctx.crawl_run_id,
            uri_identity_id=identity.uri_identity_id,
            decision_type="reject",
            reason_code="host_not_allowlisted",
            detail={"observed_uri": observed_uri},
        )
        return 0

    if robots_txt:
        allowed = evaluate_and_persist_robots(
            host_id=host_id,
            robots_txt=robots_txt,
            target_url=identity.canonical_uri,
            user_agent=user_agent,
            fetch_status=robots_fetch_status,
        )
        if not allowed:
            record_decision(
                crawl_run_id=ctx.crawl_run_id,
                uri_identity_id=identity.uri_identity_id,
                decision_type="skip",
                reason_code="robots_disallowed",
                detail={"observed_uri": observed_uri},
            )
            return 0
    elif robots_fetch_status == "failed":
        record_decision(
            crawl_run_id=ctx.crawl_run_id,
            uri_identity_id=identity.uri_identity_id,
            decision_type="defer",
            reason_code="robots_fetch_failed",
            detail={"observed_uri": observed_uri},
        )
        return 0

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
