from __future__ import annotations

import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from datetime import timedelta

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebCrawlDecision,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebCandidateEvent,
    RawWebDiscoveryEvent,
    RawWebDownloadEvent,
    RawWebIngestionEvent,
)
from material_ingestion.logging_schema import log_event
from material_ingestion.services.web_crawl_frontier_builder_service import build_frontier_from_sitemaps
from material_ingestion.services.web_crawl_frontier_evaluate_service import evaluate_frontier_batch
from material_ingestion.services.web_crawl_frontier_fetch_service import fetch_frontier_batch
from material_ingestion.services.web_crawl_frontier_get_service import fetch_promoted_frontier_batch
from material_ingestion.services.web_crawl_retention_service import apply_decision_event_retention
from material_ingestion.services.web_discovery_service import run_web_discover_pdfs
from material_ingestion.services.web_download_service import run_web_download_job
from material_ingestion.services.web_qualification_service import run_web_qualify_job

logger = logging.getLogger("material_ingestion.web")
DEFAULT_STALE_HEARTBEAT_SECONDS = 600
DEFAULT_DECISION_RETENTION_DAYS = 14
DEFAULT_EVENT_RETENTION_DAYS = 14
DEFAULT_RETENTION_SWEEP_SECONDS = 300
CORE_STAGE_EVENT_TYPES: dict[str, list[str]] = {
    "discover": ["core_discover_requested"],
    "build": ["frontier_build_requested"],
    "fetch": ["frontier_fetch_requested"],
    "evaluate": ["frontier_evaluate_requested"],
    "get": ["frontier_get_requested"],
}


def _has_pending_or_running_event(*, event_type: str) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        existing = (
            session.query(RawWebIngestionEvent.id)
            .filter(
                RawWebIngestionEvent.event_type == event_type,
                RawWebIngestionEvent.status.in_(["queued", "running"]),
            )
            .first()
        )
        return existing is not None


def _has_evaluate_eligible_frontier_items() -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        latest_attempt_id = (
            session.query(RawWebHttpFetchAttempt.uri_identity_id, RawWebHttpFetchAttempt.id.label("latest_attempt_id"))
            .filter(RawWebHttpFetchAttempt.outcome == "success")
            .order_by(RawWebHttpFetchAttempt.uri_identity_id.asc(), RawWebHttpFetchAttempt.id.desc())
            .distinct(RawWebHttpFetchAttempt.uri_identity_id)
            .subquery()
        )
        evaluated_exists = exists().where(
            and_(
                RawWebCrawlDecision.uri_identity_id == RawWebFrontierItem.uri_identity_id,
                RawWebCrawlDecision.reason_code.in_(["eval_promote", "eval_defer", "eval_skip"]),
            )
        )
        row = (
            session.query(RawWebFrontierItem.id)
            .join(latest_attempt_id, latest_attempt_id.c.uri_identity_id == RawWebFrontierItem.uri_identity_id)
            .join(RawWebHttpRepresentation, RawWebHttpRepresentation.fetch_attempt_id == latest_attempt_id.c.latest_attempt_id)
            .filter(RawWebFrontierItem.state == "completed")
            .filter(RawWebFrontierItem.state_reason_code.in_(["head_metadata_success", "recent_success_skip"]))
            .filter(~evaluated_exists)
            .order_by(RawWebFrontierItem.id.asc())
            .first()
        )
        return row is not None



def _has_get_eligible_frontier_items() -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebFrontierItem.id)
            .filter(
                RawWebFrontierItem.state == "completed",
                RawWebFrontierItem.state_reason_code.in_(["eval_promote", "get_retry_scheduled"]),
                RawWebFrontierItem.scheduled_at <= datetime.now(UTC),
            )
            .order_by(RawWebFrontierItem.id.asc())
            .first()
        )
        return row is not None


def _stale_cutoff(now: datetime | None = None) -> datetime:
    base = now or datetime.now(UTC)
    stale_seconds = int(os.getenv("MATERIAL_INGESTION_EVENT_STALE_SECONDS", str(DEFAULT_STALE_HEARTBEAT_SECONDS)))
    return base - timedelta(seconds=max(1, stale_seconds))


def requeue_stale_running_events(orchestration_id: str | None) -> int:
    cutoff = _stale_cutoff()
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebIngestionEvent).filter(
            RawWebIngestionEvent.status == "running",
            RawWebIngestionEvent.heartbeat_at.is_not(None),
            RawWebIngestionEvent.heartbeat_at < cutoff,
        )
        if orchestration_id:
            query = query.filter(RawWebIngestionEvent.orchestration_id == orchestration_id)
        stale_events = query.all()
        if not stale_events:
            return 0
        now = datetime.now(UTC)
        for event in stale_events:
            event.status = "queued"
            event.next_retry_at = now
            event.error_text = (
                f"stale running event requeued at {now.isoformat()} "
                f"(heartbeat_at={event.heartbeat_at.isoformat() if event.heartbeat_at else 'n/a'})"
            )[:4000]
            event.finished_at = now
            event.heartbeat_at = now
        session.commit()
        return len(stale_events)


def _maybe_apply_decision_event_retention(last_sweep_at: datetime | None) -> datetime:
    now = datetime.now(UTC)
    sweep_seconds = max(1, int(os.getenv("MATERIAL_INGESTION_RETENTION_SWEEP_SECONDS", str(DEFAULT_RETENTION_SWEEP_SECONDS))))
    if last_sweep_at is not None and (now - last_sweep_at).total_seconds() < sweep_seconds:
        return last_sweep_at

    decision_days = max(
        1, int(os.getenv("MATERIAL_INGESTION_CRAWL_DECISION_RETENTION_DAYS", str(DEFAULT_DECISION_RETENTION_DAYS)))
    )
    event_days = max(
        1, int(os.getenv("MATERIAL_INGESTION_INGESTION_EVENT_RETENTION_DAYS", str(DEFAULT_EVENT_RETENTION_DAYS)))
    )
    deleted_decisions, deleted_events = apply_decision_event_retention(
        decision_retention_days=decision_days,
        event_retention_days=event_days,
        now=now,
    )
    if deleted_decisions or deleted_events:
        log_event(
            logger,
            logging.INFO,
            "retention_cleanup_applied",
            deleted_decisions=deleted_decisions,
            deleted_events=deleted_events,
            decision_retention_days=decision_days,
            event_retention_days=event_days,
        )
    return now


def enqueue_web_event(*, orchestration_id: str, event_type: str, payload: dict[str, object]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        event = RawWebIngestionEvent(
            orchestration_id=orchestration_id,
            event_type=event_type,
            status="queued",
            payload_json=json.dumps(payload, sort_keys=True),
            error_text="",
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return int(event.id)


def get_next_queued_web_event(orchestration_id: str | None) -> RawWebIngestionEvent | None:
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebIngestionEvent).filter(RawWebIngestionEvent.status == "queued")
        if orchestration_id:
            query = query.filter(RawWebIngestionEvent.orchestration_id == orchestration_id)
        query = query.filter(
            (RawWebIngestionEvent.next_retry_at.is_(None)) | (RawWebIngestionEvent.next_retry_at <= datetime.now(UTC))
        )
        event = query.order_by(RawWebIngestionEvent.id.asc()).with_for_update(skip_locked=True).first()
        if event is None:
            return None
        event.status = "running"
        event.attempt_count = int(event.attempt_count or 0) + 1
        event.started_at = datetime.now(UTC)
        event.heartbeat_at = datetime.now(UTC)
        session.commit()
        session.refresh(event)
        session.expunge(event)
        return event


def get_next_queued_core_web_event(
    orchestration_id: str | None,
    *,
    stage: str | None = None,
    avoid_orchestration_id: str | None = None,
) -> RawWebIngestionEvent | None:
    session_factory = create_session_factory()
    with session_factory() as session:
        event_types = ["core_discover_requested", "frontier_build_requested", "frontier_fetch_requested"]
        if stage:
            normalized_stage = str(stage).strip().lower()
            if normalized_stage not in CORE_STAGE_EVENT_TYPES:
                raise ValueError(f"Unsupported core worker stage: {stage}")
            event_types = CORE_STAGE_EVENT_TYPES[normalized_stage]
        query = session.query(RawWebIngestionEvent).filter(
            RawWebIngestionEvent.status == "queued",
            RawWebIngestionEvent.event_type.in_(event_types),
        )
        if orchestration_id:
            query = query.filter(RawWebIngestionEvent.orchestration_id == orchestration_id)
        query = query.filter(
            (RawWebIngestionEvent.next_retry_at.is_(None)) | (RawWebIngestionEvent.next_retry_at <= datetime.now(UTC))
        )
        candidates = query.order_by(RawWebIngestionEvent.id.asc()).limit(200).with_for_update(skip_locked=True).all()
        if not candidates:
            return None
        event = None
        if avoid_orchestration_id:
            event = next((row for row in candidates if row.orchestration_id != avoid_orchestration_id), None)
        if event is None:
            event = candidates[0]
        if event is None:
            return None
        event.status = "running"
        event.attempt_count = int(event.attempt_count or 0) + 1
        event.started_at = datetime.now(UTC)
        event.heartbeat_at = datetime.now(UTC)
        session.commit()
        session.refresh(event)
        session.expunge(event)
        return event


def mark_web_event_done(event_id: int) -> None:
    session_factory = create_session_factory()
    with session_factory() as session:
        event = session.query(RawWebIngestionEvent).filter(RawWebIngestionEvent.id == event_id).first()
        if event is None:
            return
        event.status = "done"
        event.error_text = ""
        event.finished_at = datetime.now(UTC)
        event.heartbeat_at = datetime.now(UTC)
        session.commit()


def touch_web_event_heartbeat(event_id: int) -> None:
    session_factory = create_session_factory()
    with session_factory() as session:
        event = session.query(RawWebIngestionEvent).filter(RawWebIngestionEvent.id == event_id).first()
        if event is None:
            return
        event.heartbeat_at = datetime.now(UTC)
        session.commit()


def mark_web_event_failed(event_id: int, error_text: str) -> None:
    session_factory = create_session_factory()
    with session_factory() as session:
        event = session.query(RawWebIngestionEvent).filter(RawWebIngestionEvent.id == event_id).first()
        if event is None:
            return
        event.status = "failed"
        event.error_text = error_text[:4000]
        event.finished_at = datetime.now(UTC)
        event.heartbeat_at = datetime.now(UTC)
        session.commit()


def run_web_event(event: RawWebIngestionEvent) -> None:
    payload = json.loads(event.payload_json or "{}")
    if event.event_type == "core_discover_requested":
        core_payload = dict(payload)
        core_payload["core_only"] = True
        core_payload["heartbeat_callback"] = lambda: touch_web_event_heartbeat(event.id)
        run_web_discover_pdfs(argparse.Namespace(**core_payload))
        enqueue_web_event(
            orchestration_id=event.orchestration_id,
            event_type="frontier_build_requested",
            payload={
                "run_key": event.orchestration_id,
                "orchestration_id": event.orchestration_id,
                "fetch_max_concurrency": int(payload.get("fetch_max_concurrency") or 25),
            },
        )
        log_event(
            logger,
            logging.INFO,
            "core_discover_requested_completed",
            orchestration_id=event.orchestration_id,
        )
        return

    if event.event_type == "frontier_build_requested":
        run_key = str(payload.get("run_key") or event.orchestration_id)
        inserted = build_frontier_from_sitemaps(
            run_key=run_key,
            sitemap_source_id=payload.get("sitemap_source_id"),
            batch_size=int(payload.get("batch_size") or 1000),
            heartbeat_callback=lambda: touch_web_event_heartbeat(event.id),
            progress_callback=lambda processed, inserted_count: log_event(
                logger,
                logging.INFO,
                "frontier_build_requested_progress",
                orchestration_id=event.orchestration_id,
                run_key=run_key,
                processed_entries=processed,
                inserted_frontier=inserted_count,
            ),
        )
        log_event(
            logger,
            logging.INFO,
            "frontier_build_requested_completed",
            orchestration_id=event.orchestration_id,
            inserted_frontier=inserted,
        )
        enqueue_web_event(
            orchestration_id=event.orchestration_id,
            event_type="frontier_fetch_requested",
            payload={
                "run_key": run_key,
                "batch_size": int(payload.get("fetch_batch_size") or 100),
                "max_concurrency": int(payload.get("fetch_max_concurrency") or 25),
                "orchestration_id": event.orchestration_id,
            },
        )
        return

    if event.event_type == "frontier_fetch_requested":
        run_key = str(payload.get("run_key") or event.orchestration_id)
        processed, succeeded, deferred = fetch_frontier_batch(
            run_key=run_key,
            batch_size=int(payload.get("batch_size") or 100),
            max_concurrency=int(payload.get("max_concurrency") or 25),
            heartbeat_callback=lambda: touch_web_event_heartbeat(event.id),
            progress_callback=lambda processed_count, success_count, deferred_count: log_event(
                logger,
                logging.INFO,
                "frontier_fetch_requested_progress",
                orchestration_id=event.orchestration_id,
                run_key=run_key,
                processed=processed_count,
                succeeded=success_count,
                deferred=deferred_count,
            ),
        )
        log_event(
            logger,
            logging.INFO,
            "frontier_fetch_requested_completed",
            orchestration_id=event.orchestration_id,
            run_key=run_key,
            processed=processed,
            succeeded=succeeded,
            deferred=deferred,
        )
        return

    if event.event_type == "frontier_evaluate_requested":
        batch_size = int(payload.get("batch_size") or 500)
        force = bool(payload.get("force", False))
        total_processed = total_promoted = total_deferred = total_skipped = 0
        while True:
            processed, promoted, deferred, skipped = evaluate_frontier_batch(
                batch_size=batch_size,
                force=force,
                heartbeat_callback=lambda: touch_web_event_heartbeat(event.id),
                progress_callback=lambda processed_count, promoted_count, deferred_count, skipped_count: log_event(
                    logger,
                    logging.INFO,
                    "frontier_evaluate_requested_progress",
                    orchestration_id=event.orchestration_id,
                    processed=processed_count,
                    promoted=promoted_count,
                    deferred=deferred_count,
                    skipped=skipped_count,
                ),
            )
            total_processed += processed
            total_promoted += promoted
            total_deferred += deferred
            total_skipped += skipped
            if processed == 0:
                break
            log_event(
                logger,
                logging.INFO,
                "frontier_evaluate_chunk_completed",
                orchestration_id=event.orchestration_id,
                chunk_processed=processed,
                chunk_promoted=promoted,
                chunk_deferred=deferred,
                chunk_skipped=skipped,
                total_processed=total_processed,
                total_promoted=total_promoted,
            )
        log_event(
            logger,
            logging.INFO,
            "frontier_evaluate_requested_completed",
            orchestration_id=event.orchestration_id,
            processed=total_processed,
            promoted=total_promoted,
            deferred=total_deferred,
            skipped=total_skipped,
        )
        if total_promoted > 0:
            enqueue_frontier_get_event()
        return

    if event.event_type == "frontier_get_requested":
        processed, succeeded, failed, candidates = fetch_promoted_frontier_batch(
            batch_size=int(payload.get("batch_size") or 500),
            max_concurrency=int(payload.get("max_concurrency") or 20),
            heartbeat_callback=lambda: touch_web_event_heartbeat(event.id),
            progress_callback=lambda processed_count, success_count, failed_count, candidate_count: log_event(
                logger,
                logging.INFO,
                "frontier_get_requested_progress",
                orchestration_id=event.orchestration_id,
                processed=processed_count,
                succeeded=success_count,
                failed=failed_count,
                candidates=candidate_count,
            ),
        )
        log_event(
            logger,
            logging.INFO,
            "frontier_get_requested_completed",
            orchestration_id=event.orchestration_id,
            processed=processed,
            succeeded=succeeded,
            failed=failed,
            candidates=candidates,
        )
        return

    if event.event_type == "discover_requested":
        run_web_discover_pdfs(argparse.Namespace(**payload))
        if bool(payload.get("core_only", False)):
            log_event(
                logger,
                logging.INFO,
                "discover_requested_completed_core_only",
                orchestration_id=event.orchestration_id,
            )
            return
        qualify_output = str(payload.get("qualify_output_path", ""))
        enqueue_web_event(
            orchestration_id=event.orchestration_id,
            event_type="qualify_requested",
            payload={
                "ingest_batch_id": payload["ingest_batch_id"],
                "min_score": payload["min_score"],
                "limit": payload["limit"],
                "ingest_source": payload["ingest_source_download"],
                "output": qualify_output,
                "download_batch_id": payload["download_batch_id"],
                "output_root": payload["output_root"],
                "orchestration_id": event.orchestration_id,
            },
        )
        return

    if event.event_type == "qualify_requested":
        run_web_qualify_job(
            argparse.Namespace(
                ingest_batch_id=payload["ingest_batch_id"],
                min_score=payload["min_score"],
                limit=payload["limit"],
                ingest_source=payload["ingest_source"],
                output=payload["output"],
                orchestration_id=event.orchestration_id,
            )
        )
        enqueue_web_event(
            orchestration_id=event.orchestration_id,
            event_type="download_requested",
            payload={
                "qualified_input": payload["output"],
                "output_root": payload["output_root"],
                "ingest_source": payload["ingest_source"],
                "ingest_locator": "raw_web_pdf_candidate",
                "download_batch_id": payload["download_batch_id"],
                "orchestration_id": event.orchestration_id,
            },
        )
        return

    if event.event_type == "download_requested":
        run_web_download_job(
            argparse.Namespace(
                qualified_input=payload["qualified_input"],
                output_root=payload["output_root"],
                ingest_source=payload["ingest_source"],
                ingest_locator=payload["ingest_locator"],
                download_batch_id=payload["download_batch_id"],
                orchestration_id=event.orchestration_id,
                heartbeat_callback=lambda: touch_web_event_heartbeat(event.id),
            )
        )
        return

    raise ValueError(f"Unsupported web ingestion event_type: {event.event_type}")


def enqueue_core_discover_event(
    *,
    run_key: str,
    seed_url: str,
    max_pages: int = 100,
    cross_domain: bool = False,
    ingest_source: str = "web_discovery",
    fetch_max_concurrency: int = 25,
) -> int:
    payload = {
        "seed_url": seed_url,
        "max_pages": max_pages,
        "cross_domain": cross_domain,
        "ingest_source": ingest_source,
        "ingest_locator": seed_url,
        "ingest_batch_id": run_key,
        "orchestration_id": run_key,
        "fetch_max_concurrency": fetch_max_concurrency,
    }
    return enqueue_web_event(orchestration_id=run_key, event_type="core_discover_requested", payload=payload)


def enqueue_frontier_evaluate_event(
    *,
    batch_size: int = 500,
    orchestration_id: str = "global_frontier_evaluate",
    force: bool = False,
) -> int | None:
    now = datetime.now(UTC)
    cutoff = _stale_cutoff(now)
    session_factory = create_session_factory()
    with session_factory() as session:
        stale_running = (
            session.query(RawWebIngestionEvent)
            .filter(
                RawWebIngestionEvent.event_type == "frontier_evaluate_requested",
                RawWebIngestionEvent.status == "running",
                RawWebIngestionEvent.heartbeat_at.is_not(None),
                RawWebIngestionEvent.heartbeat_at < cutoff,
            )
            .all()
        )
        for row in stale_running:
            row.status = "queued"
            row.next_retry_at = now
            row.error_text = "stale evaluate event auto-requeued during enqueue"
            row.finished_at = now
            row.heartbeat_at = now
        if stale_running:
            session.commit()
        if _has_pending_or_running_event(event_type="frontier_evaluate_requested"):
            return None
        if not bool(force) and not _has_evaluate_eligible_frontier_items():
            return None
    return enqueue_web_event(
        orchestration_id=orchestration_id,
        event_type="frontier_evaluate_requested",
        payload={"batch_size": int(batch_size), "force": bool(force)},
    )


def enqueue_frontier_get_event(
    *,
    batch_size: int = 500,
    max_concurrency: int = 50,
    orchestration_id: str = "global_frontier_get",
) -> int | None:
    now = datetime.now(UTC)
    cutoff = _stale_cutoff(now)
    session_factory = create_session_factory()
    with session_factory() as session:
        stale_running = (
            session.query(RawWebIngestionEvent)
            .filter(
                RawWebIngestionEvent.event_type == "frontier_get_requested",
                RawWebIngestionEvent.status == "running",
                RawWebIngestionEvent.heartbeat_at.is_not(None),
                RawWebIngestionEvent.heartbeat_at < cutoff,
            )
            .all()
        )
        for row in stale_running:
            row.status = "queued"
            row.next_retry_at = now
            row.error_text = "stale get event auto-requeued during enqueue"
            row.finished_at = now
            row.heartbeat_at = now
        if stale_running:
            session.commit()
        if _has_pending_or_running_event(event_type="frontier_get_requested"):
            return None
        if not _has_get_eligible_frontier_items():
            return None
    return enqueue_web_event(
        orchestration_id=orchestration_id,
        event_type="frontier_get_requested",
        payload={"batch_size": int(batch_size), "max_concurrency": int(max_concurrency)},
    )


def run_web_worker(args: argparse.Namespace) -> int:
    processed = 0
    retention_last_sweep_at: datetime | None = None
    requeued = requeue_stale_running_events(args.orchestration_id)
    if requeued:
        log_event(logger, logging.WARNING, "worker_requeued_stale_running_events", count=requeued)
    while True:
        retention_last_sweep_at = _maybe_apply_decision_event_retention(retention_last_sweep_at)
        event = get_next_queued_web_event(args.orchestration_id)
        if event is None:
            break
        log_event(
            logger,
            logging.INFO,
            "worker_processing_event",
            event_id=event.id,
            orchestration_id=event.orchestration_id,
            event_type=event.event_type,
        )
        try:
            run_web_event(event)
        except KeyboardInterrupt:
            mark_web_event_failed(event.id, "interrupted by user")
            log_event(logger, logging.WARNING, "worker_interrupted_event", event_id=event.id, event_type=event.event_type)
            return 130
        except Exception as exc:
            mark_web_event_failed(event.id, str(exc))
            log_event(
                logger, logging.ERROR, "worker_event_failed",
                event_id=event.id, event_type=event.event_type,
                error_class=exc.__class__.__name__, error=str(exc)
            )
            logger.debug("event=worker_event_failed_trace event_id=%s", event.id, exc_info=True)
            return 1
        mark_web_event_done(event.id)
        processed += 1
        if args.once:
            break
    log_event(logger, logging.INFO, "worker_loop_completed", orchestration_id=args.orchestration_id or "all", processed=processed)
    return 0


def run_web_core_worker(args: argparse.Namespace) -> int:
    processed = 0
    retention_last_sweep_at: datetime | None = None
    requeued = requeue_stale_running_events(args.orchestration_id)
    if requeued:
        log_event(logger, logging.WARNING, "worker_requeued_stale_running_events", count=requeued)
    while True:
        retention_last_sweep_at = _maybe_apply_decision_event_retention(retention_last_sweep_at)
        event = get_next_queued_core_web_event(
            args.orchestration_id,
            stage=getattr(args, "stage", None),
            avoid_orchestration_id=getattr(args, "last_orchestration_id", None),
        )
        if event is None:
            break
        log_event(
            logger,
            logging.INFO,
            "core_worker_processing_event",
            event_id=event.id,
            orchestration_id=event.orchestration_id,
            event_type=event.event_type,
        )
        try:
            run_web_event(event)
        except KeyboardInterrupt:
            mark_web_event_failed(event.id, "interrupted by user")
            log_event(logger, logging.WARNING, "core_worker_interrupted_event", event_id=event.id, event_type=event.event_type)
            return 130
        except Exception as exc:
            mark_web_event_failed(event.id, str(exc))
            log_event(
                logger,
                logging.ERROR,
                "core_worker_event_failed",
                event_id=event.id,
                event_type=event.event_type,
                error_class=exc.__class__.__name__,
                error=str(exc),
            )
            logger.debug("event=core_worker_event_failed_trace event_id=%s", event.id, exc_info=True)
            return 1
        mark_web_event_done(event.id)
        # Re-enqueue GET after marking done so the duplicate-guard sees the event as finished.
        if event.event_type == "frontier_get_requested":
            _get_payload = json.loads(event.payload_json or "{}")
            enqueue_frontier_get_event(
                batch_size=int(_get_payload.get("batch_size") or 500),
                max_concurrency=int(_get_payload.get("max_concurrency") or 50),
            )
        args.last_orchestration_id = event.orchestration_id
        processed += 1
        if args.once:
            break
    log_level = logging.INFO if processed > 0 else logging.DEBUG
    log_event(
        logger,
        log_level,
        "core_worker_loop_completed",
        orchestration_id=args.orchestration_id or "all",
        processed=processed,
    )
    return 0


def run_web_run(args: argparse.Namespace) -> int:
    discover_batch_id = args.discover_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    download_batch_id = args.download_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    orchestration_id = discover_batch_id
    qualify_output_path = f"data/working/discovered/qualified_{discover_batch_id}.json"
    log_event(logger, logging.INFO, "web_run_orchestration_starting")
    enqueue_web_event(
        orchestration_id=orchestration_id,
        event_type="discover_requested",
        payload={
            "seed_url": args.seed_url,
            "max_pages": args.max_pages,
            "cross_domain": args.cross_domain,
            "output": None,
            "ingest_source": args.ingest_source_discovery,
            "ingest_locator": None,
            "ingest_batch_id": discover_batch_id,
            "min_score": args.min_score,
            "limit": args.limit,
            "ingest_source_download": args.ingest_source_download,
            "download_batch_id": download_batch_id,
            "output_root": args.output_root,
            "qualify_output_path": qualify_output_path,
            "orchestration_id": orchestration_id,
            "core_only": bool(getattr(args, "core_only", False)),
        },
    )

    log_event(
        logger,
        logging.INFO,
        "web_run_started",
        orchestration_id=orchestration_id,
        first_event="discover_requested",
        seed_url=args.seed_url,
        max_pages=args.max_pages,
        min_score=args.min_score,
        limit=args.limit,
        output_root=args.output_root,
    )
    worker_count = max(1, int(getattr(args, "worker_count", 1)))
    if worker_count == 1:
        return run_web_worker(argparse.Namespace(orchestration_id=orchestration_id, once=False))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [
            executor.submit(run_web_worker, argparse.Namespace(orchestration_id=orchestration_id, once=False))
            for _ in range(worker_count)
        ]
        for future in as_completed(futures):
            rc = int(future.result())
            if rc != 0:
                return rc
    return 0


def run_web_status(args: argparse.Namespace) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebIngestionEvent)
        if args.orchestration_id:
            query = query.filter(RawWebIngestionEvent.orchestration_id == args.orchestration_id)
        events = query.order_by(RawWebIngestionEvent.id.asc()).all()

    counts = {"queued": 0, "running": 0, "done": 0, "failed": 0, "other": 0}
    for event in events:
        counts[event.status if event.status in counts else "other"] += 1

    now = datetime.now(UTC)
    retry_backlog = sum(
        1
        for event in events
        if event.status == "queued" and event.next_retry_at is not None and event.next_retry_at > now
    )
    last_error_event = next((event for event in reversed(events) if (event.error_text or "").strip()), None)

    log_event(
        logger,
        logging.INFO,
        "web_status",
        orchestration_id=args.orchestration_id or "all",
        total_events=len(events),
        queued=counts["queued"],
        running=counts["running"],
        succeeded=counts["done"],
        failed=counts["failed"],
        other=counts["other"],
        retry_backlog=retry_backlog,
    )
    if last_error_event is None:
        log_event(logger, logging.INFO, "web_status_last_error", orchestration_id=args.orchestration_id or "all", last_error="none")
    else:
        log_event(
            logger,
            logging.WARNING,
            "web_status_last_error",
            orchestration_id=args.orchestration_id or "all",
            last_error_event_id=last_error_event.id,
            last_error_event_type=last_error_event.event_type,
            last_error=(last_error_event.error_text or "").strip(),
        )

    if getattr(args, "verbose", False):
        limit = max(1, int(getattr(args, "event_limit", 20)))
        session_factory = create_session_factory()
        with session_factory() as session:
            dq = session.query(RawWebDiscoveryEvent)
            cq = session.query(RawWebCandidateEvent)
            wq = session.query(RawWebDownloadEvent)
            if args.orchestration_id:
                dq = dq.filter(RawWebDiscoveryEvent.orchestration_id == args.orchestration_id)
                cq = cq.filter(RawWebCandidateEvent.orchestration_id == args.orchestration_id)
                wq = wq.filter(RawWebDownloadEvent.orchestration_id == args.orchestration_id)
            d_events = dq.order_by(RawWebDiscoveryEvent.id.desc()).limit(limit).all()
            c_events = cq.order_by(RawWebCandidateEvent.id.desc()).limit(limit).all()
            w_events = wq.order_by(RawWebDownloadEvent.id.desc()).limit(limit).all()

        for e in reversed(d_events):
            log_event(logger, logging.INFO, "web_status_stage_event", stage="discovery", id=e.id, orchestration_id=e.orchestration_id, event_type=e.event_type, page_url=e.page_url)
        for e in reversed(c_events):
            log_event(logger, logging.INFO, "web_status_stage_event", stage="candidate", id=e.id, orchestration_id=e.orchestration_id, event_type=e.event_type, pdf_url=e.pdf_url)
        for e in reversed(w_events):
            log_event(logger, logging.INFO, "web_status_stage_event", stage="download", id=e.id, orchestration_id=e.orchestration_id, event_type=e.event_type, source_url=e.source_url, status_code=e.status_code)
    return 0
from sqlalchemy import and_, exists
