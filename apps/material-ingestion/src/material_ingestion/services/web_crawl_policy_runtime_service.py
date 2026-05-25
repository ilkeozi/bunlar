from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from material_ingestion.services.web_crawl_robots_service import persist_robots_policy
from material_ingestion.services.web_crawl_sitemap_service import parse_sitemap_document, persist_sitemap_entries


@dataclass(slots=True)
class RobotsFetchResult:
    robots_txt: str
    fetch_status: str


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
    max_depth: int = 4,
    max_sitemaps: int = 50,
) -> int:
    total_inserted = 0
    queue: list[tuple[str, int]] = [(url, 0) for url in extract_sitemap_urls(robots_txt=robots_txt, host=host)]
    seen: set[str] = set()
    while queue and len(seen) < max_sitemaps:
        sitemap_url, depth = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        try:
            xml_text = fetch_text_url(url=sitemap_url)
            total_inserted += persist_sitemap_entries(
                host_id=host_id,
                sitemap_url=sitemap_url,
                discovered_via="robots_or_default",
                xml_text=xml_text,
            )
            _, nested_sitemaps = parse_sitemap_document(xml_text)
            if depth < max_depth:
                for nested in nested_sitemaps:
                    if nested not in seen:
                        queue.append((nested, depth + 1))
        except Exception:
            # Fail-open for crawler continuity; caller handles logging.
            continue
    return total_inserted


def host_from_url(url: str) -> str:
    return urlsplit(url).netloc
