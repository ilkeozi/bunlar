from __future__ import annotations

import argparse
import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from material_ingestion.exporters.raw_web_db_exporter import RawWebDbExporter
from material_ingestion.logging_schema import log_event
from material_ingestion.services.web_api_evidence_service import persist_api_evidence
from material_ingestion.sources.web import WebPdfDiscovery
from material_ingestion.services.web_stage_event_service import append_discovery_events
from material_ingestion.services.web_url_canonicalizer import canonicalize_url

logger = logging.getLogger("material_ingestion.web")


def _should_emit_discovery_debug(msg: str) -> bool:
    verbose_network = (os.getenv("MATERIAL_INGESTION_DEBUG_NETWORK", "0") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    noisy_prefixes = (
        "discovery: js response ",
        "discovery: json body acquired ",
        "discovery: empty json body ",
    )
    if msg.startswith(noisy_prefixes) and not verbose_network:
        return False
    return True


def _log_discovery_progress(msg: str) -> None:
    # Normalize verbose discovery traces into structured log schema.
    crawl_match = re.match(r"^discovery:\s+crawling page (\d+)/(\d+):\s+(.+)$", msg)
    if crawl_match:
        logger.debug(
            "event=discover_progress phase=crawl action=page_started page_index=%s page_total=%s page_url=%s",
            crawl_match.group(1),
            crawl_match.group(2),
            crawl_match.group(3),
        )
        return
    done_match = re.match(
        r"^discovery:\s+page done links=(\d+)\s+new_candidates=(\d+)\s+queue=(\d+)\s+total_candidates=(\d+)$",
        msg,
    )
    if done_match:
        logger.debug(
            "event=discover_progress phase=crawl action=page_finished links=%s new_candidates=%s queue=%s total_candidates=%s",
            done_match.group(1),
            done_match.group(2),
            done_match.group(3),
            done_match.group(4),
        )
        return
    log_event(logger, logging.DEBUG, "discover_progress", message=msg)


def run_web_discover_pdfs(args: argparse.Namespace) -> int:
    ingest_source = args.ingest_source
    ingest_locator = args.ingest_locator or args.seed_url
    ingest_batch_id = args.ingest_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    orchestration_id = getattr(args, "orchestration_id", None) or ingest_batch_id

    discovery = WebPdfDiscovery()
    log_event(
        logger,
        logging.INFO,
        "discover_started",
        seed_url=args.seed_url,
        max_pages=args.max_pages,
        same_domain_only=(not args.cross_domain),
    )
    pages, candidates, fetch_observations = discovery.discover(
        seed_url=args.seed_url,
        same_domain_only=not args.cross_domain,
        max_pages=args.max_pages,
        strategy="auto",
        progress=lambda msg: _log_discovery_progress(msg) if _should_emit_discovery_debug(msg) else None,
    )

    candidate_rows = [
        {
            "source_page_url": c.source_page_url,
            "pdf_url": c.pdf_url,
            "canonical_pdf_url": canonicalize_url(c.pdf_url),
            "anchor_text": c.anchor_text,
            "score": c.score,
            "reason": c.reason,
        }
        for c in candidates
    ]
    page_class_counts: dict[str, int] = {}
    for p in pages:
        cls = str(p.get("page_class", "indexable"))
        page_class_counts[cls] = page_class_counts.get(cls, 0) + 1
    exporter = RawWebDbExporter(
        ingest_source=ingest_source,
        ingest_locator=ingest_locator,
        ingest_batch_id=ingest_batch_id,
    )
    page_count = exporter.export_pages(pages)
    page_observation_count = exporter.export_page_observations(
        [
            {
                "page_url": str(p.get("url", "")),
                "page_title": str(p.get("page_title", "")),
                "text_excerpt": str(p.get("text_excerpt", "")),
                "raw_html": str(p.get("raw_html", "")),
                "raw_html_sha256": str(p.get("raw_html_sha256", "")),
                "raw_html_bytes": int(p.get("raw_html_bytes", 0)),
                "raw_html_truncated": bool(p.get("raw_html_truncated", False)),
                "anchor_count": int(p.get("anchor_count", 0)),
                "input_count": int(p.get("input_count", 0)),
                "button_count": int(p.get("button_count", 0)),
                "form_count": int(p.get("form_count", 0)),
                "has_download_keywords": bool(p.get("has_download_keywords", False)),
                "payload_json": json.dumps(
                    {
                        "status_code": int(p.get("status_code", 0)),
                        "content_type": str(p.get("content_type", "")),
                        "crawl_ok": bool(p.get("crawl_ok", False)),
                        "page_class": str(p.get("page_class", "indexable")),
                        "snapshot_profile": str(p.get("snapshot_profile", "standard")),
                        "snapshot_html_max_bytes": int(p.get("snapshot_html_max_bytes", 0)),
                        "links_sample": p.get("links_sample", []),
                        "links_sample_truncated": bool(p.get("links_sample_truncated", False)),
                        "raw_html_sha256": str(p.get("raw_html_sha256", "")),
                        "raw_html_bytes": int(p.get("raw_html_bytes", 0)),
                        "raw_html_truncated": bool(p.get("raw_html_truncated", False)),
                    },
                    sort_keys=True,
                ),
            }
            for p in pages
        ]
    )
    candidate_count = exporter.export_candidates(candidate_rows)
    fetch_observation_count = exporter.export_fetch_xhr_observations([
        {
            "source_page_url": o.source_page_url,
            "response_url": o.response_url,
            "resource_type": o.resource_type,
            "status_code": o.status_code,
            "content_type": o.content_type,
            "is_json": o.is_json,
            "extracted_urls_json": json.dumps(o.extracted_urls, sort_keys=True),
            "extracted_url_count": len(o.extracted_urls),
        }
        for o in fetch_observations
    ])
    api_evidence_summary = {"api_endpoints": 0, "api_page_fetches": 0, "api_document_candidates": 0}
    try:
        api_evidence_summary = persist_api_evidence(
            orchestration_id=orchestration_id,
            ingest_batch_id=ingest_batch_id,
            observations=fetch_observations,
        )
    except Exception as exc:
        log_event(logger, logging.WARNING, "api_evidence_write_failed", error_class=exc.__class__.__name__, error=str(exc))
    try:
        append_discovery_events(
            [
                {
                    "orchestration_id": orchestration_id,
                    "ingest_batch_id": ingest_batch_id,
                    "event_type": "discover_completed",
                    "page_url": args.seed_url,
                    "payload": {
                        "crawled_pages": page_count,
                        "page_observations": page_observation_count,
                        "pdf_candidates": candidate_count,
                        "fetch_xhr_observations": fetch_observation_count,
                    },
                }
            ]
            + [
                {
                    "orchestration_id": orchestration_id,
                    "ingest_batch_id": ingest_batch_id,
                    "event_type": "page_crawled",
                    "page_url": str(p.get("url", "")),
                    "payload": {
                        "status_code": int(p.get("status_code", 0)),
                        "content_type": str(p.get("content_type", "")),
                        "crawl_ok": bool(p.get("crawl_ok", False)),
                    },
                }
                for p in pages
            ]
        )
    except Exception as exc:
        log_event(
            logger,
            logging.WARNING,
            "stage_event_write_failed",
            stage="discovery",
            error_class=exc.__class__.__name__,
            error=str(exc),
        )

    if args.output:
        out = {
            "seed_url": args.seed_url,
            "ingest_batch_id": ingest_batch_id,
            "pages": pages,
            "candidates": candidate_rows,
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    log_event(
        logger,
        logging.INFO,
        "discover_completed",
        batch_id=ingest_batch_id,
        crawled_pages=page_count,
        page_observations=page_observation_count,
        pdf_candidates=candidate_count,
        fetch_xhr_observations=fetch_observation_count,
        api_endpoints=api_evidence_summary["api_endpoints"],
        api_page_fetches=api_evidence_summary["api_page_fetches"],
        api_document_candidates=api_evidence_summary["api_document_candidates"],
        page_classes=json.dumps(page_class_counts, sort_keys=True),
    )
    return 0
