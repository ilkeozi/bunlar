from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import json
import logging
from decimal import Decimal
from xml.etree import ElementTree
from urllib.parse import urlsplit

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebSitemapAlternate,
    RawWebSitemapEntry,
    RawWebSitemapSource,
    RawWebUriAlias,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_host_scope_service import register_discovered_host
from material_ingestion.services.web_crawl_identity_service import canonicalize_uri, ensure_uri_identity
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger("material_ingestion.web")


def _normalize_alternates(raw_alternates: object) -> list[tuple[str, str]]:
    if not isinstance(raw_alternates, list):
        return []
    out: list[tuple[str, str]] = []
    for item in raw_alternates:
        hreflang = ""
        href = ""
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            hreflang = str(item[0] or "").strip()
            href = str(item[1] or "").strip()
        elif isinstance(item, dict):
            hreflang = str(item.get("hreflang", "") or "").strip()
            href = str(item.get("href", "") or "").strip()
        if hreflang and href:
            out.append((hreflang, href))
    return out


def _parse_lastmod(text: str) -> datetime | None:
    value = (text or "").strip()
    if not value:
        return None
    # Sitemap protocol allows full datetime or date. Normalize UTC "Z" variant.
    candidates = [value, value.replace("Z", "+00:00")]
    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def _parse_priority(text: str) -> float | None:
    value = (text or "").strip()
    if not value:
        return None
    try:
        parsed = float(Decimal(value))
    except Exception:
        return None
    if parsed < 0.0 or parsed > 1.0:
        return None
    return parsed


def parse_sitemap_document(xml_text: str) -> tuple[list[tuple[str, datetime | None, str | None, float | None]], list[str]]:
    root = ElementTree.fromstring(xml_text)
    urls: list[tuple[str, datetime | None, str | None, float | None]] = []
    nested_sitemaps: list[str] = []
    ns_trim = lambda tag: tag.split("}", 1)[-1]

    for node in root.iter():
        node_tag = ns_trim(node.tag)
        if node_tag == "url":
            loc = None
            lastmod = None
            changefreq = None
            priority = None
            for child in node:
                key = ns_trim(child.tag)
                if key == "loc":
                    loc = (child.text or "").strip()
                elif key == "lastmod":
                    lastmod = _parse_lastmod(child.text or "")
                elif key == "changefreq":
                    cf = (child.text or "").strip().lower()
                    changefreq = cf or None
                elif key == "priority":
                    priority = _parse_priority(child.text or "")
            if loc:
                urls.append((loc, lastmod, changefreq, priority))
        elif node_tag == "sitemap":
            for child in node:
                key = ns_trim(child.tag)
                if key == "loc":
                    loc = (child.text or "").strip()
                    if loc:
                        nested_sitemaps.append(loc)
                    break
    return urls, nested_sitemaps


def parse_sitemap_urls(xml_text: str) -> list[tuple[str, datetime | None, str | None, float | None]]:
    urls, _ = parse_sitemap_document(xml_text)
    return urls


def has_successful_sitemap_source(*, host_id: int, sitemap_url: str) -> bool:
    session_factory = create_session_factory()
    with session_factory() as session:
        source = (
            session.query(RawWebSitemapSource)
            .filter(RawWebSitemapSource.host_id == host_id, RawWebSitemapSource.sitemap_url == sitemap_url)
            .first()
        )
        if source is None:
            return False
        return str(source.last_fetch_status or "").lower() == "success"


def persist_sitemap_entries(*, host_id: int, sitemap_url: str, discovered_via: str, xml_text: str) -> int:
    entries = parse_sitemap_urls(xml_text)
    session_factory = create_session_factory()
    with session_factory() as session:
        source = (
            session.query(RawWebSitemapSource)
            .filter(RawWebSitemapSource.host_id == host_id, RawWebSitemapSource.sitemap_url == sitemap_url)
            .first()
        )
        if source is None:
            source = RawWebSitemapSource(
                host_id=host_id,
                sitemap_url=sitemap_url,
                discovered_via=discovered_via,
                last_fetch_status="success",
                last_fetched_at=datetime.now(UTC),
            )
            session.add(source)
            session.commit()
            session.refresh(source)
        else:
            source.discovered_via = discovered_via or source.discovered_via
            source.last_fetch_status = "success"
            source.last_fetched_at = datetime.now(UTC)
            session.commit()

        inserted = 0
        for loc, lastmod, changefreq, priority in entries:
            identity = ensure_uri_identity(loc)
            register_discovered_host(urlsplit(identity.canonical_uri).netloc, discovery_source=f"sitemap:{sitemap_url}")
            exists = (
                session.query(RawWebSitemapEntry)
                .filter(
                    RawWebSitemapEntry.sitemap_source_id == source.id,
                    RawWebSitemapEntry.uri_identity_id == identity.uri_identity_id,
                )
                .first()
            )
            if exists is not None:
                continue
            session.add(
                RawWebSitemapEntry(
                    sitemap_source_id=int(source.id),
                    uri_identity_id=identity.uri_identity_id,
                    lastmod_at=lastmod,
                    changefreq=changefreq,
                    priority=priority,
                    alternates_json=None,
                    images_json=None,
                    news_story_json=None,
                )
            )
            inserted += 1
        session.commit()
        return inserted


def persist_sitemap_urls(
    *,
    host_id: int,
    sitemap_url: str,
    discovered_via: str,
    entries: list[dict[str, object]],
    heartbeat_callback: Callable[[], None] | None = None,
    progress_log_every: int = 100,
    commit_every: int = 250,
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        source = (
            session.query(RawWebSitemapSource)
            .filter(RawWebSitemapSource.host_id == host_id, RawWebSitemapSource.sitemap_url == sitemap_url)
            .first()
        )
        if source is None:
            source = RawWebSitemapSource(
                host_id=host_id,
                sitemap_url=sitemap_url,
                discovered_via=discovered_via,
                last_fetch_status="success",
                last_fetched_at=datetime.now(UTC),
            )
            session.add(source)
            session.commit()
            session.refresh(source)
        else:
            source.discovered_via = discovered_via or source.discovered_via
            source.last_fetch_status = "success"
            source.last_fetched_at = datetime.now(UTC)
            session.commit()

        if heartbeat_callback:
            heartbeat_callback()
        logger.info("event=sitemap_persist_started sitemap_url=%s total=%s", sitemap_url, len(entries))

        inserted = 0
        processed = 0
        pending = 0
        chunk_size = max(1, commit_every)
        prepared_rows: list[
            tuple[str, str, str, str, datetime | None, str | None, float | None, str | None, str | None, str | None, list[tuple[str, str]]]
        ] = []
        hostnames: set[str] = set()
        for entry in entries:
            observed_uri = str(entry.get("url", "") or "").strip()
            if not observed_uri:
                continue
            canonical = canonicalize_uri(observed_uri)
            normalized_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            hostname = urlsplit(canonical).netloc
            raw_changefreq = entry.get("changefreq")
            changefreq = str(raw_changefreq).strip().lower() if raw_changefreq is not None else None
            if not changefreq:
                changefreq = None
            raw_priority = entry.get("priority")
            priority = float(raw_priority) if isinstance(raw_priority, (float, int)) else None
            raw_lastmod = entry.get("lastmod_at")
            lastmod_at = raw_lastmod if isinstance(raw_lastmod, datetime) else None
            raw_alternates = entry.get("alternates")
            alternates = _normalize_alternates(raw_alternates)
            alternates_json = None
            raw_images = entry.get("images")
            images_json = json.dumps(raw_images, sort_keys=True) if raw_images is not None else None
            raw_news_story = entry.get("news_story")
            news_story_json = json.dumps(raw_news_story, sort_keys=True) if raw_news_story is not None else None
            prepared_rows.append(
                (
                    observed_uri,
                    canonical,
                    normalized_hash,
                    hostname,
                    lastmod_at,
                    changefreq,
                    priority,
                    alternates_json,
                    images_json,
                    news_story_json,
                    alternates,
                )
            )
            if hostname:
                hostnames.add(hostname)

        host_id_by_name: dict[str, int] = {}
        for hostname in sorted(hostnames):
            host_id_by_name[hostname] = register_discovered_host(hostname, discovery_source=f"sitemap:{sitemap_url}")
        session.commit()

        for start in range(0, len(prepared_rows), chunk_size):
            chunk = prepared_rows[start : start + chunk_size]
            processed += len(chunk)

            identity_values = []
            hashes = []
            for _observed, canonical, normalized_hash, hostname, _lastmod, _changefreq, _priority, _alternates_json, _images_json, _news_story_json, _alternates in chunk:
                host_id = host_id_by_name.get(hostname)
                if not host_id:
                    continue
                hashes.append(normalized_hash)
                identity_values.append(
                    {
                        "canonical_uri": canonical,
                        "normalized_hash": normalized_hash,
                        "host_id": host_id,
                    }
                )
            if identity_values:
                session.execute(
                    pg_insert(RawWebUriIdentity)
                    .values(identity_values)
                    .on_conflict_do_nothing(index_elements=["normalized_hash"])
                )

            identity_rows = session.execute(
                select(RawWebUriIdentity.id, RawWebUriIdentity.normalized_hash).where(
                    RawWebUriIdentity.normalized_hash.in_(hashes)
                )
            ).all()
            identity_id_by_hash = {str(row[1]): int(row[0]) for row in identity_rows}

            alias_values = []
            entry_values = []
            for (
                observed_uri,
                _canonical,
                normalized_hash,
                _hostname,
                lastmod_at,
                changefreq,
                priority,
                alternates_json,
                images_json,
                news_story_json,
                alternates,
            ) in chunk:
                uri_identity_id = identity_id_by_hash.get(normalized_hash)
                if not uri_identity_id:
                    continue
                alias_values.append(
                    {
                        "uri_identity_id": uri_identity_id,
                        "observed_uri": observed_uri,
                    }
                )
                entry_values.append(
                    {
                        "sitemap_source_id": int(source.id),
                        "uri_identity_id": uri_identity_id,
                        "lastmod_at": lastmod_at,
                        "changefreq": changefreq,
                        "priority": priority,
                        "alternates_json": alternates_json,
                        "images_json": images_json,
                        "news_story_json": news_story_json,
                        "alternates": alternates,
                    }
                )

            if alias_values:
                session.execute(
                    pg_insert(RawWebUriAlias)
                    .values(alias_values)
                    .on_conflict_do_nothing(index_elements=["uri_identity_id", "observed_uri"])
                )
            if entry_values:
                candidate_ids = sorted({int(v["uri_identity_id"]) for v in entry_values})
                entry_by_uri_id = {int(v["uri_identity_id"]): v for v in entry_values}
                existing_ids = {
                    int(row[0])
                    for row in session.execute(
                        select(RawWebSitemapEntry.uri_identity_id).where(
                            RawWebSitemapEntry.sitemap_source_id == int(source.id),
                            RawWebSitemapEntry.uri_identity_id.in_(candidate_ids),
                        )
                    ).all()
                }
                new_ids = [uri_id for uri_id in candidate_ids if uri_id not in existing_ids]
                if new_ids:
                    session.execute(
                        pg_insert(RawWebSitemapEntry)
                        .values(
                            [
                                {
                                    "sitemap_source_id": int(source.id),
                                    "uri_identity_id": uri_id,
                                    "lastmod_at": entry_by_uri_id[uri_id]["lastmod_at"],
                                    "changefreq": entry_by_uri_id[uri_id]["changefreq"],
                                    "priority": entry_by_uri_id[uri_id]["priority"],
                                    "alternates_json": entry_by_uri_id[uri_id]["alternates_json"],
                                    "images_json": entry_by_uri_id[uri_id]["images_json"],
                                    "news_story_json": entry_by_uri_id[uri_id]["news_story_json"],
                                }
                                for uri_id in new_ids
                            ]
                        )
                        .on_conflict_do_nothing(index_elements=["sitemap_source_id", "uri_identity_id"])
                    )
                    entry_rows = session.execute(
                        select(RawWebSitemapEntry.id, RawWebSitemapEntry.uri_identity_id).where(
                            RawWebSitemapEntry.sitemap_source_id == int(source.id),
                            RawWebSitemapEntry.uri_identity_id.in_(new_ids),
                        )
                    ).all()
                    alternate_values = []
                    for entry_id, uri_id in entry_rows:
                        metadata = entry_by_uri_id.get(int(uri_id)) or {}
                        alternates = metadata.get("alternates") or []
                        for hreflang, href in alternates:
                            alternate_values.append(
                                {
                                    "sitemap_entry_id": int(entry_id),
                                    "hreflang": hreflang,
                                    "href": href,
                                }
                            )
                    if alternate_values:
                        session.execute(
                            pg_insert(RawWebSitemapAlternate)
                            .values(alternate_values)
                            .on_conflict_do_nothing(index_elements=["sitemap_entry_id", "hreflang", "href"])
                        )
                    inserted += len(new_ids)

            session.commit()
            if heartbeat_callback:
                heartbeat_callback()
            if processed % max(1, progress_log_every) == 0 or processed == len(prepared_rows):
                logger.info(
                    "event=sitemap_persist_progress sitemap_url=%s processed=%s inserted=%s total=%s",
                    sitemap_url,
                    processed,
                    inserted,
                    len(prepared_rows),
                )
        logger.info(
            "event=sitemap_persist_completed sitemap_url=%s processed=%s inserted=%s total=%s",
            sitemap_url,
            processed,
            inserted,
            len(prepared_rows),
        )
        return inserted
