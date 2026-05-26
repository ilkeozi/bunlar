from __future__ import annotations

from collections.abc import Callable
import logging
import os
import re

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebFrontierItem,
    RawWebSitemapAlternate,
    RawWebSitemapEntry,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_frontier_score_rule_service import list_frontier_score_rules
from material_ingestion.services.web_crawl_frontier_service import ensure_crawl_run

logger = logging.getLogger("material_ingestion.web")


def _compile_rule(match_type: str, pattern: str):
    normalized = (match_type or "").strip().lower()
    if normalized == "contains":
        needle = pattern.lower()
        return lambda url: needle in url.lower()
    if normalized == "suffix":
        suffix = pattern.lower()
        return lambda url: url.lower().endswith(suffix)
    if normalized == "regex":
        compiled = re.compile(pattern, re.IGNORECASE)
        return lambda url: bool(compiled.search(url))
    return lambda _url: False


def build_frontier_from_sitemaps(
    *,
    run_key: str,
    sitemap_source_id: int | None = None,
    batch_size: int = 1000,
    heartbeat_callback: Callable[[], None] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> int:
    score_threshold = int(os.getenv("MATERIAL_INGESTION_FRONTIER_SCORE_THRESHOLD", "5"))
    low_score_mode = str(os.getenv("MATERIAL_INGESTION_FRONTIER_LOW_SCORE_MODE", "drop") or "drop").strip().lower()
    if low_score_mode not in {"drop", "defer"}:
        low_score_mode = "drop"
    configured_rules = list_frontier_score_rules(enabled_only=True)
    scoring_rules = [
        (int(r.weight), _compile_rule(r.match_type, r.pattern), str(r.match_type), str(r.pattern))
        for r in configured_rules
    ]
    crawl_run_id = ensure_crawl_run(run_key=run_key)
    session_factory = create_session_factory()
    inserted_frontier = 0
    processed_entries = 0
    last_seen_id = 0
    logger.info(
        "event=frontier_build_started run_key=%s sitemap_source_id=%s batch_size=%s",
        run_key,
        sitemap_source_id if sitemap_source_id is not None else "all",
        batch_size,
    )
    logger.info(
        "event=frontier_scoring_rules_loaded run_key=%s enabled_rules=%s score_threshold=%s",
        run_key,
        len(scoring_rules),
        score_threshold,
    )

    while True:
        with session_factory() as session:
            query = session.query(RawWebSitemapEntry).filter(RawWebSitemapEntry.id > last_seen_id)
            if sitemap_source_id is not None:
                query = query.filter(RawWebSitemapEntry.sitemap_source_id == sitemap_source_id)
            rows = query.order_by(RawWebSitemapEntry.id.asc()).limit(max(1, batch_size)).all()
            if not rows:
                break

            processed_entries += len(rows)
            row_ids = [int(r.id) for r in rows]
            last_seen_id = int(rows[-1].id)

            alternates = (
                session.query(
                    RawWebSitemapAlternate.sitemap_entry_id,
                    RawWebSitemapAlternate.hreflang,
                    RawWebSitemapAlternate.href,
                )
                .filter(RawWebSitemapAlternate.sitemap_entry_id.in_(row_ids))
                .all()
            )
            alternates_by_entry_id: dict[int, list[tuple[str, str]]] = {}
            for entry_id, hreflang, href in alternates:
                entry_key = int(entry_id)
                alternates_by_entry_id.setdefault(entry_key, []).append((str(hreflang or ""), str(href or "")))
            uri_by_entry_id = {
                int(entry_id): str(canonical_uri or "")
                for entry_id, canonical_uri in session.query(RawWebSitemapEntry.id, RawWebUriIdentity.canonical_uri)
                .join(RawWebUriIdentity, RawWebUriIdentity.id == RawWebSitemapEntry.uri_identity_id)
                .filter(RawWebSitemapEntry.id.in_(row_ids))
                .all()
            }
            allowed_entry_ids: set[int] = set()
            for row in rows:
                entry_id = int(row.id)
                canonical_uri = uri_by_entry_id.get(entry_id, "")
                entry_alternates = alternates_by_entry_id.get(entry_id, [])
                if not entry_alternates:
                    # No alternate metadata available: allow and rely on downstream scoring.
                    allowed_entry_ids.add(entry_id)
                    continue
                has_en_canonical = any(
                    hreflang.strip().lower() == "en" and href.strip() == canonical_uri
                    for hreflang, href in entry_alternates
                )
                if has_en_canonical:
                    allowed_entry_ids.add(entry_id)

            english_uri_identity_ids = [int(r.uri_identity_id) for r in rows if int(r.id) in allowed_entry_ids]

            existing = {
                int(row[0])
                for row in (
                    session.query(RawWebFrontierItem.uri_identity_id)
                    .filter(
                        RawWebFrontierItem.crawl_run_id == crawl_run_id,
                        RawWebFrontierItem.uri_identity_id.in_(english_uri_identity_ids),
                    )
                    .all()
                )
                if row and row[0] is not None
            }
            new_ids = sorted({uri_id for uri_id in english_uri_identity_ids if uri_id not in existing})
            if new_ids:
                identity_urls = {
                    int(uri_id): str(canonical_uri or "")
                    for uri_id, canonical_uri in session.query(RawWebUriIdentity.id, RawWebUriIdentity.canonical_uri)
                    .filter(RawWebUriIdentity.id.in_(new_ids))
                    .all()
                }
                frontier_rows: list[RawWebFrontierItem] = []
                for uri_id in new_ids:
                    url = identity_urls.get(int(uri_id), "")
                    score = 0
                    for weight, rule_fn, _match_type, _pattern in scoring_rules:
                        if rule_fn(url):
                            score += int(weight)
                    if score >= score_threshold:
                        frontier_rows.append(
                            RawWebFrontierItem(
                                uri_identity_id=uri_id,
                                crawl_run_id=crawl_run_id,
                                state="queued",
                                priority=score,
                                state_reason_code="from_sitemap_entry",
                            )
                        )
                    else:
                        if low_score_mode == "defer":
                            frontier_rows.append(
                                RawWebFrontierItem(
                                    uri_identity_id=uri_id,
                                    crawl_run_id=crawl_run_id,
                                    state="deferred",
                                    priority=score,
                                    state_reason_code="low_score_pre_fetch",
                                )
                            )
                if frontier_rows:
                    session.add_all(frontier_rows)
                    inserted_frontier += len(frontier_rows)
            session.commit()
        if heartbeat_callback:
            heartbeat_callback()
        if progress_callback:
            progress_callback(processed_entries, inserted_frontier)
        logger.info(
            "event=frontier_build_progress run_key=%s processed_entries=%s inserted_frontier=%s last_seen_sitemap_entry_id=%s score_threshold=%s low_score_mode=%s",
            run_key,
            processed_entries,
            inserted_frontier,
            last_seen_id,
            score_threshold,
            low_score_mode,
        )
    logger.info(
        "event=frontier_build_completed run_key=%s processed_entries=%s inserted_frontier=%s",
        run_key,
        processed_entries,
        inserted_frontier,
    )
    return inserted_frontier
