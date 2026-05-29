from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import and_, exists, insert, text, update

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebCrawlDecision,
    RawWebEvaluationRule,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebUriIdentity,
)
from material_ingestion.services.shared_cache_service import local_cache_get, local_cache_set
from material_ingestion.services.web_runtime_config_service import get_runtime_int_config

logger = logging.getLogger("material_ingestion.web")

_EVAL_RULES_CACHE_KEY = "eval_rules:snapshot"
_EVAL_RULES_CACHE_TTL = max(1, int(os.getenv("MATERIAL_INGESTION_EVAL_RULES_CACHE_TTL", "30")))


@dataclass(frozen=True)
class _RuleSnapshot:
    id: int
    match_type: str
    pattern: str
    weight: int
    action: str


def _rule_matches(rule: _RuleSnapshot, haystack: str) -> bool:
    match_type = str(rule.match_type or "").strip().lower()
    pattern = str(rule.pattern or "")
    if not pattern:
        return False
    if match_type == "contains":
        return pattern.lower() in haystack.lower()
    if match_type == "suffix":
        return haystack.lower().endswith(pattern.lower())
    if match_type == "regex":
        return re.search(pattern, haystack, re.IGNORECASE) is not None
    return False


def _load_rules(session_factory: object) -> list[_RuleSnapshot]:
    cached = local_cache_get(_EVAL_RULES_CACHE_KEY)
    if cached is not None:
        return cached  # type: ignore[return-value]
    with session_factory() as session:  # type: ignore[operator]
        db_rules = (
            session.query(RawWebEvaluationRule)
            .filter(RawWebEvaluationRule.enabled.is_(True))
            .order_by(RawWebEvaluationRule.priority.asc(), RawWebEvaluationRule.id.asc())
            .all()
        )
        snapshots = [
            _RuleSnapshot(
                id=int(r.id),
                match_type=str(r.match_type or ""),
                pattern=str(r.pattern or ""),
                weight=int(r.weight or 0),
                action=str(r.action or "defer"),
            )
            for r in db_rules
        ]
    local_cache_set(_EVAL_RULES_CACHE_KEY, snapshots, _EVAL_RULES_CACHE_TTL)
    return snapshots


def evaluate_frontier_batch(
    *,
    batch_size: int = 500,
    force: bool = False,
    heartbeat_callback: Callable[[], None] | None = None,
    progress_callback: Callable[[int, int, int, int], None] | None = None,
) -> tuple[int, int, int, int]:
    session_factory = create_session_factory()
    promote_threshold = get_runtime_int_config(
        key="core_evaluation_promote_threshold",
        default=int(os.getenv("MATERIAL_INGESTION_EVALUATION_PROMOTE_THRESHOLD", "6")),
    )
    process_limit = max(1, int(batch_size))
    processed = 0
    promoted = 0
    deferred = 0
    skipped = 0

    rules = _load_rules(session_factory)

    with session_factory() as session:
        latest_attempt_id = (
            session.query(RawWebHttpFetchAttempt.uri_identity_id, RawWebHttpFetchAttempt.id.label("latest_attempt_id"))
            .filter(RawWebHttpFetchAttempt.outcome == "success")
            .order_by(RawWebHttpFetchAttempt.uri_identity_id.asc(), RawWebHttpFetchAttempt.id.desc())
            .distinct(RawWebHttpFetchAttempt.uri_identity_id)
            .subquery()
        )

        evaluated_exists = exists().where(
            and_(
                RawWebCrawlDecision.uri_identity_id == RawWebFrontierItem.uri_identity_id,
                RawWebCrawlDecision.reason_code.in_(["eval_promote", "eval_defer", "eval_skip"]),
            )
        )

        query = (
            session.query(
                RawWebFrontierItem,
                RawWebUriIdentity.canonical_uri,
                RawWebHttpRepresentation.content_type,
                RawWebHttpRepresentation.content_language,
                RawWebHttpRepresentation.content_disposition,
                RawWebHttpRepresentation.link,
            )
            .join(RawWebUriIdentity, RawWebUriIdentity.id == RawWebFrontierItem.uri_identity_id)
            .join(latest_attempt_id, latest_attempt_id.c.uri_identity_id == RawWebFrontierItem.uri_identity_id)
            .join(RawWebHttpRepresentation, RawWebHttpRepresentation.fetch_attempt_id == latest_attempt_id.c.latest_attempt_id)
            .filter(RawWebFrontierItem.state == "completed")
            .filter(RawWebFrontierItem.state_reason_code.in_(["head_metadata_success", "recent_success_skip"]))
        )
        if not bool(force):
            query = query.filter(~evaluated_exists)
        rows = (
            query.order_by(RawWebFrontierItem.id.asc()).limit(process_limit).all()
        )

        if not rows:
            return 0, 0, 0, 0

        # Preload existing eval decisions for the whole batch in one query to avoid N+1.
        # In normal mode the ~evaluated_exists filter guarantees none exist, so we skip this.
        # In force mode items may already have decisions that need updating rather than inserting.
        existing_decisions: dict[tuple[int, int], RawWebCrawlDecision] = {}
        if bool(force):
            uri_ids_in_batch = [int(fi.uri_identity_id) for fi, *_ in rows]
            run_ids_in_batch = list({int(fi.crawl_run_id) for fi, *_ in rows})
            prior = (
                session.query(RawWebCrawlDecision)
                .filter(
                    RawWebCrawlDecision.crawl_run_id.in_(run_ids_in_batch),
                    RawWebCrawlDecision.uri_identity_id.in_(uri_ids_in_batch),
                    RawWebCrawlDecision.reason_code.in_(["eval_promote", "eval_defer", "eval_skip"]),
                )
                .all()
            )
            for d in prior:
                key = (int(d.crawl_run_id), int(d.uri_identity_id))
                if key not in existing_decisions or int(d.id) > int(existing_decisions[key].id):
                    existing_decisions[key] = d

        promote_ids: list[int] = []
        defer_ids: list[int] = []
        skip_ids: list[int] = []
        decisions_to_insert: list[dict] = []
        decisions_to_update: list[dict] = []

        for frontier_item, canonical_uri, content_type, content_language, content_disposition, link in rows:
            processed += 1
            if heartbeat_callback:
                heartbeat_callback()
            haystack = " ".join(
                [
                    str(canonical_uri or ""),
                    str(content_type or ""),
                    str(content_language or ""),
                    str(content_disposition or ""),
                    str(link or ""),
                ]
            )

            score = 0
            matched_rule_ids: list[int] = []
            matched_actions: set[str] = set()
            for rule in rules:
                if _rule_matches(rule, haystack):
                    score += int(rule.weight or 0)
                    matched_rule_ids.append(int(rule.id))
                    matched_actions.add(str(rule.action or "defer"))

            decision_type = "defer"
            reason_code = "eval_defer"
            if "skip" in matched_actions:
                decision_type = "skip"
                reason_code = "eval_skip"
                skipped += 1
                skip_ids.append(int(frontier_item.id))
            elif "promote" in matched_actions and score >= promote_threshold:
                decision_type = "promote"
                reason_code = "eval_promote"
                promoted += 1
                promote_ids.append(int(frontier_item.id))
            else:
                deferred += 1
                defer_ids.append(int(frontier_item.id))

            detail_json = json.dumps(
                {
                    "score": score,
                    "promote_threshold": promote_threshold,
                    "matched_rule_ids": matched_rule_ids,
                    "frontier_item_id": int(frontier_item.id),
                    "url": str(canonical_uri or ""),
                },
                sort_keys=True,
            )
            existing_eval_decision = existing_decisions.get(
                (int(frontier_item.crawl_run_id), int(frontier_item.uri_identity_id))
            )
            if existing_eval_decision is not None:
                decisions_to_update.append({
                    "id": int(existing_eval_decision.id),
                    "decision_type": decision_type,
                    "reason_code": reason_code,
                    "detail_json": detail_json,
                })
            else:
                decisions_to_insert.append({
                    "crawl_run_id": int(frontier_item.crawl_run_id),
                    "uri_identity_id": int(frontier_item.uri_identity_id),
                    "decision_type": decision_type,
                    "reason_code": reason_code,
                    "detail_json": detail_json,
                })

            if progress_callback and (processed % 100 == 0):
                progress_callback(processed, promoted, deferred, skipped)

        # Bulk frontier item state updates — 3 statements max regardless of batch size.
        if promote_ids:
            session.execute(update(RawWebFrontierItem).where(RawWebFrontierItem.id.in_(promote_ids)).values(state_reason_code="eval_promote"))
        if defer_ids:
            session.execute(update(RawWebFrontierItem).where(RawWebFrontierItem.id.in_(defer_ids)).values(state_reason_code="eval_defer"))
        if skip_ids:
            session.execute(update(RawWebFrontierItem).where(RawWebFrontierItem.id.in_(skip_ids)).values(state_reason_code="eval_skip"))

        # Bulk decision inserts — one statement.
        if decisions_to_insert:
            session.execute(insert(RawWebCrawlDecision), decisions_to_insert)

        # Bulk decision updates (force mode) — executemany, one round-trip.
        if decisions_to_update:
            session.execute(
                text("UPDATE raw_web_crawl_decision SET decision_type=:decision_type, reason_code=:reason_code, detail_json=:detail_json WHERE id=:id"),
                decisions_to_update,
            )

        session.commit()

    logger.info(
        "event=frontier_evaluate_completed processed=%s promoted=%s deferred=%s skipped=%s",
        processed,
        promoted,
        deferred,
        skipped,
    )
    return processed, promoted, deferred, skipped
