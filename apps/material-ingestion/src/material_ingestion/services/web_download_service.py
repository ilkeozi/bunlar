from __future__ import annotations

import argparse
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from material_ingestion.db import create_session_factory
from sqlalchemy.dialects.postgresql import insert

from material_ingestion.db.models import RawWebDownloadAttempt, RawWebUrlBlobMap
from material_ingestion.exporters.raw_web_db_exporter import RawWebDbExporter
from material_ingestion.logging_schema import log_event
from material_ingestion.sources.web import WebFileDownloader
from material_ingestion.services.web_stage_event_service import append_download_events
from material_ingestion.services.web_url_canonicalizer import canonicalize_url

logger = logging.getLogger("material_ingestion.web")


def download_qualified_candidates(
    *,
    qualified_rows: list[dict[str, object]],
    output_root: Path,
    ingest_source: str,
    ingest_locator: str,
    download_batch_id: str,
    orchestration_id: str,
    source_batch_id: str,
    heartbeat_callback: Callable[[], None] | None = None,
) -> int:
    attempt_rows: list[dict[str, object]] = []

    def _flush_attempt_rows() -> None:
        if not attempt_rows:
            return
        session_factory = create_session_factory()
        with session_factory() as session:
            if not hasattr(session, "add_all"):
                attempt_rows.clear()
                return
            payload = [
                RawWebDownloadAttempt(
                    ingest_source=ingest_source,
                    ingest_locator=ingest_locator,
                    ingest_batch_id=download_batch_id,
                    source_url=str(r["source_url"]),
                    status=str(r["status"]),
                    attempt_no=int(r["attempt_no"]),
                    wait_seconds=int(r["wait_seconds"]),
                    http_status=int(r["http_status"]),
                    error_class=str(r["error_class"]),
                    error_text=str(r["error_text"]),
                )
                for r in attempt_rows
            ]
            session.add_all(payload)
            session.commit()
        attempt_rows.clear()

    def _on_retry(meta: dict[str, object]) -> None:
        # Persist each network retry attempt (e.g. HTTP 429) immediately for observability.
        attempt_rows.append(
            {
                "source_url": str(meta.get("source_url", "")),
                "status": "retry_scheduled",
                "attempt_no": int(meta.get("attempt", 0) or 0),
                "wait_seconds": int(round(float(meta.get("delay_seconds", 0.0) or 0.0))),
                "http_status": int(meta.get("status", 0) or 0),
                "error_class": str(meta.get("error_class", "")),
                "error_text": str(meta.get("error_text", "")),
            }
        )
        _flush_attempt_rows()
        _heartbeat()

    downloader = WebFileDownloader(
        max_retries=int(os.getenv("MATERIAL_INGESTION_DOWNLOAD_MAX_RETRIES", "4")),
        backoff_base_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_BACKOFF_BASE_SECONDS", "1.0")),
        backoff_max_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_BACKOFF_MAX_SECONDS", "20.0")),
        jitter_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_JITTER_SECONDS", "0.25")),
        retry_callback=_on_retry,
    )
    request_delay_seconds = float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_REQUEST_DELAY_SECONDS", "0.0"))
    exporter = RawWebDbExporter(
        ingest_source=ingest_source,
        ingest_locator=ingest_locator,
        ingest_batch_id=download_batch_id,
    )
    downloaded_rows: list[dict[str, object]] = []
    flush_every = max(1, int(os.getenv("MATERIAL_INGESTION_DOWNLOAD_CHECKPOINT_SIZE", "25")))
    saved_total = 0
    attempt_no = 0

    def _heartbeat() -> None:
        if heartbeat_callback is None:
            return
        try:
            heartbeat_callback()
        except Exception:
            return

    def _flush_chunks() -> None:
        nonlocal saved_total
        if downloaded_rows:
            saved_total += exporter.export_downloaded_files(downloaded_rows, replace_existing=False)
            # Keep explicit canonical URL -> blob mapping up to date.
            session_factory = create_session_factory()
            with session_factory() as session:
                if hasattr(session, "execute"):
                    for r in downloaded_rows:
                        stmt = insert(RawWebUrlBlobMap).values(
                            canonical_source_url=str(r["canonical_source_url"]),
                            source_url=str(r["source_url"]),
                            sha256=str(r["sha256"]),
                            first_seen_batch_id=download_batch_id,
                            last_seen_batch_id=download_batch_id,
                        )
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["canonical_source_url"],
                            set_={
                                "source_url": stmt.excluded.source_url,
                                "sha256": stmt.excluded.sha256,
                                "last_seen_batch_id": stmt.excluded.last_seen_batch_id,
                            },
                        )
                        session.execute(stmt)
                    session.commit()
            downloaded_rows.clear()
        _flush_attempt_rows()

    for row in qualified_rows:
        _heartbeat()
        attempt_no += 1
        try:
            append_download_events(
                [
                    {
                        "orchestration_id": orchestration_id,
                        "ingest_batch_id": source_batch_id,
                        "event_type": "download_started",
                        "source_url": str(row["pdf_url"]),
                        "status_code": 0,
                        "payload": {"candidate_id": row.get("candidate_id", 0), "attempt_no": attempt_no},
                    }
                ]
            )
        except Exception as exc:
            log_event(
                logger, logging.WARNING, "stage_event_write_failed", stage="download", phase="start",
                error_class=exc.__class__.__name__, error=str(exc)
            )
        if request_delay_seconds > 0:
            time.sleep(request_delay_seconds)
        log_event(
            logger, logging.DEBUG, "download_candidate_started",
            candidate_id=row.get("candidate_id", "n/a"), url=row["pdf_url"]
        )
        try:
            downloaded = downloader.download_pdf(source_url=str(row["pdf_url"]), output_root=output_root)
        except Exception as exc:
            log_event(
                logger, logging.WARNING, "download_candidate_failed",
                url=row["pdf_url"], error_class=exc.__class__.__name__, error=str(exc)
            )
            attempt_rows.append(
                {
                    "source_url": str(row["pdf_url"]),
                    "status": "failed",
                    "attempt_no": attempt_no,
                    "wait_seconds": 0,
                    "http_status": 0,
                    "error_class": exc.__class__.__name__,
                    "error_text": str(exc),
                }
            )
            if len(attempt_rows) >= flush_every:
                _flush_chunks()
            try:
                append_download_events(
                    [
                        {
                            "orchestration_id": orchestration_id,
                            "ingest_batch_id": source_batch_id,
                            "event_type": "download_failed",
                            "source_url": str(row["pdf_url"]),
                            "status_code": 0,
                            "payload": {"error": str(exc), "error_class": exc.__class__.__name__},
                        }
                    ]
                )
            except Exception as stage_exc:
                log_event(
                    logger, logging.WARNING, "stage_event_write_failed", stage="download", phase="failed",
                    error_class=stage_exc.__class__.__name__, error=str(stage_exc)
                )
            continue

        log_event(
            logger, logging.DEBUG, "download_candidate_succeeded",
            bytes=downloaded.size_bytes, status=downloaded.status_code, path=downloaded.stored_path,
        )
        downloaded_rows.append(
            {
                "source_url": downloaded.source_url,
                "canonical_source_url": canonicalize_url(downloaded.source_url),
                "stored_path": downloaded.stored_path,
                "sha256": downloaded.sha256,
                "size_bytes": downloaded.size_bytes,
                "content_type": downloaded.content_type,
                "status_code": downloaded.status_code,
            }
        )
        attempt_rows.append(
            {
                "source_url": downloaded.source_url,
                "status": "succeeded",
                "attempt_no": attempt_no,
                "wait_seconds": 0,
                "http_status": downloaded.status_code,
                "error_class": "",
                "error_text": "",
            }
        )
        if len(downloaded_rows) >= flush_every or len(attempt_rows) >= flush_every:
            _flush_chunks()
        try:
            append_download_events(
                [
                    {
                        "orchestration_id": orchestration_id,
                        "ingest_batch_id": source_batch_id,
                        "event_type": "download_succeeded",
                        "source_url": downloaded.source_url,
                        "status_code": downloaded.status_code,
                        "payload": {
                            "stored_path": downloaded.stored_path,
                            "sha256": downloaded.sha256,
                            "size_bytes": downloaded.size_bytes,
                        },
                    }
                ]
            )
        except Exception as exc:
            log_event(
                logger, logging.WARNING, "stage_event_write_failed", stage="download", phase="success",
                error_class=exc.__class__.__name__, error=str(exc)
            )
        _heartbeat()

    _flush_chunks()
    _heartbeat()
    return saved_total


def run_web_download_job(args: argparse.Namespace) -> int:
    download_batch_id = args.download_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    payload = json.loads(Path(args.qualified_input).read_text(encoding="utf-8"))
    qualified_rows = list(payload.get("qualified_candidates", []))
    source_batch_id = str(payload.get("ingest_batch_id", ""))
    orchestration_id = str(getattr(args, "orchestration_id", "") or source_batch_id or download_batch_id)
    saved = download_qualified_candidates(
        qualified_rows=qualified_rows,
        output_root=Path(args.output_root),
        ingest_source=args.ingest_source,
        ingest_locator=args.ingest_locator,
        download_batch_id=download_batch_id,
        orchestration_id=orchestration_id,
        source_batch_id=source_batch_id or orchestration_id,
        heartbeat_callback=getattr(args, "heartbeat_callback", None),
    )
    log_event(
        logger,
        logging.INFO,
        "download_completed",
        batch_id=download_batch_id,
        qualified_candidates=len(qualified_rows),
        downloaded_files=saved,
        output_root=args.output_root,
    )
    return 0
