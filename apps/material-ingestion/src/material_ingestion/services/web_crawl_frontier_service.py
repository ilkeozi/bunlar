from __future__ import annotations

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlRun, RawWebFrontierItem
from material_ingestion.services.web_crawler_reason_codes import FRONTIER_STATES


def ensure_crawl_run(run_key: str, *, initiator: str = "system", force_refresh: bool = False) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        run = session.query(RawWebCrawlRun).filter(RawWebCrawlRun.run_key == run_key).first()
        if run is None:
            run = RawWebCrawlRun(run_key=run_key, initiator=initiator, force_refresh=force_refresh)
            session.add(run)
            session.commit()
            session.refresh(run)
        return int(run.id)


def enqueue_frontier_item(uri_identity_id: int, crawl_run_id: int, *, reason_code: str = "discovered", priority: int = 0) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        active = (
            session.query(RawWebFrontierItem)
            .filter(
                RawWebFrontierItem.uri_identity_id == uri_identity_id,
                RawWebFrontierItem.crawl_run_id == crawl_run_id,
                RawWebFrontierItem.state.in_(["queued", "in_progress"]),
            )
            .first()
        )
        if active is not None:
            return int(active.id)
        item = RawWebFrontierItem(
            uri_identity_id=uri_identity_id,
            crawl_run_id=crawl_run_id,
            state="queued",
            state_reason_code=reason_code,
            priority=priority,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return int(item.id)


def transition_frontier_item(item_id: int, new_state: str, *, reason_code: str = "") -> None:
    if new_state not in FRONTIER_STATES:
        raise ValueError(f"unsupported frontier state: {new_state}")
    session_factory = create_session_factory()
    with session_factory() as session:
        item = session.query(RawWebFrontierItem).filter(RawWebFrontierItem.id == item_id).first()
        if item is None:
            return
        item.state = new_state
        item.state_reason_code = reason_code
        session.commit()
