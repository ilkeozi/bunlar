from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from material_ingestion.db.models import RawWebIngestionEvent, RawWebPdfCandidate
from material_ingestion.logging_schema import log_event
from material_ingestion.services.web_discovery_service import run_web_discover_pdfs
from material_ingestion.services.web_download_service import download_qualified_candidates, run_web_download_job
from material_ingestion.services.web_event_service import (
    enqueue_web_event,
    get_next_queued_web_event,
    mark_web_event_done,
    mark_web_event_failed,
    requeue_stale_running_events,
    run_web_event,
    run_web_run,
    run_web_status,
    run_web_worker,
)
from material_ingestion.services.web_qualification_service import (
    candidate_language_hints,
    collect_qualified_candidates,
    is_probable_pdf_candidate,
    matches_preferred_language,
    parse_preferred_languages,
    run_web_qualify_job,
)

logger = logging.getLogger("material_ingestion.web")


# Backward-compatible thin wrappers for CLI/tests.
def run_web_fetch_pdfs(args: argparse.Namespace) -> int:
    download_batch_id = args.download_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    qualified_rows, summary = collect_qualified_candidates(
        ingest_batch_id=args.ingest_batch_id,
        min_score=args.min_score,
        limit=args.limit,
        ingest_source=args.ingest_source,
    )
    saved = download_qualified_candidates(
        qualified_rows=qualified_rows,
        output_root=Path(args.output_root),
        ingest_source=args.ingest_source,
        ingest_locator=args.ingest_locator,
        download_batch_id=download_batch_id,
        orchestration_id=args.ingest_batch_id,
        source_batch_id=args.ingest_batch_id,
    )
    log_event(
        logger,
        logging.INFO,
        "fetch_pdfs_completed",
        batch_id=download_batch_id,
        selected_candidates=summary["selected_candidates"],
        skipped_non_preferred_language=summary["skipped_non_preferred_language"],
        probable_pdf_candidates=summary["probable_pdf_candidates"],
        skipped_already_downloaded=summary["skipped_already_downloaded"],
        pending_candidates=summary["pending_candidates"],
        downloaded_files=saved,
    )
    return 0


__all__ = [
    "RawWebIngestionEvent",
    "RawWebPdfCandidate",
    "is_probable_pdf_candidate",
    "parse_preferred_languages",
    "candidate_language_hints",
    "matches_preferred_language",
    "run_web_discover_pdfs",
    "collect_qualified_candidates",
    "download_qualified_candidates",
    "run_web_fetch_pdfs",
    "run_web_qualify_job",
    "run_web_download_job",
    "enqueue_web_event",
    "get_next_queued_web_event",
    "mark_web_event_done",
    "mark_web_event_failed",
    "requeue_stale_running_events",
    "run_web_event",
    "run_web_run",
    "run_web_status",
    "run_web_worker",
]
