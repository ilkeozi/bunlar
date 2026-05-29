from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .db_export_models import AnalysisDataset
from .models import NextAction
from .planner import CrawlPlan
from .stats_builder import build_template_observations


@dataclass
class CrawlPlanComparison:
    """Side-by-side summary of what was actually fetched vs what the planner recommends.

    All fields are plain dicts/lists so callers can pass them directly to
    notebooks, CSV writers, or API responses without further conversion.
    """

    # Actual static GETs already in the dataset, keyed by host/template
    actual_static_gets_by_host: dict[str, int]
    planned_static_gets_by_host: dict[str, int]
    actual_static_gets_by_template: dict[str, int]
    planned_static_gets_by_template: dict[str, int]

    # How many of the already-fetched static GETs required rendering
    actual_render_needed_by_template: dict[str, int]

    # Templates the planner would stop sending static GETs to
    stopped_static_get_templates: list[str]

    # Document URLs the planner selected that have not yet been fetched
    planned_docs_not_fetched: list[dict]

    # Hosts/templates where the planner recommends fewer static GETs than were done
    hosts_where_planner_reduces: list[dict]
    templates_where_planner_reduces: list[dict]

    # Technical documents the planner would prioritise for FETCH_DOCUMENT
    promoted_technical_documents: list[dict]

    # ---------------------------------------------------------------------------
    # Convenience accessors
    # ---------------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "actual_static_gets_by_host": self.actual_static_gets_by_host,
            "planned_static_gets_by_host": self.planned_static_gets_by_host,
            "actual_static_gets_by_template": self.actual_static_gets_by_template,
            "planned_static_gets_by_template": self.planned_static_gets_by_template,
            "actual_render_needed_by_template": self.actual_render_needed_by_template,
            "stopped_static_get_templates": self.stopped_static_get_templates,
            "planned_docs_not_fetched": self.planned_docs_not_fetched,
            "hosts_where_planner_reduces": self.hosts_where_planner_reduces,
            "templates_where_planner_reduces": self.templates_where_planner_reduces,
            "promoted_technical_documents": self.promoted_technical_documents,
        }

    def reduction_summary(self) -> dict:
        """Return a compact dict of headline reduction numbers."""
        return {
            "hosts_to_reduce": len(self.hosts_where_planner_reduces),
            "templates_to_reduce": len(self.templates_where_planner_reduces),
            "total_planned_doc_fetches": len(self.promoted_technical_documents),
            "docs_not_yet_fetched": len(self.planned_docs_not_fetched),
            "stopped_static_get_template_count": len(self.stopped_static_get_templates),
        }


def compare_actual_vs_planned(
    dataset: AnalysisDataset,
    plan: CrawlPlan,
) -> CrawlPlanComparison:
    """Compare the fetch history in *dataset* against the planner's *plan*.

    Pure function — reads from both inputs, writes nothing, queries no DB.

    Parameters
    ----------
    dataset:
        The AnalysisDataset that was used to produce the plan (or any dataset
        covering the same time window).
    plan:
        A CrawlPlan produced by ``plan_from_dataset``.
    """
    observations = build_template_observations(dataset)
    static_obs = [o for o in observations if o.fetch_method == "static_get"]

    # --- Actuals from dataset -------------------------------------------------
    actual_by_host: dict[str, int] = defaultdict(int)
    actual_by_template: dict[str, int] = defaultdict(int)
    actual_render_by_template: dict[str, int] = defaultdict(int)
    for obs in static_obs:
        actual_by_host[obs.host] += 1
        actual_by_template[obs.template] += 1
        if obs.render_needed:
            actual_render_by_template[obs.template] += 1

    # --- Planned counts from plan ---------------------------------------------
    planned_by_host: dict[str, int] = {
        h: usage.get("static_gets", 0)
        for h, usage in plan.host_usage.items()
    }
    planned_by_template: dict[str, int] = {
        t: usage.get("static_gets", 0)
        for t, usage in plan.template_usage.items()
    }

    # --- Stopped templates ----------------------------------------------------
    seen_templates: set[str] = set()
    stopped_templates: list[str] = []
    for candidate, _ in plan.stopped_static_get:
        tmpl = candidate.inferred_templates[-1] if candidate.inferred_templates else ""
        if tmpl and tmpl not in seen_templates:
            seen_templates.add(tmpl)
            stopped_templates.append(tmpl)

    # --- Planned document fetches not yet in dataset -------------------------
    fetched_uri_ids: set[int] = {fa.uri_identity_id for fa in dataset.fetch_attempts}
    planned_docs_not_fetched = [
        {
            "uri_identity_id": c.uri_identity_id,
            "canonical_uri": c.canonical_uri,
            "host": c.host,
        }
        for c, d in plan.selected
        if d.next_action == NextAction.FETCH_DOCUMENT
        and c.uri_identity_id not in fetched_uri_ids
    ]

    # --- Hosts where planner recommends fewer static GETs --------------------
    all_hosts = set(actual_by_host.keys()) | set(planned_by_host.keys())
    hosts_reduces = sorted(
        [
            {
                "hostname": h,
                "actual_static_gets": actual_by_host.get(h, 0),
                "planned_static_gets": planned_by_host.get(h, 0),
                "reduction": actual_by_host.get(h, 0) - planned_by_host.get(h, 0),
            }
            for h in all_hosts
            if actual_by_host.get(h, 0) > planned_by_host.get(h, 0)
        ],
        key=lambda r: -r["reduction"],
    )

    # --- Templates where planner recommends fewer static GETs ----------------
    all_templates = set(actual_by_template.keys()) | set(planned_by_template.keys())
    templates_reduces = sorted(
        [
            {
                "template": t,
                "actual_static_gets": actual_by_template.get(t, 0),
                "planned_static_gets": planned_by_template.get(t, 0),
                "reduction": actual_by_template.get(t, 0) - planned_by_template.get(t, 0),
            }
            for t in all_templates
            if actual_by_template.get(t, 0) > planned_by_template.get(t, 0)
        ],
        key=lambda r: -r["reduction"],
    )

    # --- Technical documents the planner promotes ----------------------------
    promoted_tech = [
        {
            "uri_identity_id": c.uri_identity_id,
            "canonical_uri": c.canonical_uri,
            "host": c.host,
            "final_score": d.scores.final_score,
        }
        for c, d in plan.selected
        if d.next_action == NextAction.FETCH_DOCUMENT
    ]

    return CrawlPlanComparison(
        actual_static_gets_by_host=dict(actual_by_host),
        planned_static_gets_by_host=planned_by_host,
        actual_static_gets_by_template=dict(actual_by_template),
        planned_static_gets_by_template=planned_by_template,
        actual_render_needed_by_template=dict(actual_render_by_template),
        stopped_static_get_templates=stopped_templates,
        planned_docs_not_fetched=planned_docs_not_fetched,
        hosts_where_planner_reduces=hosts_reduces,
        templates_where_planner_reduces=templates_reduces,
        promoted_technical_documents=promoted_tech,
    )
