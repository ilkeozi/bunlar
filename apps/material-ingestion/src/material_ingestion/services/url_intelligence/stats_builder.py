from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .db_export_models import (
    AnalysisDataset,
    CandidateDocumentRow,
    HttpFetchAttemptRow,
)
from .models import PatternStats
from .template_inference import infer_templates
from .uri_parser import parse_url


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class UriContext:
    """All known facts about one URI, assembled from multiple exported tables."""

    uri_identity_id: int
    canonical_uri: str
    host_id: int
    hostname: str

    # frontier
    frontier_state: str | None = None
    frontier_priority: int = 0

    # latest fetch
    latest_fetch_outcome: str | None = None
    latest_fetch_status_code: int = 0
    latest_total_ms: int = 0

    # representation
    content_type: str = ""
    content_length: int = 0
    content_language: str = ""

    # page_text
    text_length: int = 0
    text_ratio: float = 0.0
    render_needed: bool | None = None  # None = not yet fetched

    # graph
    extracted_link_count: int = 0     # outbound links found ON this page
    inbound_link_count: int = 0       # pages that link TO this URI

    # candidate documents
    candidate_document_count: int = 0
    technical_candidate_document_count: int = 0

    # sitemap
    is_in_sitemap: bool = False
    has_english_hreflang: bool = False


@dataclass
class TemplateObservation:
    """One observed fetch outcome, classified into a host+template bucket."""

    uri_identity_id: int
    host: str
    template: str          # medium-level template path
    template_level: str    # "medium", "specific", "exact"
    fetch_method: str      # "static_get" | "document_fetch"
    url_role: str          # from URLRole enum value
    outcome: str           # "success" | "error" | "not_fetched"
    total_ms: int = 0
    render_needed: bool = False
    text_ratio: float = 0.0
    extracted_link_count: int = 0
    candidate_document_count: int = 0
    technical_candidate_document_count: int = 0
    noise_candidate_count: int = 0


@dataclass
class HostStats:
    hostname: str
    total_uri_count: int = 0
    fetched_count: int = 0
    candidate_document_count: int = 0
    technical_document_count: int = 0
    render_needed_count: int = 0
    total_ms_sum: int = 0
    fetch_count_for_ms: int = 0
    has_sitemap: bool = False
    total_inbound_links: int = 0

    @property
    def avg_total_ms(self) -> float:
        if self.fetch_count_for_ms == 0:
            return 0.0
        return self.total_ms_sum / self.fetch_count_for_ms


# ---------------------------------------------------------------------------
# Internal index helpers
# ---------------------------------------------------------------------------


def _index_one(rows: list, key_fn) -> dict:
    """Build a dict mapping key → first row (most recent by insertion order)."""
    result: dict = {}
    for row in rows:
        k = key_fn(row)
        if k not in result:
            result[k] = row
    return result


def _index_last(rows: list, key_fn) -> dict:
    """Build a dict mapping key → last row (by id, descending = most recent)."""
    result: dict = {}
    for row in rows:
        k = key_fn(row)
        existing = result.get(k)
        if existing is None or row.id > existing.id:
            result[k] = row
    return result


def _group_by(rows: list, key_fn) -> dict:
    result: dict[object, list] = defaultdict(list)
    for row in rows:
        result[key_fn(row)].append(row)
    return dict(result)


def _is_technical_candidate(doc: CandidateDocumentRow) -> bool:
    mime_lower = doc.mime_type.lower()
    cls_lower = doc.classification.lower()
    return "pdf" in mime_lower or "technical" in cls_lower


def _is_noise_candidate(doc: CandidateDocumentRow) -> bool:
    return doc.decision_state == "rejected" or doc.classification.lower() == "noise"


def _latest_attempt(attempts: list[HttpFetchAttemptRow]) -> HttpFetchAttemptRow | None:
    if not attempts:
        return None
    return max(attempts, key=lambda r: r.id)


# ---------------------------------------------------------------------------
# Public builder functions
# ---------------------------------------------------------------------------


def build_uri_contexts(dataset: AnalysisDataset) -> dict[int, UriContext]:
    """Assemble one UriContext per URI from all exported table rows."""

    hosts_by_id = {h.id: h for h in dataset.hosts}
    attempts_by_uri = _group_by(dataset.fetch_attempts, lambda r: r.uri_identity_id)
    repr_by_attempt = _index_last(dataset.representations, lambda r: r.fetch_attempt_id)
    text_by_attempt = _index_last(dataset.page_texts, lambda r: r.fetch_attempt_id)
    docs_by_uri = _group_by(dataset.candidate_documents, lambda r: r.uri_identity_id)
    links_from_uri = _group_by(dataset.extracted_links, lambda r: r.source_uri_identity_id)
    links_to_uri = _group_by(dataset.extracted_links, lambda r: r.target_uri_identity_id)
    sitemap_uris: set[int] = {e.uri_identity_id for e in dataset.sitemap_entries}
    sitemap_entry_by_uri = _group_by(dataset.sitemap_entries, lambda r: r.uri_identity_id)
    alts_by_entry = _group_by(dataset.sitemap_alternates, lambda r: r.sitemap_entry_id)
    frontier_by_uri = _group_by(dataset.frontier_items, lambda r: r.uri_identity_id)

    contexts: dict[int, UriContext] = {}

    for uri in dataset.uri_identities:
        host = hosts_by_id.get(uri.host_id)
        hostname = host.hostname if host else ""

        ctx = UriContext(
            uri_identity_id=uri.id,
            canonical_uri=uri.canonical_uri,
            host_id=uri.host_id,
            hostname=hostname,
        )

        # frontier — use latest (highest id) item
        fi_list = frontier_by_uri.get(uri.id, [])
        if fi_list:
            latest_fi = max(fi_list, key=lambda r: r.id)
            ctx.frontier_state = latest_fi.state
            ctx.frontier_priority = latest_fi.priority

        # fetch outcome — use latest attempt
        attempt = _latest_attempt(attempts_by_uri.get(uri.id, []))
        if attempt is not None:
            ctx.latest_fetch_outcome = attempt.outcome
            ctx.latest_fetch_status_code = attempt.status_code
            ctx.latest_total_ms = attempt.total_ms

            rep = repr_by_attempt.get(attempt.id)
            if rep is not None:
                ctx.content_type = rep.content_type
                ctx.content_length = rep.content_length
                ctx.content_language = rep.content_language

            pt = text_by_attempt.get(attempt.id)
            if pt is not None:
                ctx.text_length = pt.text_length
                ctx.text_ratio = pt.text_ratio
                ctx.render_needed = pt.render_needed

        # graph counts
        ctx.extracted_link_count = len(links_from_uri.get(uri.id, []))
        ctx.inbound_link_count = len(links_to_uri.get(uri.id, []))

        # candidate documents
        docs = docs_by_uri.get(uri.id, [])
        ctx.candidate_document_count = len(docs)
        ctx.technical_candidate_document_count = sum(
            1 for d in docs if _is_technical_candidate(d)
        )

        # sitemap
        ctx.is_in_sitemap = uri.id in sitemap_uris
        if ctx.is_in_sitemap:
            for entry in sitemap_entry_by_uri.get(uri.id, []):
                alts = alts_by_entry.get(entry.id, [])
                if any(a.hreflang.lower().startswith("en") for a in alts):
                    ctx.has_english_hreflang = True
                    break

        contexts[uri.id] = ctx

    return contexts


def build_template_observations(dataset: AnalysisDataset) -> list[TemplateObservation]:
    """Create one TemplateObservation per URI that has at least one fetch attempt."""

    contexts = build_uri_contexts(dataset)
    attempts_by_uri = _group_by(dataset.fetch_attempts, lambda r: r.uri_identity_id)
    repr_by_attempt = _index_last(dataset.representations, lambda r: r.fetch_attempt_id)
    text_by_attempt = _index_last(dataset.page_texts, lambda r: r.fetch_attempt_id)
    docs_by_uri = _group_by(dataset.candidate_documents, lambda r: r.uri_identity_id)
    links_from_uri = _group_by(dataset.extracted_links, lambda r: r.source_uri_identity_id)

    observations: list[TemplateObservation] = []

    for uri_id, ctx in contexts.items():
        if not attempts_by_uri.get(uri_id):
            continue

        attempt = _latest_attempt(attempts_by_uri[uri_id])
        if attempt is None:
            continue

        try:
            parsed = parse_url(ctx.canonical_uri)
        except Exception:
            continue

        templates = infer_templates(parsed)
        if not templates:
            continue

        # Choose medium template as the primary grouping key; fall back to first
        medium = next((t for t in templates if t.level == "medium"), templates[0])
        template_str = medium.template
        template_level = medium.level

        # Infer fetch method from content_type
        content_type = ""
        rep = repr_by_attempt.get(attempt.id)
        if rep is not None:
            content_type = rep.content_type.lower()
        is_document = "pdf" in content_type or any(
            ext in content_type
            for ext in ("msword", "vnd.openxmlformats", "vnd.ms-excel", "vnd.ms-powerpoint")
        )
        fetch_method = "document_fetch" if is_document else "static_get"

        # Render signal from page_text
        render_needed = False
        text_ratio = 0.0
        pt = text_by_attempt.get(attempt.id)
        if pt is not None:
            render_needed = pt.render_needed
            text_ratio = pt.text_ratio

        # Document counts
        docs = docs_by_uri.get(uri_id, [])
        tech_count = sum(1 for d in docs if _is_technical_candidate(d))
        noise_count = sum(1 for d in docs if _is_noise_candidate(d))

        # Link count from this page
        link_count = len(links_from_uri.get(uri_id, []))

        outcome = attempt.outcome if attempt.outcome else "success"

        # Quick URL role via decide() would be expensive in a loop; derive simply
        url_role = _quick_role(parsed)

        obs = TemplateObservation(
            uri_identity_id=uri_id,
            host=parsed.host,
            template=template_str,
            template_level=template_level,
            fetch_method=fetch_method,
            url_role=url_role,
            outcome=outcome,
            total_ms=attempt.total_ms,
            render_needed=render_needed,
            text_ratio=text_ratio,
            extracted_link_count=link_count,
            candidate_document_count=len(docs),
            technical_candidate_document_count=tech_count,
            noise_candidate_count=noise_count,
        )
        observations.append(obs)

    return observations


def build_pattern_stats(
    observations: list[TemplateObservation],
) -> dict[tuple[str, str, str], PatternStats]:
    """Aggregate TemplateObservations into PatternStats per (host, template, fetch_method)."""

    groups: dict[tuple[str, str, str], list[TemplateObservation]] = defaultdict(list)
    for obs in observations:
        key = (obs.host, obs.template, obs.fetch_method)
        groups[key].append(obs)

    result: dict[tuple[str, str, str], PatternStats] = {}
    for key, obs_list in groups.items():
        n = len(obs_list)
        render_needed = sum(1 for o in obs_list if o.render_needed)
        candidate_docs = sum(o.candidate_document_count for o in obs_list)
        tech_docs = sum(o.technical_candidate_document_count for o in obs_list)
        noise = sum(
            1 for o in obs_list
            if o.outcome != "success"
            or (o.render_needed and o.candidate_document_count == 0 and o.extracted_link_count == 0)
        )
        useful_links = sum(1 for o in obs_list if o.extracted_link_count > 0)
        success_count = sum(1 for o in obs_list if o.outcome == "success")
        total_ms_sum = sum(o.total_ms for o in obs_list)
        avg_ms = total_ms_sum / n if n > 0 else 0.0

        result[key] = PatternStats(
            sample_count=n,
            success_count=success_count,
            avg_total_ms=avg_ms,
            render_needed_count=render_needed,
            candidate_document_count=candidate_docs,
            technical_document_count=tech_docs,
            noise_count=noise,
            useful_link_count=useful_links,
        )

    return result


def build_host_stats(
    dataset: AnalysisDataset,
    observations: list[TemplateObservation],
) -> dict[str, HostStats]:
    """Compute per-host aggregate stats from dataset rows and observations."""

    hosts_by_id = {h.id: h for h in dataset.hosts}
    sitemap_host_ids: set[int] = set()
    for entry in dataset.sitemap_entries:
        uri = next((u for u in dataset.uri_identities if u.id == entry.uri_identity_id), None)
        if uri is not None:
            sitemap_host_ids.add(uri.host_id)

    links_to_uri = _group_by(dataset.extracted_links, lambda r: r.target_uri_identity_id)
    uri_host_map = {u.id: u.host_id for u in dataset.uri_identities}

    # Initialise from host rows
    stats: dict[str, HostStats] = {}
    for host in dataset.hosts:
        stats[host.hostname] = HostStats(
            hostname=host.hostname,
            has_sitemap=host.id in sitemap_host_ids,
        )

    # Count URIs per host
    for uri in dataset.uri_identities:
        h = hosts_by_id.get(uri.host_id)
        if h and h.hostname in stats:
            stats[h.hostname].total_uri_count += 1

    # Aggregate inbound link counts (links pointing to URIs on this host)
    for target_uid, link_list in links_to_uri.items():
        host_id = uri_host_map.get(target_uid)
        if host_id is None:
            continue
        h = hosts_by_id.get(host_id)
        if h and h.hostname in stats:
            stats[h.hostname].total_inbound_links += len(link_list)

    # Aggregate from observations
    for obs in observations:
        if obs.host not in stats:
            stats[obs.host] = HostStats(hostname=obs.host)
        hs = stats[obs.host]
        if obs.outcome == "success":
            hs.fetched_count += 1
            hs.total_ms_sum += obs.total_ms
            hs.fetch_count_for_ms += 1
        hs.candidate_document_count += obs.candidate_document_count
        hs.technical_document_count += obs.technical_candidate_document_count
        if obs.render_needed:
            hs.render_needed_count += 1

    return stats


# ---------------------------------------------------------------------------
# Internal helper — cheap URL role approximation (avoids calling decide() in
# tight loops while preserving document / asset / noise distinction)
# ---------------------------------------------------------------------------


def _quick_role(parsed) -> str:  # type: ignore[type-arg]
    from .models import SegmentKind

    for seg in parsed.segments:
        if seg.kind == SegmentKind.TECHNICAL_DOCUMENT_FILE:
            return "technical_document"
        if seg.kind == SegmentKind.ASSET_FILE:
            return "asset"
        if seg.kind == SegmentKind.DOCUMENT_FILE:
            return "document"
    return "generic_html"
