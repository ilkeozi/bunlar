from __future__ import annotations

import argparse
import json
import logging
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from material_ingestion.ai import DeepseekPdfClassifier
from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebDownloadedFile, RawWebPdfCandidate
from material_ingestion.logging_schema import log_event
from material_ingestion.services.web_stage_event_service import append_candidate_events
from material_ingestion.services.web_url_canonicalizer import canonicalize_url

logger = logging.getLogger("material_ingestion.web")


def is_probable_pdf_candidate(candidate: RawWebPdfCandidate) -> bool:
    pdf_url = (getattr(candidate, "pdf_url", "") or "").strip().lower()
    reason = (getattr(candidate, "reason", "") or "").strip().lower()
    if pdf_url.endswith(".pdf") or "url_pdf_suffix" in reason:
        return True
    return "api_json_url" in reason


def parse_preferred_languages() -> set[str]:
    raw = os.getenv("MATERIAL_INGESTION_PREFERRED_LANGUAGES", "en,english")
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def candidate_language_hints(candidate: RawWebPdfCandidate) -> set[str]:
    hints: set[str] = set()
    url = (getattr(candidate, "pdf_url", "") or "").strip()
    reason = (getattr(candidate, "reason", "") or "").strip().lower()

    parsed = urlparse(url)
    for seg in [p for p in parsed.path.split("/") if p]:
        low = seg.lower()
        if re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", low):
            hints.add(low.split("-", 1)[0])

    decoded = unquote(url).lower()
    if "_english" in decoded or "-english" in decoded or "/english" in decoded:
        hints.add("english")

    for token in reason.split(","):
        token = token.strip()
        if token.startswith("lang_"):
            hints.add(token.removeprefix("lang_"))
    return hints


def matches_preferred_language(candidate: RawWebPdfCandidate, preferred_languages: set[str]) -> bool:
    if not preferred_languages:
        return True
    hints = candidate_language_hints(candidate)
    if not hints:
        return True
    return any(hint in preferred_languages for hint in hints)


def collect_qualified_candidates(
    *,
    ingest_batch_id: str,
    min_score: int,
    limit: int | None,
    ingest_source: str,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    log_event(
        logger,
        logging.INFO,
        "qualify_started",
        discovery_batch_id=ingest_batch_id,
        min_score=min_score,
        limit=limit,
        output_root="n/a",
    )
    session_factory = create_session_factory()
    dedupe_scope = (os.getenv("MATERIAL_INGESTION_DEDUPE_SCOPE", "global") or "global").strip().lower()
    with session_factory() as session:
        query = (
            session.query(RawWebPdfCandidate)
            .filter(
                RawWebPdfCandidate.ingest_batch_id == ingest_batch_id,
                RawWebPdfCandidate.score >= min_score,
            )
            .order_by(RawWebPdfCandidate.score.desc(), RawWebPdfCandidate.id.asc())
        )
        if limit is not None:
            query = query.limit(limit)
        rows = query.all()
        downloaded_query = session.query(RawWebDownloadedFile.canonical_source_url).filter(
            RawWebDownloadedFile.ingest_locator == "raw_web_pdf_candidate",
            RawWebDownloadedFile.ingest_source == ingest_source,
        )
        if dedupe_scope == "batch":
            downloaded_query = downloaded_query.filter(RawWebDownloadedFile.ingest_batch_id == ingest_batch_id)
        already_downloaded_urls = {row[0] for row in downloaded_query.all() if row and row[0]}

    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    deepseek_classifier = DeepseekPdfClassifier(api_key=deepseek_key) if deepseek_key else None
    preferred_languages = parse_preferred_languages()
    filtered_rows: list[RawWebPdfCandidate] = []
    skipped_non_pdf = 0
    skipped_non_preferred_language = 0
    deepseek_promoted = 0
    for row in rows:
        if not matches_preferred_language(row, preferred_languages):
            skipped_non_preferred_language += 1
            continue
        if is_probable_pdf_candidate(row):
            filtered_rows.append(row)
            continue
        if deepseek_classifier is None:
            skipped_non_pdf += 1
            continue
        try:
            if deepseek_classifier.is_likely_pdf(
                pdf_url=getattr(row, "pdf_url", "") or "",
                anchor_text=getattr(row, "anchor_text", "") or "",
                reason=getattr(row, "reason", "") or "",
                source_page_url=getattr(row, "source_page_url", "") or "",
            ):
                filtered_rows.append(row)
                deepseek_promoted += 1
            else:
                skipped_non_pdf += 1
        except Exception as exc:
            log_event(
                logger,
                logging.WARNING,
                "deepseek_classification_failed",
                candidate_id=getattr(row, "id", "n/a"),
                error_class=exc.__class__.__name__,
                error=str(exc),
            )
            skipped_non_pdf += 1

    if skipped_non_pdf:
        log_event(logger, logging.INFO, "qualify_skipped_non_pdf_like", count=skipped_non_pdf)
    if skipped_non_preferred_language:
        log_event(logger, logging.INFO, "qualify_skipped_non_preferred_language", count=skipped_non_preferred_language)
    if deepseek_promoted:
        log_event(logger, logging.INFO, "qualify_deepseek_promoted", count=deepseek_promoted)

    deduped_rows: list[RawWebPdfCandidate] = []
    seen_urls: set[str] = set()
    skipped_duplicate_url = 0
    for row in filtered_rows:
        url = canonicalize_url((getattr(row, "pdf_url", "") or "").strip())
        if not url:
            continue
        if url in seen_urls:
            skipped_duplicate_url += 1
            continue
        seen_urls.add(url)
        deduped_rows.append(row)
    if skipped_duplicate_url:
        log_event(logger, logging.INFO, "qualify_skipped_duplicate_url", count=skipped_duplicate_url)

    skipped_already_downloaded = 0
    pending_rows: list[RawWebPdfCandidate] = []
    for row in deduped_rows:
        url = canonicalize_url((getattr(row, "pdf_url", "") or "").strip())
        if url in already_downloaded_urls:
            skipped_already_downloaded += 1
            continue
        pending_rows.append(row)
    if skipped_already_downloaded:
        log_event(logger, logging.INFO, "qualify_skipped_already_downloaded", count=skipped_already_downloaded)

    qualified_rows = [
        {
            "candidate_id": getattr(row, "id", None),
            "source_page_url": getattr(row, "source_page_url", ""),
            "pdf_url": getattr(row, "pdf_url", ""),
            "canonical_pdf_url": canonicalize_url(getattr(row, "pdf_url", "") or ""),
            "score": getattr(row, "score", 0),
            "reason": getattr(row, "reason", ""),
        }
        for row in pending_rows
    ]
    summary = {
        "selected_candidates": len(rows),
        "skipped_non_preferred_language": skipped_non_preferred_language,
        "probable_pdf_candidates": len(deduped_rows),
        "skipped_already_downloaded": skipped_already_downloaded,
        "pending_candidates": len(pending_rows),
    }
    return qualified_rows, summary


def run_web_qualify_job(args: argparse.Namespace) -> int:
    orchestration_id = getattr(args, "orchestration_id", None) or args.ingest_batch_id
    qualified_rows, summary = collect_qualified_candidates(
        ingest_batch_id=args.ingest_batch_id,
        min_score=args.min_score,
        limit=args.limit,
        ingest_source=args.ingest_source,
    )
    output = args.output or f"data/working/discovered/qualified_{args.ingest_batch_id}.json"
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "ingest_batch_id": args.ingest_batch_id,
                "ingest_source": args.ingest_source,
                "qualified_candidates": qualified_rows,
                "summary": summary,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        append_candidate_events(
            [
                {
                    "orchestration_id": orchestration_id,
                    "ingest_batch_id": args.ingest_batch_id,
                    "event_type": "qualify_completed",
                    "candidate_id": 0,
                    "source_page_url": "",
                    "pdf_url": "",
                    "payload": summary,
                }
            ]
            + [
                {
                    "orchestration_id": orchestration_id,
                    "ingest_batch_id": args.ingest_batch_id,
                    "event_type": "candidate_qualified",
                    "candidate_id": int(r.get("candidate_id", 0) or 0),
                    "source_page_url": str(r.get("source_page_url", "")),
                    "pdf_url": str(r.get("pdf_url", "")),
                    "payload": {"score": int(r.get("score", 0)), "reason": str(r.get("reason", ""))},
                }
                for r in qualified_rows
            ]
        )
    except Exception as exc:
        log_event(
            logger,
            logging.WARNING,
            "stage_event_write_failed",
            stage="qualification",
            error_class=exc.__class__.__name__,
            error=str(exc),
        )
    log_event(
        logger,
        logging.INFO,
        "qualify_completed",
        batch_id=args.ingest_batch_id,
        selected_candidates=summary["selected_candidates"],
        skipped_non_preferred_language=summary["skipped_non_preferred_language"],
        probable_pdf_candidates=summary["probable_pdf_candidates"],
        skipped_already_downloaded=summary["skipped_already_downloaded"],
        pending_candidates=summary["pending_candidates"],
        output=str(out_path),
    )
    return 0
