"""Realistic synthetic fixture covering multiple URL intelligence scenarios end-to-end.

Dataset summary
---------------
catalog.bigmfg.com  (SPA manufacturer — known bad static pattern)
  • 50 product pages, all render_needed=True   → static pattern stops at threshold
  • 8 new candidate product pages (same path)  → STOP_STATIC_GET, not global reject
  • 2 TDS/SDS PDF URLs (not yet fetched)       → FETCH_DOCUMENT (bypass pattern block)
  • 1 /en/downloads listing (not yet fetched)  → INSPECT_STATIC_HTML
  • 1 /legal/privacy-policy with 8 inb. links → REJECT (LEGAL_NOISE)
  • 1 /en/catalog JS-shell (fetched, rend=T)   → deferred (render_needed keeps it eligible)

new-supplier.com  (unknown host — no fetch history)
  • 4 candidate product pages                  → exploration slots
  • 1 TDS PDF (not yet fetched)               → FETCH_DOCUMENT

Row counts: 75 URIs, 51 fetch attempts, 51 representations, 51 page texts, 12 extracted links.
"""
from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.comparison import compare_actual_vs_planned
from material_ingestion.services.url_intelligence.db_export_models import (
    AnalysisDataset,
    CrawlHostRow,
    ExtractedLinkRow,
    HttpFetchAttemptRow,
    HttpRepresentationRow,
    PageTextRow,
    UriIdentityRow,
)
from material_ingestion.services.url_intelligence.models import NextAction
from material_ingestion.services.url_intelligence.planner import (
    CrawlBudget,
    plan_from_dataset,
)
from material_ingestion.services.url_intelligence.planning_report import _build_report


# ---------------------------------------------------------------------------
# Fixture constants
# ---------------------------------------------------------------------------

_HOST_BIG = "catalog.bigmfg.com"
_HOST_NEW = "new-supplier.com"
_HOST_BIG_ID = 1
_HOST_NEW_ID = 2

# URI ID ranges (non-overlapping):
_PROD_OBS = list(range(1, 51))      # 50 observed product pages (fetched, render_needed=True)
_PROD_CAND = list(range(51, 59))    # 8 new candidate product pages (not fetched)
_TDS_BIG = [61, 62]                 # 2 TDS/SDS PDFs on catalog.bigmfg.com (not fetched)
_DOWNLOADS_ID = 63                   # /en/downloads listing (not fetched)
_LEGAL_ID = 64                       # /legal/privacy-policy (not fetched)
_JSSHELL_ID = 65                     # /en/catalog JS-shell (fetched, render_needed=True)
_NEWSUP_PROD = list(range(71, 75))  # 4 product pages on new-supplier.com (not fetched)
_TDS_NEW = 75                        # TDS PDF on new-supplier.com (not fetched)

_FIXTURE_BUDGET = CrawlBudget(
    max_static_gets=60,
    max_renders=20,
    max_document_fetches=20,
    max_static_gets_per_host=30,
    max_renders_per_host=10,
    max_static_gets_per_template=15,
    min_host_exploration_slots=5,
    hard_stop_sample_size=50,
)


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------


def _build_fixture_dataset() -> AnalysisDataset:
    hosts = [
        CrawlHostRow(id=_HOST_BIG_ID, hostname=_HOST_BIG),
        CrawlHostRow(id=_HOST_NEW_ID, hostname=_HOST_NEW),
    ]

    # catalog.bigmfg.com/en/products/item-{N} — 50 observed, 8 candidates
    prod_obs_uris = [
        UriIdentityRow(
            id=i, normalized_hash=f"h{i}", host_id=_HOST_BIG_ID,
            canonical_uri=f"https://{_HOST_BIG}/en/products/item-{1000 + i}",
        )
        for i in _PROD_OBS
    ]
    prod_cand_uris = [
        UriIdentityRow(
            id=i, normalized_hash=f"h{i}", host_id=_HOST_BIG_ID,
            canonical_uri=f"https://{_HOST_BIG}/en/products/item-{5000 + i}",
        )
        for i in _PROD_CAND
    ]

    # TDS / SDS PDFs
    tds_big_uris = [
        UriIdentityRow(id=61, normalized_hash="h61", host_id=_HOST_BIG_ID,
                       canonical_uri=f"https://{_HOST_BIG}/tds/ProductA_TDS.pdf"),
        UriIdentityRow(id=62, normalized_hash="h62", host_id=_HOST_BIG_ID,
                       canonical_uri=f"https://{_HOST_BIG}/tds/ProductB_SDS.pdf"),
    ]

    # /en/downloads, /legal/privacy-policy, /en/catalog (JS-shell)
    other_big_uris = [
        UriIdentityRow(id=_DOWNLOADS_ID, normalized_hash="h63", host_id=_HOST_BIG_ID,
                       canonical_uri=f"https://{_HOST_BIG}/en/downloads"),
        UriIdentityRow(id=_LEGAL_ID, normalized_hash="h64", host_id=_HOST_BIG_ID,
                       canonical_uri=f"https://{_HOST_BIG}/legal/privacy-policy"),
        UriIdentityRow(id=_JSSHELL_ID, normalized_hash="h65", host_id=_HOST_BIG_ID,
                       canonical_uri=f"https://{_HOST_BIG}/en/catalog"),
    ]

    # new-supplier.com: 4 product pages + 1 TDS PDF
    newsup_uris = [
        UriIdentityRow(
            id=i, normalized_hash=f"h{i}", host_id=_HOST_NEW_ID,
            canonical_uri=f"https://{_HOST_NEW}/products/item-{100 + i}",
        )
        for i in _NEWSUP_PROD
    ]
    tds_new_uri = UriIdentityRow(
        id=_TDS_NEW, normalized_hash="h75", host_id=_HOST_NEW_ID,
        canonical_uri=f"https://{_HOST_NEW}/docs/MaterialA_TDS.pdf",
    )

    all_uris = prod_obs_uris + prod_cand_uris + tds_big_uris + other_big_uris + newsup_uris + [tds_new_uri]

    # Fetch attempts: 50 product pages (IDs 1-50) + JS-shell (ID 51)
    prod_attempts = [
        HttpFetchAttemptRow(
            id=i, uri_identity_id=i, crawl_run_id=1,
            outcome="success", status_code=200, total_ms=400,
        )
        for i in _PROD_OBS
    ]
    jsshell_attempt = HttpFetchAttemptRow(
        id=51, uri_identity_id=_JSSHELL_ID, crawl_run_id=1,
        outcome="success", status_code=200, total_ms=350,
    )
    all_attempts = prod_attempts + [jsshell_attempt]

    # Representations (all text/html)
    prod_reprs = [
        HttpRepresentationRow(id=i, fetch_attempt_id=i, content_type="text/html")
        for i in _PROD_OBS
    ]
    jsshell_repr = HttpRepresentationRow(id=51, fetch_attempt_id=51, content_type="text/html")
    all_reprs = prod_reprs + [jsshell_repr]

    # Page texts: all render_needed=True (bad static pattern + JS-shell)
    prod_pts = [
        PageTextRow(id=i, fetch_attempt_id=i, render_needed=True, text_ratio=0.05)
        for i in _PROD_OBS
    ]
    jsshell_pt = PageTextRow(id=51, fetch_attempt_id=51, render_needed=True, text_ratio=0.03)
    all_pts = prod_pts + [jsshell_pt]

    # Extracted links:
    #   - 8 product pages → legal URL (high inbound count, but legal is still REJECT)
    #   - 2 product pages → each TDS PDF (tech anchor text)
    legal_links = [
        ExtractedLinkRow(
            id=i, source_uri_identity_id=i, target_uri_identity_id=_LEGAL_ID,
            anchor_text="Privacy Policy",
        )
        for i in range(1, 9)
    ]
    tds_links = [
        ExtractedLinkRow(id=10, source_uri_identity_id=1, target_uri_identity_id=61, anchor_text="Technical Data Sheet"),
        ExtractedLinkRow(id=11, source_uri_identity_id=2, target_uri_identity_id=61, anchor_text="TDS Download"),
        ExtractedLinkRow(id=12, source_uri_identity_id=3, target_uri_identity_id=62, anchor_text="Safety Data Sheet"),
        ExtractedLinkRow(id=13, source_uri_identity_id=4, target_uri_identity_id=62, anchor_text="SDS"),
    ]
    all_links = legal_links + tds_links

    return AnalysisDataset(
        uri_identities=all_uris,
        hosts=hosts,
        frontier_items=[],
        fetch_attempts=all_attempts,
        representations=all_reprs,
        page_texts=all_pts,
        extracted_links=all_links,
        candidate_documents=[],
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestRealisticFixture(unittest.TestCase):
    """End-to-end scenario tests on a small but realistic synthetic dataset."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = _build_fixture_dataset()
        cls.plan = plan_from_dataset(cls.dataset, _FIXTURE_BUDGET)

    def _selected_ids(self) -> set[int]:
        return {c.uri_identity_id for c, _ in self.plan.selected}

    def _deferred_ids(self) -> set[int]:
        return {c.uri_identity_id for c, _ in self.plan.deferred}

    def _stopped_ids(self) -> set[int]:
        return {c.uri_identity_id for c, _ in self.plan.stopped_static_get}

    def _rejected_ids(self) -> set[int]:
        return {c.uri_identity_id for c, _ in self.plan.rejected}

    # -----------------------------------------------------------------------
    # 1. Bad static pattern: product candidates stopped, not globally rejected
    # -----------------------------------------------------------------------

    def test_product_candidates_in_stopped_not_rejected(self) -> None:
        for uid in _PROD_CAND:
            self.assertIn(uid, self._stopped_ids(),
                          f"URI {uid} (product candidate) should be in stopped_static_get")
            self.assertNotIn(uid, self._rejected_ids(),
                             f"URI {uid} (product candidate) must NOT be in rejected")

    def test_stopped_items_do_not_consume_static_get_budget(self) -> None:
        # Only downloads listing (1) and new-supplier pages (up to 4) consume static GETs.
        # The 8 stopped product candidates must NOT be counted.
        self.assertLessEqual(
            self.plan.budget_usage.static_gets, 20,
            f"Stopped items should not consume budget; got {self.plan.budget_usage.static_gets}",
        )

    def test_stopped_list_contains_only_stop_static_get_actions(self) -> None:
        for _, decision in self.plan.stopped_static_get:
            self.assertEqual(decision.next_action, NextAction.STOP_STATIC_GET)

    # -----------------------------------------------------------------------
    # 2. Technical PDFs bypass pattern block and are selected
    # -----------------------------------------------------------------------

    def test_tds_pdfs_on_bad_host_are_selected(self) -> None:
        for uid in _TDS_BIG:
            self.assertIn(uid, self._selected_ids(),
                          f"PDF URI {uid} should be selected despite bad static pattern on host")

    def test_tds_pdfs_have_fetch_document_action(self) -> None:
        for candidate, decision in self.plan.selected:
            if candidate.uri_identity_id in _TDS_BIG:
                self.assertEqual(
                    decision.next_action, NextAction.FETCH_DOCUMENT,
                    f"URI {candidate.uri_identity_id}: expected FETCH_DOCUMENT, got {decision.next_action}",
                )

    def test_tds_pdf_on_new_supplier_is_selected(self) -> None:
        self.assertIn(_TDS_NEW, self._selected_ids(),
                      "TDS PDF on new-supplier.com should be selected")

    def test_tds_pdf_on_new_supplier_fetch_document_action(self) -> None:
        for candidate, decision in self.plan.selected:
            if candidate.uri_identity_id == _TDS_NEW:
                self.assertEqual(decision.next_action, NextAction.FETCH_DOCUMENT)
                return
        self.fail(f"URI {_TDS_NEW} not found in selected")

    # -----------------------------------------------------------------------
    # 3. Downloads listing is inspected (document_listing role)
    # -----------------------------------------------------------------------

    def test_downloads_listing_is_in_plan(self) -> None:
        in_plan = self._selected_ids() | self._deferred_ids()
        self.assertIn(_DOWNLOADS_ID, in_plan, "/en/downloads should appear in plan")

    def test_downloads_listing_action_is_inspect_static_html(self) -> None:
        for candidate, decision in self.plan.selected + self.plan.deferred:
            if candidate.uri_identity_id == _DOWNLOADS_ID:
                self.assertEqual(
                    decision.next_action, NextAction.INSPECT_STATIC_HTML,
                    f"/en/downloads should get INSPECT_STATIC_HTML, got {decision.next_action}",
                )
                return
        self.fail(f"URI {_DOWNLOADS_ID} (/en/downloads) not found in selected or deferred")

    # -----------------------------------------------------------------------
    # 4. Legal URL is globally rejected even with high inbound link count
    # -----------------------------------------------------------------------

    def test_legal_url_is_globally_rejected(self) -> None:
        self.assertIn(_LEGAL_ID, self._rejected_ids(),
                      "legal/privacy-policy (with 8 inbound links) should be in rejected")
        self.assertNotIn(_LEGAL_ID, self._selected_ids(),
                         "legal/privacy-policy must NOT be selected")

    def test_legal_url_has_legal_noise_reason(self) -> None:
        for candidate, decision in self.plan.rejected:
            if candidate.uri_identity_id == _LEGAL_ID:
                self.assertIn("LEGAL_NOISE", decision.reason_codes,
                              "LEGAL_NOISE reason code expected for privacy-policy URL")
                return
        self.fail(f"URI {_LEGAL_ID} not found in rejected list")

    # -----------------------------------------------------------------------
    # 5. JS-shell (fetched with render_needed=True) remains eligible
    # -----------------------------------------------------------------------

    def test_jsshell_remains_in_plan(self) -> None:
        in_plan = self._selected_ids() | self._deferred_ids() | self._stopped_ids()
        self.assertIn(_JSSHELL_ID, in_plan,
                      "/en/catalog (fetched with render_needed=True) should remain in plan")

    def test_jsshell_not_globally_rejected(self) -> None:
        self.assertNotIn(_JSSHELL_ID, self._rejected_ids(),
                         "/en/catalog JS-shell should not be globally rejected")

    # -----------------------------------------------------------------------
    # 6. New-supplier.com gets exploration slots (no history → selected)
    # -----------------------------------------------------------------------

    def test_new_supplier_product_pages_appear_in_plan(self) -> None:
        in_plan = (self._selected_ids() | self._deferred_ids()) & set(_NEWSUP_PROD)
        self.assertGreater(len(in_plan), 0, "new-supplier.com product pages should appear in plan")

    def test_new_supplier_at_least_one_page_selected(self) -> None:
        selected = self._selected_ids() & set(_NEWSUP_PROD)
        self.assertGreater(len(selected), 0,
                           "At least 1 new-supplier.com page should be selected for exploration")

    # -----------------------------------------------------------------------
    # 7. Report summarises stopped vs globally rejected correctly
    # -----------------------------------------------------------------------

    def test_report_stopped_count_positive(self) -> None:
        report = _build_report(self.plan, crawl_run_id=1, crawl_run_key="fixture", budget=_FIXTURE_BUDGET)
        self.assertGreater(report.to_summary_dict()["stopped_static_get_count"], 0)

    def test_report_globally_rejected_count_positive(self) -> None:
        report = _build_report(self.plan, crawl_run_id=1, crawl_run_key="fixture", budget=_FIXTURE_BUDGET)
        self.assertGreater(report.to_summary_dict()["globally_rejected_count"], 0)

    def test_report_top_document_fetches_includes_all_pdfs(self) -> None:
        report = _build_report(self.plan, crawl_run_id=1, crawl_run_key="fixture", budget=_FIXTURE_BUDGET)
        pdf_ids = {item["uri_identity_id"] for item in report.top_document_fetches}
        for uid in _TDS_BIG + [_TDS_NEW]:
            self.assertIn(uid, pdf_ids, f"PDF URI {uid} should appear in top_document_fetches")

    def test_report_stopped_summary_items_have_correct_action(self) -> None:
        report = _build_report(self.plan, crawl_run_id=1, crawl_run_key="fixture", budget=_FIXTURE_BUDGET)
        for item in report.stopped_static_get_summary:
            self.assertEqual(item["next_action"], NextAction.STOP_STATIC_GET.value)

    def test_report_rejected_summary_has_no_stop_static_get(self) -> None:
        report = _build_report(self.plan, crawl_run_id=1, crawl_run_key="fixture", budget=_FIXTURE_BUDGET)
        for item in report.rejected_summary:
            self.assertNotEqual(item["next_action"], NextAction.STOP_STATIC_GET.value)

    # -----------------------------------------------------------------------
    # 8. Actual-vs-planned comparison
    # -----------------------------------------------------------------------

    def test_comparison_detects_reduction_on_big_host(self) -> None:
        """51 actual static GETs (50 products + 1 JS-shell) vs few planned → reduction."""
        comparison = compare_actual_vs_planned(self.dataset, self.plan)
        actual = comparison.actual_static_gets_by_host.get(_HOST_BIG, 0)
        planned = comparison.planned_static_gets_by_host.get(_HOST_BIG, 0)
        self.assertGreater(
            actual, planned,
            f"Expected reduction on {_HOST_BIG}: actual={actual}, planned={planned}",
        )

    def test_comparison_planned_docs_not_fetched_includes_pdfs(self) -> None:
        comparison = compare_actual_vs_planned(self.dataset, self.plan)
        not_fetched_uris = {d["canonical_uri"] for d in comparison.planned_docs_not_fetched}
        has_pdf = any(
            "_TDS.pdf" in u or "_SDS.pdf" in u or "_TDS.pdf" in u
            for u in not_fetched_uris
        )
        self.assertTrue(has_pdf, f"PDF URLs should be in planned_docs_not_fetched: {not_fetched_uris}")

    def test_comparison_promoted_technical_documents_includes_pdfs(self) -> None:
        comparison = compare_actual_vs_planned(self.dataset, self.plan)
        promoted = {d["uri_identity_id"] for d in comparison.promoted_technical_documents}
        for uid in _TDS_BIG + [_TDS_NEW]:
            self.assertIn(uid, promoted, f"PDF URI {uid} should be promoted")

    def test_comparison_reduction_summary_has_required_keys(self) -> None:
        comparison = compare_actual_vs_planned(self.dataset, self.plan)
        summary = comparison.reduction_summary()
        for key in ("hosts_to_reduce", "templates_to_reduce", "docs_not_yet_fetched"):
            self.assertIn(key, summary)


if __name__ == "__main__":
    unittest.main()
