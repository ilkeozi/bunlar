from __future__ import annotations

import fnmatch
import os
from urllib.parse import urlsplit

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlHost


def _allowlist_patterns() -> list[str]:
    raw = os.getenv("MATERIAL_INGESTION_CRAWL_ALLOWLIST", "")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def is_host_allowlisted(hostname: str) -> bool:
    patterns = _allowlist_patterns()
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
