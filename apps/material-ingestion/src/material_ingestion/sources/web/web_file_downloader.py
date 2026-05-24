from __future__ import annotations

import hashlib
import random
import time
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


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
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.backoff_max_seconds = backoff_max_seconds
        self.jitter_seconds = jitter_seconds

    def download_pdf(self, *, source_url: str, output_root: Path) -> DownloadedFile:
        status_code, content_type, data = self._read_with_retries(source_url=source_url)

        digest = hashlib.sha256(data).hexdigest()
        ext = self._guess_extension(source_url=source_url, content_type=content_type)
        host = (urlparse(source_url).netloc or "unknown-host").replace(":", "_")
        target_dir = output_root / host
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{digest}{ext}"
        target_path.write_bytes(data)

        return DownloadedFile(
            source_url=source_url,
            stored_path=str(target_path),
            sha256=digest,
            size_bytes=len(data),
            content_type=content_type,
            status_code=status_code,
        )

    def _read_with_retries(self, *, source_url: str) -> tuple[int, str, bytes]:
        req = Request(source_url, headers={"User-Agent": self.user_agent})
        attempt = 0
        while True:
            try:
                with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                    status_code = int(getattr(resp, "status", 200))
                    content_type = str(resp.headers.get("Content-Type", ""))
                    return status_code, content_type, resp.read()
            except HTTPError as exc:
                if not self._should_retry_status(exc.code) or attempt >= self.max_retries:
                    raise
                retry_after_delay = self._retry_after_seconds(exc)
            except URLError:
                if attempt >= self.max_retries:
                    raise
                retry_after_delay = None

            delay = min(self.backoff_base_seconds * (2**attempt), self.backoff_max_seconds)
            delay += random.uniform(0.0, self.jitter_seconds)
            if retry_after_delay is not None:
                delay = max(delay, retry_after_delay)
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
