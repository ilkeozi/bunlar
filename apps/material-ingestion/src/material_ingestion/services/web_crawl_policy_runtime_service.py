from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
import re
from decimal import Decimal
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from material_ingestion.services.web_crawl_robots_service import persist_robots_policy
from material_ingestion.services.web_crawl_sitemap_service import (
    has_successful_sitemap_source,
    persist_sitemap_urls,
)
from usp.tree import sitemap_tree_for_homepage
from usp.web_client.requests_client import RequestsWebClient

USP_LOGGER_NAME = "usp.objects.sitemap"
INVALID_SITEMAP_RE = re.compile(r"Invalid sitemap:\s*(?P<url>\S+)\s*,\s*reason:\s*(?P<reason>.+)$")
logger = logging.getLogger("material_ingestion.web")


@dataclass(slots=True)
class RobotsFetchResult:
    robots_txt: str
    fetch_status: str


class _UspInvalidSitemapCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.invalid_urls: set[str] = set()

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        match = INVALID_SITEMAP_RE.search(message)
        if not match:
            return
        url = (match.group("url") or "").strip()
        if url:
            self.invalid_urls.add(url)


def fetch_robots_txt(*, host: str, timeout_seconds: float = 5.0, user_agent: str = "material-ingestion-bot/1.0") -> RobotsFetchResult:
    robots_url = f"https://{host}/robots.txt"
    req = Request(robots_url, headers={"User-Agent": user_agent})
    try:
        with urlopen(req, timeout=timeout_seconds) as res:  # nosec B310 - controlled crawler fetch target
            body = res.read().decode("utf-8", errors="replace")
            return RobotsFetchResult(robots_txt=body, fetch_status="success")
    except Exception:
        return RobotsFetchResult(robots_txt="", fetch_status="failed")


def extract_sitemap_urls(*, robots_txt: str, host: str) -> list[str]:
    discovered: list[str] = []
    seen: set[str] = set()
    for line in (robots_txt or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() != "sitemap":
            continue
        url = value.strip()
        if not url:
            continue
        if url not in seen:
            discovered.append(url)
            seen.add(url)
    default = f"https://{host}/sitemap.xml"
    if default not in seen:
        discovered.append(default)
    return discovered


def fetch_text_url(*, url: str, timeout_seconds: float = 8.0, user_agent: str = "material-ingestion-bot/1.0") -> str:
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as res:  # nosec B310 - controlled crawler fetch target
        return res.read().decode("utf-8", errors="replace")


def bootstrap_host_policy(*, host_id: int, host: str, sample_target_url: str) -> RobotsFetchResult:
    robots = fetch_robots_txt(host=host)
    persist_robots_policy(
        host_id=host_id,
        robots_txt=robots.robots_txt,
        fetch_status=robots.fetch_status,
        evaluation_summary={
            "target_url": sample_target_url,
            "host": host,
        },
    )
    return robots


def discover_and_persist_host_sitemaps(
    *,
    host_id: int,
    host: str,
    robots_txt: str,
    max_depth: int = 0,
    max_sitemaps: int = 0,
    heartbeat_callback: Callable[[], None] | None = None,
) -> int:
    _ = max_depth
    _ = max_sitemaps
    sitemap_url = f"https://{host}/sitemap.xml"
    if has_successful_sitemap_source(host_id=host_id, sitemap_url=sitemap_url):
        logger.info("event=sitemap_fetch_skipped_already_successful host=%s sitemap_url=%s", host, sitemap_url)
        return 0

    web_client = RequestsWebClient()
    web_client.set_timeout((5.0, 20.0))

    collector = _UspInvalidSitemapCollector()
    usp_logger = logging.getLogger(USP_LOGGER_NAME)
    usp_logger.addHandler(collector)
    try:
        tree = sitemap_tree_for_homepage(
            f"https://{host}/",
            web_client=web_client,
            use_robots=True,
            use_known_paths=False,
        )
        raw_entries = []
        for page in tree.all_pages():
            page_url = getattr(page, "url", "")
            if not page_url:
                continue
            raw_priority = getattr(page, "priority", None)
            priority = float(raw_priority) if isinstance(raw_priority, (int, float, Decimal)) else None
            raw_changefreq = getattr(page, "change_frequency", None)
            changefreq = getattr(raw_changefreq, "value", None) if raw_changefreq is not None else None
            raw_entries.append(
                {
                    "url": page_url,
                    "lastmod_at": getattr(page, "last_modified", None),
                    "changefreq": changefreq,
                    "priority": priority,
                    "alternates": list(getattr(page, "alternates", []) or []),
                    "images": [img.to_dict() for img in (getattr(page, "images", None) or [])],
                    "news_story": getattr(getattr(page, "news_story", None), "to_dict", lambda: None)(),
                }
            )
    finally:
        usp_logger.removeHandler(collector)

    invalid_urls = collector.invalid_urls
    entries = [entry for entry in raw_entries if str(entry.get("url", "")) not in invalid_urls]
    logger.info("event=sitemap_fetch_completed host=%s discovered_urls=%s invalid_urls=%s", host, len(entries), len(invalid_urls))
    return persist_sitemap_urls(
        host_id=host_id,
        sitemap_url=sitemap_url,
        discovered_via="usp_homepage_discovery",
        entries=entries,
        heartbeat_callback=heartbeat_callback,
    )


def host_from_url(url: str) -> str:
    return urlsplit(url).netloc
