from __future__ import annotations

import argparse
import logging
import logging.config
import os
import signal
import sys
import threading
import time
from datetime import UTC, datetime
from urllib.parse import urlsplit

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uvicorn.logging import DefaultFormatter
from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebIngestionEvent
from material_ingestion.services.web_crawl_host_scope_service import (
    create_allowlist_rule,
    delete_allowlist_rule,
    is_host_allowlisted,
    list_allowlist_rules,
    replace_allowlist_rules,
    update_allowlist_rule,
)
from material_ingestion.services.web_crawl_frontier_score_rule_service import (
    create_frontier_score_rule,
    delete_frontier_score_rule,
    list_frontier_score_rules,
    replace_frontier_score_rules,
    update_frontier_score_rule,
)
from material_ingestion.services.web_crawl_evaluation_rule_service import (
    create_evaluation_rule,
    delete_evaluation_rule,
    list_evaluation_rules,
    replace_evaluation_rules,
    update_evaluation_rule,
)
from material_ingestion.services.web_runtime_config_service import (
    create_runtime_config,
    delete_runtime_config,
    get_runtime_int_config,
    list_runtime_configs,
    replace_runtime_configs,
    update_runtime_config,
)
from material_ingestion.services.web_event_service import (
    enqueue_core_discover_event,
    enqueue_frontier_evaluate_event,
    enqueue_frontier_get_event,
)
from material_ingestion.services.web_event_service import run_web_core_worker
from material_ingestion.services.url_intelligence import (
    CrawlBudget,
    PatternStats,
    SourceContext,
    compare_actual_vs_planned,
    decide as url_intelligence_decide,
    load_analysis_dataset_from_db,
    run_planning_from_db,
)
from sqlalchemy import desc, text

logger = logging.getLogger("material_ingestion.runtime")


class RuntimeState:
    def __init__(self) -> None:
        self.started_at = time.time()
        self.stop_event = threading.Event()
        self.worker_iterations = 0
        self.worker_errors = 0
        self.last_worker_rc = 0


def _configure_logging() -> None:
    level_name = os.getenv("MATERIAL_INGESTION_LOG_LEVEL", "INFO").upper()
    use_colors = bool(getattr(sys.stderr, "isatty", lambda: False)())
    formatter_path = "uvicorn.logging.DefaultFormatter" if use_colors else "logging.Formatter"
    fmt = "%(levelprefix)s %(name)s:%(message)s" if use_colors else "%(levelname)s %(name)s:%(message)s"
    level = getattr(logging, level_name, logging.INFO)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": formatter_path,
                    "fmt": fmt,
                    "use_colors": use_colors,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                    "formatter": "default",
                }
            },
            "root": {
                "level": level_name,
                "handlers": ["default"],
            },
            "loggers": {
                "uvicorn": {"level": level_name, "handlers": ["default"], "propagate": False},
                "uvicorn.error": {"level": level_name, "handlers": ["default"], "propagate": False},
                "uvicorn.access": {"level": level_name, "handlers": ["default"], "propagate": False},
                "material_ingestion": {"level": level_name, "handlers": ["default"], "propagate": False},
            },
        }
    )


class RunRequest(BaseModel):
    seed_url: str = Field(
        ...,
        min_length=1,
        description="Seed page URL to start discovery from.",
        examples=["https://www.basf.com"],
    )
    run_key: str | None = Field(
        default=None,
        description="Optional client-defined run identifier. If omitted, runtime generates one.",
        examples=["core_run_basf_001"],
    )
    max_pages: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of HTML pages to crawl during discovery.",
        examples=[20],
    )
    cross_domain: bool = Field(
        default=False,
        description="Allow crawling across domains discovered from links/sitemaps.",
        examples=[False],
    )
    ingest_source: str = Field(
        default="web_discovery",
        description="Source label persisted with run events.",
        examples=["web_discovery"],
    )
    fetch_max_concurrency: int = Field(
        default=25,
        ge=1,
        le=200,
        description="Maximum concurrent HEAD requests used by frontier fetch stage.",
        examples=[25],
    )


class HealthResponse(BaseModel):
    ok: bool = Field(description="Process is alive.")


class ReadyResponse(BaseModel):
    ready: bool = Field(description="Service is ready to accept runs (DB reachable and runtime active).")


class ErrorResponse(BaseModel):
    detail: str = Field(description="Error code string.")


class VersionResponse(BaseModel):
    service: str = Field(description="Service identifier.")
    runtime: str = Field(description="Runtime mode.")
    pid: int = Field(description="Current process ID.")


class MetricsResponse(BaseModel):
    uptime_seconds: int = Field(description="Elapsed process uptime in seconds.")
    worker_iterations: int = Field(description="Number of worker polling loop iterations.")
    worker_errors: int = Field(description="Number of worker loop errors encountered.")
    last_worker_rc: int = Field(description="Last worker run return code.")


class CoreMetricsResponse(BaseModel):
    runtime: dict[str, int]
    events: dict[str, int]
    backlog: dict[str, int]
    volumes: dict[str, int]
    funnel: dict[str, int]
    eligibility: dict[str, int]


class RunAcceptedResponse(BaseModel):
    accepted: bool = Field(description="Run event accepted for queueing.")
    event_id: int = Field(description="Queued event primary key.")
    run_key: str = Field(description="Resolved run key used for this run.")
    event_type: str = Field(description="Queued event type.", examples=["core_discover_requested"])
    reason_code: str | None = Field(
        default=None,
        description="Optional machine-readable reason when accepted is false.",
    )


class EvaluateRequest(BaseModel):
    batch_size: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Maximum number of eligible frontier items to evaluate in one event.",
        examples=[500],
    )
    force: bool = Field(
        default=False,
        description="When true, enqueue evaluate even if normal eligibility check is empty.",
        examples=[False],
    )



class RunErrorDetail(BaseModel):
    code: str = Field(description="Stable machine-readable error code.", examples=["invalid_seed_url"])
    message: str = Field(description="Human-readable error message.")
    reason_code: str | None = Field(
        default=None,
        description="Optional crawler/runtime reason code for diagnostics.",
        examples=["runtime_stopping"],
    )
    details: dict[str, object] | None = Field(
        default=None,
        description="Optional structured error details for client handling.",
    )


class RunErrorResponse(BaseModel):
    error: RunErrorDetail


class RunEventSummary(BaseModel):
    event_id: int
    event_type: str
    status: str
    attempt_count: int
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    heartbeat_at: datetime | None
    heartbeat_age_seconds: int | None
    is_stale: bool
    error_text: str | None


class RunStatusResponse(BaseModel):
    run_key: str
    latest_status: str
    latest_event_type: str
    active_event_id: int | None
    is_running: bool
    latest_heartbeat_age_seconds: int | None
    stale_threshold_seconds: int
    events: list[RunEventSummary]


class RunListItem(BaseModel):
    run_key: str
    latest_status: str
    latest_event_type: str
    is_running: bool
    heartbeat_age_seconds: int | None
    updated_at: datetime | None


class RunListResponse(BaseModel):
    runs: list[RunListItem]


class AllowlistRule(BaseModel):
    id: int
    pattern: str
    enabled: bool
    priority: int
    note: str


class AllowlistRuleCreate(BaseModel):
    pattern: str = Field(..., min_length=1)
    enabled: bool = True
    priority: int = 100
    note: str = ""


class AllowlistRulePatch(BaseModel):
    pattern: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    note: str | None = None


class AllowlistReplaceRequest(BaseModel):
    rules: list[AllowlistRuleCreate]


class FrontierScoreRule(BaseModel):
    id: int
    match_type: str
    pattern: str
    weight: int
    enabled: bool
    priority: int
    note: str


class FrontierScoreRuleCreate(BaseModel):
    match_type: str = Field(default="contains", description="Rule matcher type: contains|regex|suffix")
    pattern: str = Field(..., min_length=1)
    weight: int = 0
    enabled: bool = True
    priority: int = 100
    note: str = ""


class FrontierScoreRulePatch(BaseModel):
    match_type: str | None = None
    pattern: str | None = None
    weight: int | None = None
    enabled: bool | None = None
    priority: int | None = None
    note: str | None = None


class FrontierScoreReplaceRequest(BaseModel):
    rules: list[FrontierScoreRuleCreate]


class EvaluationRule(BaseModel):
    id: int
    action: str
    match_type: str
    pattern: str
    weight: int
    enabled: bool
    priority: int
    note: str


class EvaluationRuleCreate(BaseModel):
    action: str = Field(default="defer", description="Rule action: promote|defer|skip")
    match_type: str = Field(default="contains", description="Rule matcher type: contains|regex|suffix")
    pattern: str = Field(..., min_length=1)
    weight: int = 0
    enabled: bool = True
    priority: int = 100
    note: str = ""


class EvaluationRulePatch(BaseModel):
    action: str | None = None
    match_type: str | None = None
    pattern: str | None = None
    weight: int | None = None
    enabled: bool | None = None
    priority: int | None = None
    note: str | None = None


class EvaluationRuleReplaceRequest(BaseModel):
    rules: list[EvaluationRuleCreate]


class RuntimeConfigItem(BaseModel):
    id: int
    config_key: str
    config_value: str
    enabled: bool
    note: str


class RuntimeConfigCreate(BaseModel):
    config_key: str = Field(..., min_length=1)
    config_value: str
    enabled: bool = True
    note: str = ""


class RuntimeConfigPatch(BaseModel):
    config_key: str | None = None
    config_value: str | None = None
    enabled: bool | None = None
    note: str | None = None


class RuntimeConfigReplaceRequest(BaseModel):
    rows: list[RuntimeConfigCreate]


# ---------------------------------------------------------------------------
# URL intelligence models
# ---------------------------------------------------------------------------


class URLDecideRequest(BaseModel):
    url: str = Field(..., min_length=1, description="URL to classify.", examples=["https://example.com/tds/ProductA_TDS.pdf"])
    # Source context (all optional)
    source_type: str = Field(default="", description="Discovery source: sitemap | extracted_link | manual_seed.", examples=["sitemap"])
    anchor_text: str = Field(default="", description="Anchor text of the inbound link.", examples=["Technical Data Sheet"])
    source_page_role: str = Field(default="", description="Role of the linking page, e.g. document_listing.", examples=["document_listing"])
    has_english_hreflang: bool = Field(default=False, description="Source page has an English hreflang alternate.")
    came_from_sitemap: bool = Field(default=False, description="URL appeared directly in a sitemap.")
    source_page_produced_document_candidates: bool = Field(default=False, description="Linking page previously yielded document candidates.")
    source_is_navigation_heavy: bool = Field(default=False, description="Linking page is a navigation element (footer/header).")
    # Pattern stats (all optional; omit or set pattern_sample_count=null to skip)
    pattern_sample_count: int | None = Field(default=None, ge=0, description="Observed fetches for this URL pattern. Omit to skip pattern scoring.")
    pattern_render_needed_count: int = Field(default=0, ge=0, description="Of the sample, how many required JS rendering.")
    pattern_candidate_document_count: int = Field(default=0, ge=0, description="Total candidate documents found across the sample.")
    pattern_technical_document_count: int = Field(default=0, ge=0, description="Technical documents (TDS/SDS) found in the sample.")
    pattern_noise_count: int = Field(default=0, ge=0, description="Noise/error outcomes in the sample.")
    pattern_useful_link_count: int = Field(default=0, ge=0, description="Samples that produced useful outbound links.")
    pattern_avg_total_ms: float = Field(default=0.0, ge=0, description="Average fetch latency for this pattern (ms).")


class URLDecideResponse(BaseModel):
    canonical_url: str = Field(description="Normalised canonical form of the input URL.")
    next_action: str = Field(description="Recommended crawl action.", examples=["fetch_document"])
    url_role: str = Field(description="Inferred URL role.", examples=["technical_document"])
    final_score: int = Field(description="Sum of url_score + source_score + pattern_score.")
    url_score: int = Field(description="Score derived from URL string signals.")
    source_score: int = Field(description="Score derived from discovery context.")
    pattern_score: int = Field(description="Score derived from historical pattern stats.")
    reason_codes: list[str] = Field(description="All reason codes that influenced the decision.")
    selected_template: str = Field(description="RFC-6570-style route template inferred for the URL.")


class CrawlPlanResponse(BaseModel):
    crawl_run_key: str | None
    crawl_run_id: int | None
    budget_usage: dict[str, int] = Field(description="Consumed budget counters: static_gets, renders, document_fetches.")
    reason_summary: dict[str, int] = Field(description="Reason code → count across all planned URLs.")
    host_summary: list[dict] = Field(description="Per-host static_gets / renders / document_fetches, sorted by total descending.")
    template_summary: list[dict] = Field(description="Per-template static_gets / renders, sorted by total descending.")
    stopped_static_get_count: int = Field(description="URLs where only static GET is stopped (not globally rejected).")
    globally_rejected_count: int = Field(description="URLs globally rejected as noise/asset.")
    top_selected: list[dict] = Field(description="Top-20 selected URLs with action, score, and reason codes.")
    top_deferred: list[dict] = Field(description="Top-20 deferred URLs.")
    top_rejected: list[dict] = Field(description="Top-20 globally rejected URLs.")
    top_stopped_static_templates: list[dict] = Field(description="Top-20 URLs where static GET was stopped.")
    top_document_fetches: list[dict] = Field(description="Top-20 selected FETCH_DOCUMENT URLs.")


class CrawlPlanCompareResponse(BaseModel):
    actual_static_gets_by_host: dict[str, int]
    planned_static_gets_by_host: dict[str, int]
    actual_static_gets_by_template: dict[str, int]
    planned_static_gets_by_template: dict[str, int]
    actual_render_needed_by_template: dict[str, int]
    stopped_static_get_templates: list[str]
    planned_docs_not_fetched: list[dict]
    hosts_where_planner_reduces: list[dict]
    templates_where_planner_reduces: list[dict]
    promoted_technical_documents: list[dict]


def _is_db_ready() -> bool:
    try:
        session_factory = create_session_factory()
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _run_worker_loop(state: RuntimeState, sleep_seconds: float, stage: str | None = None) -> None:
    args = argparse.Namespace(orchestration_id=None, once=True, stage=stage, last_orchestration_id=None)
    while not state.stop_event.is_set():
        try:
            rc = run_web_core_worker(args)
            state.last_worker_rc = rc
            state.worker_iterations += 1
            if rc != 0:
                state.worker_errors += 1
        except Exception:
            state.worker_errors += 1
            logger.exception("worker loop error")
        state.stop_event.wait(sleep_seconds)


def _run_evaluate_scheduler_loop(state: RuntimeState, interval_seconds: float, batch_size: int) -> None:
    while not state.stop_event.is_set():
        try:
            enqueue_frontier_evaluate_event(batch_size=batch_size)
        except Exception:
            logger.exception("evaluate scheduler loop error")
        state.stop_event.wait(interval_seconds)


def _run_get_scheduler_loop(state: RuntimeState, interval_seconds: float, batch_size: int, max_concurrency: int) -> None:
    while not state.stop_event.is_set():
        try:
            enqueue_frontier_get_event(batch_size=batch_size, max_concurrency=max_concurrency)
        except Exception:
            logger.exception("get scheduler loop error")
        state.stop_event.wait(interval_seconds)


def _stale_threshold_seconds() -> int:
    return max(1, int(os.getenv("MATERIAL_INGESTION_EVENT_STALE_SECONDS", "600")))


def _heartbeat_age_seconds(heartbeat_at: datetime | None, now: datetime) -> int | None:
    if heartbeat_at is None:
        return None
    delta = now - heartbeat_at
    return max(0, int(delta.total_seconds()))


def _event_summary(event: RawWebIngestionEvent, now: datetime, stale_seconds: int) -> RunEventSummary:
    age_seconds = _heartbeat_age_seconds(event.heartbeat_at, now)
    is_stale = bool(event.status == "running" and age_seconds is not None and age_seconds > stale_seconds)
    return RunEventSummary(
        event_id=int(event.id),
        event_type=event.event_type,
        status=event.status,
        attempt_count=int(event.attempt_count or 0),
        created_at=event.created_at,
        started_at=event.started_at,
        finished_at=event.finished_at,
        heartbeat_at=event.heartbeat_at,
        heartbeat_age_seconds=age_seconds,
        is_stale=is_stale,
        error_text=event.error_text or None,
    )


def build_app(state: RuntimeState) -> FastAPI:
    app = FastAPI(
        title="Material Ingestion Runtime API",
        version="1.0.0",
        summary="Core-only crawler runtime and control plane API",
        description=(
            "Single-process runtime for crawler-core event ingestion.\n\n"
            "- Exposes health/readiness and runtime metrics.\n"
            "- Accepts run requests and enqueues `core_discover_requested` events.\n"
            "- Worker loop processes core events in the background."
        ),
        openapi_tags=[
            {"name": "system", "description": "Service health, readiness, version, and runtime metrics."},
            {"name": "runs", "description": "Create crawler-core run requests."},
            {"name": "allowlist", "description": "Host allowlist CRUD for crawl scope control."},
            {"name": "scoring", "description": "Frontier URL scoring rule CRUD for pre-fetch gating."},
            {"name": "evaluation", "description": "Frontier evaluation rule CRUD for post-fetch promotion/defer decisions."},
            {"name": "runtime-config", "description": "Runtime scheduling/configuration CRUD."},
            {"name": "url-intelligence", "description": "URL classification, crawl planning, and actual-vs-planned analysis."},
        ],
    )

    @app.get(
        "/healthz",
        tags=["system"],
        summary="Liveness probe",
        description="Returns process liveness. Does not validate database connectivity.",
        response_model=HealthResponse,
    )
    def healthz() -> HealthResponse:
        return {"ok": True}

    @app.get(
        "/readyz",
        tags=["system"],
        summary="Readiness probe",
        description="Returns readiness based on DB connectivity and runtime stop state.",
        response_model=ReadyResponse,
        responses={503: {"model": ErrorResponse, "description": "Service not ready."}},
    )
    def readyz() -> ReadyResponse:
        ready = _is_db_ready() and not state.stop_event.is_set()
        if not ready:
            raise HTTPException(status_code=503, detail="not_ready")
        return {"ready": True}

    @app.get(
        "/version",
        tags=["system"],
        summary="Runtime identity",
        description="Returns service/runtime identity details and current process ID.",
        response_model=VersionResponse,
    )
    def version() -> VersionResponse:
        return {"service": "material-ingestion", "runtime": "single-process", "pid": os.getpid()}

    @app.get(
        "/metrics",
        tags=["system"],
        summary="Runtime counters",
        description="Returns in-memory runtime counters for worker loop health and uptime.",
        response_model=MetricsResponse,
    )
    def metrics() -> MetricsResponse:
        return {
            "uptime_seconds": int(time.time() - state.started_at),
            "worker_iterations": state.worker_iterations,
            "worker_errors": state.worker_errors,
            "last_worker_rc": state.last_worker_rc,
        }

    @app.get(
        "/metrics/core",
        tags=["system"],
        summary="Crawler core metrics",
        description="Returns DB-backed core crawler metrics for queue health, backlog, and table volumes.",
        response_model=CoreMetricsResponse,
    )
    def metrics_core() -> CoreMetricsResponse:
        session_factory = create_session_factory()
        with session_factory() as session:
            event_rows = (
                session.query(RawWebIngestionEvent.event_type, RawWebIngestionEvent.status)
                .all()
            )
            events_running = 0
            events_queued = 0
            events_done = 0
            events_failed = 0
            discover_queued = 0
            build_queued = 0
            fetch_queued = 0
            evaluate_queued = 0
            get_queued = 0
            discover_running = 0
            build_running = 0
            fetch_running = 0
            evaluate_running = 0
            get_running = 0
            for event_type, status in event_rows:
                status_s = str(status or "")
                event_type_s = str(event_type or "")
                if status_s == "running":
                    events_running += 1
                    if event_type_s == "core_discover_requested":
                        discover_running += 1
                    elif event_type_s == "frontier_build_requested":
                        build_running += 1
                    elif event_type_s == "frontier_fetch_requested":
                        fetch_running += 1
                    elif event_type_s == "frontier_evaluate_requested":
                        evaluate_running += 1
                    elif event_type_s == "frontier_get_requested":
                        get_running += 1
                elif status_s == "queued":
                    events_queued += 1
                    if event_type_s == "core_discover_requested":
                        discover_queued += 1
                    elif event_type_s == "frontier_build_requested":
                        build_queued += 1
                    elif event_type_s == "frontier_fetch_requested":
                        fetch_queued += 1
                    elif event_type_s == "frontier_evaluate_requested":
                        evaluate_queued += 1
                    elif event_type_s == "frontier_get_requested":
                        get_queued += 1
                elif status_s == "done":
                    events_done += 1
                elif status_s == "failed":
                    events_failed += 1

            volumes_row = session.execute(
                text(
                    """
                    select
                      (select count(*) from raw_web_crawl_run) as crawl_runs,
                      (select count(*) from raw_web_crawl_host) as crawl_hosts,
                      (select count(*) from raw_web_sitemap_source) as sitemap_sources,
                      (select count(*) from raw_web_sitemap_entry) as sitemap_entries,
                      (select count(*) from raw_web_sitemap_alternate) as sitemap_alternates,
                      (select count(*) from raw_web_frontier_item) as frontier_items,
                      (select count(*) from raw_web_http_fetch_attempt) as fetch_attempts,
                      (select count(*) from raw_web_http_representation) as http_representations,
                      (select count(*) from raw_web_crawl_decision) as decisions
                    """
                )
            ).mappings().first()
            funnel_row = session.execute(
                text(
                    """
                    select
                      (select count(*) from raw_web_frontier_item) as frontier_total,
                      (
                        select count(*)
                        from raw_web_frontier_item
                        where state_reason_code in ('head_metadata_success', 'recent_success_skip')
                      ) as fetched,
                      (
                        select count(*)
                        from raw_web_frontier_item
                        where state_reason_code in ('eval_promote', 'eval_defer', 'eval_skip')
                      ) as evaluated,
                      (
                        select count(*)
                        from raw_web_frontier_item
                        where state_reason_code = 'eval_promote'
                      ) as promoted,
                      (
                        select count(*)
                        from raw_web_frontier_item
                        where state_reason_code = 'get_success'
                      ) as get_success,
                      (select count(*) from raw_web_candidate_document) as candidate_count
                    """
                )
            ).mappings().first()
            eligibility_row = session.execute(
                text(
                    """
                    select
                      (
                        select count(*)
                        from raw_web_frontier_item f
                        where f.state = 'completed'
                          and f.state_reason_code in ('head_metadata_success', 'recent_success_skip')
                          and not exists (
                            select 1
                            from raw_web_crawl_decision d
                            where d.uri_identity_id = f.uri_identity_id
                              and d.reason_code in ('eval_promote', 'eval_defer', 'eval_skip')
                          )
                      ) as eval_eligible_not_evaluated,
                      (
                        select count(*)
                        from raw_web_frontier_item f
                        where f.state = 'completed'
                          and f.state_reason_code in ('head_metadata_success', 'recent_success_skip')
                          and exists (
                            select 1
                            from raw_web_crawl_decision d
                            where d.uri_identity_id = f.uri_identity_id
                              and d.reason_code in ('eval_promote', 'eval_defer', 'eval_skip')
                          )
                      ) as eval_already_evaluated,
                      (
                        select count(*)
                        from raw_web_frontier_item
                        where state = 'completed'
                          and state_reason_code in ('eval_promote', 'get_retry_scheduled')
                          and scheduled_at <= now()
                      ) as get_eligible_now
                    """
                )
            ).mappings().first()

        return {
            "runtime": {
                "uptime_seconds": int(time.time() - state.started_at),
                "worker_iterations": int(state.worker_iterations),
                "worker_errors": int(state.worker_errors),
                "last_worker_rc": int(state.last_worker_rc),
            },
            "events": {
                "queued": int(events_queued),
                "running": int(events_running),
                "done": int(events_done),
                "failed": int(events_failed),
            },
            "backlog": {
                "discover_queued": int(discover_queued),
                "discover_running": int(discover_running),
                "build_queued": int(build_queued),
                "build_running": int(build_running),
                "fetch_queued": int(fetch_queued),
                "fetch_running": int(fetch_running),
                "evaluate_queued": int(evaluate_queued),
                "evaluate_running": int(evaluate_running),
                "get_queued": int(get_queued),
                "get_running": int(get_running),
            },
            "volumes": {k: int(v or 0) for k, v in dict(volumes_row or {}).items()},
            "funnel": {k: int(v or 0) for k, v in dict(funnel_row or {}).items()},
            "eligibility": {k: int(v or 0) for k, v in dict(eligibility_row or {}).items()},
        }

    @app.post(
        "/evaluate",
        tags=["runs"],
        status_code=202,
        summary="Queue a global frontier evaluation event",
        description=(
            "Creates a new `frontier_evaluate_requested` event for the background worker.\n\n"
            "This evaluates globally eligible HEAD-fetched frontier items and does not require run_key."
        ),
        response_model=RunAcceptedResponse,
        responses={
            503: {"model": RunErrorResponse, "description": "Runtime cannot accept events right now."},
            500: {"model": RunErrorResponse, "description": "Unexpected server error."},
        },
    )
    def trigger_evaluate(req: EvaluateRequest) -> RunAcceptedResponse:
        if state.stop_event.is_set():
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "runtime_unavailable",
                        "message": "runtime is shutting down and cannot accept evaluate events.",
                        "reason_code": "runtime_stopping",
                    }
                },
            )
        try:
            force = bool(getattr(req, "force", False))
            if force:
                event_id = enqueue_frontier_evaluate_event(batch_size=int(req.batch_size), force=True)
            else:
                event_id = enqueue_frontier_evaluate_event(batch_size=int(req.batch_size))
        except Exception:
            logger.exception("trigger_evaluate failed")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "unexpected error while queueing evaluate event.",
                        "reason_code": "queue_failure",
                    }
                },
            )
        if event_id is None:
            return {
                "accepted": False,
                "event_id": 0,
                "run_key": "global_frontier_evaluate",
                "event_type": "frontier_evaluate_requested",
                "reason_code": "no_eligible_frontier_items_or_already_queued",
            }
        return {
            "accepted": True,
            "event_id": int(event_id or 0),
            "run_key": "global_frontier_evaluate",
            "event_type": "frontier_evaluate_requested",
        }

    @app.post(
        "/runs",
        tags=["runs"],
        status_code=202,
        summary="Queue a crawler-core run",
        description=(
            "Creates a new `core_discover_requested` event for the background worker.\n\n"
            "Use this endpoint to trigger core-only discovery/indexing runs."
        ),
        response_model=RunAcceptedResponse,
        responses={
            400: {"model": RunErrorResponse, "description": "Invalid request semantics."},
            409: {"model": RunErrorResponse, "description": "Run conflict (for example duplicate run key)."},
            503: {"model": RunErrorResponse, "description": "Runtime cannot accept runs right now."},
            500: {"model": RunErrorResponse, "description": "Unexpected server error."},
        },
    )
    def create_run(req: RunRequest) -> RunAcceptedResponse:
        seed_url = req.seed_url.strip()
        parsed = urlsplit(seed_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "invalid_seed_url",
                        "message": "seed_url must be an absolute http(s) URL.",
                        "reason_code": "invalid_input",
                        "details": {"seed_url": req.seed_url},
                    }
                },
            )
        if not is_host_allowlisted(parsed.netloc):
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "host_not_allowlisted",
                        "message": "seed host is not allowlisted.",
                        "reason_code": "host_not_allowlisted",
                        "details": {"host": parsed.netloc},
                    }
                },
            )
        if state.stop_event.is_set():
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "runtime_unavailable",
                        "message": "runtime is shutting down and cannot accept new runs.",
                        "reason_code": "runtime_stopping",
                    }
                },
            )
        run_key = (req.run_key or "").strip() or datetime.now(UTC).strftime("core_run_%Y%m%d_%H%M%S")
        try:
            event_id = enqueue_core_discover_event(
                run_key=run_key,
                seed_url=seed_url,
                max_pages=req.max_pages,
                cross_domain=req.cross_domain,
                ingest_source=req.ingest_source,
                fetch_max_concurrency=req.fetch_max_concurrency,
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "run_conflict",
                        "message": str(exc),
                        "reason_code": "duplicate_or_invalid_run_state",
                        "details": {"run_key": run_key},
                    }
                },
            )
        except Exception:
            logger.exception("create_run failed")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "unexpected error while queueing run event.",
                        "reason_code": "queue_failure",
                    }
                },
            )
        return {"accepted": True, "event_id": event_id, "run_key": run_key, "event_type": "core_discover_requested"}

    @app.get("/allowlist/rules", tags=["allowlist"], response_model=list[AllowlistRule], summary="List allowlist rules")
    def get_allowlist_rules() -> list[AllowlistRule]:
        rows = list_allowlist_rules()
        return [
            AllowlistRule(id=int(r.id), pattern=r.pattern, enabled=bool(r.enabled), priority=int(r.priority), note=r.note or "")
            for r in rows
        ]

    @app.post("/allowlist/rules", tags=["allowlist"], response_model=AllowlistRule, summary="Create allowlist rule")
    def post_allowlist_rule(req: AllowlistRuleCreate) -> AllowlistRule:
        rule_id = create_allowlist_rule(pattern=req.pattern, enabled=req.enabled, priority=req.priority, note=req.note)
        rows = list_allowlist_rules()
        row = next((r for r in rows if int(r.id) == int(rule_id)), None)
        assert row is not None
        return AllowlistRule(id=int(row.id), pattern=row.pattern, enabled=bool(row.enabled), priority=int(row.priority), note=row.note or "")

    @app.patch("/allowlist/rules/{rule_id}", tags=["allowlist"], response_model=AllowlistRule, summary="Patch allowlist rule")
    def patch_allowlist_rule(rule_id: int, req: AllowlistRulePatch) -> AllowlistRule:
        ok = update_allowlist_rule(
            rule_id=rule_id,
            pattern=req.pattern,
            enabled=req.enabled,
            priority=req.priority,
            note=req.note,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="allowlist_rule_not_found")
        rows = list_allowlist_rules()
        row = next((r for r in rows if int(r.id) == int(rule_id)), None)
        if row is None:
            raise HTTPException(status_code=404, detail="allowlist_rule_not_found")
        return AllowlistRule(id=int(row.id), pattern=row.pattern, enabled=bool(row.enabled), priority=int(row.priority), note=row.note or "")

    @app.delete("/allowlist/rules/{rule_id}", tags=["allowlist"], summary="Delete allowlist rule")
    def remove_allowlist_rule(rule_id: int) -> dict[str, bool]:
        ok = delete_allowlist_rule(rule_id=rule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="allowlist_rule_not_found")
        return {"deleted": True}

    @app.put("/allowlist/rules", tags=["allowlist"], summary="Replace allowlist rules")
    def put_allowlist_rules(req: AllowlistReplaceRequest) -> dict[str, int]:
        count = replace_allowlist_rules(
            rules=[
                {"pattern": r.pattern, "enabled": r.enabled, "priority": r.priority, "note": r.note}
                for r in req.rules
            ]
        )
        return {"replaced": count}

    @app.get("/scoring/rules", tags=["scoring"], response_model=list[FrontierScoreRule], summary="List scoring rules")
    def get_scoring_rules() -> list[FrontierScoreRule]:
        rows = list_frontier_score_rules()
        return [
            FrontierScoreRule(
                id=int(r.id),
                match_type=r.match_type,
                pattern=r.pattern,
                weight=int(r.weight),
                enabled=bool(r.enabled),
                priority=int(r.priority),
                note=r.note or "",
            )
            for r in rows
        ]

    @app.post("/scoring/rules", tags=["scoring"], response_model=FrontierScoreRule, summary="Create scoring rule")
    def post_scoring_rule(req: FrontierScoreRuleCreate) -> FrontierScoreRule:
        try:
            rule_id = create_frontier_score_rule(
                match_type=req.match_type,
                pattern=req.pattern,
                weight=req.weight,
                enabled=req.enabled,
                priority=req.priority,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        row = next((r for r in list_frontier_score_rules() if int(r.id) == int(rule_id)), None)
        assert row is not None
        return FrontierScoreRule(
            id=int(row.id),
            match_type=row.match_type,
            pattern=row.pattern,
            weight=int(row.weight),
            enabled=bool(row.enabled),
            priority=int(row.priority),
            note=row.note or "",
        )

    @app.patch("/scoring/rules/{rule_id}", tags=["scoring"], response_model=FrontierScoreRule, summary="Patch scoring rule")
    def patch_scoring_rule(rule_id: int, req: FrontierScoreRulePatch) -> FrontierScoreRule:
        try:
            ok = update_frontier_score_rule(
                rule_id=rule_id,
                match_type=req.match_type,
                pattern=req.pattern,
                weight=req.weight,
                enabled=req.enabled,
                priority=req.priority,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not ok:
            raise HTTPException(status_code=404, detail="scoring_rule_not_found")
        row = next((r for r in list_frontier_score_rules() if int(r.id) == int(rule_id)), None)
        if row is None:
            raise HTTPException(status_code=404, detail="scoring_rule_not_found")
        return FrontierScoreRule(
            id=int(row.id),
            match_type=row.match_type,
            pattern=row.pattern,
            weight=int(row.weight),
            enabled=bool(row.enabled),
            priority=int(row.priority),
            note=row.note or "",
        )

    @app.delete("/scoring/rules/{rule_id}", tags=["scoring"], summary="Delete scoring rule")
    def remove_scoring_rule(rule_id: int) -> dict[str, bool]:
        ok = delete_frontier_score_rule(rule_id=rule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="scoring_rule_not_found")
        return {"deleted": True}

    @app.put("/scoring/rules", tags=["scoring"], summary="Replace scoring rules")
    def put_scoring_rules(req: FrontierScoreReplaceRequest) -> dict[str, int]:
        try:
            count = replace_frontier_score_rules(
                rules=[
                    {
                        "match_type": r.match_type,
                        "pattern": r.pattern,
                        "weight": r.weight,
                        "enabled": r.enabled,
                        "priority": r.priority,
                        "note": r.note,
                    }
                    for r in req.rules
                ]
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"replaced": count}

    @app.get("/evaluation/rules", tags=["evaluation"], response_model=list[EvaluationRule], summary="List evaluation rules")
    def get_evaluation_rules() -> list[EvaluationRule]:
        rows = list_evaluation_rules()
        return [
            EvaluationRule(
                id=int(r.id),
                action=r.action,
                match_type=r.match_type,
                pattern=r.pattern,
                weight=int(r.weight),
                enabled=bool(r.enabled),
                priority=int(r.priority),
                note=r.note or "",
            )
            for r in rows
        ]

    @app.post("/evaluation/rules", tags=["evaluation"], response_model=EvaluationRule, summary="Create evaluation rule")
    def post_evaluation_rule(req: EvaluationRuleCreate) -> EvaluationRule:
        try:
            rule_id = create_evaluation_rule(
                action=req.action,
                match_type=req.match_type,
                pattern=req.pattern,
                weight=req.weight,
                enabled=req.enabled,
                priority=req.priority,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        row = next((r for r in list_evaluation_rules() if int(r.id) == int(rule_id)), None)
        assert row is not None
        return EvaluationRule(
            id=int(row.id),
            action=row.action,
            match_type=row.match_type,
            pattern=row.pattern,
            weight=int(row.weight),
            enabled=bool(row.enabled),
            priority=int(row.priority),
            note=row.note or "",
        )

    @app.patch("/evaluation/rules/{rule_id}", tags=["evaluation"], response_model=EvaluationRule, summary="Patch evaluation rule")
    def patch_evaluation_rule(rule_id: int, req: EvaluationRulePatch) -> EvaluationRule:
        try:
            ok = update_evaluation_rule(
                rule_id=rule_id,
                action=req.action,
                match_type=req.match_type,
                pattern=req.pattern,
                weight=req.weight,
                enabled=req.enabled,
                priority=req.priority,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not ok:
            raise HTTPException(status_code=404, detail="evaluation_rule_not_found")
        row = next((r for r in list_evaluation_rules() if int(r.id) == int(rule_id)), None)
        if row is None:
            raise HTTPException(status_code=404, detail="evaluation_rule_not_found")
        return EvaluationRule(
            id=int(row.id),
            action=row.action,
            match_type=row.match_type,
            pattern=row.pattern,
            weight=int(row.weight),
            enabled=bool(row.enabled),
            priority=int(row.priority),
            note=row.note or "",
        )

    @app.delete("/evaluation/rules/{rule_id}", tags=["evaluation"], summary="Delete evaluation rule")
    def remove_evaluation_rule(rule_id: int) -> dict[str, bool]:
        ok = delete_evaluation_rule(rule_id=rule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="evaluation_rule_not_found")
        return {"deleted": True}

    @app.put("/evaluation/rules", tags=["evaluation"], summary="Replace evaluation rules")
    def put_evaluation_rules(req: EvaluationRuleReplaceRequest) -> dict[str, int]:
        try:
            count = replace_evaluation_rules(
                rules=[
                    {
                        "action": r.action,
                        "match_type": r.match_type,
                        "pattern": r.pattern,
                        "weight": r.weight,
                        "enabled": r.enabled,
                        "priority": r.priority,
                        "note": r.note,
                    }
                    for r in req.rules
                ]
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"replaced": count}

    @app.get("/runtime-config", tags=["runtime-config"], response_model=list[RuntimeConfigItem], summary="List runtime config")
    def get_runtime_config() -> list[RuntimeConfigItem]:
        rows = list_runtime_configs()
        return [
            RuntimeConfigItem(
                id=int(r.id),
                config_key=r.config_key,
                config_value=r.config_value,
                enabled=bool(r.enabled),
                note=r.note or "",
            )
            for r in rows
        ]

    @app.post("/runtime-config", tags=["runtime-config"], response_model=RuntimeConfigItem, summary="Create runtime config")
    def post_runtime_config(req: RuntimeConfigCreate) -> RuntimeConfigItem:
        try:
            row_id = create_runtime_config(
                config_key=req.config_key,
                config_value=req.config_value,
                enabled=req.enabled,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        row = next((r for r in list_runtime_configs() if int(r.id) == int(row_id)), None)
        assert row is not None
        return RuntimeConfigItem(
            id=int(row.id),
            config_key=row.config_key,
            config_value=row.config_value,
            enabled=bool(row.enabled),
            note=row.note or "",
        )

    @app.patch("/runtime-config/{config_id}", tags=["runtime-config"], response_model=RuntimeConfigItem, summary="Patch runtime config")
    def patch_runtime_config(config_id: int, req: RuntimeConfigPatch) -> RuntimeConfigItem:
        try:
            ok = update_runtime_config(
                config_id=config_id,
                config_key=req.config_key,
                config_value=req.config_value,
                enabled=req.enabled,
                note=req.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not ok:
            raise HTTPException(status_code=404, detail="runtime_config_not_found")
        row = next((r for r in list_runtime_configs() if int(r.id) == int(config_id)), None)
        if row is None:
            raise HTTPException(status_code=404, detail="runtime_config_not_found")
        return RuntimeConfigItem(
            id=int(row.id),
            config_key=row.config_key,
            config_value=row.config_value,
            enabled=bool(row.enabled),
            note=row.note or "",
        )

    @app.delete("/runtime-config/{config_id}", tags=["runtime-config"], summary="Delete runtime config")
    def remove_runtime_config(config_id: int) -> dict[str, bool]:
        ok = delete_runtime_config(config_id=config_id)
        if not ok:
            raise HTTPException(status_code=404, detail="runtime_config_not_found")
        return {"deleted": True}

    @app.put("/runtime-config", tags=["runtime-config"], summary="Replace runtime config")
    def put_runtime_config(req: RuntimeConfigReplaceRequest) -> dict[str, int]:
        try:
            count = replace_runtime_configs(
                rows=[
                    {
                        "config_key": r.config_key,
                        "config_value": r.config_value,
                        "enabled": r.enabled,
                        "note": r.note,
                    }
                    for r in req.rows
                ]
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"replaced": count}

    @app.get(
        "/runs/{run_key}",
        tags=["runs"],
        summary="Get run status and recent event history",
        description="Returns latest status plus recent event history for a single run key.",
        response_model=RunStatusResponse,
        responses={404: {"model": ErrorResponse, "description": "Run key not found."}},
    )
    def get_run_status(run_key: str, history_limit: int = 20) -> RunStatusResponse:
        session_factory = create_session_factory()
        with session_factory() as session:
            rows = (
                session.query(RawWebIngestionEvent)
                .filter(RawWebIngestionEvent.orchestration_id == run_key)
                .order_by(desc(RawWebIngestionEvent.id))
                .limit(max(1, min(history_limit, 200)))
                .all()
            )
        if not rows:
            raise HTTPException(status_code=404, detail="run_not_found")
        now = datetime.now(UTC)
        stale_seconds = _stale_threshold_seconds()
        events = [_event_summary(row, now, stale_seconds) for row in rows]
        latest = events[0]
        return RunStatusResponse(
            run_key=run_key,
            latest_status=latest.status,
            latest_event_type=latest.event_type,
            active_event_id=latest.event_id if latest.status == "running" else None,
            is_running=latest.status == "running",
            latest_heartbeat_age_seconds=latest.heartbeat_age_seconds,
            stale_threshold_seconds=stale_seconds,
            events=events,
        )

    @app.get(
        "/runs",
        tags=["runs"],
        summary="List recent runs",
        description="Returns a summary of recent runs ordered by latest event id descending.",
        response_model=RunListResponse,
    )
    def list_runs(limit: int = 20) -> RunListResponse:
        bounded_limit = max(1, min(limit, 200))
        session_factory = create_session_factory()
        with session_factory() as session:
            recent_events = (
                session.query(RawWebIngestionEvent)
                .order_by(desc(RawWebIngestionEvent.id))
                .limit(1000)
                .all()
            )
        now = datetime.now(UTC)
        items: list[RunListItem] = []
        seen: set[str] = set()
        for event in recent_events:
            run_key = event.orchestration_id
            if run_key in seen:
                continue
            seen.add(run_key)
            items.append(
                RunListItem(
                    run_key=run_key,
                    latest_status=event.status,
                    latest_event_type=event.event_type,
                    is_running=event.status == "running",
                    heartbeat_age_seconds=_heartbeat_age_seconds(event.heartbeat_at, now),
                    updated_at=event.updated_at,
                )
            )
            if len(items) >= bounded_limit:
                break
        return RunListResponse(runs=items)

    # -----------------------------------------------------------------------
    # URL intelligence endpoints
    # -----------------------------------------------------------------------

    @app.post(
        "/url-intelligence/decide",
        tags=["url-intelligence"],
        response_model=URLDecideResponse,
        summary="Classify a URL",
        description=(
            "Classifies a single URL and returns a recommended crawl action, URL role, scores, "
            "and reason codes.\n\n"
            "No database access — purely in-memory analysis of the URL string plus optional "
            "source context and pattern stats you supply in the request body."
        ),
        responses={400: {"model": ErrorResponse, "description": "URL could not be parsed."}},
    )
    def post_url_decide(req: URLDecideRequest) -> URLDecideResponse:
        ctx = SourceContext(
            source_type=req.source_type,
            anchor_text=req.anchor_text,
            source_page_role=req.source_page_role,
            has_english_hreflang=req.has_english_hreflang,
            came_from_sitemap=req.came_from_sitemap,
            source_page_produced_document_candidates=req.source_page_produced_document_candidates,
            source_is_navigation_heavy=req.source_is_navigation_heavy,
        )
        stats: PatternStats | None = None
        if req.pattern_sample_count is not None:
            stats = PatternStats(
                sample_count=req.pattern_sample_count,
                render_needed_count=req.pattern_render_needed_count,
                candidate_document_count=req.pattern_candidate_document_count,
                technical_document_count=req.pattern_technical_document_count,
                noise_count=req.pattern_noise_count,
                useful_link_count=req.pattern_useful_link_count,
                avg_total_ms=req.pattern_avg_total_ms,
            )
        try:
            decision = url_intelligence_decide(req.url, context=ctx, stats=stats)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"url_parse_error: {exc}") from exc
        return URLDecideResponse(
            canonical_url=decision.canonical_url,
            next_action=decision.next_action.value,
            url_role=decision.url_role.value,
            final_score=decision.scores.final_score,
            url_score=decision.scores.url_score,
            source_score=decision.scores.source_score,
            pattern_score=decision.scores.pattern_score,
            reason_codes=list(decision.reason_codes),
            selected_template=decision.selected_template,
        )

    @app.get(
        "/url-intelligence/crawl-plans/{run_key}",
        tags=["url-intelligence"],
        response_model=CrawlPlanResponse,
        summary="Run a crawl plan for a crawl run",
        description=(
            "Loads DB data for the given crawl run, runs the URL intelligence planner, "
            "and returns a structured planning report.\n\n"
            "Read-only — does not mutate the frontier or any database rows."
        ),
        responses={404: {"model": ErrorResponse, "description": "Crawl run key not found."}},
    )
    def get_crawl_plan(
        run_key: str,
        max_static_gets: int = 200,
        max_renders: int = 20,
        max_document_fetches: int = 100,
        max_static_gets_per_host: int = 50,
        max_renders_per_host: int = 5,
        max_static_gets_per_template: int = 30,
        max_renders_per_template: int = 3,
        min_host_exploration_slots: int = 5,
    ) -> CrawlPlanResponse:
        budget = CrawlBudget(
            max_static_gets=max_static_gets,
            max_renders=max_renders,
            max_document_fetches=max_document_fetches,
            max_static_gets_per_host=max_static_gets_per_host,
            max_renders_per_host=max_renders_per_host,
            max_static_gets_per_template=max_static_gets_per_template,
            max_renders_per_template=max_renders_per_template,
            min_host_exploration_slots=min_host_exploration_slots,
        )
        session_factory = create_session_factory()
        try:
            with session_factory() as session:
                report = run_planning_from_db(session, crawl_run_key=run_key, budget=budget)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        summary = report.to_summary_dict()
        return CrawlPlanResponse(
            crawl_run_key=report.crawl_run_key,
            crawl_run_id=report.crawl_run_id,
            budget_usage=summary["budget_usage"],
            reason_summary=summary["reason_summary"],
            host_summary=summary["host_summary"],
            template_summary=summary["template_summary"],
            stopped_static_get_count=summary["stopped_static_get_count"],
            globally_rejected_count=summary["globally_rejected_count"],
            top_selected=report.top_selected,
            top_deferred=report.top_deferred,
            top_rejected=report.top_rejected,
            top_stopped_static_templates=report.top_stopped_static_templates,
            top_document_fetches=report.top_document_fetches,
        )

    @app.get(
        "/url-intelligence/crawl-plans/{run_key}/compare",
        tags=["url-intelligence"],
        response_model=CrawlPlanCompareResponse,
        summary="Compare actual fetches vs crawl plan",
        description=(
            "Loads DB data for the given crawl run, produces a crawl plan, then compares "
            "what was actually fetched against what the planner would recommend.\n\n"
            "Returns per-host and per-template reduction opportunities, "
            "document URLs the planner would prioritise that have not yet been fetched, "
            "and templates where static GET should be stopped.\n\n"
            "Read-only — does not mutate the frontier or any database rows."
        ),
        responses={404: {"model": ErrorResponse, "description": "Crawl run key not found."}},
    )
    def get_crawl_plan_compare(
        run_key: str,
        max_static_gets: int = 200,
        max_renders: int = 20,
        max_document_fetches: int = 100,
        max_static_gets_per_host: int = 50,
        max_renders_per_host: int = 5,
        max_static_gets_per_template: int = 30,
        max_renders_per_template: int = 3,
        min_host_exploration_slots: int = 5,
    ) -> CrawlPlanCompareResponse:
        budget = CrawlBudget(
            max_static_gets=max_static_gets,
            max_renders=max_renders,
            max_document_fetches=max_document_fetches,
            max_static_gets_per_host=max_static_gets_per_host,
            max_renders_per_host=max_renders_per_host,
            max_static_gets_per_template=max_static_gets_per_template,
            max_renders_per_template=max_renders_per_template,
            min_host_exploration_slots=min_host_exploration_slots,
        )
        session_factory = create_session_factory()
        try:
            with session_factory() as session:
                dataset = load_analysis_dataset_from_db(session, crawl_run_key=run_key)
                report = run_planning_from_db(session, crawl_run_key=run_key, budget=budget)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        comparison = compare_actual_vs_planned(dataset, report.plan)
        d = comparison.to_dict()
        return CrawlPlanCompareResponse(**d)

    @app.on_event("shutdown")
    def _shutdown() -> None:
        state.stop_event.set()

    return app


def main() -> int:
    _configure_logging()
    host = os.getenv("MATERIAL_INGESTION_RUNTIME_HOST", "0.0.0.0")
    port = int(os.getenv("MATERIAL_INGESTION_RUNTIME_PORT", "8080"))
    sleep_seconds = float(os.getenv("MATERIAL_INGESTION_RUNTIME_POLL_SECONDS", "2.0"))

    state = RuntimeState()
    discover_workers = max(
        0,
        get_runtime_int_config(
            key="core_worker_discover_count",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_WORKER_DISCOVER_COUNT", "1")),
        ),
    )
    build_workers = max(
        0,
        get_runtime_int_config(
            key="core_worker_build_count",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_WORKER_BUILD_COUNT", "1")),
        ),
    )
    fetch_workers = max(
        0,
        get_runtime_int_config(
            key="core_worker_fetch_count",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_WORKER_FETCH_COUNT", "1")),
        ),
    )
    evaluate_workers = max(
        0,
        get_runtime_int_config(
            key="core_worker_evaluate_count",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_WORKER_EVALUATE_COUNT", "1")),
        ),
    )
    get_workers = max(
        0,
        get_runtime_int_config(
            key="core_worker_get_count",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_WORKER_GET_COUNT", "0")),
        ),
    )
    if discover_workers + build_workers + fetch_workers + evaluate_workers + get_workers == 0:
        discover_workers = 1

    worker_threads: list[threading.Thread] = []
    for idx in range(discover_workers):
        thread = threading.Thread(
            target=_run_worker_loop,
            args=(state, sleep_seconds, "discover"),
            daemon=True,
            name=f"web-worker-discover-{idx+1}",
        )
        worker_threads.append(thread)
    for idx in range(build_workers):
        thread = threading.Thread(
            target=_run_worker_loop,
            args=(state, sleep_seconds, "build"),
            daemon=True,
            name=f"web-worker-build-{idx+1}",
        )
        worker_threads.append(thread)
    for idx in range(fetch_workers):
        thread = threading.Thread(
            target=_run_worker_loop,
            args=(state, sleep_seconds, "fetch"),
            daemon=True,
            name=f"web-worker-fetch-{idx+1}",
        )
        worker_threads.append(thread)
    for idx in range(evaluate_workers):
        thread = threading.Thread(
            target=_run_worker_loop,
            args=(state, sleep_seconds, "evaluate"),
            daemon=True,
            name=f"web-worker-evaluate-{idx+1}",
        )
        worker_threads.append(thread)
    for idx in range(get_workers):
        thread = threading.Thread(
            target=_run_worker_loop,
            args=(state, sleep_seconds, "get"),
            daemon=True,
            name=f"web-worker-get-{idx+1}",
        )
        worker_threads.append(thread)

    evaluate_scheduler_enabled = bool(
        get_runtime_int_config(
            key="core_evaluate_scheduler_enabled",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_EVALUATE_SCHEDULER_ENABLED", "1")),
        )
    )
    evaluate_scheduler_interval = float(os.getenv("MATERIAL_INGESTION_CORE_EVALUATE_SCHEDULER_SECONDS", "10"))
    evaluate_scheduler_batch_size = max(1, int(os.getenv("MATERIAL_INGESTION_CORE_EVALUATE_BATCH_SIZE", "500")))
    get_scheduler_enabled = bool(
        get_runtime_int_config(
            key="core_get_scheduler_enabled",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_GET_SCHEDULER_ENABLED", "0")),
        )
    )
    get_scheduler_interval = float(os.getenv("MATERIAL_INGESTION_CORE_GET_SCHEDULER_SECONDS", "15"))
    get_scheduler_batch_size = max(1, int(os.getenv("MATERIAL_INGESTION_CORE_GET_BATCH_SIZE", "500")))
    get_scheduler_concurrency = max(1, int(os.getenv("MATERIAL_INGESTION_CORE_GET_MAX_CONCURRENCY", "20")))
    scheduler_threads: list[threading.Thread] = []
    if evaluate_scheduler_enabled:
        scheduler = threading.Thread(
            target=_run_evaluate_scheduler_loop,
            args=(state, evaluate_scheduler_interval, evaluate_scheduler_batch_size),
            daemon=True,
            name="web-evaluate-scheduler",
        )
        scheduler_threads.append(scheduler)
    if get_scheduler_enabled:
        scheduler = threading.Thread(
            target=_run_get_scheduler_loop,
            args=(state, get_scheduler_interval, get_scheduler_batch_size, get_scheduler_concurrency),
            daemon=True,
            name="web-get-scheduler",
        )
        scheduler_threads.append(scheduler)
    for thread in worker_threads:
        thread.start()
    for thread in scheduler_threads:
        thread.start()

    app = build_app(state)
    previous_sigint = signal.getsignal(signal.SIGINT)
    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def _handle_shutdown_signal(_sig: int, _frame: object) -> None:
        state.stop_event.set()

    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    signal.signal(signal.SIGTERM, _handle_shutdown_signal)
    logger.info(
        "runtime started host=%s port=%s scope=global-core-events workers_discover=%s workers_build=%s workers_fetch=%s workers_evaluate=%s workers_get=%s evaluate_scheduler_enabled=%s get_scheduler_enabled=%s",
        host,
        port,
        discover_workers,
        build_workers,
        fetch_workers,
        evaluate_workers,
        get_workers,
        evaluate_scheduler_enabled,
        get_scheduler_enabled,
    )
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)
        state.stop_event.set()
        for thread in worker_threads + scheduler_threads:
            thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
