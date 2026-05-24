from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
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
            if candidates:
                log(f"discovery: html phase found {len(candidates)} candidates; js fallback skipped")
                return pages, candidates, observations
            try:
                log("discovery: html phase found 0 candidates; falling back to js-rendered crawl")
                return self._discover_with_fetcher(
                    seed_url=seed_url,
                    same_domain_only=same_domain_only,
                    max_pages=max_pages,
                    fetcher=lambda url: self._fetch_html_rendered(url, progress=log),
                    progress=log,
                )
            except Exception:
                log("discovery: js fallback unavailable/failed; returning html phase result")
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
            pages.append(
                {
                    "url": current,
                    "status_code": status_code,
                    "content_type": content_type,
                    "crawl_ok": bool(html),
                }
            )
            if not html:
                progress(f"discovery: no html body (status={status_code}, content_type={content_type})")
                continue

            parser = _LinkParser()
            parser.feed(html)
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
                        is_json = "json" in content_type
                        if is_json:
                            json_payload_count += 1
                            body_source = "response.text"
                            body = resp.text()
                            if not body:
                                try:
                                    body = resp.body().decode("utf-8", errors="ignore")
                                    body_source = "response.body"
                                except Exception:
                                    body = ""
                            if not body and str(resp.request.method).upper() == "GET":
                                # Try browser-context API request first (shares browser context/session).
                                try:
                                    api_resp = context.request.get(
                                        response_url,
                                        timeout=self.timeout_seconds * 1000,
                                        headers={"Accept": "application/json"},
                                    )
                                    if api_resp.ok:
                                        body = api_resp.text()
                                        body_source = "context.request.get"
                                except Exception:
                                    body = ""
                            if not body and str(resp.request.method).upper() == "GET":
                                # Some sites return empty playwright response text/body for fetch responses.
                                # Fallback to direct GET to recover JSON payload for generic extraction.
                                try:
                                    req = Request(response_url, headers={"User-Agent": self.user_agent})
                                    with urlopen(req, timeout=self.timeout_seconds) as direct_resp:  # noqa: S310
                                        body = direct_resp.read().decode("utf-8", errors="ignore")
                                        body_source = "urlopen"
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
                                    if "/dss-proxy/v1/results" in response_url:
                                        log(
                                            "discovery: results payload parsed "
                                            f"url={response_url} candidates={len(doc_candidates)} relevance={relevance}"
                                        )
                                    if relevance >= 3:
                                        relevant_json_payload_count += 1
                                        extracted_urls = [c["url"] for c in doc_candidates]
                                        for candidate in doc_candidates:
                                            candidate_url = str(candidate["url"])
                                            api_discovered_urls.add(candidate_url)
                                            existing_reason = api_discovered_reasons.get(candidate_url, "")
                                            new_reason = str(candidate["reason"])
                                            if not existing_reason or new_reason.startswith("api_payload_pdf"):
                                                api_discovered_reasons[candidate_url] = new_reason
                                    if "/dss-proxy/v1/results" in response_url:
                                        paginated_result_urls.append(response_url)
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
                            )
                        )
                    except Exception:
                        return

                page.on("response", on_response)
                resp = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_seconds * 1000)
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
                    page.wait_for_load_state("networkidle", timeout=self.timeout_seconds * 1000)
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
        page_values = query.get("page", ["0"])
        limit_values = query.get("limit", ["30"])
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
            if len(results) < limit:
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

        def add_candidate(url: str, score: int, reason: str) -> None:
            normalized = WebPdfDiscovery._normalize_url(url)
            if not normalized:
                return
            existing = candidates.get(normalized)
            if existing is None or score > int(existing["score"]):
                candidates[normalized] = {"url": normalized, "score": score, "reason": reason}

        def walk(node: object) -> None:
            if isinstance(node, dict):
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
                        add_candidate(url=url, score=score, reason=reason)

                for value in node.values():
                    walk(value)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return

        walk(payload)
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
            # Generic fast-path for common result APIs.
            if "results" in keys and "/results" in lower_response_url:
                score += 4
        if candidates:
            score += 2
            best = max(int(c["score"]) for c in candidates)
            score += min(4, best)
        return score
