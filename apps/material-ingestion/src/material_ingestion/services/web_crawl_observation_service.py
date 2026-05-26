from __future__ import annotations

from datetime import UTC, datetime, timedelta

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebExtractedLink, RawWebHttpFetchAttempt, RawWebHttpRepresentation


def persist_fetch_attempt(
    *,
    uri_identity_id: int,
    crawl_run_id: int,
    status_code: int,
    outcome: str,
    reason_code: str,
    requested_url: str = "",
    final_url: str = "",
    redirect_count: int = 0,
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebHttpFetchAttempt(
            uri_identity_id=uri_identity_id,
            crawl_run_id=crawl_run_id,
            status_code=status_code,
            outcome=outcome,
            reason_code=reason_code,
            requested_url=requested_url,
            final_url=final_url,
            redirect_count=max(0, int(redirect_count)),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def persist_http_representation(
    *,
    fetch_attempt_id: int,
    storage_ref: str,
    content_type: str,
    etag: str = "",
    last_modified: str = "",
    cache_control: str = "",
    content_length: int = 0,
    content_language: str = "",
    content_encoding: str = "",
    content_disposition: str = "",
    location: str = "",
    content_location: str = "",
    link: str = "",
    vary: str = "",
    allow: str = "",
    accept_ranges: str = "",
    server: str = "",
    x_robots_tag: str = "",
    retry_after: str = "",
    retention_days: int = 10,
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebHttpRepresentation(
            fetch_attempt_id=fetch_attempt_id,
            storage_ref=storage_ref,
            content_type=content_type,
            etag=etag,
            last_modified=last_modified,
            cache_control=cache_control,
            content_length=max(0, int(content_length)),
            content_language=content_language,
            content_encoding=content_encoding,
            content_disposition=content_disposition,
            location=location,
            content_location=content_location,
            link=link,
            vary=vary,
            allow=allow,
            accept_ranges=accept_ranges,
            server=server,
            x_robots_tag=x_robots_tag,
            retry_after=retry_after,
            expires_full_at=datetime.now(UTC) + timedelta(days=retention_days),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)


def persist_extracted_link(
    *,
    source_uri_identity_id: int,
    target_uri_identity_id: int,
    rel: str = "",
    anchor_text: str = "",
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebExtractedLink(
            source_uri_identity_id=source_uri_identity_id,
            target_uri_identity_id=target_uri_identity_id,
            rel=rel,
            anchor_text=anchor_text,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
