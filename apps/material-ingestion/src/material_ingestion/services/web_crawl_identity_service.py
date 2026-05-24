from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlHost, RawWebUriAlias, RawWebUriIdentity


@dataclass(slots=True)
class UriIdentityResult:
    host_id: int
    uri_identity_id: int
    canonical_uri: str
    normalized_hash: str


def canonicalize_uri(uri: str) -> str:
    parts = urlsplit(uri.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    while "//" in path:
        path = path.replace("//", "/")
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def _hash_uri(uri: str) -> str:
    return hashlib.sha256(uri.encode("utf-8")).hexdigest()


def ensure_host(hostname: str, source_type: str = "seed", allowlist_match: bool = True) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        host = session.query(RawWebCrawlHost).filter(RawWebCrawlHost.hostname == hostname).first()
        if host is None:
            host = RawWebCrawlHost(
                hostname=hostname,
                source_type=source_type,
                allowlist_match=allowlist_match,
                auto_crawl_enabled=allowlist_match,
            )
            session.add(host)
            session.commit()
            session.refresh(host)
            return int(host.id)
        return int(host.id)


def ensure_uri_identity(observed_uri: str, *, host_id: int | None = None) -> UriIdentityResult:
    canonical = canonicalize_uri(observed_uri)
    normalized_hash = _hash_uri(canonical)
    hostname = urlsplit(canonical).netloc
    host_id = host_id or ensure_host(hostname, source_type="discovered", allowlist_match=False)

    session_factory = create_session_factory()
    with session_factory() as session:
        identity = session.query(RawWebUriIdentity).filter(RawWebUriIdentity.normalized_hash == normalized_hash).first()
        if identity is None:
            identity = RawWebUriIdentity(canonical_uri=canonical, normalized_hash=normalized_hash, host_id=host_id)
            session.add(identity)
            session.commit()
            session.refresh(identity)
        alias = session.query(RawWebUriAlias).filter(
            RawWebUriAlias.uri_identity_id == identity.id,
            RawWebUriAlias.observed_uri == observed_uri,
        ).first()
        if alias is None:
            session.add(RawWebUriAlias(uri_identity_id=int(identity.id), observed_uri=observed_uri))
            session.commit()

        return UriIdentityResult(
            host_id=int(identity.host_id),
            uri_identity_id=int(identity.id),
            canonical_uri=str(identity.canonical_uri),
            normalized_hash=str(identity.normalized_hash),
        )
