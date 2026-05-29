"""Compact end-to-end sanity check for URL intelligence scoring + planner behaviour.

Covers:
- Document scoring cap lives in score_url, not only in reporting.
- Document dedup lives in _allocate, not only in top_document_fetches.
- Soft noise demotes contact/fairs/archive pages below SAMPLE threshold.
- Legal/footer PDFs are rejected.
- Renders remain zero for generic pages without pattern-data evidence.
- stopped_static_get is separate from global rejection.
"""
from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.decision import decide
from material_ingestion.services.url_intelligence.models import NextAction, URLRole
from material_ingestion.services.url_intelligence.planner import (
    CrawlBudget,
    CrawlPlan,
    PlanCandidate,
    _allocate,
)
from material_ingestion.services.url_intelligence.scoring import score_url
from material_ingestion.services.url_intelligence.uri_parser import parse_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plan(urls: list[str], budget: CrawlBudget | None = None) -> CrawlPlan:
    """Run decide() for each URL then _allocate() — mirrors plan_from_dataset ranking."""
    if budget is None:
        budget = CrawlBudget(max_document_fetches=20, max_static_gets=50, max_renders=5)

    scored = []
    for i, url in enumerate(urls):
        decision = decide(url)
        host = url.split("//")[1].split("/")[0] if "//" in url else "unknown"
        candidate = PlanCandidate(
            uri_identity_id=i + 1,
            canonical_uri=url,
            source_type="frontier",
            host=host,
            inferred_templates=[],
        )
        scored.append((candidate, decision))

    scored.sort(key=lambda x: (
        -1 if x[1].url_role == URLRole.TECHNICAL_DOCUMENT else 0,
        -x[1].scores.final_score,
    ))
    return _allocate(scored, budget, {})


# ---------------------------------------------------------------------------
# 1. Document scoring cap verified inside score_url
# ---------------------------------------------------------------------------

class TestDocumentScoringCapInScoreUrl(unittest.TestCase):
    """Confirm cap is applied before any reporting layer."""

    _DAM_BASE = "https://www.basf.com/global/documents/en/products/polymers"

    def test_generic_pdf_url_score_capped_at_45(self) -> None:
        score, reasons = score_url(parse_url(f"{self._DAM_BASE}/polymer-A-overview.pdf"))
        self.assertLessEqual(score, 45)
        self.assertIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_tds_pdf_url_score_uncapped(self) -> None:
        score, reasons = score_url(parse_url(f"{self._DAM_BASE}/polymer-A-TDS.pdf"))
        self.assertGreaterEqual(score, 100)
        self.assertNotIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_tds_outranks_generic_pdf_url_score(self) -> None:
        tds, _ = score_url(parse_url(f"{self._DAM_BASE}/polymer-A-TDS.pdf"))
        gen, _ = score_url(parse_url(f"{self._DAM_BASE}/polymer-A-overview.pdf"))
        self.assertGreater(tds - gen, 50)

    def test_brochure_pdf_capped_at_30(self) -> None:
        score, reasons = score_url(parse_url(f"{self._DAM_BASE}/polymer-A-brochure.pdf"))
        self.assertLessEqual(score, 30)
        self.assertIn("BROCHURE_FILENAME", reasons)
        self.assertIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_generic_pdf_needs_source_context_to_fetch(self) -> None:
        # url_score capped at 45 < 50 threshold → DEFER without extra source score
        result = decide(f"{self._DAM_BASE}/polymer-A-overview.pdf")
        self.assertEqual(result.next_action, NextAction.DEFER)

    def test_tds_always_fetched_regardless_of_cap(self) -> None:
        result = decide(f"{self._DAM_BASE}/polymer-A-TDS.pdf")
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)
        self.assertEqual(result.url_role, URLRole.TECHNICAL_DOCUMENT)


# ---------------------------------------------------------------------------
# 2. Document dedup happens in _allocate before budget consumption
# ---------------------------------------------------------------------------

class TestDocumentDedupInAllocate(unittest.TestCase):

    def _ranked_pair(self, uid: int, url: str) -> tuple:
        decision = decide(url)
        candidate = PlanCandidate(
            uri_identity_id=uid,
            canonical_uri=url,
            source_type="frontier",
            host="example.com",
            inferred_templates=[],
        )
        return candidate, decision

    def test_tds_and_vid_variant_one_budget_slot(self) -> None:
        base = "https://example.com/tds/Product_A_TDS.pdf"
        vid = "https://example.com/tds/Product_A_TDS.pdf?vid=abc123"
        ranked = [self._ranked_pair(1, base), self._ranked_pair(2, vid)]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 1)
        self.assertEqual(len(plan.selected), 1)

    def test_vid_variant_goes_to_deferred_not_dropped(self) -> None:
        base = "https://example.com/tds/Product_A_TDS.pdf"
        vid = "https://example.com/tds/Product_A_TDS.pdf?vid=abc123"
        ranked = [self._ranked_pair(1, base), self._ranked_pair(2, vid)]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        deferred_urls = [c.canonical_uri for c, _ in plan.deferred]
        self.assertIn(vid, deferred_urls)

    def test_distinct_docs_not_merged(self) -> None:
        url_a = "https://example.com/tds/TDS_A.pdf"
        url_b = "https://example.com/tds/TDS_B.pdf"
        ranked = [self._ranked_pair(1, url_a), self._ranked_pair(2, url_b)]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 2)

    def test_selected_summary_no_duplicate_docs(self) -> None:
        base = "https://example.com/docs/Safety_Data_Sheet.pdf"
        utm = f"{base}?utm_source=email&utm_campaign=q1"
        ranked = [self._ranked_pair(1, base), self._ranked_pair(2, utm)]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        fetch_selected = [
            c.canonical_uri for c, d in plan.selected
            if d.next_action == NextAction.FETCH_DOCUMENT
        ]
        # Both map to same stripped URL — only one selected
        self.assertEqual(len(fetch_selected), 1)


# ---------------------------------------------------------------------------
# 3. Soft noise demotes low-value static pages
# ---------------------------------------------------------------------------

class TestSoftNoiseDemotion(unittest.TestCase):

    def test_contact_page_gets_soft_noise(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/contact"))
        self.assertIn("SOFT_NOISE", reasons)
        self.assertLess(score, 0)

    def test_thank_you_page_gets_soft_noise(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/thank-you"))
        self.assertIn("SOFT_NOISE", reasons)

    def test_fairs_page_gets_soft_noise(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/fairs"))
        self.assertIn("SOFT_NOISE", reasons)

    def test_archive_page_gets_soft_noise(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/en/archive"))
        self.assertIn("SOFT_NOISE", reasons)

    def test_history_page_gets_soft_noise(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/our-history"))
        self.assertIn("SOFT_NOISE", reasons)

    def test_contact_page_deferred_not_sampled(self) -> None:
        result = decide("https://example.com/contact")
        # Soft noise brings score below SAMPLE threshold (25); should not be SAMPLE or REJECT
        self.assertEqual(result.next_action, NextAction.DEFER)

    def test_fairs_page_deferred_not_rejected(self) -> None:
        result = decide("https://example.com/fairs")
        self.assertNotEqual(result.next_action, NextAction.REJECT)
        self.assertEqual(result.next_action, NextAction.DEFER)

    def test_contact_with_download_path_still_crawlable(self) -> None:
        # A URL like /downloads/contact-form still has enough DOWNLOAD_PATH bonus
        # to exceed the SAMPLE threshold even with soft noise.
        # DOWNLOAD(60) - SOFT_NOISE(20) = 40 → still >= 25 → SAMPLE or INSPECT
        score, reasons = score_url(parse_url("https://example.com/downloads/contact"))
        self.assertGreaterEqual(score, 25)

    def test_normal_product_page_no_soft_noise(self) -> None:
        _, reasons = score_url(parse_url("https://example.com/products/polymer-a"))
        self.assertNotIn("SOFT_NOISE", reasons)


# ---------------------------------------------------------------------------
# 4 + 5. Combined plan sanity check
# ---------------------------------------------------------------------------

class TestPlanSanityCheck(unittest.TestCase):
    """Full scenario: mixed URLs through decide() + _allocate()."""

    @classmethod
    def setUpClass(cls) -> None:
        urls = [
            # Technical docs — must be selected
            "https://example.com/tds/Product_A_TDS.pdf",
            "https://example.com/sds/Safety_Data_Sheet_B.pdf",
            # Duplicate TDS — must not double-count budget
            "https://example.com/tds/Product_A_TDS.pdf?vid=abc123",
            # Generic PDF under deep BASF DAM path — capped, needs source context
            "https://www.basf.com/global/documents/en/products/polymers/polymer-A-overview.pdf",
            # Legal PDFs — must be rejected
            "https://example.com/downloads/General_Conditions.pdf",
            "https://example.com/docs/Terms_of_Sale.pdf",
            # Soft noise pages — must be deferred, not selected
            "https://example.com/contact",
            "https://example.com/fairs",
            "https://example.com/en/archive",
            # Download listing — should be selected (INSPECT_STATIC_HTML)
            "https://example.com/downloads/",
            # Normal product page — low priority, may defer
            "https://example.com/products/polymer-a",
        ]
        cls.plan = _plan(urls)
        cls.selected_urls = [c.canonical_uri for c, _ in cls.plan.selected]
        cls.rejected_urls = [c.canonical_uri for c, _ in cls.plan.rejected]
        cls.deferred_urls = [c.canonical_uri for c, _ in cls.plan.deferred]
        cls.selected_actions = [d.next_action for _, d in cls.plan.selected]
        cls.selected_roles = [d.url_role for _, d in cls.plan.selected]

    def test_tech_docs_selected(self) -> None:
        self.assertIn("https://example.com/tds/Product_A_TDS.pdf", self.selected_urls)
        self.assertIn("https://example.com/sds/Safety_Data_Sheet_B.pdf", self.selected_urls)

    def test_duplicate_tds_does_not_double_consume_budget(self) -> None:
        tds_in_selected = sum(
            1 for u in self.selected_urls if "Product_A_TDS.pdf" in u
        )
        self.assertEqual(tds_in_selected, 1)

    def test_document_budget_matches_selected_count(self) -> None:
        fetch_count = sum(
            1 for _, d in self.plan.selected
            if d.next_action == NextAction.FETCH_DOCUMENT
        )
        self.assertEqual(self.plan.budget_usage.document_fetches, fetch_count)

    def test_legal_pdfs_rejected(self) -> None:
        self.assertTrue(any("General_Conditions" in u for u in self.rejected_urls))
        self.assertTrue(any("Terms_of_Sale" in u for u in self.rejected_urls))

    def test_contact_and_fairs_not_selected(self) -> None:
        self.assertFalse(any("/contact" in u for u in self.selected_urls))
        self.assertFalse(any("/fairs" in u for u in self.selected_urls))

    def test_contact_and_fairs_deferred_not_rejected(self) -> None:
        self.assertTrue(any("/contact" in u for u in self.deferred_urls))
        self.assertTrue(any("/fairs" in u for u in self.deferred_urls))
        self.assertFalse(any("/contact" in u for u in self.rejected_urls))
        self.assertFalse(any("/fairs" in u for u in self.rejected_urls))

    def test_generic_pdf_not_selected_without_source_context(self) -> None:
        self.assertFalse(any("polymer-A-overview" in u for u in self.selected_urls))

    def test_renders_zero_for_generic_pages(self) -> None:
        self.assertEqual(self.plan.budget_usage.renders, 0)

    def test_stopped_static_get_empty_without_pattern_data(self) -> None:
        self.assertEqual(len(self.plan.stopped_static_get), 0)

    def test_tech_docs_outrank_generic_pages_in_selection(self) -> None:
        # All FETCH_DOCUMENT actions in selected should be technical docs
        fetch_roles = [
            d.url_role for _, d in self.plan.selected
            if d.next_action == NextAction.FETCH_DOCUMENT
        ]
        self.assertTrue(all(r == URLRole.TECHNICAL_DOCUMENT for r in fetch_roles))


if __name__ == "__main__":
    unittest.main()
