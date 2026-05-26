from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebCrawlRun,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebIngestionEvent,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_decision_service import record_decision
from material_ingestion.services.web_crawl_host_scope_service import is_host_allowlisted, register_discovered_host

logger = logging.getLogger("material_ingestion.web")


def _enqueue_core_discover_for_redirect_host(
    *,
    host: str,
    source_url: str,
    max_pages: int = 20,
    fetch_max_concurrency: int = 25,
) -> int:
    host_slug = host.replace(".", "_")
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    digest = hashlib.sha1(host.encode("utf-8")).hexdigest()[:8]
    run_key = f"core_redirect_{host_slug}_{digest}_{ts}"
    if len(run_key) > 64:
        run_key = run_key[:64]
    payload = {
        "seed_url": f"https://{host}",
        "max_pages": max_pages,
        "cross_domain": False,
        "ingest_source": "web_discovery",
        "ingest_locator": f"https://{host}",
        "ingest_batch_id": run_key,
        "orchestration_id": run_key,
        "fetch_max_concurrency": fetch_max_concurrency,
        "discovered_via": "redirect_cross_host",
        "discovered_from_url": source_url,
    }
    session_factory = create_session_factory()
    with session_factory() as session:
        event = RawWebIngestionEvent(
            orchestration_id=run_key,
            event_type="core_discover_requested",
            status="queued",
            payload_json=json.dumps(payload, sort_keys=True),
            error_text="",
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return int(event.id)


def _has_recent_discover_event_for_host(*, host: str, window_hours: int) -> bool:
    cutoff = datetime.now(UTC) - timedelta(hours=max(1, int(window_hours)))
    needle = f"\"seed_url\": \"https://{host}\""
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebIngestionEvent.id)
            .filter(
                RawWebIngestionEvent.event_type == "core_discover_requested",
                RawWebIngestionEvent.created_at >= cutoff,
                RawWebIngestionEvent.payload_json.like(f"%{needle}%"),
            )
            .order_by(RawWebIngestionEvent.id.desc())
            .first()
        )
        return row is not None


def _has_pending_discover_event_for_host(*, host: str) -> bool:
    needle = f"\"seed_url\": \"https://{host}\""
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebIngestionEvent.id)
            .filter(
                RawWebIngestionEvent.event_type == "core_discover_requested",
                RawWebIngestionEvent.status.in_(["queued", "running"]),
                RawWebIngestionEvent.payload_json.like(f"%{needle}%"),
            )
            .order_by(RawWebIngestionEvent.id.desc())
            .first()
        )
        return row is not None


def _head_scan_url(*, canonical_uri: str, timeout_seconds: float) -> dict[str, object]:
    status_code = 0
    content_type = ""
    etag = ""
    last_modified = ""
    cache_control = ""
    content_length = 0
    content_language = ""
    content_encoding = ""
    content_disposition = ""
    location = ""
    content_location = ""
    link = ""
    vary = ""
    allow = ""
    accept_ranges = ""
    server = ""
    x_robots_tag = ""
    retry_after = ""
    outcome = "failed"
    reason_code = "head_request_failed"
    error_text = ""
    final_url = str(canonical_uri)
    redirect_count = 0

    try:
        req = Request(
            str(canonical_uri),
            headers={"User-Agent": "material-ingestion-bot/1.0"},
            method="HEAD",
        )
        with urlopen(req, timeout=timeout_seconds) as response:  # nosec B310
            status_code = int(getattr(response, "status", 200) or 200)
            final_url = str(response.geturl() or canonical_uri)
            requested_parts = urlsplit(str(canonical_uri))
            final_parts = urlsplit(final_url)
            if requested_parts.netloc and final_parts.netloc:
                same_host = requested_parts.netloc.lower() == final_parts.netloc.lower()
                same_path = requested_parts.path == final_parts.path
                same_query = requested_parts.query == final_parts.query
                redirect_count = 0 if (same_host and same_path and same_query) else 1
            response_headers = response.headers
            content_type = str(response_headers.get("Content-Type", "") or "")
            etag = str(response_headers.get("ETag", "") or "")
            last_modified = str(response_headers.get("Last-Modified", "") or "")
            cache_control = str(response_headers.get("Cache-Control", "") or "")
            content_language = str(response_headers.get("Content-Language", "") or "")
            content_encoding = str(response_headers.get("Content-Encoding", "") or "")
            content_disposition = str(response_headers.get("Content-Disposition", "") or "")
            location = str(response_headers.get("Location", "") or "")
            content_location = str(response_headers.get("Content-Location", "") or "")
            link = str(response_headers.get("Link", "") or "")
            vary = str(response_headers.get("Vary", "") or "")
            allow = str(response_headers.get("Allow", "") or "")
            accept_ranges = str(response_headers.get("Accept-Ranges", "") or "")
            server = str(response_headers.get("Server", "") or "")
            x_robots_tag = str(response_headers.get("X-Robots-Tag", "") or "")
            retry_after = str(response_headers.get("Retry-After", "") or "")
            raw_content_length = str(response_headers.get("Content-Length", "") or "").strip()
            if raw_content_length.isdigit():
                content_length = int(raw_content_length)
        outcome = "success"
        reason_code = "head_metadata_success"
    except Exception as exc:
        error_text = str(exc)

    return {
        "status_code": status_code,
        "content_type": content_type,
        "etag": etag,
        "last_modified": last_modified,
        "cache_control": cache_control,
        "content_length": content_length,
        "content_language": content_language,
        "content_encoding": content_encoding,
        "content_disposition": content_disposition,
        "location": location,
        "content_location": content_location,
        "link": link,
        "vary": vary,
        "allow": allow,
        "accept_ranges": accept_ranges,
        "server": server,
        "x_robots_tag": x_robots_tag,
        "retry_after": retry_after,
        "outcome": outcome,
        "reason_code": reason_code,
        "error_text": error_text,
        "final_url": final_url,
        "redirect_count": redirect_count,
    }


def fetch_frontier_batch(
    *,
    run_key: str,
    batch_size: int = 100,
    timeout_seconds: float = 10.0,
    max_concurrency: int = 25,
    heartbeat_callback: Callable[[], None] | None = None,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> tuple[int, int, int]:
    session_factory = create_session_factory()
    with session_factory() as session:
        run = session.query(RawWebCrawlRun).filter(RawWebCrawlRun.run_key == run_key).first()
        if run is None:
            return (0, 0, 0)
        crawl_run_id = int(run.id)

    processed = 0
    succeeded = 0
    deferred = 0
    redirect_hosts_enqueued: set[str] = set()
    recent_success_window_hours = max(1, int(os.getenv("MATERIAL_INGESTION_RECENT_SUCCESS_WINDOW_HOURS", "24")))
    redirect_reenqueue_window_hours = max(1, int(os.getenv("MATERIAL_INGESTION_REDIRECT_REENQUEUE_WINDOW_HOURS", "168")))
    representation_retention_days = max(1, int(os.getenv("MATERIAL_INGESTION_CRAWL_REPRESENTATION_RETENTION_DAYS", "10")))

    while True:
        with session_factory() as session:
            rows = (
                session.query(RawWebFrontierItem.id, RawWebFrontierItem.uri_identity_id, RawWebUriIdentity.canonical_uri)
                .join(RawWebUriIdentity, RawWebUriIdentity.id == RawWebFrontierItem.uri_identity_id)
                .filter(
                    RawWebFrontierItem.crawl_run_id == crawl_run_id,
                    RawWebFrontierItem.state == "queued",
                )
                .order_by(RawWebFrontierItem.priority.desc(), RawWebFrontierItem.id.asc())
                .limit(max(1, batch_size))
                .all()
            )
            if not rows:
                break

            row_lookup = {int(frontier_id): (int(uri_identity_id), str(canonical_uri)) for frontier_id, uri_identity_id, canonical_uri in rows}
            item_ids = [int(frontier_id) for frontier_id, _uri_identity_id, _canonical_uri in rows]
            items = {
                int(item.id): item
                for item in (
                    session.query(RawWebFrontierItem)
                    .filter(RawWebFrontierItem.id.in_(item_ids))
                    .all()
                )
            }
            for frontier_id in item_ids:
                item = items.get(int(frontier_id))
                if item is None:
                    continue
                item.state = "in_progress"
                item.state_reason_code = "frontier_fetch_started"
            session.commit()

            cutoff = datetime.now(UTC) - timedelta(hours=max(1, int(recent_success_window_hours)))
            recent_success_ids = {
                int(row[0])
                for row in (
                    session.query(RawWebHttpFetchAttempt.uri_identity_id)
                    .filter(
                        RawWebHttpFetchAttempt.uri_identity_id.in_([uri_id for uri_id, _url in row_lookup.values()]),
                        RawWebHttpFetchAttempt.outcome == "success",
                        RawWebHttpFetchAttempt.completed_at >= cutoff,
                    )
                    .all()
                )
                if row and row[0] is not None
            }

            for frontier_id, (uri_identity_id, canonical_uri) in row_lookup.items():
                if uri_identity_id not in recent_success_ids:
                    continue
                item = items.get(int(frontier_id))
                if item is None:
                    continue
                processed += 1
                succeeded += 1
                item.state = "completed"
                item.state_reason_code = "recent_success_skip"
                record_decision(
                    crawl_run_id=crawl_run_id,
                    uri_identity_id=int(uri_identity_id),
                    decision_type="skip",
                    reason_code="recent_success_skip",
                    detail={"url": str(canonical_uri), "frontier_item_id": int(frontier_id), "window_hours": int(recent_success_window_hours)},
                )
            session.commit()

            network_results: dict[int, dict[str, object]] = {}
            to_fetch = {fid: payload for fid, payload in row_lookup.items() if payload[0] not in recent_success_ids}
            if not to_fetch:
                if heartbeat_callback:
                    heartbeat_callback()
                if progress_callback:
                    progress_callback(processed, succeeded, deferred)
                logger.info(
                    "event=frontier_fetch_progress run_key=%s processed=%s succeeded=%s deferred=%s",
                    run_key,
                    processed,
                    succeeded,
                    deferred,
                )
                continue
            pool_size = max(1, min(max_concurrency, len(to_fetch)))
            with ThreadPoolExecutor(max_workers=pool_size) as executor:
                future_map = {
                    executor.submit(_head_scan_url, canonical_uri=canonical_uri, timeout_seconds=timeout_seconds): frontier_id
                    for frontier_id, (_, canonical_uri) in to_fetch.items()
                }
                for future in as_completed(future_map):
                    frontier_id = future_map[future]
                    try:
                        network_results[frontier_id] = future.result()
                    except Exception as exc:
                        network_results[frontier_id] = {
                            "status_code": 0,
                            "content_type": "",
                            "etag": "",
                            "last_modified": "",
                            "cache_control": "",
                            "content_length": 0,
                            "content_language": "",
                            "content_encoding": "",
                            "content_disposition": "",
                            "location": "",
                            "content_location": "",
                            "link": "",
                            "vary": "",
                            "allow": "",
                            "accept_ranges": "",
                            "server": "",
                            "x_robots_tag": "",
                            "retry_after": "",
                            "outcome": "failed",
                            "reason_code": "head_request_failed",
                            "error_text": str(exc),
                        }

            fetch_attempt_rows: list[RawWebHttpFetchAttempt] = []
            fetch_attempt_representation_payloads: list[dict[str, object]] = []
            expires_full_at = datetime.now(UTC) + timedelta(days=representation_retention_days)

            for frontier_id, (uri_identity_id, canonical_uri) in to_fetch.items():
                item = items.get(int(frontier_id))
                if item is None:
                    continue
                processed += 1
                result = network_results.get(frontier_id, {})
                status_code = int(result.get("status_code", 0))
                content_type = str(result.get("content_type", ""))
                etag = str(result.get("etag", ""))
                last_modified = str(result.get("last_modified", ""))
                cache_control = str(result.get("cache_control", ""))
                content_length = int(result.get("content_length", 0))
                content_language = str(result.get("content_language", ""))
                content_encoding = str(result.get("content_encoding", ""))
                content_disposition = str(result.get("content_disposition", ""))
                location = str(result.get("location", ""))
                content_location = str(result.get("content_location", ""))
                link = str(result.get("link", ""))
                vary = str(result.get("vary", ""))
                allow = str(result.get("allow", ""))
                accept_ranges = str(result.get("accept_ranges", ""))
                server = str(result.get("server", ""))
                x_robots_tag = str(result.get("x_robots_tag", ""))
                retry_after = str(result.get("retry_after", ""))
                outcome = str(result.get("outcome", "failed"))
                reason_code = str(result.get("reason_code", "head_request_failed"))
                final_url = str(result.get("final_url", canonical_uri))
                redirect_count = int(result.get("redirect_count", 0))

                if outcome == "success":
                    succeeded += 1
                    item.state = "completed"
                    item.state_reason_code = "head_metadata_success"
                    record_decision(
                        crawl_run_id=crawl_run_id,
                        uri_identity_id=int(uri_identity_id),
                        decision_type="queue",
                        reason_code="head_metadata_success",
                        detail={"url": str(canonical_uri), "frontier_item_id": int(frontier_id), "status_code": status_code},
                    )
                    requested_host = urlsplit(str(canonical_uri)).netloc.lower()
                    final_host = urlsplit(final_url).netloc.lower()
                    if final_host and final_host != requested_host:
                        register_discovered_host(final_host, discovery_source=f"redirect:{canonical_uri}")
                        if (
                            final_host not in redirect_hosts_enqueued
                            and is_host_allowlisted(final_host)
                            and not _has_pending_discover_event_for_host(host=final_host)
                            and not _has_recent_discover_event_for_host(
                                host=final_host,
                                window_hours=redirect_reenqueue_window_hours,
                            )
                        ):
                            redirect_event_id = _enqueue_core_discover_for_redirect_host(
                                host=final_host,
                                source_url=str(canonical_uri),
                                fetch_max_concurrency=max_concurrency,
                            )
                            redirect_hosts_enqueued.add(final_host)
                            logger.info(
                                "event=redirect_host_discover_enqueued host=%s source_url=%s event_id=%s",
                                final_host,
                                canonical_uri,
                                redirect_event_id,
                            )
                        elif final_host not in redirect_hosts_enqueued and is_host_allowlisted(final_host) and _has_pending_discover_event_for_host(host=final_host):
                            record_decision(
                                crawl_run_id=crawl_run_id,
                                uri_identity_id=int(uri_identity_id),
                                decision_type="skip",
                                reason_code="redirect_pending_run_skip",
                                detail={"host": final_host, "source": "redirect_auto_trigger"},
                            )
                        elif final_host not in redirect_hosts_enqueued and is_host_allowlisted(final_host):
                            record_decision(
                                crawl_run_id=crawl_run_id,
                                uri_identity_id=int(uri_identity_id),
                                decision_type="skip",
                                reason_code="redirect_recent_run_skip",
                                detail={
                                    "host": final_host,
                                    "source": "redirect_auto_trigger",
                                    "window_hours": redirect_reenqueue_window_hours,
                                },
                            )
                        elif final_host not in redirect_hosts_enqueued:
                            record_decision(
                                crawl_run_id=crawl_run_id,
                                uri_identity_id=int(uri_identity_id),
                                decision_type="skip",
                                reason_code="host_not_allowlisted",
                                detail={"host": final_host, "source": "redirect_auto_trigger"},
                            )
                        record_decision(
                            crawl_run_id=crawl_run_id,
                            uri_identity_id=int(uri_identity_id),
                            decision_type="queue",
                            reason_code="redirect_cross_host",
                            detail={"from_url": str(canonical_uri), "to_url": final_url, "redirect_count": redirect_count},
                        )
                    elif redirect_count > 0:
                        record_decision(
                            crawl_run_id=crawl_run_id,
                            uri_identity_id=int(uri_identity_id),
                            decision_type="queue",
                            reason_code="redirect_same_host",
                            detail={"from_url": str(canonical_uri), "to_url": final_url, "redirect_count": redirect_count},
                        )
                else:
                    deferred += 1
                    item.state = "deferred"
                    item.state_reason_code = "head_request_failed"
                    record_decision(
                        crawl_run_id=crawl_run_id,
                        uri_identity_id=int(uri_identity_id),
                        decision_type="defer",
                        reason_code="head_request_failed",
                        detail={
                            "url": str(canonical_uri),
                            "frontier_item_id": int(frontier_id),
                            "error": str(result.get("error_text", "")),
                        },
                    )

                fetch_attempt_rows.append(
                    RawWebHttpFetchAttempt(
                        uri_identity_id=int(uri_identity_id),
                        crawl_run_id=crawl_run_id,
                        status_code=status_code,
                        outcome=outcome,
                        reason_code=reason_code,
                        requested_url=str(canonical_uri),
                        final_url=final_url,
                        redirect_count=max(0, int(redirect_count)),
                    )
                )
                fetch_attempt_representation_payloads.append(
                    {
                        "storage_ref": str(canonical_uri),
                        "content_type": content_type,
                        "etag": etag,
                        "last_modified": last_modified,
                        "cache_control": cache_control,
                        "content_length": max(0, int(content_length)),
                        "content_language": content_language,
                        "content_encoding": content_encoding,
                        "content_disposition": content_disposition,
                        "location": location,
                        "content_location": content_location,
                        "link": link,
                        "vary": vary,
                        "allow": allow,
                        "accept_ranges": accept_ranges,
                        "server": server,
                        "x_robots_tag": x_robots_tag,
                        "retry_after": retry_after,
                    }
                )

            if fetch_attempt_rows:
                session.add_all(fetch_attempt_rows)
                session.flush()
                representation_rows = []
                for attempt_row, payload in zip(fetch_attempt_rows, fetch_attempt_representation_payloads, strict=False):
                    representation_rows.append(
                        RawWebHttpRepresentation(
                            fetch_attempt_id=int(attempt_row.id),
                            storage_ref=str(payload["storage_ref"]),
                            content_type=str(payload["content_type"]),
                            etag=str(payload["etag"]),
                            last_modified=str(payload["last_modified"]),
                            cache_control=str(payload["cache_control"]),
                            content_length=int(payload["content_length"]),
                            content_language=str(payload["content_language"]),
                            content_encoding=str(payload["content_encoding"]),
                            content_disposition=str(payload["content_disposition"]),
                            location=str(payload["location"]),
                            content_location=str(payload["content_location"]),
                            link=str(payload["link"]),
                            vary=str(payload["vary"]),
                            allow=str(payload["allow"]),
                            accept_ranges=str(payload["accept_ranges"]),
                            server=str(payload["server"]),
                            x_robots_tag=str(payload["x_robots_tag"]),
                            retry_after=str(payload["retry_after"]),
                            expires_full_at=expires_full_at,
                        )
                    )
                session.add_all(representation_rows)
            session.commit()
            if heartbeat_callback:
                heartbeat_callback()

        if progress_callback:
            progress_callback(processed, succeeded, deferred)
        logger.info(
            "event=frontier_fetch_progress run_key=%s processed=%s succeeded=%s deferred=%s",
            run_key,
            processed,
            succeeded,
            deferred,
        )

    logger.info(
        "event=frontier_fetch_completed run_key=%s processed=%s succeeded=%s deferred=%s",
        run_key,
        processed,
        succeeded,
        deferred,
    )
    return processed, succeeded, deferred
