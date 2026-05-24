from __future__ import annotations

import hashlib
import logging
import random
import re
import time
import unicodedata
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from material_ingestion.logging_schema import log_event

logger = logging.getLogger("material_ingestion.web")


@dataclass(slots=True)
class DownloadedFile:
    source_url: str
    stored_path: str
    sha256: str
    size_bytes: int
    content_type: str
    status_code: int


class WebFileDownloader:
    def __init__(
        self,
        *,
        user_agent: str = "material-ingestion-bot/1.0",
        timeout_seconds: int = 60,
        max_retries: int = 4,
        backoff_base_seconds: float = 1.0,
        backoff_max_seconds: float = 20.0,
        jitter_seconds: float = 0.25,
        retry_callback: Callable[[dict[str, object]], None] | None = None,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.backoff_max_seconds = backoff_max_seconds
        self.jitter_seconds = jitter_seconds
        self.retry_callback = retry_callback

    def download_pdf(self, *, source_url: str, output_root: Path) -> DownloadedFile:
        normalized_url = self._normalize_download_url(source_url)
        status_code, content_type, data = self._read_with_retries(source_url=normalized_url)

        digest = hashlib.sha256(data).hexdigest()
        ext = self._guess_extension(source_url=normalized_url, content_type=content_type)
        host = (urlparse(normalized_url).netloc or "unknown-host").replace(":", "_")
        target_dir = output_root / host
        target_dir.mkdir(parents=True, exist_ok=True)
        base_slug = self._safe_slug_from_url(normalized_url)
        if base_slug:
            target_path = target_dir / f"{base_slug}__{digest[:16]}{ext}"
        else:
            target_path = target_dir / f"{digest}{ext}"
        target_path.write_bytes(data)

        return DownloadedFile(
            source_url=normalized_url,
            stored_path=str(target_path),
            sha256=digest,
            size_bytes=len(data),
            content_type=content_type,
            status_code=status_code,
        )

    @staticmethod
    def _safe_slug_from_url(source_url: str) -> str:
        parsed = urlparse(source_url)
        raw_name = unquote((parsed.path or "").rstrip("/").split("/")[-1]).strip()
        if not raw_name:
            return ""
        # Drop extension and normalize to readable, bounded ASCII slug.
        stem = raw_name.rsplit(".", 1)[0]
        normalized = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized).strip("._-")
        if not normalized:
            return ""
        return normalized[:72]

    @staticmethod
    def _normalize_download_url(source_url: str) -> str:
        raw = (source_url or "").strip()
        split = urlsplit(raw)
        if not split.scheme or not split.netloc:
            return raw
        # Keep semantic structure but ensure unsafe chars (e.g. spaces) are percent-encoded.
        path = quote(unquote(split.path), safe="/:@%+._~-")
        query = quote(unquote(split.query), safe="=&%+/:@,._~-")
        return urlunsplit((split.scheme, split.netloc, path, query, split.fragment))

    def _read_with_retries(self, *, source_url: str) -> tuple[int, str, bytes]:
        req = Request(source_url, headers={"User-Agent": self.user_agent})
        attempt = 0
        while True:
            try:
                with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                    status_code = int(getattr(resp, "status", 200))
                    content_type = str(resp.headers.get("Content-Type", ""))
                    if attempt > 0:
                        log_event(
                            logger,
                            logging.INFO,
                            "download_retry_succeeded",
                            url=source_url,
                            attempt=attempt + 1,
                            status=status_code,
                            content_type=content_type or "-",
                        )
                    return status_code, content_type, resp.read()
            except HTTPError as exc:
                is_retryable = self._should_retry_status(exc.code)
                if not is_retryable:
                    log_event(
                        logger,
                        logging.ERROR,
                        "download_http_error",
                        url=source_url,
                        attempt=attempt + 1,
                        status=exc.code,
                        retryable=False,
                        error_class=exc.__class__.__name__,
                        error=str(exc),
                    )
                    raise
                if attempt >= self.max_retries:
                    log_event(
                        logger,
                        logging.ERROR,
                        "download_max_retries_exhausted",
                        url=source_url,
                        attempts=attempt + 1,
                        status=exc.code,
                        error_class=exc.__class__.__name__,
                        error=str(exc),
                    )
                    raise
                retry_after_delay = self._retry_after_seconds(exc)
                error_class = "HTTPError"
                error_text = str(exc)
                status_code = exc.code
            except URLError as exc:
                if attempt >= self.max_retries:
                    log_event(
                        logger,
                        logging.ERROR,
                        "download_max_retries_exhausted",
                        url=source_url,
                        attempts=attempt + 1,
                        status=0,
                        error_class=exc.__class__.__name__,
                        error=str(exc),
                    )
                    raise
                retry_after_delay = None
                error_class = "URLError"
                error_text = str(exc)
                status_code = 0

            delay = min(self.backoff_base_seconds * (2**attempt), self.backoff_max_seconds)
            delay += random.uniform(0.0, self.jitter_seconds)
            if retry_after_delay is not None:
                delay = max(delay, retry_after_delay)
            log_event(
                logger,
                logging.WARNING,
                "download_retry_scheduled",
                url=source_url,
                attempt=attempt + 1,
                status=status_code,
                error_class=error_class,
                delay_seconds=round(delay, 3),
                retry_after_seconds=(round(retry_after_delay, 3) if retry_after_delay is not None else "none"),
                max_retries=self.max_retries,
                error=error_text,
            )
            if self.retry_callback is not None:
                try:
                    self.retry_callback(
                        {
                            "source_url": source_url,
                            "attempt": attempt + 1,
                            "status": status_code,
                            "error_class": error_class,
                            "error_text": error_text,
                            "delay_seconds": delay,
                            "retry_after_seconds": retry_after_delay,
                            "max_retries": self.max_retries,
                        }
                    )
                except Exception:
                    pass
            time.sleep(delay)
            attempt += 1

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    @staticmethod
    def _retry_after_seconds(exc: HTTPError) -> float | None:
        headers = getattr(exc, "headers", None)
        if headers is None:
            return None
        value = headers.get("Retry-After")
        if not value:
            return None
        value = str(value).strip()
        if value.isdigit():
            return float(value)
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            return max(0.0, (retry_at - now).total_seconds())
        except Exception:
            return None

    @staticmethod
    def _guess_extension(*, source_url: str, content_type: str) -> str:
        lower_url = source_url.lower()
        lower_ct = content_type.lower()
        if lower_url.endswith(".pdf") or "pdf" in lower_ct:
            return ".pdf"
        return ".bin"
