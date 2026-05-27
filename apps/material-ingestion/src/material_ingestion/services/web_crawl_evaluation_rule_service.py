from __future__ import annotations

import re

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebEvaluationRule

VALID_MATCH_TYPES = {"contains", "regex", "suffix"}
VALID_ACTIONS = {"promote", "defer", "skip"}


def list_evaluation_rules(*, enabled_only: bool = False) -> list[RawWebEvaluationRule]:
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebEvaluationRule)
        if enabled_only:
            query = query.filter(RawWebEvaluationRule.enabled.is_(True))
        rows = query.order_by(RawWebEvaluationRule.priority.asc(), RawWebEvaluationRule.id.asc()).all()
        for row in rows:
            session.expunge(row)
        return rows


def create_evaluation_rule(
    *,
    action: str,
    match_type: str,
    pattern: str,
    weight: int,
    enabled: bool = True,
    priority: int = 100,
    note: str = "",
) -> int:
    normalized_action = str(action or "").strip().lower()
    if normalized_action not in VALID_ACTIONS:
        raise ValueError("invalid_action")
    normalized_match_type = str(match_type or "").strip().lower()
    if normalized_match_type not in VALID_MATCH_TYPES:
        raise ValueError("invalid_match_type")
    cleaned_pattern = str(pattern or "").strip()
    if not cleaned_pattern:
        raise ValueError("empty_pattern")
    if normalized_match_type == "regex":
        re.compile(cleaned_pattern)
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebEvaluationRule(
            action=normalized_action,
            match_type=normalized_match_type,
            pattern=cleaned_pattern,
            weight=int(weight),
            enabled=bool(enabled),
            priority=int(priority),
            note=str(note or ""),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def update_evaluation_rule(
    *,
    rule_id: int,
    action: str | None = None,
    match_type: str | None = None,
    pattern: str | None = None,
    weight: int | None = None,
    enabled: bool | None = None,
    priority: int | None = None,
    note: str | None = None,
) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebEvaluationRule).filter(RawWebEvaluationRule.id == int(rule_id)).first()
        if row is None:
            return False
        if action is not None:
            normalized_action = str(action).strip().lower()
            if normalized_action not in VALID_ACTIONS:
                raise ValueError("invalid_action")
            row.action = normalized_action
        if match_type is not None:
            normalized_match_type = str(match_type).strip().lower()
            if normalized_match_type not in VALID_MATCH_TYPES:
                raise ValueError("invalid_match_type")
            row.match_type = normalized_match_type
        if pattern is not None:
            cleaned_pattern = str(pattern).strip()
            if not cleaned_pattern:
                raise ValueError("empty_pattern")
            if row.match_type == "regex":
                re.compile(cleaned_pattern)
            row.pattern = cleaned_pattern
        elif row.match_type == "regex" and pattern is None and match_type is not None:
            re.compile(str(row.pattern or ""))
        if weight is not None:
            row.weight = int(weight)
        if enabled is not None:
            row.enabled = bool(enabled)
        if priority is not None:
            row.priority = int(priority)
        if note is not None:
            row.note = str(note)
        session.commit()
        return True


def delete_evaluation_rule(*, rule_id: int) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebEvaluationRule).filter(RawWebEvaluationRule.id == int(rule_id)).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def replace_evaluation_rules(*, rules: list[dict[str, object]]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        session.query(RawWebEvaluationRule).delete()
        for item in rules:
            normalized_action = str(item.get("action", "defer")).strip().lower()
            if normalized_action not in VALID_ACTIONS:
                raise ValueError("invalid_action")
            normalized_match_type = str(item.get("match_type", "contains")).strip().lower()
            if normalized_match_type not in VALID_MATCH_TYPES:
                raise ValueError("invalid_match_type")
            cleaned_pattern = str(item.get("pattern", "")).strip()
            if not cleaned_pattern:
                raise ValueError("empty_pattern")
            if normalized_match_type == "regex":
                re.compile(cleaned_pattern)
            session.add(
                RawWebEvaluationRule(
                    action=normalized_action,
                    match_type=normalized_match_type,
                    pattern=cleaned_pattern,
                    weight=int(item.get("weight", 0)),
                    enabled=bool(item.get("enabled", True)),
                    priority=int(item.get("priority", 100)),
                    note=str(item.get("note", "") or ""),
                )
            )
        session.commit()
        return len(rules)
