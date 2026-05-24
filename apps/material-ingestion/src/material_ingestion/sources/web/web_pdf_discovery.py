from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
import hashlib
import json
import re
from html import escape
import os
from typing import Callable, Literal
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

DiscoveryStrategy = Literal["html", "js", "auto"]


@dataclass(slots=True)
class PdfCandidate:
    source_page_url: str
    pdf_url: str
    anchor_text: str
    score: int
    reason: str


@dataclass(slots=True)
class FetchXhrObservation:
    source_page_url: str
    response_url: str
    resource_type: str
    status_code: int
    content_type: str
    is_json: bool
    extracted_urls: list[str]
    extracted_documents: list[dict[str, object]]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href" and value:
                href = value.strip()
                break
        if href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None and data.strip():
            self._current_text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return
        text = " ".join(self._current_text).strip()
        self.links.append((self._current_href, text))
        self._current_href = None
        self._current_text = []


class WebPdfDiscovery:
    def __init__(self, *, user_agent: str = "material-ingestion-bot/1.0", timeout_seconds: int = 20):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    def discover(
        self,
        *,
        seed_url: str,
        same_domain_only: bool = True,
        max_pages: int = 100,
        strategy: DiscoveryStrategy = "auto",
        progress: Callable[[str], None] | None = None,
    ) -> tuple[list[dict[str, object]], list[PdfCandidate], list[FetchXhrObservation]]:
        log = progress or (lambda _msg: None)
        if strategy == "auto":
            log("discovery: strategy=auto, phase=html")
            pages, candidates, observations = self._discover_with_fetcher(
                seed_url=seed_url,
                same_domain_only=same_domain_only,
                max_pages=max_pages,
                fetcher=self._fetch_html,
                progress=log,
            )
            # Always run js-rendered discovery on the seed page as well, so
            # network/API-origin candidates are still captured in auto mode.
            try:
                log(
                    "discovery: auto mode running js-rendered seed-page discovery "
                    f"(html_candidates={len(candidates)})"
                )
                js_pages, js_candidates, js_observations = self._discover_with_fetcher(
                    seed_url=seed_url,
                    same_domain_only=same_domain_only,
                    max_pages=1,
                    fetcher=lambda url: self._fetch_html_rendered(url, progress=log),
                    progress=log,
                )
                merged_pages = list(pages)
                page_urls = {str(p.get("url", "")) for p in merged_pages}
                for p in js_pages:
                    url = str(p.get("url", ""))
                    if url in page_urls:
                        continue
                    merged_pages.append(p)
                    page_urls.add(url)

                candidate_by_url: dict[str, PdfCandidate] = {c.pdf_url: c for c in candidates}
                for c in js_candidates:
                    existing = candidate_by_url.get(c.pdf_url)
                    if existing is None or c.score > existing.score:
                        candidate_by_url[c.pdf_url] = c

                merged_observations = observations + js_observations
                merged_candidates = sorted(candidate_by_url.values(), key=lambda c: (-c.score, c.pdf_url))
                return merged_pages, merged_candidates, merged_observations
            except Exception as exc:
                log(
                    "discovery: js discovery unavailable/failed; returning html phase result "
                    f"error={exc.__class__.__name__}: {exc}"
                )
                return pages, candidates, observations
        if strategy == "js":
            log("discovery: strategy=js")
            return self._discover_with_fetcher(
                seed_url=seed_url,
                same_domain_only=same_domain_only,
                max_pages=max_pages,
                fetcher=lambda url: self._fetch_html_rendered(url, progress=log),
                progress=log,
            )
        log("discovery: strategy=html")
        return self._discover_with_fetcher(
            seed_url=seed_url,
            same_domain_only=same_domain_only,
            max_pages=max_pages,
            fetcher=self._fetch_html,
            progress=log,
        )

    def _discover_with_fetcher(
        self,
        *,
        seed_url: str,
        same_domain_only: bool,
        max_pages: int,
        fetcher: Callable[[str], tuple[str, int, str] | tuple[str, int, str, list[FetchXhrObservation]]],
        progress: Callable[[str], None],
    ) -> tuple[list[dict[str, object]], list[PdfCandidate], list[FetchXhrObservation]]:
        seed = self._normalize_url(seed_url, keep_fragment=True)
        seed_host = urlparse(seed).netloc.lower()

        visited: set[str] = set()
        queued: set[str] = {seed}
        queue: deque[str] = deque([seed])

        pages: list[dict[str, object]] = []
        candidates: dict[str, PdfCandidate] = {}
        fetch_observations: list[FetchXhrObservation] = []

        while queue and len(visited) < max_pages:
            current = queue.popleft()
            queued.discard(current)
            if current in visited:
                continue
            visited.add(current)
            progress(f"discovery: crawling page {len(visited)}/{max_pages}: {current}")

            fetched = fetcher(current)
            if len(fetched) == 3:
                html, status_code, content_type = fetched
                page_fetch_observations: list[FetchXhrObservation] = []
            else:
                html, status_code, content_type, page_fetch_observations = fetched
            fetch_observations.extend(page_fetch_observations)
            page_row = {
                "url": current,
                "status_code": status_code,
                "content_type": content_type,
                "crawl_ok": bool(html),
            }
            if not html:
                pages.append(page_row)
                progress(f"discovery: no html body (status={status_code}, content_type={content_type})")
                continue

            parser = _LinkParser()
            parser.feed(html)
            page_row.update(
                self._extract_page_observation(
                    page_url=current,
                    html=html,
                    links=parser.links,
                )
            )
            pages.append(page_row)
            page_new_candidates = 0
            for href, anchor_text in parser.links:
                absolute = self._normalize_url(urljoin(current, href))
                if not absolute:
                    continue
                parsed = urlparse(absolute)
                if parsed.scheme not in {"http", "https"}:
                    continue

                score, reason = self._score_pdf_candidate(absolute, anchor_text)
                if score > 0:
                    is_api_derived = str(anchor_text).startswith("__api_json_url__")
                    if same_domain_only and parsed.netloc.lower() != seed_host and not is_api_derived:
                        continue
                    existing = candidates.get(absolute)
                    new_candidate = PdfCandidate(
                        source_page_url=current,
                        pdf_url=absolute,
                        anchor_text=anchor_text,
                        score=score,
                        reason=reason,
                    )
                    if existing is None or new_candidate.score > existing.score:
                        candidates[absolute] = new_candidate
                        page_new_candidates += 1
                    continue

                if same_domain_only and parsed.netloc.lower() != seed_host:
                    continue

                if self._looks_like_html_page(absolute) and absolute not in visited and absolute not in queued:
                    queue.append(absolute)
                    queued.add(absolute)
            progress(
                f"discovery: page done links={len(parser.links)} new_candidates={page_new_candidates} "
                f"queue={len(queue)} total_candidates={len(candidates)}"
            )

        return pages, sorted(candidates.values(), key=lambda c: (-c.score, c.pdf_url)), fetch_observations

    @staticmethod
    def _extract_page_observation(*, page_url: str, html: str, links: list[tuple[str, str]]) -> dict[str, object]:
        lower = html.lower()
        title = ""
        m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        excerpt = text[:500]
        input_count = len(re.findall(r"<input\b", lower))
        button_count = len(re.findall(r"<button\b", lower))
        form_count = len(re.findall(r"<form\b", lower))
        has_download_keywords = any(
            token in lower for token in ("download", "datasheet", "technical data sheet", "pdf", "brochure", "sds", "tds")
        )
        page_class = WebPdfDiscovery._classify_page(
            page_url=page_url,
            has_download_keywords=has_download_keywords,
            input_count=input_count,
            form_count=form_count,
            anchor_count=len(links),
            title=title,
            lower_html=lower,
        )
        html_profile, max_html_bytes = WebPdfDiscovery._snapshot_policy(page_class=page_class)
        html_bytes = html.encode("utf-8", errors="ignore")
        raw_html_sha256 = hashlib.sha256(html_bytes).hexdigest()
        raw_html_truncated = len(html_bytes) > max_html_bytes if max_html_bytes > 0 else False
        raw_html = html_bytes[:max_html_bytes].decode("utf-8", errors="ignore") if max_html_bytes > 0 else ""
        extracted_links = [
            {"url": href, "text": text[:160]}
            for href, text in links[:100]
        ]
        return {
            "page_title": title,
            "text_excerpt": excerpt,
            "raw_html": raw_html,
            "raw_html_sha256": raw_html_sha256,
            "raw_html_bytes": len(html_bytes),
            "raw_html_truncated": raw_html_truncated,
            "anchor_count": len(links),
            "input_count": input_count,
            "button_count": button_count,
            "form_count": form_count,
            "has_download_keywords": has_download_keywords,
            "page_class": page_class,
            "snapshot_profile": html_profile,
            "snapshot_html_max_bytes": max_html_bytes,
            "links_sample": extracted_links,
            "links_sample_truncated": len(links) > len(extracted_links),
        }

    @staticmethod
    def _snapshot_policy(*, page_class: str) -> tuple[str, int]:
        mode = (os.getenv("MATERIAL_INGESTION_PAGE_SNAPSHOT_MODE", "auto") or "auto").strip().lower()
        legacy_default = (os.getenv("MATERIAL_INGESTION_PAGE_HTML_MAX_BYTES", "250000") or "250000").strip()

        def _env_int(name: str, default: str) -> int:
            try:
                value = int((os.getenv(name, default) or default).strip())
            except ValueError:
                value = int(default)
            return max(value, 0)

        if mode == "none":
            return ("none", 0)
        if mode == "full":
            return ("full", _env_int("MATERIAL_INGESTION_PAGE_HTML_MAX_BYTES", legacy_default))

        # auto mode by class
        if page_class in {"interactive_search", "document_hub"}:
            return (
                "rich",
                _env_int("MATERIAL_INGESTION_PAGE_HTML_MAX_BYTES_RICH", "75000"),
            )
        if page_class == "indexable":
            return (
                "standard",
                _env_int("MATERIAL_INGESTION_PAGE_HTML_MAX_BYTES_STANDARD", "0"),
            )
        return (
            "minimal",
            _env_int("MATERIAL_INGESTION_PAGE_HTML_MAX_BYTES_LOW_VALUE", "0"),
        )

    @staticmethod
    def _classify_page(
        *,
        page_url: str,
        has_download_keywords: bool,
        input_count: int,
        form_count: int,
        anchor_count: int,
        title: str,
        lower_html: str,
    ) -> str:
        url = page_url.lower()
        title_l = title.lower()
        if any(token in url for token in ("/legal", "/privacy", "terms", "/contact", "/imprint")):
            if not has_download_keywords and form_count == 0:
                return "low_value"
        if any(token in url for token in ("download", "datasheet", "documents", "library", "catalog")):
            if has_download_keywords or anchor_count >= 20:
                return "document_hub"
        if input_count > 0 or form_count > 0:
            if any(token in lower_html for token in ("search", "filter", "facet", "results", "document type", "language")):
                return "interactive_search"
        if any(token in title_l for token in ("download", "results", "catalog", "document")) and has_download_keywords:
            return "document_hub"
        return "indexable"

    def _fetch_html_rendered(
        self,
        url: str,
        *,
        progress: Callable[[str], None] | None = None,
    ) -> tuple[str, int, str, list[FetchXhrObservation]]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed. Install with: pip install playwright") from exc

        log = progress or (lambda _msg: None)
        page_host = urlparse(url).netloc.lower()
        render_timeout_seconds = int(os.getenv("MATERIAL_INGESTION_RENDER_TIMEOUT_SECONDS", "45"))
        render_timeout_ms = max(self.timeout_seconds, render_timeout_seconds) * 1000

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                api_discovered_urls: set[str] = set()
                api_discovered_reasons: dict[str, str] = {}
                fetch_response_count = 0
                json_payload_count = 0
                relevant_json_payload_count = 0
                observations: list[FetchXhrObservation] = []
                response_logs: list[str] = []
                paginated_result_urls: list[str] = []

                def on_response(resp) -> None:
                    nonlocal fetch_response_count, json_payload_count, relevant_json_payload_count
                    try:
                        resource_type = str(resp.request.resource_type)
                        if resource_type not in {"xhr", "fetch"}:
                            return
                        fetch_response_count += 1
                        response_url = str(resp.url or "")
                        response_host = urlparse(response_url).netloc.lower()
                        if response_host and response_host != page_host:
                            return
                        status_code = int(resp.status)
                        content_type = str(resp.header_value("content-type") or "").lower()
                        response_logs.append(
                            f"{resource_type} status={status_code} ct={content_type or '-'} url={response_url}"
                        )
                        extracted_urls: list[str] = []
                        extracted_documents: list[dict[str, object]] = []
                        is_json = "json" in content_type
                        if self._looks_like_paginated_api_url(response_url):
                            paginated_result_urls.append(response_url)
                        if is_json:
                            json_payload_count += 1
                            body_source = "response.text"
                            try:
                                body = resp.text()
                            except Exception:
                                body = ""
                            if body:
                                log(
                                    f"discovery: json body acquired url={response_url} source={body_source} bytes={len(body)}"
                                )
                                try:
                                    payload = json.loads(body)
                                except Exception as exc:
                                    log(f"discovery: json parse failed url={response_url} error={exc}")
                                    payload = None
                                if payload is not None:
                                    doc_candidates = self._extract_document_candidates_from_json_payload(payload)
                                    relevance = self._score_json_response_relevance(
                                        payload=payload,
                                        candidates=doc_candidates,
                                        response_url=response_url,
                                    )
                                    if self._looks_like_paginated_api_url(response_url):
                                        log(
                                            "discovery: paginated payload parsed "
                                            f"url={response_url} candidates={len(doc_candidates)} relevance={relevance}"
                                        )
                                    if relevance >= 3:
                                        relevant_json_payload_count += 1
                                        extracted_documents = doc_candidates
                                        extracted_urls = [str(c["url"]) for c in doc_candidates]
                                        for candidate in doc_candidates:
                                            candidate_url = str(candidate["url"])
                                            api_discovered_urls.add(candidate_url)
                                            existing_reason = api_discovered_reasons.get(candidate_url, "")
                                            new_reason = str(candidate["reason"])
                                            if not existing_reason or new_reason.startswith("api_payload_pdf"):
                                                api_discovered_reasons[candidate_url] = new_reason
                            else:
                                log(f"discovery: empty json body url={response_url}")
                        observations.append(
                            FetchXhrObservation(
                                source_page_url=url,
                                response_url=response_url,
                                resource_type=resource_type,
                                status_code=status_code,
                                content_type=content_type,
                                is_json=is_json,
                                extracted_urls=extracted_urls,
                                extracted_documents=extracted_documents,
                            )
                        )
                    except Exception:
                        return

                page.on("response", on_response)
                resp = page.goto(url, wait_until="domcontentloaded", timeout=render_timeout_ms)
                # Trigger lazy client-side fetches that often appear only after user-like movement.
                page.wait_for_timeout(600)
                try:
                    page.mouse.wheel(0, 1400)
                    page.wait_for_timeout(400)
                    page.mouse.wheel(0, -500)
                    page.wait_for_timeout(400)
                except Exception:
                    pass
                try:
                    page.wait_for_load_state("networkidle", timeout=render_timeout_ms)
                except Exception:
                    pass
                page.wait_for_timeout(500)
                status_code = int(resp.status) if resp is not None else 0
                content_type = ""
                if resp is not None:
                    content_type = str(resp.header_value("content-type") or "")
                html = page.content()
                for results_url in sorted(set(paginated_result_urls)):
                    paginated_candidates = self._harvest_paginated_results_api(
                        results_url=results_url,
                        progress=log,
                    )
                    for candidate in paginated_candidates:
                        api_discovered_urls.add(candidate["url"])
                        existing_reason = api_discovered_reasons.get(candidate["url"], "")
                        if not existing_reason or candidate["reason"].startswith("api_payload_pdf"):
                            api_discovered_reasons[candidate["url"]] = candidate["reason"]

                if api_discovered_urls:
                    synthetic_links = "".join([
                        f'<a href="{escape(u, quote=True)}">__api_json_url__:{escape(api_discovered_reasons.get(u, "api_json_url"))}</a>'
                        for u in sorted(api_discovered_urls)
                    ])
                    html = f"{html}\n{synthetic_links}"
                log(
                    "discovery: js network scan page="
                    f"{url} fetch_xhr_responses={fetch_response_count} "
                    f"json_payloads={json_payload_count} relevant_json_payloads={relevant_json_payload_count} "
                    f"api_urls={len(api_discovered_urls)}"
                )
                for line in response_logs[:20]:
                    log(f"discovery: js response {line}")
                if content_type and "text/html" not in content_type.lower():
                    return "", status_code, content_type, observations
                return html, status_code, content_type or "text/html", observations
            except Exception as exc:
                log(f"discovery: js rendered fetch failed url={url} error={exc.__class__.__name__}: {exc}")
                raise
            finally:
                browser.close()

    def _harvest_paginated_results_api(
        self,
        *,
        results_url: str,
        progress: Callable[[str], None],
    ) -> list[dict[str, str]]:
        parsed = urlparse(results_url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        page_key = self._first_present_key(query, ("page", "p", "pageindex", "page_index", "offset", "start"))
        limit_key = self._first_present_key(query, ("limit", "pagesize", "page_size", "size", "per_page", "count"))
        page_values = query.get(page_key, ["0"]) if page_key else ["0"]
        limit_values = query.get(limit_key, ["30"]) if limit_key else ["30"]
        try:
            start_page = max(0, int(page_values[0]))
        except Exception:
            start_page = 0
        try:
            limit = max(1, int(limit_values[0]))
        except Exception:
            limit = 30

        max_pages = int(os.getenv("MATERIAL_INGESTION_API_PAGINATION_MAX_PAGES", "50"))
        max_docs = int(os.getenv("MATERIAL_INGESTION_API_PAGINATION_MAX_DOCS", "5000"))

        all_candidates: dict[str, dict[str, str]] = {}
        page = start_page
        pages_seen = 0
        while pages_seen < max_pages and len(all_candidates) < max_docs:
            page_query = dict(query)
            if page_key:
                page_query[page_key] = [str(page)]
            else:
                page_query["page"] = [str(page)]
            new_query = urlencode(page_query, doseq=True)
            page_url = urlunparse(parsed._replace(query=new_query))
            req = Request(page_url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
            try:
                with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                    body = resp.read().decode("utf-8", errors="ignore")
                payload = json.loads(body)
            except Exception as exc:
                progress(f"discovery: pagination fetch failed page={page} url={page_url} error={exc}")
                break

            results = payload.get("results", []) if isinstance(payload, dict) else []
            if not isinstance(results, list):
                results = []
            page_candidates = self._extract_document_candidates_from_json_payload(payload)
            for cand in page_candidates:
                all_candidates[cand["url"]] = {"url": str(cand["url"]), "reason": str(cand["reason"])}

            progress(
                f"discovery: pagination page={page} results={len(results)} candidates={len(page_candidates)} "
                f"total_candidates={len(all_candidates)}"
            )
            pages_seen += 1
            if len(results) < limit or len(results) == 0:
                break
            page += 1

        return list(all_candidates.values())

    def _fetch_html(self, url: str) -> tuple[str, int, str]:
        req = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                status_code = int(getattr(resp, "status", 200))
                content_type = str(resp.headers.get("Content-Type", ""))
                if "text/html" not in content_type.lower():
                    return "", status_code, content_type
                body = resp.read().decode("utf-8", errors="ignore")
                return body, status_code, content_type
        except Exception:
            return "", 0, ""

    @staticmethod
    def _first_present_key(query: dict[str, list[str]], candidates: tuple[str, ...]) -> str | None:
        lowered = {str(k).lower(): k for k in query}
        for key in candidates:
            matched = lowered.get(key)
            if matched:
                return matched
        return None

    @staticmethod
    def _looks_like_paginated_api_url(url: str) -> bool:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        if not query:
            return False
        keys = {str(k).lower() for k in query}
        has_page = any(k in keys for k in {"page", "p", "pageindex", "page_index", "offset", "start"})
        has_size = any(k in keys for k in {"limit", "pagesize", "page_size", "size", "per_page", "count"})
        return has_page and has_size

    @staticmethod
    def _normalize_url(url: str, *, keep_fragment: bool = False) -> str:
        if not url:
            return ""
        parsed = urlparse(url.strip())
        if not parsed.scheme:
            return ""
        if keep_fragment:
            return parsed.geturl()
        fragmentless = parsed._replace(fragment="")
        return fragmentless.geturl()

    @staticmethod
    def _looks_like_html_page(url: str) -> bool:
        lower = url.lower()
        if lower.endswith(".pdf"):
            return False
        blocked_suffixes = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".zip", ".csv", ".json")
        return not lower.endswith(blocked_suffixes)

    @staticmethod
    def _score_pdf_candidate(url: str, anchor_text: str) -> tuple[int, str]:
        lower_url = url.lower()
        lower_text = anchor_text.lower()
        score = 0
        reasons: list[str] = []

        if lower_url.endswith(".pdf"):
            score += 5
            reasons.append("url_pdf_suffix")

        pdf_keywords = ("pdf", "datasheet", "data-sheet", "tds", "sds", "msds", "spec", "specification")
        if any(k in lower_url for k in pdf_keywords):
            score += 2
            reasons.append("url_keyword")
        if any(k in lower_text for k in pdf_keywords):
            score += 2
            reasons.append("anchor_keyword")
        if lower_text.startswith("__api_json_url__"):
            score += 3
            reasons.append("api_json_url")
            marker_reason = ""
            if ":" in lower_text:
                marker_reason = lower_text.split(":", 1)[1].strip()
            if marker_reason:
                reasons.append(marker_reason)
            if marker_reason.startswith("api_payload_pdf"):
                score += 4
            elif marker_reason.startswith("api_payload_document"):
                score += 2
            if any(k in lower_url for k in ("download", "document", "datasheet", "sds", "tds", "pdf")):
                score += 2
                reasons.append("api_document_hint")

        if score == 0:
            return 0, ""
        return score, ",".join(reasons)

    @staticmethod
    def _extract_urls_from_json_payload(payload: object) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()

        def add_if_url(value: str) -> None:
            match_iter = re.finditer(r"https?://[^\s\"'<>]+", value)
            for match in match_iter:
                candidate = match.group(0).rstrip(".,);")
                normalized = WebPdfDiscovery._normalize_url(candidate)
                if not normalized:
                    continue
                if normalized in seen:
                    continue
                seen.add(normalized)
                urls.append(normalized)

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, str):
                        lowered_key = str(key).lower()
                        if lowered_key in {"url", "href", "downloadurl", "documenturl", "asseturl", "link"}:
                            add_if_url(value)
                        else:
                            add_if_url(value)
                    else:
                        walk(value)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if isinstance(node, str):
                add_if_url(node)

        walk(payload)
        return urls

    @staticmethod
    def _extract_document_candidates_from_json_payload(payload: object) -> list[dict[str, object]]:
        url_keys = {"downloadurl", "viewurl", "fileurl", "url", "href", "link"}
        mime_keys = {"mimetype", "contenttype", "format"}
        doc_hint_tokens = ("technical data sheet", "datasheet", "specification", "sds", "msds", "tds")

        candidates: dict[str, dict[str, object]] = {}

        def add_candidate(url: str, score: int, reason: str, metadata: dict[str, object] | None = None) -> None:
            normalized = WebPdfDiscovery._normalize_url(url)
            if not normalized:
                return
            existing = candidates.get(normalized)
            row = {"url": normalized, "score": score, "reason": reason, "metadata": metadata or {}}
            if existing is None or score > int(existing["score"]):
                candidates[normalized] = row

        def metadata_from_node(node: dict[str, object], inherited: dict[str, object]) -> dict[str, object]:
            lowered = {str(k).lower(): v for k, v in node.items()}
            out = dict(inherited)
            for key in ("id", "title", "originaltitle", "type", "filename", "fileid", "format", "mimetype", "contenttype", "size"):
                if key in lowered:
                    out[key] = lowered[key]
            for key in ("languages", "locations", "legalareas"):
                if key in lowered and isinstance(lowered[key], list):
                    out[key] = lowered[key]
            return out

        def walk(node: object, inherited_meta: dict[str, object]) -> None:
            if isinstance(node, dict):
                current_meta = metadata_from_node(node, inherited_meta)
                lowered = {str(k).lower(): v for k, v in node.items()}
                mime_values = []
                for mk in mime_keys:
                    value = lowered.get(mk)
                    if isinstance(value, str):
                        mime_values.append(value.lower())
                doc_type_text = ""
                type_value = lowered.get("type")
                if isinstance(type_value, str):
                    doc_type_text = type_value.lower()

                for key, value in lowered.items():
                    if not isinstance(value, str):
                        continue
                    if key not in url_keys and "http" not in value.lower():
                        continue
                    for matched in re.finditer(r"https?://[^\s\"'<>]+", value):
                        url = matched.group(0).rstrip(".,);")
                        score = 1
                        reason = "api_json_url"
                        if key in {"downloadurl", "viewurl", "fileurl"}:
                            score += 3
                            reason = "api_payload_download_url"
                        if any("pdf" in mv for mv in mime_values) or any(mv == "pdf" for mv in mime_values):
                            score += 5
                            reason = "api_payload_pdf_mime"
                        elif any(tok in doc_type_text for tok in doc_hint_tokens):
                            score += 3
                            reason = "api_payload_document_type"
                        add_candidate(url=url, score=score, reason=reason, metadata=current_meta)

                for value in node.values():
                    walk(value, current_meta)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item, inherited_meta)
                return

        walk(payload, {})
        return sorted(candidates.values(), key=lambda c: (-(int(c["score"])), str(c["url"])))

    @staticmethod
    def _score_json_response_relevance(
        *,
        payload: object,
        candidates: list[dict[str, object]],
        response_url: str = "",
    ) -> int:
        score = 0
        lower_response_url = response_url.lower()
        if isinstance(payload, dict):
            keys = {str(k).lower() for k in payload.keys()}
            if "results" in keys or "items" in keys or "documents" in keys:
                score += 2
            if "variants" in keys:
                score += 2
            if ("results" in keys or "items" in keys or "documents" in keys) and WebPdfDiscovery._looks_like_paginated_api_url(response_url):
                score += 4
        if candidates:
            score += 2
            best = max(int(c["score"]) for c in candidates)
            score += min(4, best)
        return score
