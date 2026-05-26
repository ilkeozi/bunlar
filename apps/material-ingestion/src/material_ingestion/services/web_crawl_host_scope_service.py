from __future__ import annotations

import fnmatch
from urllib.parse import urlsplit

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlAllowlistRule, RawWebCrawlHost


def is_host_allowlisted(hostname: str) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        rows = (
            session.query(RawWebCrawlAllowlistRule.pattern)
            .filter(
                RawWebCrawlAllowlistRule.enabled.is_(True),
                RawWebCrawlAllowlistRule.rule_type == "host_glob",
            )
            .order_by(RawWebCrawlAllowlistRule.priority.asc(), RawWebCrawlAllowlistRule.id.asc())
            .all()
        )
    patterns = [str(row[0]).strip().lower() for row in rows if row and row[0]]
    if not patterns:
        return True
    target = hostname.lower()
    for pattern in patterns:
        if fnmatch.fnmatch(target, pattern):
            return True
        if target == pattern:
            return True
    return False


def register_discovered_host(hostname: str, *, discovery_source: str = "") -> int:
    allowlisted = is_host_allowlisted(hostname)
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebCrawlHost).filter(RawWebCrawlHost.hostname == hostname).first()
        if row is None:
            row = RawWebCrawlHost(
                hostname=hostname,
                source_type="discovered",
                discovery_source=discovery_source,
                allowlist_match=allowlisted,
                auto_crawl_enabled=allowlisted,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

        row.discovery_source = discovery_source or row.discovery_source
        row.allowlist_match = allowlisted
        row.auto_crawl_enabled = allowlisted
        session.commit()
        return int(row.id)


def is_url_host_allowlisted(url: str) -> bool:
    return is_host_allowlisted(urlsplit(url).netloc)


def list_allowlist_rules() -> list[RawWebCrawlAllowlistRule]:
    session_factory = create_session_factory()
    with session_factory() as session:
        rows = (
            session.query(RawWebCrawlAllowlistRule)
            .order_by(RawWebCrawlAllowlistRule.priority.asc(), RawWebCrawlAllowlistRule.id.asc())
            .all()
        )
        for row in rows:
            session.expunge(row)
        return rows


def create_allowlist_rule(*, pattern: str, enabled: bool = True, priority: int = 100, note: str = "") -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebCrawlAllowlistRule(
            pattern=pattern.strip(),
            rule_type="host_glob",
            enabled=bool(enabled),
            priority=int(priority),
            note=note or "",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def update_allowlist_rule(
    *,
    rule_id: int,
    pattern: str | None = None,
    enabled: bool | None = None,
    priority: int | None = None,
    note: str | None = None,
) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebCrawlAllowlistRule).filter(RawWebCrawlAllowlistRule.id == int(rule_id)).first()
        if row is None:
            return False
        if pattern is not None:
            row.pattern = pattern.strip()
        if enabled is not None:
            row.enabled = bool(enabled)
        if priority is not None:
            row.priority = int(priority)
        if note is not None:
            row.note = note
        session.commit()
        return True


def delete_allowlist_rule(*, rule_id: int) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = session.query(RawWebCrawlAllowlistRule).filter(RawWebCrawlAllowlistRule.id == int(rule_id)).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def replace_allowlist_rules(*, rules: list[dict[str, object]]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        session.query(RawWebCrawlAllowlistRule).delete()
        for item in rules:
            session.add(
                RawWebCrawlAllowlistRule(
                    pattern=str(item.get("pattern", "")).strip(),
                    rule_type="host_glob",
                    enabled=bool(item.get("enabled", True)),
                    priority=int(item.get("priority", 100)),
                    note=str(item.get("note", "") or ""),
                )
            )
        session.commit()
        return len(rules)
