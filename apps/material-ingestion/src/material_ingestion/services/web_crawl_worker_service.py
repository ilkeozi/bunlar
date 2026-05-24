from __future__ import annotations

from material_ingestion.services.web_crawl_scheduler_service import HostThrottleScheduler


def process_candidate_urls(urls: list[str], *, per_host_limit: int = 2) -> tuple[list[str], list[str]]:
    scheduler = HostThrottleScheduler(per_host_limit=per_host_limit)
    accepted: list[str] = []
    deferred: list[str] = []
    for url in urls:
        decision = scheduler.try_acquire(url)
        if decision.allowed:
            accepted.append(url)
        else:
            deferred.append(url)
    # Release all accepted at end of batch unit for stateless queue chunk processing.
    for url in accepted:
        scheduler.release(url)
    return accepted, deferred
