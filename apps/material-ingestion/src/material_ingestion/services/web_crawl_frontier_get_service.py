from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
import gzip
import json
import logging
import os
import statistics
import time
import zlib
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebCandidateDocument,
    RawWebCrawlRun,
    RawWebExtractedLink,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebPageMetadata,
    RawWebPageText,
    RawWebStructuredDataRecord,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_identity_service import ensure_uri_identity
from material_ingestion.services.shared_cache_service import cache_get, cache_setex
from material_ingestion.services.web_runtime_config_service import get_runtime_float_config, get_runtime_int_config
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger("material_ingestion.web")
_INSERT_EXTRACTED_LINK = (
    pg_insert(RawWebExtractedLink).on_conflict_do_nothing(
        index_elements=["source_uri_identity_id", "target_uri_identity_id"]
    )
)
SKIP_LINK_PREFIXES = ("mailto:", "tel:", "javascript:", "data:")
SKIP_LINK_SUFFIXES = (
    ".css",
    ".js",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".zip",
)


def _is_valuable_target_url(url: str) -> bool:
    lower = str(url or "").strip().lower()
    if not lower:
        return False
    if lower.startswith(SKIP_LINK_PREFIXES):
        return False
    if any(lower.endswith(suffix) for suffix in SKIP_LINK_SUFFIXES):
        return False
    return lower.startswith("http://") or lower.startswith("https://")


def _is_document_like_url(url: str) -> bool:
    lower = str(url or "").lower()
    doc_hints = [".pdf", "/download", "datasheet", "sds", "msds", "tds", "/document", "document/download"]
    return any(hint in lower for hint in doc_hints)


def _authority_score_for_distinct_sources(distinct_source_count: int) -> int:
    count = max(0, int(distinct_source_count))
    if count >= 100:
        return 40
    if count >= 50:
        return 30
    if count >= 20:
        return 20
    if count >= 5:
        return 10
    return 0


def _resolve_identity_cached(
    url: str,
    *,
    local_cache: dict[str, int],
    redis_enabled: bool,
    redis_ttl_seconds: int,
) -> int:
    cached = local_cache.get(url)
    if cached is not None:
        return cached
    if redis_enabled:
        redis_value = cache_get(f"mi:uri_identity:{url}")
        if redis_value and str(redis_value).isdigit():
            identity_id = int(redis_value)
            local_cache[url] = identity_id
            return identity_id
    identity = ensure_uri_identity(url)
    identity_id = int(identity.uri_identity_id)
    local_cache[url] = identity_id
    if redis_enabled:
        cache_setex(f"mi:uri_identity:{url}", max(60, int(redis_ttl_seconds)), str(identity_id))
    return identity_id


def _parse_retry_after(value: str) -> float | None:
    value = str(value or "").strip()
    if not value:
        return None
    if value.isdigit():
        return float(value)
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
    except Exception:
        return None


def _is_host_rate_limited(host: str) -> bool:
    return bool(cache_get(f"mi:host_ratelimited:{host}"))


def _set_host_rate_limited(host: str, delay_seconds: float) -> None:
    ttl = max(60, min(3600, int(delay_seconds)))
    cache_setex(f"mi:host_ratelimited:{host}", ttl, "1")


def _empty_parse_result(raw_html_length: int) -> dict[str, object]:
    return {
        "lang": "",
        "title": "",
        "meta_description": "",
        "h1": "",
        "canonical": "",
        "robots_content": "",
        "hreflang_map": {},
        "jsonld_blobs": [],
        "links": [],
        "visible_text": "",
        "raw_html_length": raw_html_length,
        "text_length": 0,
        "text_ratio": 0.0,
    }


def _parse_page(html: str, base_url: str) -> dict[str, object]:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        return _empty_parse_result(len(html))

    html_tag = soup.find("html")
    lang = str(html_tag.get("lang", "") or "").strip()[:32] if html_tag else ""

    title_tag = soup.find("title")
    title = str(title_tag.get_text(strip=True) or "")[:512] if title_tag else ""

    meta_desc_tag = soup.find("meta", attrs={"name": lambda n: str(n or "").lower() == "description"})
    meta_description = str(meta_desc_tag.get("content", "") or "")[:1024] if meta_desc_tag else ""

    h1_tag = soup.find("h1")
    h1 = str(h1_tag.get_text(strip=True) or "")[:512] if h1_tag else ""

    canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    canonical = str(canonical_tag.get("href", "") or "")[:2048] if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": lambda n: str(n or "").lower() == "robots"})
    robots_content = str(robots_tag.get("content", "") or "")[:255] if robots_tag else ""

    hreflang_map: dict[str, str] = {}
    for tag in soup.find_all("link", rel=lambda r: r and "alternate" in r):
        hl = str(tag.get("hreflang", "") or "").strip()
        href = str(tag.get("href", "") or "").strip()
        if hl and href:
            hreflang_map[hl] = href[:2048]

    # collect JSON-LD before decomposing script tags
    jsonld_blobs: list[str] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = str(tag.string or "").strip()
        if raw:
            try:
                json.loads(raw)
                jsonld_blobs.append(raw)
            except Exception:
                pass

    # collect links with anchor text before decomposing anything
    links: list[tuple[str, str]] = []
    for tag in soup.find_all("a", href=True):
        href = str(tag.get("href", "") or "").strip()
        if not href:
            continue
        try:
            abs_url = urljoin(base_url, href)
        except Exception:
            continue
        anchor_text = str(tag.get_text(separator=" ", strip=True) or "")[:500]
        links.append((abs_url, anchor_text))

    for tag in soup(["script", "style", "noscript", "head"]):
        tag.decompose()
    visible_text = " ".join(soup.get_text(separator=" ").split())

    raw_html_length = len(html)
    text_length = len(visible_text)
    text_ratio = round(text_length / raw_html_length, 4) if raw_html_length > 0 else 0.0

    return {
        "lang": lang,
        "title": title,
        "meta_description": meta_description,
        "h1": h1,
        "canonical": canonical,
        "robots_content": robots_content,
        "hreflang_map": hreflang_map,
        "jsonld_blobs": jsonld_blobs,
        "links": links,
        "visible_text": visible_text,
        "raw_html_length": raw_html_length,
        "text_length": text_length,
        "text_ratio": text_ratio,
    }


def _get_url(*, canonical_uri: str, timeout_seconds: float, max_bytes: int) -> dict[str, object]:
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
    reason_code = "get_request_failed"
    final_url = str(canonical_uri)
    redirect_count = 0
    body_bytes = 0
    body_text = ""
    ttfb_s = 0.0
    read_s = 0.0
    total_s = 0.0
    error_class = ""

    t0 = time.perf_counter()
    try:
        req = Request(
            str(canonical_uri),
            headers={"User-Agent": "material-ingestion-bot/1.0", "Accept-Encoding": "gzip, deflate"},
            method="GET",
        )
        with urlopen(req, timeout=timeout_seconds) as response:  # nosec B310
            t_ttfb = time.perf_counter()
            ttfb_s = t_ttfb - t0
            status_code = int(getattr(response, "status", 200) or 200)
            final_url = str(response.geturl() or canonical_uri)
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
            if max_bytes > 0:
                body = response.read(max_bytes)
                body_bytes = len(body)
            else:
                body = response.read()
                body_bytes = len(body)
            read_s = time.perf_counter() - t_ttfb
            if "html" in content_type.lower() and body:
                enc = content_encoding.lower()
                try:
                    if enc in ("gzip", "x-gzip"):
                        body = gzip.decompress(body)
                    elif enc == "deflate":
                        body = zlib.decompress(body)
                except Exception:
                    pass
                body_text = body.decode("utf-8", errors="ignore")
        outcome = "success"
        reason_code = "get_body_success"
    except HTTPError as exc:
        status_code = int(exc.code or 0)
        error_class = type(exc).__name__
        if exc.headers:
            retry_after = str(exc.headers.get("Retry-After", "") or "")
    except Exception as exc:
        error_class = type(exc).__name__
    total_s = time.perf_counter() - t0

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
        "final_url": final_url,
        "redirect_count": redirect_count,
        "body_bytes": body_bytes,
        "body_text": body_text,
        "ttfb_s": ttfb_s,
        "read_s": read_s,
        "total_s": total_s,
        "error_class": error_class,
    }


def fetch_promoted_frontier_batch(
    *,
    batch_size: int = 100,
    timeout_seconds: float = 15.0,
    max_concurrency: int = 5,
    heartbeat_callback: Callable[[], None] | None = None,
    progress_callback: Callable[[int, int, int, int], None] | None = None,
) -> tuple[int, int, int, int]:
    session_factory = create_session_factory()
    representation_retention_days = max(1, int(os.getenv("MATERIAL_INGESTION_CRAWL_REPRESENTATION_RETENTION_DAYS", "10")))
    max_body_bytes = max(1, int(os.getenv("MATERIAL_INGESTION_GET_MAX_BYTES", "524288")))
    render_min_text_length = int(os.getenv("MATERIAL_INGESTION_RENDER_MIN_TEXT_LENGTH", "300"))
    render_min_text_ratio = float(os.getenv("MATERIAL_INGESTION_RENDER_MIN_TEXT_RATIO", "0.07"))
    effective_concurrency = max(
        1,
        get_runtime_int_config(key="core_get_max_concurrency", default=int(max_concurrency)),
    )
    max_retries = max(
        0,
        get_runtime_int_config(
            key="core_get_max_retries",
            default=int(os.getenv("MATERIAL_INGESTION_GET_MAX_RETRIES", "3")),
        ),
    )
    backoff_base_seconds = max(
        1.0,
        get_runtime_float_config(
            key="core_get_backoff_base_seconds",
            default=float(os.getenv("MATERIAL_INGESTION_GET_BACKOFF_BASE_SECONDS", "15")),
        ),
    )
    backoff_max_seconds = max(
        5.0,
        get_runtime_float_config(
            key="core_get_backoff_max_seconds",
            default=float(os.getenv("MATERIAL_INGESTION_GET_BACKOFF_MAX_SECONDS", "300")),
        ),
    )
    commit_every = max(
        1,
        get_runtime_int_config(
            key="core_get_commit_every",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_GET_COMMIT_EVERY", "10")),
        ),
    )
    progress_every = max(
        1,
        get_runtime_int_config(
            key="core_get_progress_every",
            default=int(os.getenv("MATERIAL_INGESTION_CORE_GET_PROGRESS_EVERY", "25")),
        ),
    )
    max_links_per_page = get_runtime_int_config(
        key="core_get_max_links_per_page",
        default=int(os.getenv("MATERIAL_INGESTION_CORE_GET_MAX_LINKS_PER_PAGE", "0")),
    )
    redis_cache_enabled = bool(
        get_runtime_int_config(
            key="core_identity_cache_redis_enabled",
            default=int(os.getenv("MATERIAL_INGESTION_IDENTITY_CACHE_REDIS_ENABLED", "1")),
        )
    )
    redis_ttl_seconds = max(
        60,
        get_runtime_int_config(
            key="core_identity_cache_redis_ttl_seconds",
            default=int(os.getenv("MATERIAL_INGESTION_IDENTITY_CACHE_REDIS_TTL_SECONDS", "3600")),
        ),
    )
    processed = 0
    succeeded = 0
    failed = 0
    candidates = 0
    local_identity_cache: dict[str, int] = {}
    extracted_link_data: dict[tuple[int, int], str] = {}  # (source_id, target_id) -> anchor_text
    doc_signal_sources_by_target: dict[int, set[int]] = {}
    slow_request_threshold_s = max(
        1.0,
        get_runtime_float_config(key="core_get_slow_request_threshold_s", default=10.0),
    )
    batch_ttfb: list[float] = []
    batch_read: list[float] = []
    batch_total: list[float] = []

    with session_factory() as session:
        rows = (
            session.query(
                RawWebFrontierItem.id,
                RawWebFrontierItem.uri_identity_id,
                RawWebFrontierItem.crawl_run_id,
                RawWebUriIdentity.canonical_uri,
            )
            .join(RawWebUriIdentity, RawWebUriIdentity.id == RawWebFrontierItem.uri_identity_id)
            .filter(
                RawWebFrontierItem.state == "completed",
                RawWebFrontierItem.state_reason_code.in_(["eval_promote", "get_retry_scheduled"]),
                RawWebFrontierItem.scheduled_at <= datetime.now(UTC),
            )
            .order_by(RawWebFrontierItem.id.asc())
            .limit(max(1, int(batch_size)))
            .all()
        )
        if not rows:
            return (0, 0, 0, 0)
        logger.info(
            "event=frontier_get_selected batch_size=%s selected_rows=%s max_concurrency=%s",
            batch_size,
            len(rows),
            effective_concurrency,
        )

        ids = [int(r[0]) for r in rows]
        item_map = {int(item.id): item for item in session.query(RawWebFrontierItem).filter(RawWebFrontierItem.id.in_(ids)).all()}
        for item_id in ids:
            row = item_map.get(item_id)
            if row is None:
                continue
            row.state = "in_progress"
            row.state_reason_code = "frontier_get_started"
        session.commit()

        row_lookup = {int(fid): (int(uid), int(run_id), str(url)) for fid, uid, run_id, url in rows}

        # Skip items whose host is currently cooling down from a 429 — revert them
        # untouched so they stay eligible for the next batch without burning a retry.
        rate_limited_fids: set[int] = set()
        rate_limited_by_host: dict[str, int] = {}
        if redis_cache_enabled:
            for fid, (_uid, _runid, url) in row_lookup.items():
                host = urlsplit(url).netloc.lower()
                if host and _is_host_rate_limited(host):
                    rate_limited_fids.add(fid)
                    rate_limited_by_host[host] = rate_limited_by_host.get(host, 0) + 1
            if rate_limited_fids:
                for fid in rate_limited_fids:
                    item = item_map.get(fid)
                    if item is not None:
                        item.state = "completed"
                        item.state_reason_code = "eval_promote"
                session.commit()
                host_breakdown = " ".join(f"{h}={c}" for h, c in sorted(rate_limited_by_host.items()))
                logger.warning(
                    "event=frontier_get_host_ratelimit_skipped count=%s hosts=[%s]",
                    len(rate_limited_fids),
                    host_breakdown,
                )

        to_fetch = {fid: payload for fid, payload in row_lookup.items() if fid not in rate_limited_fids}
        network_results: dict[int, dict[str, object]] = {}
        if to_fetch:
            pool_size = max(1, min(effective_concurrency, len(to_fetch)))
            with ThreadPoolExecutor(max_workers=pool_size) as executor:
                future_map = {
                    executor.submit(_get_url, canonical_uri=url, timeout_seconds=timeout_seconds, max_bytes=max_body_bytes): fid
                    for fid, (_uid, _runid, url) in to_fetch.items()
                }
                for future in as_completed(future_map):
                    if heartbeat_callback:
                        heartbeat_callback()
                    fid = future_map[future]
                    try:
                        network_results[fid] = future.result()
                    except Exception as _exc:
                        network_results[fid] = {"outcome": "failed", "reason_code": "get_request_failed", "status_code": 0, "final_url": row_lookup[fid][2], "error_class": type(_exc).__name__}

        expires_full_at = datetime.now(UTC) + timedelta(days=representation_retention_days)
        for fid, (uri_identity_id, crawl_run_id, canonical_uri) in row_lookup.items():
            if fid in rate_limited_fids:
                continue
            if heartbeat_callback:
                heartbeat_callback()
            processed += 1
            result = network_results.get(fid, {})
            outcome = str(result.get("outcome", "failed"))
            status_code = int(result.get("status_code", 0))
            final_url = str(result.get("final_url", canonical_uri))
            redirect_count = int(result.get("redirect_count", 0))
            ttfb_s = float(result.get("ttfb_s", 0.0))
            read_s = float(result.get("read_s", 0.0))
            total_s = float(result.get("total_s", 0.0))
            error_class = str(result.get("error_class", ""))

            # Classify by HTTP status first, fall back to exception type for network errors
            if outcome == "failed":
                if status_code == 429:
                    reason_code = "get_rate_limited"
                elif status_code == 404:
                    reason_code = "get_not_found"
                elif status_code == 410:
                    reason_code = "get_gone"
                elif status_code == 403:
                    reason_code = "get_forbidden"
                elif 400 <= status_code <= 499:
                    reason_code = "get_client_error"
                elif 500 <= status_code <= 599:
                    reason_code = "get_server_error"
                else:
                    ec = error_class.lower()
                    if "timeout" in ec:
                        reason_code = "get_timeout"
                    elif "connectionreset" in ec or "connectionrefused" in ec or "connectionerror" in ec or "broken" in ec:
                        reason_code = "get_connection_error"
                    elif "urlerror" in ec or "socket" in ec:
                        reason_code = "get_network_error"
                    else:
                        reason_code = str(result.get("reason_code", "get_request_failed"))
            else:
                reason_code = str(result.get("reason_code", "get_request_failed"))

            batch_ttfb.append(ttfb_s)
            batch_read.append(read_s)
            batch_total.append(total_s)

            if outcome == "success":
                succeeded += 1
                if total_s >= slow_request_threshold_s:
                    logger.info(
                        "event=get_slow_request url=%s total_s=%.2f ttfb_s=%.2f read_s=%.2f body_bytes=%s status=%s",
                        canonical_uri, total_s, ttfb_s, read_s, result.get("body_bytes", 0), status_code,
                    )
            else:
                failed += 1
                logger.debug(
                    "event=get_request_failed url=%s reason=%s error_class=%s total_s=%.2f status=%s",
                    canonical_uri, reason_code, error_class, total_s, status_code,
                )
            existing_failures = (
                session.query(RawWebHttpFetchAttempt)
                .filter(
                    RawWebHttpFetchAttempt.uri_identity_id == uri_identity_id,
                    RawWebHttpFetchAttempt.reason_code == "get_request_failed",
                )
                .count()
            )

            attempt = RawWebHttpFetchAttempt(
                uri_identity_id=uri_identity_id,
                crawl_run_id=crawl_run_id,
                status_code=status_code,
                outcome=outcome,
                reason_code=reason_code,
                requested_url=canonical_uri,
                final_url=final_url,
                redirect_count=max(0, redirect_count),
                ttfb_ms=int(ttfb_s * 1000),
                read_ms=int(read_s * 1000),
                total_ms=int(total_s * 1000),
            )
            session.add(attempt)
            session.flush()

            content_type = str(result.get("content_type", ""))
            content_disposition = str(result.get("content_disposition", ""))
            body_bytes = int(result.get("body_bytes", 0))
            session.add(
                RawWebHttpRepresentation(
                    fetch_attempt_id=int(attempt.id),
                    storage_ref=final_url,
                    content_type=content_type,
                    etag=str(result.get("etag", "")),
                    last_modified=str(result.get("last_modified", "")),
                    cache_control=str(result.get("cache_control", "")),
                    content_length=int(result.get("content_length", 0) or body_bytes),
                    content_language=str(result.get("content_language", "")),
                    content_encoding=str(result.get("content_encoding", "")),
                    content_disposition=content_disposition,
                    location=str(result.get("location", "")),
                    content_location=str(result.get("content_location", "")),
                    link=str(result.get("link", "")),
                    vary=str(result.get("vary", "")),
                    allow=str(result.get("allow", "")),
                    accept_ranges=str(result.get("accept_ranges", "")),
                    server=str(result.get("server", "")),
                    x_robots_tag=str(result.get("x_robots_tag", "")),
                    retry_after=str(result.get("retry_after", "")),
                    expires_full_at=expires_full_at,
                )
            )

            item = item_map.get(fid)
            if item is not None:
                item.state = "completed"
                if outcome == "success":
                    item.state_reason_code = "get_success"
                else:
                    is_permanent = 400 <= status_code <= 499 and status_code != 429
                    is_retryable = status_code == 429 or 500 <= status_code <= 599 or status_code == 0
                    if is_permanent:
                        item.state_reason_code = "get_failed_permanent"
                    elif is_retryable:
                        retry_index = max(1, int(existing_failures))
                        if retry_index <= max_retries:
                            delay = min(backoff_max_seconds, backoff_base_seconds * (2 ** (retry_index - 1)))
                            retry_after_val = str(result.get("retry_after", "") or "")
                            if retry_after_val:
                                parsed_delay = _parse_retry_after(retry_after_val)
                                if parsed_delay is not None:
                                    delay = max(delay, parsed_delay)
                                    logger.warning(
                                        "event=get_retry_after_applied url=%s status=%s retry_after=%s delay_s=%.1f",
                                        canonical_uri, status_code, retry_after_val, delay,
                                    )
                            if status_code == 429 and redis_cache_enabled:
                                host = urlsplit(canonical_uri).netloc.lower()
                                if host:
                                    _set_host_rate_limited(host, delay)
                                    logger.warning(
                                        "event=host_rate_limited host=%s delay_s=%.1f",
                                        host, delay,
                                    )
                            item.state_reason_code = "get_retry_scheduled"
                            item.scheduled_at = datetime.now(UTC) + timedelta(seconds=float(delay))
                        else:
                            item.state_reason_code = "get_failed_max_retries"
                    else:
                        item.state_reason_code = "get_failed_max_retries"

            lower_url = canonical_uri.lower()
            lower_type = content_type.lower()
            lower_disp = content_disposition.lower()
            is_pdf_candidate = (
                ".pdf" in lower_url
                or "application/pdf" in lower_type
                or ".pdf" in lower_disp
                or "filename=" in lower_disp and ".pdf" in lower_disp
            )
            if outcome == "success" and is_pdf_candidate:
                candidate_stmt = pg_insert(RawWebCandidateDocument).values(
                    uri_identity_id=uri_identity_id,
                    source_uri_identity_id=uri_identity_id,
                    mime_type=content_type or "application/pdf",
                    classification="datasheet_candidate",
                    score=0,
                    distinct_source_count=0,
                    score_reason_json="{}",
                    decision_state="new",
                    decision_reason_code="phase_b_get_pdf_signal",
                )
                candidate_stmt = candidate_stmt.on_conflict_do_update(
                    constraint="uq_raw_web_candidate_document_unique",
                    set_={
                        "mime_type": content_type or "application/pdf",
                        "classification": "datasheet_candidate",
                        "score": 0,
                        "distinct_source_count": 0,
                        "score_reason_json": "{}",
                        "decision_state": "new",
                        "decision_reason_code": "phase_b_get_pdf_signal",
                        "updated_at": datetime.now(UTC),
                    },
                )
                session.execute(candidate_stmt)
                candidates += 1

            if outcome == "success":
                html_text = str(result.get("body_text", "") or "")
                if html_text:
                    parsed = _parse_page(html_text, canonical_uri)

                    render_needed = (
                        int(parsed["text_length"]) < render_min_text_length
                        or float(parsed["text_ratio"]) < render_min_text_ratio
                    )
                    session.add(
                        RawWebPageText(
                            fetch_attempt_id=int(attempt.id),
                            title=str(parsed["title"]),
                            meta_description=str(parsed["meta_description"]),
                            h1=str(parsed["h1"]),
                            lang=str(parsed["lang"]),
                            body_text=str(parsed["visible_text"]),
                            raw_html_length=int(parsed["raw_html_length"]),
                            text_length=int(parsed["text_length"]),
                            text_ratio=float(parsed["text_ratio"]),
                            render_needed=bool(render_needed),
                        )
                    )

                    canonical_hint = str(parsed["canonical"])
                    robots_content = str(parsed["robots_content"])
                    hreflang_map = dict(parsed["hreflang_map"])
                    if canonical_hint or robots_content or hreflang_map:
                        session.add(
                            RawWebPageMetadata(
                                uri_identity_id=uri_identity_id,
                                canonical_hint=canonical_hint,
                                robots_meta_json=json.dumps({"content": robots_content} if robots_content else {}),
                                hreflang_map_json=json.dumps(hreflang_map),
                            )
                        )

                    for blob in list(parsed["jsonld_blobs"]):
                        session.add(
                            RawWebStructuredDataRecord(
                                uri_identity_id=uri_identity_id,
                                format="jsonld",
                                payload_json=str(blob),
                            )
                        )

                    source_identity_id = _resolve_identity_cached(
                        canonical_uri,
                        local_cache=local_identity_cache,
                        redis_enabled=redis_cache_enabled,
                        redis_ttl_seconds=redis_ttl_seconds,
                    )
                    raw_links: list[tuple[str, str]] = list(parsed["links"])
                    if max_links_per_page > 0 and len(raw_links) > max_links_per_page:
                        logger.info(
                            "event=frontier_get_link_budget_applied url=%s extracted=%s capped=%s",
                            canonical_uri,
                            len(raw_links),
                            max_links_per_page,
                        )
                        raw_links = raw_links[:max_links_per_page]
                    for target_url, anchor_text in raw_links:
                        if not _is_valuable_target_url(target_url):
                            continue
                        try:
                            target_identity_id = _resolve_identity_cached(
                                target_url,
                                local_cache=local_identity_cache,
                                redis_enabled=redis_cache_enabled,
                                redis_ttl_seconds=redis_ttl_seconds,
                            )
                            link_key = (int(source_identity_id), int(target_identity_id))
                            if link_key not in extracted_link_data:
                                extracted_link_data[link_key] = anchor_text
                            if _is_document_like_url(target_url):
                                target_key = int(target_identity_id)
                                source_set = doc_signal_sources_by_target.get(target_key)
                                if source_set is None:
                                    source_set = set()
                                    doc_signal_sources_by_target[target_key] = source_set
                                source_set.add(int(source_identity_id))
                        except Exception:
                            continue

            if extracted_link_data and processed % commit_every == 0:
                session.execute(
                    _INSERT_EXTRACTED_LINK,
                    [
                        {"source_uri_identity_id": s, "target_uri_identity_id": t, "rel": "", "anchor_text": anchor}
                        for (s, t), anchor in extracted_link_data.items()
                    ],
                )
                extracted_link_data.clear()

            if progress_callback and (processed % progress_every == 0):
                progress_callback(processed, succeeded, failed, candidates)
            if processed % commit_every == 0:
                session.commit()

        if extracted_link_data:
            session.execute(
                _INSERT_EXTRACTED_LINK,
                [
                    {"source_uri_identity_id": s, "target_uri_identity_id": t, "rel": "", "anchor_text": anchor}
                    for (s, t), anchor in extracted_link_data.items()
                ],
            )
            extracted_link_data.clear()

        for target_identity_id, source_identity_ids in doc_signal_sources_by_target.items():
            distinct_source_count = (
                session.query(RawWebExtractedLink.source_uri_identity_id)
                .filter(RawWebExtractedLink.target_uri_identity_id == target_identity_id)
                .distinct()
                .count()
            )
            authority_score = _authority_score_for_distinct_sources(distinct_source_count)
            doc_hint_score = 10
            total_score = authority_score + doc_hint_score
            decision_state = "promoted_authority" if distinct_source_count >= 5 else "new"
            score_reason_json = json.dumps(
                {
                    "signal": "phase_b_get_extracted_link_signal",
                    "doc_hint_score": doc_hint_score,
                    "authority_score": authority_score,
                    "distinct_source_count": int(distinct_source_count),
                },
                sort_keys=True,
            )
            for source_identity_id in source_identity_ids:
                candidate_stmt = pg_insert(RawWebCandidateDocument).values(
                    uri_identity_id=int(target_identity_id),
                    source_uri_identity_id=int(source_identity_id),
                    mime_type="",
                    classification="datasheet_candidate",
                    score=total_score,
                    distinct_source_count=int(distinct_source_count),
                    score_reason_json=score_reason_json,
                    decision_state=decision_state,
                    decision_reason_code="phase_b_get_extracted_link_signal",
                )
                candidate_stmt = candidate_stmt.on_conflict_do_update(
                    constraint="uq_raw_web_candidate_document_unique",
                    set_={
                        "mime_type": "",
                        "classification": "datasheet_candidate",
                        "score": total_score,
                        "distinct_source_count": int(distinct_source_count),
                        "score_reason_json": score_reason_json,
                        "decision_state": decision_state,
                        "decision_reason_code": "phase_b_get_extracted_link_signal",
                        "updated_at": datetime.now(UTC),
                    },
                )
                session.execute(candidate_stmt)
                candidates += 1
        session.commit()

    if batch_total:
        def _pct(data: list[float], p: float) -> float:
            return sorted(data)[int(len(data) * p)] if data else 0.0
        logger.info(
            "event=frontier_get_timing_summary count=%s "
            "ttfb_avg=%.2f ttfb_p50=%.2f ttfb_p95=%.2f ttfb_max=%.2f "
            "read_avg=%.2f read_p50=%.2f read_p95=%.2f read_max=%.2f "
            "total_avg=%.2f total_p50=%.2f total_p95=%.2f total_max=%.2f",
            len(batch_total),
            statistics.mean(batch_ttfb), _pct(batch_ttfb, 0.5), _pct(batch_ttfb, 0.95), max(batch_ttfb),
            statistics.mean(batch_read), _pct(batch_read, 0.5), _pct(batch_read, 0.95), max(batch_read),
            statistics.mean(batch_total), _pct(batch_total, 0.5), _pct(batch_total, 0.95), max(batch_total),
        )
    logger.info(
        "event=frontier_get_completed processed=%s succeeded=%s failed=%s candidates=%s",
        processed,
        succeeded,
        failed,
        candidates,
    )
    return processed, succeeded, failed, candidates
