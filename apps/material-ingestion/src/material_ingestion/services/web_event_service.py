from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import UTC, datetime
from datetime import timedelta

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebCandidateEvent,
    RawWebDiscoveryEvent,
    RawWebDownloadEvent,
    RawWebIngestionEvent,
)
from material_ingestion.logging_schema import log_event
from material_ingestion.services.web_discovery_service import run_web_discover_pdfs
from material_ingestion.services.web_download_service import run_web_download_job
from material_ingestion.services.web_qualification_service import run_web_qualify_job

logger = logging.getLogger("material_ingestion.web")
DEFAULT_STALE_HEARTBEAT_SECONDS = 600


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
    if event.event_type == "discover_requested":
        run_web_discover_pdfs(argparse.Namespace(**payload))
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


def run_web_worker(args: argparse.Namespace) -> int:
    processed = 0
    requeued = requeue_stale_running_events(args.orchestration_id)
    if requeued:
        log_event(logger, logging.WARNING, "worker_requeued_stale_running_events", count=requeued)
    while True:
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
    return run_web_worker(argparse.Namespace(orchestration_id=orchestration_id, once=False))


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
