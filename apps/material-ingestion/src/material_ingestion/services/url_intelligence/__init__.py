"""
URL Intelligence
================

Standalone URL analysis module for material/document discovery sites.

Classifies URLs, infers RFC-6570-style route templates, and produces
explainable crawl-action decisions — all without network access or DB access.

Quick start
-----------
Classify a single URL::

    from material_ingestion.services.url_intelligence import decide
    result = decide("https://example.com/tds/Product_TDS.pdf")
    print(result.next_action)  # NextAction.FETCH_DOCUMENT
    print(result.url_role)     # URLRole.TECHNICAL_DOCUMENT
    print(result.reason_codes) # ["TECH_DOC_FILE_URL"]

Pass source context::

    from material_ingestion.services.url_intelligence import decide, SourceContext
    ctx = SourceContext(came_from_sitemap=True, has_english_hreflang=True)
    result = decide("https://example.com/downloads", context=ctx)

Pass optional pattern stats::

    from material_ingestion.services.url_intelligence import decide, PatternStats
    stats = PatternStats(sample_count=60, render_needed_count=58)
    result = decide("https://example.com/some-page", stats=stats)
    # → NextAction.STOP_STATIC_GET when no documents have ever been found

Interpreting next_action
------------------------
fetch_document
    URL is a direct document (PDF, etc.); fetch it now.
inspect_static_html
    URL is a listing or download-center page; crawl to find document links.
sample_static_html
    Pattern is unknown; take a sample crawl to gather pattern data.
stop_static_get
    Pattern data shows static GET yields nothing; skip this URL class.
render_sample
    Page likely requires JS rendering; try a JS-rendered sample.
api_discovery
    Page may expose a bulk-discovery API endpoint.
defer
    Low priority; schedule for a later crawl cycle.
reject
    Asset file, obvious noise (legal/career/login), or actively harmful — do
    not crawl.

Scores
------
Three independent scores are summed into ``final_score``:

url_score
    Signals derivable purely from the URL string and its path segments.
source_score
    Signals from how the URL was discovered (sitemap, anchor text, etc.).
pattern_score
    Historical per-pattern yield stats (only applied when sample_count >= 10).
"""

from .comparison import CrawlPlanComparison, compare_actual_vs_planned
from .db_loader import load_analysis_dataset_from_db
from .decision import decide
from .models import (
    NextAction,
    ParsedSegment,
    ParsedURL,
    PatternStats,
    ScoreBreakdown,
    SegmentKind,
    SourceContext,
    TemplateCandidate,
    URLDecision,
    URLRole,
)
from .planning_report import CrawlPlanningReport, run_planning_from_db
from .planner import CrawlBudget
from .segment_predicates import classify_segment
from .template_inference import infer_templates
from .uri_parser import parse_url

__all__ = [
    "decide",
    "load_analysis_dataset_from_db",
    "run_planning_from_db",
    "CrawlPlanningReport",
    "CrawlBudget",
    "CrawlPlanComparison",
    "compare_actual_vs_planned",
    "parse_url",
    "classify_segment",
    "infer_templates",
    "SegmentKind",
    "URLRole",
    "NextAction",
    "ParsedSegment",
    "ParsedURL",
    "TemplateCandidate",
    "SourceContext",
    "PatternStats",
    "ScoreBreakdown",
    "URLDecision",
]
