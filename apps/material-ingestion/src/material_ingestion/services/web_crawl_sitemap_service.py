from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree
from urllib.parse import urlsplit

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebSitemapEntry, RawWebSitemapSource
from material_ingestion.services.web_crawl_host_scope_service import register_discovered_host
from material_ingestion.services.web_crawl_identity_service import ensure_uri_identity


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


def parse_sitemap_document(xml_text: str) -> tuple[list[tuple[str, datetime | None]], list[str]]:
    root = ElementTree.fromstring(xml_text)
    urls: list[tuple[str, datetime | None]] = []
    nested_sitemaps: list[str] = []
    ns_trim = lambda tag: tag.split("}", 1)[-1]

    for node in root.iter():
        node_tag = ns_trim(node.tag)
        if node_tag == "url":
            loc = None
            lastmod = None
            for child in node:
                key = ns_trim(child.tag)
                if key == "loc":
                    loc = (child.text or "").strip()
                elif key == "lastmod":
                    lastmod = _parse_lastmod(child.text or "")
            if loc:
                urls.append((loc, lastmod))
        elif node_tag == "sitemap":
            for child in node:
                key = ns_trim(child.tag)
                if key == "loc":
                    loc = (child.text or "").strip()
                    if loc:
                        nested_sitemaps.append(loc)
                    break
    return urls, nested_sitemaps


def parse_sitemap_urls(xml_text: str) -> list[tuple[str, datetime | None]]:
    urls, _ = parse_sitemap_document(xml_text)
    return urls


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
            )
            session.add(source)
            session.commit()
            session.refresh(source)

        inserted = 0
        for loc, lastmod in entries:
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
                )
            )
            inserted += 1
        session.commit()
        return inserted
