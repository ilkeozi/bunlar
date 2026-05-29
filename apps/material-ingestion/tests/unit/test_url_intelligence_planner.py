from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.db_export_models import (
    AnalysisDataset,
    CandidateDocumentRow,
    CrawlHostRow,
    ExtractedLinkRow,
    HttpFetchAttemptRow,
    HttpRepresentationRow,
    PageTextRow,
    UriIdentityRow,
)
from material_ingestion.services.url_intelligence.models import NextAction, URLRole
from material_ingestion.services.url_intelligence.planner import (
    CrawlBudget,
    plan_from_dataset,
)


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------


def _host(id: int, hostname: str) -> CrawlHostRow:
    return CrawlHostRow(id=id, hostname=hostname)


def _uri(id: int, host_id: int, uri: str) -> UriIdentityRow:
    return UriIdentityRow(id=id, canonical_uri=uri, normalized_hash=f"h{id}", host_id=host_id)


def _attempt(id: int, uri_id: int, *, outcome: str = "success", total_ms: int = 300) -> HttpFetchAttemptRow:
    return HttpFetchAttemptRow(
        id=id, uri_identity_id=uri_id, crawl_run_id=1,
        outcome=outcome, status_code=200, total_ms=total_ms,
    )


def _repr(id: int, attempt_id: int, *, content_type: str = "text/html") -> HttpRepresentationRow:
    return HttpRepresentationRow(id=id, fetch_attempt_id=attempt_id, content_type=content_type)


def _page_text(id: int, attempt_id: int, *, render_needed: bool, total_ms: int = 300) -> PageTextRow:
    return PageTextRow(id=id, fetch_attempt_id=attempt_id, render_needed=render_needed, text_ratio=0.2)


def _candidate_doc(id: int, uri_id: int, *, mime: str = "application/pdf") -> CandidateDocumentRow:
    return CandidateDocumentRow(id=id, uri_identity_id=uri_id, source_uri_identity_id=1, mime_type=mime)


def _make_bad_pattern_dataset(
    *,
    big_host_count: int = 60,
    big_host_name: str = "big-host.com",
    big_host_id: int = 1,
    template_prefix: str = "https://big-host.com/en/products/",
) -> tuple[AnalysisDataset, list[UriIdentityRow]]:
    """Build a dataset with big_host_count observed URIs on a high-render-rate template."""
    host = _host(big_host_id, big_host_name)
    # Observed (already fetched, render_needed=True, no docs)
    obs_uris = [_uri(i, big_host_id, f"{template_prefix}{10000 + i}") for i in range(1, big_host_count + 1)]
    attempts = [_attempt(i, i, total_ms=400) for i in range(1, big_host_count + 1)]
    reprs = [_repr(i, i, content_type="text/html") for i in range(1, big_host_count + 1)]
    pts = [_page_text(i, i, render_needed=True) for i in range(1, big_host_count + 1)]
    return (
        AnalysisDataset(
            uri_identities=obs_uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        ),
        obs_uris,
    )


# ---------------------------------------------------------------------------
# Test C: large bad host must not exhaust the static GET budget
# ---------------------------------------------------------------------------


class TestLargeBadHostBudgetCap(unittest.TestCase):
    """1000 candidates from big-host (bad pattern) + 20 from small-host (unknown)."""

    def setUp(self) -> None:
        big_host = _host(1, "big-host.com")
        small_host = _host(2, "small-host.com")

        # 60 already-fetched URIs on big-host that create a bad pattern
        obs_uris = [_uri(i, 1, f"https://big-host.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i, total_ms=400) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]

        # 1000 new candidate URIs on big-host (same bad template pattern)
        cand_start = 1000
        big_cands = [_uri(cand_start + i, 1, f"https://big-host.com/en/products/{20000 + i}") for i in range(1000)]

        # 20 unknown candidates on small-host — product-like URLs so they score
        # positively and qualify for sample_static_html rather than defer.
        small_start = 3000
        small_cands = [
            _uri(small_start + i, 2, f"https://small-host.com/en/products/{20000 + i}")
            for i in range(20)
        ]

        self.dataset = AnalysisDataset(
            uri_identities=obs_uris + big_cands + small_cands,
            hosts=[big_host, small_host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        )

        self.budget = CrawlBudget(
            max_static_gets=50,
            max_renders=5,
            max_document_fetches=20,
            max_static_gets_per_host=20,
            max_renders_per_host=2,
            max_static_gets_per_template=20,
            hard_stop_sample_size=50,
        )

    def test_big_host_does_not_exhaust_all_slots(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        big_static = plan.host_usage.get("big-host.com", {}).get("static_gets", 0)
        total_static = plan.budget_usage.static_gets
        # big-host must not take more than its per-host cap
        self.assertLessEqual(big_static, self.budget.max_static_gets_per_host)
        # and must leave room for small-host
        small_static = plan.host_usage.get("small-host.com", {}).get("static_gets", 0)
        self.assertGreater(small_static, 0, "small-host should get at least some static GET slots")

    def test_total_static_gets_within_budget(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        self.assertLessEqual(plan.budget_usage.static_gets, self.budget.max_static_gets)


# ---------------------------------------------------------------------------
# Test D: direct TDS documents override low-yield static pattern
# ---------------------------------------------------------------------------


class TestTechDocOverridesLowYieldPattern(unittest.TestCase):

    def setUp(self) -> None:
        big_host = _host(1, "big-host.com")

        # 60 observed URIs creating a bad pattern
        obs_uris = [_uri(i, 1, f"https://big-host.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]

        # 5 TDS PDF candidates on same host
        tds_start = 500
        tds_uris = [
            _uri(tds_start + i, 1, f"https://big-host.com/tds/Product_{i}_TDS.pdf")
            for i in range(1, 6)
        ]

        self.dataset = AnalysisDataset(
            uri_identities=obs_uris + tds_uris,
            hosts=[big_host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        )

        self.budget = CrawlBudget(
            max_static_gets=10,
            max_renders=5,
            max_document_fetches=20,
            hard_stop_sample_size=50,
        )

    def test_tds_pdfs_are_selected(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        selected_uris = {c.canonical_uri for c, _ in plan.selected}
        tds_selected = [u for u in selected_uris if "_TDS.pdf" in u]
        self.assertEqual(len(tds_selected), 5, f"Expected 5 TDS PDFs selected, got: {tds_selected}")

    def test_tds_pdfs_have_fetch_document_action(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        for candidate, decision in plan.selected:
            if "_TDS.pdf" in candidate.canonical_uri:
                self.assertEqual(decision.next_action, NextAction.FETCH_DOCUMENT)

    def test_tds_pdfs_are_technical_document_role(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        for candidate, decision in plan.selected:
            if "_TDS.pdf" in candidate.canonical_uri:
                self.assertEqual(decision.url_role, URLRole.TECHNICAL_DOCUMENT)


# ---------------------------------------------------------------------------
# Test E: unknown large template is sampled, not expanded
# ---------------------------------------------------------------------------


class TestLargeUnknownTemplateCapped(unittest.TestCase):

    def setUp(self) -> None:
        host = _host(1, "example.com")
        # 500 candidate URLs all on the same unknown template.
        # Use 4-digit IDs so they all classify as numeric_id and share the
        # single medium template /{language}/products/{numeric_id}.
        uris = [_uri(i, 1, f"https://example.com/en/products/{1000 + i}") for i in range(1, 501)]

        self.dataset = AnalysisDataset(
            uri_identities=uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        self.budget = CrawlBudget(
            max_static_gets=200,
            max_renders=20,
            max_document_fetches=50,
            max_static_gets_per_template=10,
        )

    def test_at_most_cap_selected_from_template(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        # Count selected static-GET actions
        selected_static = [
            c for c, d in plan.selected
            if d.next_action in (NextAction.SAMPLE_STATIC_HTML, NextAction.INSPECT_STATIC_HTML, NextAction.API_DISCOVERY)
        ]
        self.assertLessEqual(len(selected_static), self.budget.max_static_gets_per_template)


# ---------------------------------------------------------------------------
# Test F: high-yield template candidates outrank unknown generic HTML
# ---------------------------------------------------------------------------


class TestHighYieldTemplateRanking(unittest.TestCase):

    def setUp(self) -> None:
        host = _host(1, "docs.example.com")

        # 30 already-fetched URLs on a good pattern (tech docs found)
        obs_uris = [_uri(i, 1, f"https://docs.example.com/en/products/{i}") for i in range(1, 31)]
        attempts = [_attempt(i, i) for i in range(1, 31)]
        reprs = [_repr(i, i) for i in range(1, 31)]
        pts = [_page_text(i, i, render_needed=False) for i in range(1, 31)]
        # 10 tech docs + 15 candidate docs found
        tech_docs = [_candidate_doc(i, i, mime="application/pdf") for i in range(1, 11)]
        cand_docs = [
            CandidateDocumentRow(id=100 + i, uri_identity_id=10 + i, source_uri_identity_id=1,
                                 mime_type="application/pdf", classification="material_document")
            for i in range(1, 16)
        ]

        # 10 new candidate URLs on good pattern
        good_cands = [_uri(200 + i, 1, f"https://docs.example.com/en/products/{100 + i}") for i in range(1, 11)]

        # 10 unknown-pattern candidates on same host
        unknown_cands = [_uri(300 + i, 1, f"https://docs.example.com/random/{i}") for i in range(1, 11)]

        self.dataset = AnalysisDataset(
            uri_identities=obs_uris + good_cands + unknown_cands,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=tech_docs + cand_docs,
        )
        self.budget = CrawlBudget(
            max_static_gets=10,
            max_static_gets_per_host=10,
            max_static_gets_per_template=5,
        )

    def test_good_pattern_candidates_selected(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        selected_uris = {c.canonical_uri for c, _ in plan.selected}
        # At least some good-pattern candidates must be selected
        good_selected = [u for u in selected_uris if "/en/products/1" in u]
        self.assertGreater(len(good_selected), 0)


# ---------------------------------------------------------------------------
# Test G: render budget is capped
# ---------------------------------------------------------------------------


class TestRenderBudgetCapped(unittest.TestCase):

    def setUp(self) -> None:
        host = _host(1, "spa.example.com")

        # 60 observed URIs creating a high-render pattern (render_rate ~0.75 → render_sample)
        obs_uris = [_uri(i, 1, f"https://spa.example.com/page/{i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        # 45 render_needed → 75% rate → between 0.7 and 0.95 → render_sample action
        pts = [_page_text(i, i, render_needed=(i <= 45)) for i in range(1, 61)]

        # 100 new render candidates
        cand_uris = [_uri(200 + i, 1, f"https://spa.example.com/page/{100 + i}") for i in range(1, 101)]

        self.dataset = AnalysisDataset(
            uri_identities=obs_uris + cand_uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=attempts,
            representations=reprs,
            page_texts=pts,
            extracted_links=[],
            candidate_documents=[],
        )
        self.budget = CrawlBudget(
            max_static_gets=200,
            max_renders=5,
            max_renders_per_host=2,
            max_renders_per_template=2,
        )

    def test_total_renders_within_budget(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        self.assertLessEqual(plan.budget_usage.renders, self.budget.max_renders)

    def test_renders_per_host_capped(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        host_renders = plan.host_usage.get("spa.example.com", {}).get("renders", 0)
        self.assertLessEqual(host_renders, self.budget.max_renders_per_host)


# ---------------------------------------------------------------------------
# Test H: download listing page prefers API/static inspection, not render
# ---------------------------------------------------------------------------


class TestDownloadListingPrefersInspection(unittest.TestCase):

    def test_download_url_gets_inspect_or_api_not_render(self) -> None:
        host = _host(1, "example.com")
        uri = _uri(1, 1, "https://example.com/global/en/downloads")

        dataset = AnalysisDataset(
            uri_identities=[uri],
            hosts=[host],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        budget = CrawlBudget(max_static_gets=10, max_renders=10)
        plan = plan_from_dataset(dataset, budget)

        self.assertTrue(
            len(plan.selected) > 0 or len(plan.deferred) > 0,
            "URL should be planned, not only rejected",
        )
        all_planned = plan.selected + plan.deferred
        for _, decision in all_planned:
            if decision.canonical_url.endswith("/downloads"):
                self.assertNotEqual(decision.next_action, NextAction.RENDER_SAMPLE)
                self.assertIn(
                    decision.next_action,
                    (NextAction.INSPECT_STATIC_HTML, NextAction.API_DISCOVERY, NextAction.SAMPLE_STATIC_HTML, NextAction.DEFER),
                )


# ---------------------------------------------------------------------------
# Test I: footer/legal high-inbound target is not prioritised
# ---------------------------------------------------------------------------


class TestLegalHighInboundRejected(unittest.TestCase):

    def setUp(self) -> None:
        host = _host(1, "example.com")
        # 1 regular page that links to legal/privacy
        source_uri = _uri(1, 1, "https://example.com/products/page1")
        legal_uri = _uri(2, 1, "https://example.com/legal/privacy-policy")

        # Many links pointing to privacy page (simulating footer links)
        links = [
            ExtractedLinkRow(id=i, source_uri_identity_id=i + 10, target_uri_identity_id=2,
                             anchor_text="Privacy Policy")
            for i in range(1, 21)
        ]

        self.dataset = AnalysisDataset(
            uri_identities=[source_uri, legal_uri],
            hosts=[host],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=links,
            candidate_documents=[],
        )
        self.budget = CrawlBudget(max_static_gets=50, max_document_fetches=50)

    def test_legal_url_not_high_priority(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)

        # Find decision for the legal URL
        legal_decision = None
        for candidate, decision in plan.selected + plan.deferred + plan.rejected:
            if "privacy" in candidate.canonical_uri or "legal" in candidate.canonical_uri:
                legal_decision = decision
                break

        self.assertIsNotNone(legal_decision, "Legal URL must be in the plan")
        # It must NOT be fetch_document and should have a negative-ish score or be rejected/deferred
        if legal_decision is not None:
            self.assertNotEqual(legal_decision.next_action, NextAction.FETCH_DOCUMENT)
            self.assertIn("LEGAL_NOISE", legal_decision.reason_codes)

    def test_legal_url_rejected_or_deferred(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        legal_in_rejected_or_deferred = any(
            "privacy" in c.canonical_uri or "legal" in c.canonical_uri
            for c, _ in plan.rejected + plan.deferred
        )
        self.assertTrue(legal_in_rejected_or_deferred, "Legal URL should be in rejected or deferred")


# ---------------------------------------------------------------------------
# Structural / edge-case tests
# ---------------------------------------------------------------------------


class TestPlanStructure(unittest.TestCase):

    def _minimal_dataset(self, uri: str) -> AnalysisDataset:
        return AnalysisDataset(
            uri_identities=[_uri(1, 1, uri)],
            hosts=[_host(1, "example.com")],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )

    def test_empty_dataset_returns_empty_plan(self) -> None:
        ds = AnalysisDataset(
            uri_identities=[],
            hosts=[],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        plan = plan_from_dataset(ds, CrawlBudget())
        self.assertEqual(len(plan.selected) + len(plan.deferred) + len(plan.rejected), 0)

    def test_total_budget_not_exceeded(self) -> None:
        host = _host(1, "example.com")
        uris = [_uri(i, 1, f"https://example.com/products/{i}") for i in range(1, 200)]
        ds = AnalysisDataset(
            uri_identities=uris,
            hosts=[host],
            frontier_items=[],
            fetch_attempts=[],
            representations=[],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        budget = CrawlBudget(max_static_gets=30, max_renders=5, max_document_fetches=10)
        plan = plan_from_dataset(ds, budget)
        self.assertLessEqual(plan.budget_usage.static_gets, budget.max_static_gets)
        self.assertLessEqual(plan.budget_usage.renders, budget.max_renders)
        self.assertLessEqual(plan.budget_usage.document_fetches, budget.max_document_fetches)

    def test_already_fetched_uri_not_replanned(self) -> None:
        host = _host(1, "example.com")
        uri = _uri(1, 1, "https://example.com/page")
        attempt = _attempt(1, 1, outcome="success")
        ds = AnalysisDataset(
            uri_identities=[uri],
            hosts=[host],
            frontier_items=[],
            fetch_attempts=[attempt],
            representations=[_repr(1, 1)],
            page_texts=[],
            extracted_links=[],
            candidate_documents=[],
        )
        plan = plan_from_dataset(ds, CrawlBudget())
        total = len(plan.selected) + len(plan.deferred) + len(plan.rejected)
        self.assertEqual(total, 0, "Already-fetched URIs should not appear in the plan")

    def test_asset_file_is_rejected(self) -> None:
        plan = plan_from_dataset(
            self._minimal_dataset("https://example.com/static/app.12345.js"),
            CrawlBudget(),
        )
        for candidate, decision in plan.selected:
            self.assertNotEqual(decision.url_role, URLRole.ASSET)
        asset_rejected = any(decision.url_role == URLRole.ASSET for _, decision in plan.rejected)
        self.assertTrue(asset_rejected)

    def test_tds_pdf_directly_selected(self) -> None:
        plan = plan_from_dataset(
            self._minimal_dataset("https://example.com/tds/Product_TDS.pdf"),
            CrawlBudget(),
        )
        self.assertEqual(len(plan.selected), 1)
        _, decision = plan.selected[0]
        self.assertEqual(decision.next_action, NextAction.FETCH_DOCUMENT)


if __name__ == "__main__":
    unittest.main()
