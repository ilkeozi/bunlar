from __future__ import annotations

from .db_export_models import (
    AnalysisDataset,
    CandidateDocumentRow,
    CrawlDecisionRow,
    CrawlHostRow,
    ExtractedLinkRow,
    FrontierItemRow,
    HttpFetchAttemptRow,
    HttpRepresentationRow,
    PageTextRow,
    RobotsPolicyRow,
    SitemapAlternateRow,
    SitemapEntryRow,
    UriIdentityRow,
)
from material_ingestion.db.models import (
    RawWebCandidateDocument,
    RawWebCrawlDecision,
    RawWebCrawlHost,
    RawWebCrawlRun,
    RawWebExtractedLink,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebPageText,
    RawWebRobotsPolicy,
    RawWebSitemapAlternate,
    RawWebSitemapEntry,
    RawWebUriIdentity,
)


def _resolve_crawl_run_id(session, crawl_run_key: str) -> int:
    row = (
        session.query(RawWebCrawlRun)
        .filter(RawWebCrawlRun.run_key == crawl_run_key)
        .first()
    )
    if row is None:
        raise ValueError(f"No crawl run found with run_key={crawl_run_key!r}")
    return int(row.id)


def _load_frontier_items(
    session, crawl_run_id: int, limit: int | None
) -> list[FrontierItemRow]:
    q = session.query(RawWebFrontierItem).filter(
        RawWebFrontierItem.crawl_run_id == crawl_run_id
    )
    if limit is not None:
        q = q.limit(limit)
    return [
        FrontierItemRow(
            id=int(r.id),
            uri_identity_id=int(r.uri_identity_id),
            crawl_run_id=int(r.crawl_run_id),
            state=r.state or "",
            priority=int(r.priority or 0),
            state_reason_code=r.state_reason_code or "",
            scheduled_at=r.scheduled_at,
            updated_at=r.updated_at,
        )
        for r in q.all()
    ]


def _load_fetch_attempts(session, crawl_run_id: int) -> list[HttpFetchAttemptRow]:
    rows = (
        session.query(RawWebHttpFetchAttempt)
        .filter(RawWebHttpFetchAttempt.crawl_run_id == crawl_run_id)
        .all()
    )
    return [
        HttpFetchAttemptRow(
            id=int(r.id),
            uri_identity_id=int(r.uri_identity_id),
            crawl_run_id=int(r.crawl_run_id),
            status_code=int(r.status_code or 0),
            outcome=r.outcome or "",
            reason_code=r.reason_code or "",
            requested_url=r.requested_url or "",
            final_url=r.final_url or "",
            redirect_count=int(r.redirect_count or 0),
            ttfb_ms=int(r.ttfb_ms or 0),
            read_ms=int(r.read_ms or 0),
            total_ms=int(r.total_ms or 0),
            requested_at=r.requested_at,
            completed_at=r.completed_at,
        )
        for r in rows
    ]


def _load_uri_identities(session, uri_ids: set[int]) -> list[UriIdentityRow]:
    if not uri_ids:
        return []
    rows = (
        session.query(RawWebUriIdentity)
        .filter(RawWebUriIdentity.id.in_(uri_ids))
        .all()
    )
    return [
        UriIdentityRow(
            id=int(r.id),
            canonical_uri=r.canonical_uri or "",
            normalized_hash=r.normalized_hash or "",
            host_id=int(r.host_id),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


def _load_hosts(session, host_ids: set[int]) -> list[CrawlHostRow]:
    if not host_ids:
        return []
    rows = (
        session.query(RawWebCrawlHost)
        .filter(RawWebCrawlHost.id.in_(host_ids))
        .all()
    )
    return [
        CrawlHostRow(
            id=int(r.id),
            hostname=r.hostname or "",
            source_type=r.source_type or "",
            discovery_source=r.discovery_source or "",
            allowlist_match=bool(r.allowlist_match),
            auto_crawl_enabled=bool(r.auto_crawl_enabled),
            first_seen_at=r.first_seen_at,
            last_seen_at=r.last_seen_at,
        )
        for r in rows
    ]


def _load_representations(
    session, fetch_attempt_ids: set[int]
) -> list[HttpRepresentationRow]:
    if not fetch_attempt_ids:
        return []
    rows = (
        session.query(RawWebHttpRepresentation)
        .filter(RawWebHttpRepresentation.fetch_attempt_id.in_(fetch_attempt_ids))
        .all()
    )
    return [
        HttpRepresentationRow(
            id=int(r.id),
            fetch_attempt_id=int(r.fetch_attempt_id),
            content_type=r.content_type or "",
            content_length=int(r.content_length or 0),
            content_language=r.content_language or "",
            content_encoding=r.content_encoding or "",
        )
        for r in rows
    ]


def _load_page_texts(session, fetch_attempt_ids: set[int]) -> list[PageTextRow]:
    if not fetch_attempt_ids:
        return []
    rows = (
        session.query(RawWebPageText)
        .filter(RawWebPageText.fetch_attempt_id.in_(fetch_attempt_ids))
        .all()
    )
    return [
        PageTextRow(
            id=int(r.id),
            fetch_attempt_id=int(r.fetch_attempt_id),
            title=r.title or "",
            meta_description=r.meta_description or "",
            h1=r.h1 or "",
            lang=r.lang or "",
            raw_html_length=int(r.raw_html_length or 0),
            text_length=int(r.text_length or 0),
            text_ratio=float(r.text_ratio or 0.0),
            render_needed=bool(r.render_needed),
            extracted_at=r.extracted_at,
        )
        for r in rows
    ]


def _load_extracted_links(session, uri_ids: set[int]) -> list[ExtractedLinkRow]:
    if not uri_ids:
        return []
    rows = (
        session.query(RawWebExtractedLink)
        .filter(
            RawWebExtractedLink.source_uri_identity_id.in_(uri_ids)
            | RawWebExtractedLink.target_uri_identity_id.in_(uri_ids)
        )
        .all()
    )
    return [
        ExtractedLinkRow(
            id=int(r.id),
            source_uri_identity_id=int(r.source_uri_identity_id),
            target_uri_identity_id=int(r.target_uri_identity_id),
            rel=r.rel or "",
            anchor_text=r.anchor_text or "",
            discovered_at=r.discovered_at,
        )
        for r in rows
    ]


def _load_candidate_documents(session, uri_ids: set[int]) -> list[CandidateDocumentRow]:
    if not uri_ids:
        return []
    rows = (
        session.query(RawWebCandidateDocument)
        .filter(
            RawWebCandidateDocument.uri_identity_id.in_(uri_ids)
            | RawWebCandidateDocument.source_uri_identity_id.in_(uri_ids)
        )
        .all()
    )
    return [
        CandidateDocumentRow(
            id=int(r.id),
            uri_identity_id=int(r.uri_identity_id),
            source_uri_identity_id=int(r.source_uri_identity_id),
            mime_type=r.mime_type or "",
            classification=r.classification or "new",
            decision_state=r.decision_state or "new",
            decision_reason_code=r.decision_reason_code or "",
            score=int(r.score or 0),
            distinct_source_count=int(r.distinct_source_count or 0),
            score_reason_json=r.score_reason_json or "{}",
        )
        for r in rows
    ]


def _load_crawl_decisions(session, crawl_run_id: int) -> list[CrawlDecisionRow]:
    rows = (
        session.query(RawWebCrawlDecision)
        .filter(RawWebCrawlDecision.crawl_run_id == crawl_run_id)
        .all()
    )
    return [
        CrawlDecisionRow(
            id=int(r.id),
            crawl_run_id=int(r.crawl_run_id),
            uri_identity_id=int(r.uri_identity_id) if r.uri_identity_id is not None else None,
            decision_type=r.decision_type or "",
            reason_code=r.reason_code or "",
            detail_json=r.detail_json or "{}",
            recorded_at=r.recorded_at,
        )
        for r in rows
    ]


def _load_sitemap_entries(session, uri_ids: set[int]) -> list[SitemapEntryRow]:
    if not uri_ids:
        return []
    rows = (
        session.query(RawWebSitemapEntry)
        .filter(RawWebSitemapEntry.uri_identity_id.in_(uri_ids))
        .all()
    )
    return [
        SitemapEntryRow(
            id=int(r.id),
            sitemap_source_id=int(r.sitemap_source_id),
            uri_identity_id=int(r.uri_identity_id),
            lastmod_at=r.lastmod_at,
            changefreq=r.changefreq,
            priority=float(r.priority) if r.priority is not None else None,
        )
        for r in rows
    ]


def _load_sitemap_alternates(
    session, sitemap_entry_ids: set[int]
) -> list[SitemapAlternateRow]:
    if not sitemap_entry_ids:
        return []
    rows = (
        session.query(RawWebSitemapAlternate)
        .filter(RawWebSitemapAlternate.sitemap_entry_id.in_(sitemap_entry_ids))
        .all()
    )
    return [
        SitemapAlternateRow(
            id=int(r.id),
            sitemap_entry_id=int(r.sitemap_entry_id),
            hreflang=r.hreflang or "",
            href=r.href or "",
        )
        for r in rows
    ]


def _load_robots_policies(session, host_ids: set[int]) -> list[RobotsPolicyRow]:
    if not host_ids:
        return []
    rows = (
        session.query(RawWebRobotsPolicy)
        .filter(RawWebRobotsPolicy.host_id.in_(host_ids))
        .all()
    )
    return [
        RobotsPolicyRow(
            id=int(r.id),
            host_id=int(r.host_id),
            fetch_status=r.fetch_status or "",
            policy_blob=r.policy_blob or "",
            evaluation_summary_json=r.evaluation_summary_json or "{}",
            fetched_at=r.fetched_at,
        )
        for r in rows
    ]


def load_analysis_dataset_from_db(
    session,
    *,
    crawl_run_key: str | None = None,
    crawl_run_id: int | None = None,
    include_all_uri_identities: bool = True,
    limit: int | None = None,
) -> AnalysisDataset:
    """Load an AnalysisDataset from the database for a specific crawl run.

    Uses separate normalized SELECTs rather than a large join so that tables
    with one-to-many relationships (fetch attempts × extracted links × candidate
    documents) do not multiply rows.

    Parameters
    ----------
    session:
        SQLAlchemy session (read-only use — no commit/flush/add/delete).
    crawl_run_key:
        Human-readable run key (e.g. "core_run_20260526_152345"). Resolved to
        crawl_run_id on first query.
    crawl_run_id:
        Numeric primary key of the crawl run. Provide this or crawl_run_key.
    include_all_uri_identities:
        When True (default), URI identities referenced by extracted links and
        candidate documents but not present in the frontier or fetch tables are
        also loaded. Set to False to restrict to URIs seen in the run itself.
    limit:
        Cap on the number of frontier items loaded. Useful for sampling in tests.
    """
    if crawl_run_key is not None and crawl_run_id is not None:
        raise ValueError("Provide crawl_run_key or crawl_run_id, not both.")
    if crawl_run_key is None and crawl_run_id is None:
        raise ValueError("One of crawl_run_key or crawl_run_id must be provided.")

    if crawl_run_key is not None:
        crawl_run_id = _resolve_crawl_run_id(session, crawl_run_key)

    # 1. Frontier items for this run
    frontier_items = _load_frontier_items(session, crawl_run_id, limit)
    frontier_uri_ids: set[int] = {fi.uri_identity_id for fi in frontier_items}

    # 2. Fetch attempts for this run
    fetch_attempts = _load_fetch_attempts(session, crawl_run_id)
    fetch_attempt_ids: set[int] = {fa.id for fa in fetch_attempts}
    fetch_uri_ids: set[int] = {fa.uri_identity_id for fa in fetch_attempts}

    # Seed URI set from frontier + fetch
    initial_uri_ids: set[int] = frontier_uri_ids | fetch_uri_ids

    # 3–4. Expand URI set by discovering IDs referenced in linked tables
    all_uri_ids: set[int] = set(initial_uri_ids)

    if include_all_uri_identities and initial_uri_ids:
        # Preliminary load of links and candidates to find referenced URI IDs
        for link in _load_extracted_links(session, initial_uri_ids):
            all_uri_ids.add(link.source_uri_identity_id)
            all_uri_ids.add(link.target_uri_identity_id)
        for doc in _load_candidate_documents(session, initial_uri_ids):
            all_uri_ids.add(doc.uri_identity_id)
            all_uri_ids.add(doc.source_uri_identity_id)

    # 5. URI identities for the full expanded set
    uri_identities = _load_uri_identities(session, all_uri_ids)
    host_ids: set[int] = {u.host_id for u in uri_identities}

    # 6. Crawl hosts
    hosts = _load_hosts(session, host_ids)

    # 7. Representations and page texts keyed by fetch attempt
    representations = _load_representations(session, fetch_attempt_ids)
    page_texts = _load_page_texts(session, fetch_attempt_ids)

    # 8. Extracted links for the full URI set (normalized — one row per link)
    extracted_links = _load_extracted_links(session, all_uri_ids)

    # 9. Candidate documents for the full URI set (one row per candidate)
    candidate_documents = _load_candidate_documents(session, all_uri_ids)

    # 10. Crawl decisions for this run
    crawl_decisions = _load_crawl_decisions(session, crawl_run_id)

    # 11. Sitemap entries for all loaded URI identities
    sitemap_entries = _load_sitemap_entries(session, all_uri_ids)
    sitemap_entry_ids: set[int] = {se.id for se in sitemap_entries}

    # 12. Sitemap alternates for loaded entries
    sitemap_alternates = _load_sitemap_alternates(session, sitemap_entry_ids)

    # 13. Robots policies for all loaded hosts
    robots_policies = _load_robots_policies(session, host_ids)

    return AnalysisDataset(
        uri_identities=uri_identities,
        hosts=hosts,
        frontier_items=frontier_items,
        fetch_attempts=fetch_attempts,
        representations=representations,
        page_texts=page_texts,
        extracted_links=extracted_links,
        candidate_documents=candidate_documents,
        crawl_decisions=crawl_decisions,
        sitemap_entries=sitemap_entries,
        sitemap_alternates=sitemap_alternates,
        robots_policies=robots_policies,
    )
