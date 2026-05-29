from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .comparison import CrawlPlanComparison, compare_actual_vs_planned
from .db_export_models import AnalysisDataset
from .db_loader import load_analysis_dataset_from_db
from .models import NextAction, URLDecision
from .planner import CrawlBudget, CrawlPlan, PlanCandidate, _strip_tracking_params, plan_from_dataset

_TOP_N = 20


@dataclass
class CrawlPlanningReport:
    """Structured result of running the URL intelligence planner against DB data."""

    crawl_run_id: int | None
    crawl_run_key: str | None
    budget: CrawlBudget

    # Budget counters: {"static_gets": N, "renders": N, "document_fetches": N}
    budget_usage: dict[str, int]

    # Per-host usage: {"hostname": {"static_gets": N, "renders": N, "document_fetches": N}}
    host_usage: dict[str, dict[str, int]]

    # Per-template usage: {"template": {"static_gets": N, "renders": N}}
    template_usage: dict[str, dict[str, int]]

    # Reason code → count across all planned URLs
    reason_summary: dict[str, int]

    # Aggregate stats per host/template (for reporting / export)
    host_summary: list[dict]
    template_summary: list[dict]

    # Full serialised lists — all items, not capped
    selected_summary: list[dict]
    deferred_summary: list[dict]
    # Globally bad URLs (NOISE / ASSET / score < -20) — never useful
    rejected_summary: list[dict]
    # URLs where only static GET is stopped; may still be valid for render/doc/API
    stopped_static_get_summary: list[dict]

    # Top-N subsets for quick inspection
    top_selected: list[dict]
    top_deferred: list[dict]
    top_rejected: list[dict]

    # Specialised views
    top_stopped_static_templates: list[dict]
    top_document_fetches: list[dict]

    # Raw plan retained for advanced use (e.g. compare_with).
    # Excluded from repr and equality checks to keep diffs readable.
    plan: CrawlPlan = field(repr=False, compare=False)

    # ---------------------------------------------------------------------------
    # Convenience accessors
    # ---------------------------------------------------------------------------

    def to_summary_dict(self) -> dict:
        """Return a flat dict suitable for notebooks or API responses."""
        return {
            "crawl_run_id": self.crawl_run_id,
            "crawl_run_key": self.crawl_run_key,
            "budget_usage": self.budget_usage,
            "reason_summary": self.reason_summary,
            "host_summary": self.host_summary,
            "template_summary": self.template_summary,
            "stopped_static_get_count": len(self.stopped_static_get_summary),
            "globally_rejected_count": len(self.rejected_summary),
        }

    def selected_as_dicts(self) -> list[dict]:
        return list(self.selected_summary)

    def deferred_as_dicts(self) -> list[dict]:
        return list(self.deferred_summary)

    def rejected_as_dicts(self) -> list[dict]:
        return list(self.rejected_summary)

    def stopped_static_get_as_dicts(self) -> list[dict]:
        """Return all URLs where static GET was stopped (method-specific, not global)."""
        return list(self.stopped_static_get_summary)

    def template_stats_as_dicts(self) -> list[dict]:
        return list(self.template_summary)

    def host_stats_as_dicts(self) -> list[dict]:
        return list(self.host_summary)

    def compare_with(self, dataset: AnalysisDataset) -> CrawlPlanComparison:
        """Compare the fetch history in *dataset* against this plan."""
        return compare_actual_vs_planned(dataset, self.plan)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _group_stopped_static_templates(
    stopped_pairs: list[tuple[PlanCandidate, URLDecision]],
) -> list[dict]:
    """Group stopped-static-GET candidates by (host, template) for the report."""
    groups: dict[tuple[str, str], list[tuple[PlanCandidate, URLDecision]]] = defaultdict(list)
    for candidate, decision in stopped_pairs:
        template = candidate.inferred_templates[-1] if candidate.inferred_templates else ""
        key = (candidate.host, template)
        groups[key].append((candidate, decision))

    rows = []
    for (host, template), pairs in groups.items():
        first_decision = pairs[0][1]
        row: dict = {
            "host": host,
            "template": template,
            "stopped_count": len(pairs),
            "next_action": first_decision.next_action.value,
            "reason_codes": list(first_decision.reason_codes),
            "representative_urls": [c.canonical_uri for c, _ in pairs[:3]],
        }
        # Attach numeric pattern metrics when available (populated by score_pattern
        # via URLDecision.debug["pattern_details"]).
        details = first_decision.debug.get("pattern_details", {})
        if details:
            row["sample_count"] = details.get("sample_count")
            row["avg_total_ms"] = details.get("avg_total_ms")
            row["render_needed_rate"] = details.get("render_needed_rate")
            row["candidate_document_count"] = details.get("candidate_document_count")
            row["technical_document_count"] = details.get("technical_document_count")
        rows.append(row)
    return sorted(rows, key=lambda r: -r["stopped_count"])


def _item_dict(candidate: PlanCandidate, decision: URLDecision) -> dict:
    return {
        "uri_identity_id": candidate.uri_identity_id,
        "canonical_uri": candidate.canonical_uri,
        "host": candidate.host,
        "source_type": candidate.source_type,
        "next_action": decision.next_action.value,
        "url_role": decision.url_role.value,
        "final_score": decision.scores.final_score,
        "url_score": decision.scores.url_score,
        "source_score": decision.scores.source_score,
        "pattern_score": decision.scores.pattern_score,
        "reason_codes": list(decision.reason_codes),
        "template": candidate.inferred_templates[-1] if candidate.inferred_templates else "",
        "anchor_text": candidate.anchor_text or "",
    }


def _build_host_summary(host_usage: dict[str, dict[str, int]]) -> list[dict]:
    rows = [
        {
            "hostname": hostname,
            "static_gets": usage.get("static_gets", 0),
            "renders": usage.get("renders", 0),
            "document_fetches": usage.get("document_fetches", 0),
        }
        for hostname, usage in host_usage.items()
    ]
    return sorted(rows, key=lambda r: -(r["static_gets"] + r["renders"] + r["document_fetches"]))


def _build_template_summary(template_usage: dict[str, dict[str, int]]) -> list[dict]:
    rows = [
        {
            "template": template,
            "static_gets": usage.get("static_gets", 0),
            "renders": usage.get("renders", 0),
        }
        for template, usage in template_usage.items()
    ]
    return sorted(rows, key=lambda r: -(r["static_gets"] + r["renders"]))


def _build_report(
    plan: CrawlPlan,
    crawl_run_id: int | None,
    crawl_run_key: str | None,
    budget: CrawlBudget,
) -> CrawlPlanningReport:
    bu = plan.budget_usage
    budget_usage = {
        "static_gets": bu.static_gets,
        "renders": bu.renders,
        "document_fetches": bu.document_fetches,
    }

    selected_dicts = [_item_dict(c, d) for c, d in plan.selected]
    deferred_dicts = [_item_dict(c, d) for c, d in plan.deferred]
    rejected_dicts = [_item_dict(c, d) for c, d in plan.rejected]
    stopped_static_dicts = [_item_dict(c, d) for c, d in plan.stopped_static_get]

    # Deduplicate document fetches by canonical URL (strip tracking params first)
    seen_canonical: set[str] = set()
    deduped_document_fetches: list[dict] = []
    for item in selected_dicts:
        if item["next_action"] != NextAction.FETCH_DOCUMENT.value:
            continue
        key = _strip_tracking_params(item["canonical_uri"])
        if key not in seen_canonical:
            seen_canonical.add(key)
            deduped_document_fetches.append(item)

    grouped_stopped = _group_stopped_static_templates(plan.stopped_static_get)

    return CrawlPlanningReport(
        crawl_run_id=crawl_run_id,
        crawl_run_key=crawl_run_key,
        budget=budget,
        budget_usage=budget_usage,
        host_usage=plan.host_usage,
        template_usage=plan.template_usage,
        reason_summary=plan.reason_summary,
        host_summary=_build_host_summary(plan.host_usage),
        template_summary=_build_template_summary(plan.template_usage),
        selected_summary=selected_dicts,
        deferred_summary=deferred_dicts,
        rejected_summary=rejected_dicts,
        stopped_static_get_summary=stopped_static_dicts,
        top_selected=selected_dicts[:_TOP_N],
        top_deferred=deferred_dicts[:_TOP_N],
        top_rejected=rejected_dicts[:_TOP_N],
        top_stopped_static_templates=grouped_stopped[:_TOP_N],
        top_document_fetches=deduped_document_fetches[:_TOP_N],
        plan=plan,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_planning_from_db(
    session,
    *,
    crawl_run_key: str | None = None,
    crawl_run_id: int | None = None,
    budget: CrawlBudget,
) -> CrawlPlanningReport:
    """Load DB data for a crawl run, run the planner, and return a structured report.

    Does not print, write files, or mutate the database.

    Parameters
    ----------
    session:
        SQLAlchemy session (read-only).
    crawl_run_key / crawl_run_id:
        Exactly one must be provided to identify the crawl run.
    budget:
        Budget caps passed to the planner unchanged.
    """
    dataset = load_analysis_dataset_from_db(
        session,
        crawl_run_key=crawl_run_key,
        crawl_run_id=crawl_run_id,
    )

    # Resolve the numeric run ID for the report (may already be known)
    resolved_run_id: int | None = crawl_run_id
    if resolved_run_id is None and dataset.frontier_items:
        resolved_run_id = dataset.frontier_items[0].crawl_run_id
    elif resolved_run_id is None and dataset.fetch_attempts:
        resolved_run_id = dataset.fetch_attempts[0].crawl_run_id

    plan = plan_from_dataset(dataset, budget, crawl_run_id=resolved_run_id)

    return _build_report(plan, resolved_run_id, crawl_run_key, budget)
