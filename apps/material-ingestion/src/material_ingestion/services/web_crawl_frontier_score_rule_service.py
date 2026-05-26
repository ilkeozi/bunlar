from __future__ import annotations

import re

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebFrontierScoreRule

VALID_MATCH_TYPES = {"contains", "regex", "suffix"}


def list_frontier_score_rules(*, enabled_only: bool = False) -> list[RawWebFrontierScoreRule]:
    session_factory = create_session_factory()
    with session_factory() as session:
        query = session.query(RawWebFrontierScoreRule)
        if enabled_only:
            query = query.filter(RawWebFrontierScoreRule.enabled.is_(True))
        rows = query.order_by(RawWebFrontierScoreRule.priority.asc(), RawWebFrontierScoreRule.id.asc()).all()
        for row in rows:
            session.expunge(row)
        return rows


def create_frontier_score_rule(
    *,
    match_type: str,
    pattern: str,
    weight: int,
    enabled: bool = True,
    priority: int = 100,
    note: str = "",
) -> int:
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
        row = RawWebFrontierScoreRule(
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


def update_frontier_score_rule(
    *,
    rule_id: int,
    match_type: str | None = None,
    pattern: str | None = None,
    weight: int | None = None,
    enabled: bool | None = None,
    priority: int | None = None,
    note: str | None = None,
) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebFrontierScoreRule).filter(RawWebFrontierScoreRule.id == int(rule_id)).first()
        if row is None:
            return False
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


def delete_frontier_score_rule(*, rule_id: int) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebFrontierScoreRule).filter(RawWebFrontierScoreRule.id == int(rule_id)).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def replace_frontier_score_rules(*, rules: list[dict[str, object]]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        session.query(RawWebFrontierScoreRule).delete()
        for item in rules:
            normalized_match_type = str(item.get("match_type", "contains")).strip().lower()
            if normalized_match_type not in VALID_MATCH_TYPES:
                raise ValueError("invalid_match_type")
            cleaned_pattern = str(item.get("pattern", "")).strip()
            if not cleaned_pattern:
                raise ValueError("empty_pattern")
            if normalized_match_type == "regex":
                re.compile(cleaned_pattern)
            session.add(
                RawWebFrontierScoreRule(
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
