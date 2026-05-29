from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.db_export_models import (
    AnalysisDataset,
    CandidateDocumentRow,
    CrawlHostRow,
    ExtractedLinkRow,
    FrontierItemRow,
    HttpFetchAttemptRow,
    HttpRepresentationRow,
    PageTextRow,
    SitemapAlternateRow,
    SitemapEntryRow,
    UriIdentityRow,
)
from material_ingestion.services.url_intelligence.stats_builder import (
    build_host_stats,
    build_pattern_stats,
    build_template_observations,
    build_uri_contexts,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _host(id: int, hostname: str) -> CrawlHostRow:
    return CrawlHostRow(id=id, hostname=hostname)


def _uri(id: int, host_id: int, uri: str) -> UriIdentityRow:
    return UriIdentityRow(id=id, canonical_uri=uri, normalized_hash=f"hash{id}", host_id=host_id)


def _attempt(id: int, uri_id: int, *, outcome: str = "success", status: int = 200, total_ms: int = 300) -> HttpFetchAttemptRow:
    return HttpFetchAttemptRow(id=id, uri_identity_id=uri_id, crawl_run_id=1, outcome=outcome, status_code=status, total_ms=total_ms)


def _repr(id: int, attempt_id: int, *, content_type: str = "text/html") -> HttpRepresentationRow:
    return HttpRepresentationRow(id=id, fetch_attempt_id=attempt_id, content_type=content_type, content_language="en")


def _page_text(id: int, attempt_id: int, *, render_needed: bool = False, text_ratio: float = 0.2) -> PageTextRow:
    return PageTextRow(id=id, fetch_attempt_id=attempt_id, render_needed=render_needed, text_ratio=text_ratio, text_length=500)


def _candidate_doc(id: int, uri_id: int, *, mime: str = "application/pdf", classification: str = "material_document") -> CandidateDocumentRow:
    return CandidateDocumentRow(id=id, uri_identity_id=uri_id, source_uri_identity_id=1, mime_type=mime, classification=classification)


# ---------------------------------------------------------------------------
# Test A: URI contexts are assembled from joined rows
# ---------------------------------------------------------------------------


class TestBuildUriContexts(unittest.TestCase):

    def setUp(self) -> None:
        self.host = _host(1, "example.com")
        self.uri = _uri(1, 1, "https://example.com/en/products/12345")
        attempt = _attempt(1, 1, total_ms=450)
        rep = _repr(1, 1, content_type="text/html")
        pt = _page_text(1, 1, render_needed=True, text_ratio=0.05)
        fi = FrontierItemRow(id=1, uri_identity_id=1, crawl_run_id=1, state="completed", priority=5)

        self.dataset = AnalysisDataset(
            uri_identities=[self.uri],
            hosts=[self.host],
            frontier_items=[fi],
            fetch_attempts=[attempt],
            representations=[rep],
            page_texts=[pt],
            extracted_links=[],
            candidate_documents=[],
        )

    def test_context_has_hostname(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].hostname, "example.com")

    def test_context_has_fetch_outcome(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].latest_fetch_outcome, "success")

    def test_context_has_total_ms(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].latest_total_ms, 450)

    def test_context_has_render_needed(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertTrue(ctx[1].render_needed)

    def test_context_has_text_ratio(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertAlmostEqual(ctx[1].text_ratio, 0.05)

    def test_context_has_content_language(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].content_language, "en")

    def test_frontier_state_propagated(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].frontier_state, "completed")

    def test_frontier_priority_propagated(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[1].frontier_priority, 5)


class TestBuildUriContextsWithLinks(unittest.TestCase):

    def setUp(self) -> None:
        self.dataset = AnalysisDataset(
            uri_identities=[
                _uri(1, 1, "https://example.com/page"),
                _uri(2, 1, "https://example.com/download.pdf"),
            ],
            hosts=[_host(1, "example.com")],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[
                ExtractedLinkRow(id=1, source_uri_identity_id=1, target_uri_identity_id=2, anchor_text="Download PDF"),
                ExtractedLinkRow(id=2, source_uri_identity_id=1, target_uri_identity_id=2, anchor_text=""),
            ],
            candidate_documents=[
                _candidate_doc(1, 2, mime="application/pdf"),
            ],
        )

    def test_outbound_link_count(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        # URI 1 has 2 outbound links
        self.assertEqual(ctx[1].extracted_link_count, 2)

    def test_inbound_link_count(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        # URI 2 has 2 inbound links from URI 1
        self.assertEqual(ctx[2].inbound_link_count, 2)

    def test_candidate_document_count(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertEqual(ctx[2].candidate_document_count, 1)

    def test_technical_candidate_count_pdf(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        # mime_type=application/pdf → counts as technical candidate
        self.assertEqual(ctx[2].technical_candidate_document_count, 1)


class TestBuildUriContextsSitemap(unittest.TestCase):

    def setUp(self) -> None:
        self.dataset = AnalysisDataset(
            uri_identities=[_uri(1, 1, "https://example.com/products/abc")],
            hosts=[_host(1, "example.com")],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
            sitemap_entries=[SitemapEntryRow(id=10, sitemap_source_id=1, uri_identity_id=1)],
            sitemap_alternates=[
                SitemapAlternateRow(id=1, sitemap_entry_id=10, hreflang="en", href="https://example.com/products/abc"),
                SitemapAlternateRow(id=2, sitemap_entry_id=10, hreflang="de", href="https://example.com/de/products/abc"),
            ],
        )

    def test_is_in_sitemap(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertTrue(ctx[1].is_in_sitemap)

    def test_has_english_hreflang(self) -> None:
        ctx = build_uri_contexts(self.dataset)
        self.assertTrue(ctx[1].has_english_hreflang)


class TestBuildUriContextsNoFetch(unittest.TestCase):

    def test_render_needed_is_none_when_not_fetched(self) -> None:
        dataset = AnalysisDataset(
            uri_identities=[_uri(1, 1, "https://example.com/page")],
            hosts=[_host(1, "example.com")],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        ctx = build_uri_contexts(dataset)
        self.assertIsNone(ctx[1].render_needed)
        self.assertIsNone(ctx[1].latest_fetch_outcome)


# ---------------------------------------------------------------------------
# Test B: pattern stats derived from fetch/page_text/candidate rows
# ---------------------------------------------------------------------------


class TestBuildPatternStats(unittest.TestCase):
    """60 URIs on same template, 59 render_needed, 0 candidate docs."""

    def setUp(self) -> None:
        host = _host(1, "big-host.com")
        uris = [_uri(i, 1, f"https://big-host.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i, total_ms=400) for i in range(1, 61)]
        reprs = [_repr(i, i, content_type="text/html") for i in range(1, 61)]
        # 59 render_needed, 1 not
        pts = [_page_text(i, i, render_needed=(i < 60)) for i in range(1, 61)]

        self.dataset = AnalysisDataset(
            uri_identities=uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        )

    def test_sample_count(self) -> None:
        observations = build_template_observations(self.dataset)
        stats_map = build_pattern_stats(observations)
        # All 60 URIs share /en/products/{numeric_id} as medium template
        key = next(k for k in stats_map if "big-host.com" in k[0])
        self.assertEqual(stats_map[key].sample_count, 60)

    def test_render_needed_count(self) -> None:
        observations = build_template_observations(self.dataset)
        stats_map = build_pattern_stats(observations)
        key = next(k for k in stats_map if "big-host.com" in k[0])
        self.assertEqual(stats_map[key].render_needed_count, 59)

    def test_candidate_document_count_zero(self) -> None:
        observations = build_template_observations(self.dataset)
        stats_map = build_pattern_stats(observations)
        key = next(k for k in stats_map if "big-host.com" in k[0])
        self.assertEqual(stats_map[key].candidate_document_count, 0)

    def test_technical_document_count_zero(self) -> None:
        observations = build_template_observations(self.dataset)
        stats_map = build_pattern_stats(observations)
        key = next(k for k in stats_map if "big-host.com" in k[0])
        self.assertEqual(stats_map[key].technical_document_count, 0)


class TestBuildPatternStatsTechDocs(unittest.TestCase):
    """Pattern with technical PDFs should show positive tech_doc counts."""

    def setUp(self) -> None:
        host = _host(1, "docs.example.com")
        uris = [_uri(i, 1, f"https://docs.example.com/tds/product_{i}_TDS.pdf") for i in range(1, 11)]
        attempts = [_attempt(i, i) for i in range(1, 11)]
        reprs = [_repr(i, i, content_type="application/pdf") for i in range(1, 11)]
        docs = [_candidate_doc(i, i, mime="application/pdf", classification="material_document") for i in range(1, 11)]

        self.dataset = AnalysisDataset(
            uri_identities=uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=[],
            extracted_links=[],
            candidate_documents=docs,
        )

    def test_technical_document_count_positive(self) -> None:
        observations = build_template_observations(self.dataset)
        stats_map = build_pattern_stats(observations)
        total_tech = sum(ps.technical_document_count for ps in stats_map.values())
        self.assertGreater(total_tech, 0)

    def test_document_fetch_method_used(self) -> None:
        observations = build_template_observations(self.dataset)
        methods = {obs.fetch_method for obs in observations}
        self.assertIn("document_fetch", methods)


class TestBuildHostStats(unittest.TestCase):

    def setUp(self) -> None:
        hosts = [_host(1, "host-a.com"), _host(2, "host-b.com")]
        uris = [
            _uri(1, 1, "https://host-a.com/page1"),
            _uri(2, 1, "https://host-a.com/page2"),
            _uri(3, 2, "https://host-b.com/page1"),
        ]
        attempts = [
            _attempt(1, 1),
            _attempt(2, 2),
            _attempt(3, 3),
        ]
        pts = [
            _page_text(1, 1, render_needed=True),
            _page_text(2, 2, render_needed=False),
            _page_text(3, 3, render_needed=False),
        ]
        self.dataset = AnalysisDataset(
            uri_identities=uris,
            hosts=hosts,
            frontier_items=[],
            fetch_attempts=attempts,
            representations=[_repr(i, i) for i in range(1, 4)],
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        )

    def test_total_uri_count(self) -> None:
        obs = build_template_observations(self.dataset)
        hstats = build_host_stats(self.dataset, obs)
        self.assertEqual(hstats["host-a.com"].total_uri_count, 2)
        self.assertEqual(hstats["host-b.com"].total_uri_count, 1)

    def test_render_needed_count(self) -> None:
        obs = build_template_observations(self.dataset)
        hstats = build_host_stats(self.dataset, obs)
        self.assertEqual(hstats["host-a.com"].render_needed_count, 1)

    def test_fetched_count(self) -> None:
        obs = build_template_observations(self.dataset)
        hstats = build_host_stats(self.dataset, obs)
        self.assertEqual(hstats["host-a.com"].fetched_count, 2)


if __name__ == "__main__":
    unittest.main()
