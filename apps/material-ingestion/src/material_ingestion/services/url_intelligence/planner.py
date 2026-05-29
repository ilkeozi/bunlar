from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from .db_export_models import AnalysisDataset, ExtractedLinkRow
from .decision import decide
from .models import NextAction, PatternStats, SourceContext, URLDecision, URLRole
from .stats_builder import (
    build_host_stats,
    build_pattern_stats,
    build_template_observations,
    build_uri_contexts,
)
from .template_inference import infer_templates
from .uri_parser import parse_url


# ---------------------------------------------------------------------------
# Input / configuration models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class CrawlBudget:
    max_static_gets: int = 200
    max_renders: int = 20
    max_document_fetches: int = 100
    max_static_gets_per_host: int = 50
    max_renders_per_host: int = 5
    max_static_gets_per_template: int = 30
    max_renders_per_template: int = 3
    min_host_exploration_slots: int = 5
    min_template_sample_size: int = 5
    hard_stop_sample_size: int = 50


@dataclass(slots=True)
class PlanCandidate:
    uri_identity_id: int
    canonical_uri: str
    source_type: str
    host: str
    inferred_templates: list[str]
    source_uri_identity_id: int | None = None
    anchor_text: str | None = None
    existing_frontier_state: str | None = None


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


@dataclass
class BudgetUsage:
    static_gets: int = 0
    renders: int = 0
    document_fetches: int = 0


@dataclass
class CrawlPlan:
    selected: list[tuple[PlanCandidate, URLDecision]] = field(default_factory=list)
    deferred: list[tuple[PlanCandidate, URLDecision]] = field(default_factory=list)
    # Globally bad URLs (NOISE/ASSET/score < -20).  These are never useful.
    rejected: list[tuple[PlanCandidate, URLDecision]] = field(default_factory=list)
    # URLs where only static GET is stopped due to low yield.
    # The URL may still be valid for fetch_document / render_sample / api_discovery.
    stopped_static_get: list[tuple[PlanCandidate, URLDecision]] = field(default_factory=list)
    budget_usage: BudgetUsage = field(default_factory=BudgetUsage)
    host_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    template_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    reason_summary: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _best_anchor(links: list[ExtractedLinkRow], target_uid: int) -> str:
    """Return the most informative anchor text pointing to target_uid."""
    candidates = [lnk.anchor_text for lnk in links if lnk.target_uri_identity_id == target_uid and lnk.anchor_text]
    if not candidates:
        return ""
    # Prefer longer anchor texts (more descriptive)
    return max(candidates, key=len)


def _make_source_context(
    candidate: PlanCandidate,
    ctx_map: dict,
    all_links: list[ExtractedLinkRow],
) -> SourceContext:
    is_sitemap = candidate.source_type == "sitemap"
    has_en_hreflang = False
    source_page_role = ""
    produced_docs = False

    uri_ctx = ctx_map.get(candidate.uri_identity_id)
    if uri_ctx is not None:
        has_en_hreflang = uri_ctx.has_english_hreflang
        if is_sitemap and not has_en_hreflang:
            has_en_hreflang = uri_ctx.has_english_hreflang

    # Infer source page role from source URI context
    if candidate.source_uri_identity_id is not None:
        src_ctx = ctx_map.get(candidate.source_uri_identity_id)
        if src_ctx is not None:
            if src_ctx.candidate_document_count > 0:
                produced_docs = True
            # If source page itself looks like a listing, propagate that signal
            try:
                src_parsed = parse_url(src_ctx.canonical_uri)
                src_templates = infer_templates(src_parsed)
                if src_templates:
                    # Simple heuristic: if source template has "download" or "document"
                    tpl = src_templates[-1].template.lower()
                    if any(tok in tpl for tok in ("download", "document", "resource", "literature")):
                        source_page_role = "document_listing"
            except Exception:
                pass

    anchor = candidate.anchor_text or _best_anchor(all_links, candidate.uri_identity_id)

    return SourceContext(
        source_type=candidate.source_type,
        anchor_text=anchor,
        source_page_role=source_page_role,
        has_english_hreflang=has_en_hreflang,
        came_from_sitemap=is_sitemap,
        source_page_produced_document_candidates=produced_docs,
    )


def _primary_template(uri: str) -> str:
    """Return the medium-level template path for a URI, or empty string on failure."""
    try:
        parsed = parse_url(uri)
        templates = infer_templates(parsed)
        medium = next((t for t in templates if t.level == "medium"), None)
        if medium:
            return medium.template
        if templates:
            return templates[0].template
    except Exception:
        pass
    return ""


_TRACKING_PARAMS_EXACT: frozenset[str] = frozenset({
    "vid", "fbclid", "gclid", "sid", "session", "token",
})
_TRACKING_PARAMS_PREFIX: tuple[str, ...] = ("utm_", "cache")


def _strip_tracking_params(url: str) -> str:
    """Return url with well-known duplicate-producing query params removed."""
    parsed = urlparse(url)
    if not parsed.query:
        return url
    qs = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {
        k: v for k, v in qs.items()
        if k.lower() not in _TRACKING_PARAMS_EXACT
        and not any(k.lower().startswith(pfx) for pfx in _TRACKING_PARAMS_PREFIX)
    }
    new_query = urlencode(filtered, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _is_document_content(content_type: str) -> bool:
    """Return True when the content-type indicates a directly-fetched document."""
    ct = content_type.lower()
    return (
        "pdf" in ct
        or "msword" in ct
        or "vnd.openxmlformats" in ct
        or "vnd.ms-excel" in ct
        or "vnd.ms-powerpoint" in ct
    )


def _build_candidates(
    dataset: AnalysisDataset,
    ctx_map: dict,
) -> list[PlanCandidate]:
    """Build PlanCandidates for URIs that have not been fully resolved.

    A URI is considered done (skipped) only when the static GET succeeded AND
    render was not required.  URIs where static GET succeeded but
    render_needed=True remain eligible for render_sample / api_discovery
    planning.  HEAD failures, timeouts, and other non-success outcomes are
    always kept so the planner can recommend a follow-up action.
    """

    sitemap_uri_ids: set[int] = {e.uri_identity_id for e in dataset.sitemap_entries}
    links_to_uri: dict[int, list[ExtractedLinkRow]] = defaultdict(list)
    for lnk in dataset.extracted_links:
        links_to_uri[lnk.target_uri_identity_id].append(lnk)

    candidates: list[PlanCandidate] = []

    for uri in dataset.uri_identities:
        ctx = ctx_map.get(uri.id)
        if ctx is None:
            continue

        if ctx.latest_fetch_outcome == "success":
            # Document already downloaded — nothing more to do.
            if ctx.content_type and _is_document_content(ctx.content_type):
                continue
            # Static GET succeeded and rendering is not needed — fully resolved.
            # render_needed=None means no page_text row was recorded, which we
            # treat the same as False (no render signal → done).
            if ctx.render_needed is not True:
                continue
            # render_needed=True after a static GET: the page needs JS rendering.
            # Fall through so the planner can recommend render_sample / api_discovery.

        # Skip if explicitly rejected in crawl_decisions
        if any(
            d.uri_identity_id == uri.id and "reject" in d.reason_code.lower()
            for d in dataset.crawl_decisions
        ):
            continue

        # Determine source_type
        if uri.id in sitemap_uri_ids:
            source_type = "sitemap"
        elif uri.id in links_to_uri:
            source_type = "extracted_link"
        else:
            source_type = "manual_seed"

        # Best source page
        inbound = links_to_uri.get(uri.id, [])
        source_uid = inbound[0].source_uri_identity_id if inbound else None
        anchor = _best_anchor(dataset.extracted_links, uri.id)

        try:
            parsed = parse_url(uri.canonical_uri)
            templates = infer_templates(parsed)
            template_strs = [t.template for t in templates]
        except Exception:
            template_strs = []

        candidates.append(
            PlanCandidate(
                uri_identity_id=uri.id,
                canonical_uri=uri.canonical_uri,
                source_type=source_type,
                host=ctx.hostname,
                inferred_templates=template_strs,
                source_uri_identity_id=source_uid,
                anchor_text=anchor or None,
                existing_frontier_state=ctx.frontier_state,
            )
        )

    return candidates


# ---------------------------------------------------------------------------
# Budget allocator
# ---------------------------------------------------------------------------


_STATIC_ACTIONS: frozenset[NextAction] = frozenset({
    NextAction.INSPECT_STATIC_HTML,
    NextAction.SAMPLE_STATIC_HTML,
    NextAction.API_DISCOVERY,
})

_RENDER_ACTIONS: frozenset[NextAction] = frozenset({
    NextAction.RENDER_SAMPLE,
})


def _allocate(
    ranked: list[tuple[PlanCandidate, URLDecision]],
    budget: CrawlBudget,
    host_explored_count: dict[str, int],
) -> CrawlPlan:
    plan = CrawlPlan()
    bu = plan.budget_usage

    host_static: dict[str, int] = defaultdict(int)
    host_render: dict[str, int] = defaultdict(int)
    host_doc: dict[str, int] = defaultdict(int)
    tmpl_static: dict[str, int] = defaultdict(int)
    tmpl_render: dict[str, int] = defaultdict(int)
    # Track canonical (tracking-param-stripped) document URLs to avoid
    # counting the same document twice against the budget.
    seen_doc_keys: set[str] = set()

    for candidate, decision in ranked:
        host = candidate.host
        # Use the most-abstract (medium) template for cap grouping so that all
        # URLs like /en/products/1234 and /en/products/5678 share one bucket.
        template = candidate.inferred_templates[-1] if candidate.inferred_templates else ""
        action = decision.next_action

        # Count reason codes for summary
        for rc in decision.reason_codes:
            plan.reason_summary[rc] = plan.reason_summary.get(rc, 0) + 1

        # --- GLOBAL REJECT: noise/asset/score < -20 — never useful ---
        if action == NextAction.REJECT:
            plan.rejected.append((candidate, decision))
            continue

        # --- STOP_STATIC_GET: only static GET is low-yield for this template.
        # The URL itself is not globally bad; render / doc / api paths remain open.
        if action == NextAction.STOP_STATIC_GET:
            plan.stopped_static_get.append((candidate, decision))
            continue

        # --- DOCUMENT fetch ---
        if action == NextAction.FETCH_DOCUMENT:
            doc_key = _strip_tracking_params(candidate.canonical_uri)
            if doc_key in seen_doc_keys:
                # Same document reachable via a tracking-param variant — skip
                plan.deferred.append((candidate, decision))
            elif bu.document_fetches >= budget.max_document_fetches:
                plan.deferred.append((candidate, decision))
            else:
                seen_doc_keys.add(doc_key)
                bu.document_fetches += 1
                host_doc[host] += 1
                plan.selected.append((candidate, decision))
            continue

        # --- STATIC GET actions ---
        if action in _STATIC_ACTIONS:
            # Effective per-host cap: relax for unexplored hosts
            explored = host_explored_count.get(host, 0)
            effective_host_cap = max(
                budget.max_static_gets_per_host,
                budget.min_host_exploration_slots - explored
                if explored < budget.min_host_exploration_slots else 0,
            )

            if (
                bu.static_gets >= budget.max_static_gets
                or host_static[host] >= effective_host_cap
                or tmpl_static[template] >= budget.max_static_gets_per_template
            ):
                plan.deferred.append((candidate, decision))
            else:
                bu.static_gets += 1
                host_static[host] += 1
                tmpl_static[template] += 1
                plan.selected.append((candidate, decision))
            continue

        # --- RENDER actions ---
        if action in _RENDER_ACTIONS:
            if (
                bu.renders >= budget.max_renders
                or host_render[host] >= budget.max_renders_per_host
                or tmpl_render[template] >= budget.max_renders_per_template
            ):
                plan.deferred.append((candidate, decision))
            else:
                bu.renders += 1
                host_render[host] += 1
                tmpl_render[template] += 1
                plan.selected.append((candidate, decision))
            continue

        # --- DEFER ---
        plan.deferred.append((candidate, decision))

    # Expose per-host and per-template usage in the plan output
    for h in set(list(host_static) + list(host_render) + list(host_doc)):
        plan.host_usage[h] = {
            "static_gets": host_static[h],
            "renders": host_render[h],
            "document_fetches": host_doc[h],
        }
    for t in set(list(tmpl_static) + list(tmpl_render)):
        plan.template_usage[t] = {
            "static_gets": tmpl_static[t],
            "renders": tmpl_render[t],
        }

    return plan


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def plan_from_dataset(
    dataset: AnalysisDataset,
    budget: CrawlBudget,
    crawl_run_id: int | None = None,
) -> CrawlPlan:
    """Produce a budget-aware crawl plan from exported DB rows.

    Steps
    -----
    1. Build URI contexts from all exported tables.
    2. Build per-pattern stats from historical fetch/page_text/candidate rows.
    3. Build PlanCandidates for every URI that has not been successfully fetched.
    4. For each candidate, call ``decide()`` with the best available SourceContext
       and PatternStats.
    5. Rank by (technical_document first, then final_score descending) and
       allocate against the budget, enforcing per-host and per-template caps.
    """
    ctx_map = build_uri_contexts(dataset)

    observations = build_template_observations(dataset)
    pattern_stats_map = build_pattern_stats(observations)
    host_stats_map = build_host_stats(dataset, observations)

    # How many URIs have already been explored per host (for minimum-slot logic)
    host_explored_count: dict[str, int] = {
        hostname: hs.fetched_count for hostname, hs in host_stats_map.items()
    }

    candidates = _build_candidates(dataset, ctx_map)

    # --- Score every candidate ---
    scored: list[tuple[PlanCandidate, URLDecision]] = []
    for candidate in candidates:
        template = _primary_template(candidate.canonical_uri)
        stats = pattern_stats_map.get((candidate.host, template, "static_get"))

        src_ctx = _make_source_context(candidate, ctx_map, dataset.extracted_links)

        decision = decide(candidate.canonical_uri, context=src_ctx, stats=stats)
        scored.append((candidate, decision))

    # --- Rank: tech docs first, then by final_score descending ---
    def _rank_key(item: tuple[PlanCandidate, URLDecision]) -> tuple[int, int]:
        _, dec = item
        is_tech_doc = 1 if dec.url_role == URLRole.TECHNICAL_DOCUMENT else 0
        return (-is_tech_doc, -dec.scores.final_score)

    scored.sort(key=_rank_key)

    return _allocate(scored, budget, host_explored_count)
