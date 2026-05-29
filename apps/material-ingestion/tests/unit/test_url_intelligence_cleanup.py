"""Tests covering the cleanup/fix pass:

1. STOP_STATIC_GET lands in stopped_static_get, not rejected.
2. REJECT is reserved for globally bad URLs (NOISE / ASSET / score < -20).
3. render_needed=True after static GET keeps URL eligible for render/API planning.
4. Non-success fetch outcomes (HEAD fail, timeout, error) remain in candidates.
5. Pattern stats are fetch-method-scoped: bad static_get stats don't block
   FETCH_DOCUMENT or render/API paths.
6. High-inbound legal/footer links are not promoted over technical documents.
7. compare_actual_vs_planned returns correct structure and reduction data.
8. CrawlPlanningReport carries stopped_static_get_summary separately.
"""
from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.comparison import (
    CrawlPlanComparison,
    compare_actual_vs_planned,
)
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
    CrawlPlan,
    plan_from_dataset,
)
from material_ingestion.services.url_intelligence.planning_report import (
    CrawlPlanningReport,
    _build_report,
)


# ---------------------------------------------------------------------------
# Shared fixture helpers (mirrors test_url_intelligence_planner.py style)
# ---------------------------------------------------------------------------

def _host(id: int, hostname: str) -> CrawlHostRow:
    return CrawlHostRow(id=id, hostname=hostname)


def _uri(id: int, host_id: int, uri: str) -> UriIdentityRow:
    return UriIdentityRow(id=id, canonical_uri=uri, normalized_hash=f"h{id}", host_id=host_id)


def _attempt(
    id: int,
    uri_id: int,
    *,
    outcome: str = "success",
    total_ms: int = 300,
    content_type: str = "",
) -> HttpFetchAttemptRow:
    return HttpFetchAttemptRow(
        id=id, uri_identity_id=uri_id, crawl_run_id=1,
        outcome=outcome, status_code=200, total_ms=total_ms,
    )


def _repr(id: int, attempt_id: int, *, content_type: str = "text/html") -> HttpRepresentationRow:
    return HttpRepresentationRow(id=id, fetch_attempt_id=attempt_id, content_type=content_type)


def _page_text(id: int, attempt_id: int, *, render_needed: bool) -> PageTextRow:
    return PageTextRow(id=id, fetch_attempt_id=attempt_id, render_needed=render_needed, text_ratio=0.2)


def _empty_ds() -> AnalysisDataset:
    return AnalysisDataset(
        uri_identities=[], hosts=[], frontier_items=[],
        fetch_attempts=[], representations=[], page_texts=[],
        extracted_links=[], candidate_documents=[],
    )


def _default_budget(**overrides) -> CrawlBudget:
    defaults = dict(
        max_static_gets=50, max_renders=10, max_document_fetches=20,
        max_static_gets_per_host=20, max_renders_per_host=5,
        max_static_gets_per_template=10, hard_stop_sample_size=50,
    )
    defaults.update(overrides)
    return CrawlBudget(**defaults)


def _bad_pattern_dataset(
    host_id: int = 1,
    hostname: str = "big.example.com",
    n_observed: int = 60,
    render_needed: bool = True,
    template_prefix: str = "https://big.example.com/en/products/",
) -> AnalysisDataset:
    """Dataset with n_observed already-fetched URIs producing a bad static pattern."""
    host = _host(host_id, hostname)
    obs_uris = [_uri(i, host_id, f"{template_prefix}{10000 + i}") for i in range(1, n_observed + 1)]
    attempts = [_attempt(i, i, total_ms=400) for i in range(1, n_observed + 1)]
    reprs = [_repr(i, i) for i in range(1, n_observed + 1)]
    pts = [_page_text(i, i, render_needed=render_needed) for i in range(1, n_observed + 1)]
    return AnalysisDataset(
        uri_identities=obs_uris, hosts=[host], frontier_items=[],
        fetch_attempts=attempts, representations=reprs, page_texts=pts,
        extracted_links=[], candidate_documents=[],
    )


# ---------------------------------------------------------------------------
# 1. STOP_STATIC_GET lands in stopped_static_get, not rejected
# ---------------------------------------------------------------------------


class TestStopStaticGetIsSeparateFromReject(unittest.TestCase):

    def setUp(self) -> None:
        # 60 already-fetched with render_needed=True → bad static pattern.
        # 20 new candidates on same template → should get STOP_STATIC_GET.
        host = _host(1, "spa.example.com")
        obs_uris = [_uri(i, 1, f"https://spa.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i, total_ms=400) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        cands = [_uri(1000 + i, 1, f"https://spa.example.com/en/products/{20000 + i}") for i in range(20)]

        self.dataset = AnalysisDataset(
            uri_identities=obs_uris + cands, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        self.budget = _default_budget(hard_stop_sample_size=50)

    def test_stop_static_get_not_in_rejected(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        for _, decision in plan.rejected:
            self.assertNotEqual(
                decision.next_action, NextAction.STOP_STATIC_GET,
                "STOP_STATIC_GET must not appear in plan.rejected",
            )

    def test_stop_static_get_in_dedicated_list(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        stop_actions = [d.next_action for _, d in plan.stopped_static_get]
        self.assertTrue(
            all(a == NextAction.STOP_STATIC_GET for a in stop_actions),
            "plan.stopped_static_get must contain only STOP_STATIC_GET decisions",
        )

    def test_stopped_static_get_is_non_empty(self) -> None:
        plan = plan_from_dataset(self.dataset, self.budget)
        self.assertGreater(
            len(plan.stopped_static_get), 0,
            "Expected some candidates to be stopped for static GET",
        )

    def test_reject_only_contains_globally_bad_urls(self) -> None:
        """rejected list must only hold REJECT-action items."""
        plan = plan_from_dataset(self.dataset, self.budget)
        for _, decision in plan.rejected:
            self.assertEqual(
                decision.next_action, NextAction.REJECT,
                f"plan.rejected contains non-REJECT action: {decision.next_action}",
            )


# ---------------------------------------------------------------------------
# 2. REJECT is reserved for noise/asset/globally-bad
# ---------------------------------------------------------------------------


class TestRejectOnlyGloballyBad(unittest.TestCase):

    def _plan_for(self, uri: str) -> CrawlPlan:
        host = _host(1, "example.com")
        u = _uri(1, 1, uri)
        ds = AnalysisDataset(
            uri_identities=[u], hosts=[host], frontier_items=[],
            fetch_attempts=[], representations=[], page_texts=[],
            extracted_links=[], candidate_documents=[],
        )
        return plan_from_dataset(ds, _default_budget())

    def test_legal_url_is_globally_rejected(self) -> None:
        plan = self._plan_for("https://example.com/legal/privacy-policy")
        actions = {d.next_action for _, d in plan.rejected}
        self.assertIn(NextAction.REJECT, actions)
        self.assertNotIn(
            NextAction.STOP_STATIC_GET,
            {d.next_action for _, d in plan.rejected},
        )

    def test_asset_url_is_globally_rejected(self) -> None:
        plan = self._plan_for("https://example.com/static/bundle.min.js")
        asset_rejected = any(d.url_role == URLRole.ASSET for _, d in plan.rejected)
        self.assertTrue(asset_rejected)

    def test_career_url_is_globally_rejected(self) -> None:
        plan = self._plan_for("https://example.com/careers/software-engineer")
        actions_in_rejected = {d.next_action for _, d in plan.rejected}
        self.assertIn(NextAction.REJECT, actions_in_rejected)

    def test_bad_pattern_url_not_globally_rejected(self) -> None:
        """A URL with a bad static pattern must NOT end up in plan.rejected."""
        host = _host(1, "spa.example.com")
        # Use 5-digit IDs so all segments are NUMERIC_ID and share one medium template.
        obs = [_uri(i, 1, f"https://spa.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        cand = _uri(999, 1, "https://spa.example.com/en/products/99999")
        ds = AnalysisDataset(
            uri_identities=obs + [cand], hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        in_rejected = any(c.uri_identity_id == 999 for c, _ in plan.rejected)
        self.assertFalse(
            in_rejected,
            "Product URL with bad static pattern should be in stopped_static_get, not rejected",
        )
        in_stopped = any(c.uri_identity_id == 999 for c, _ in plan.stopped_static_get)
        self.assertTrue(in_stopped, "Product URL with bad static pattern should be in stopped_static_get")


# ---------------------------------------------------------------------------
# 3. render_needed=True after static GET keeps URL eligible for render/API
# ---------------------------------------------------------------------------


class TestRenderNeededAfterStaticGetRemainsEligible(unittest.TestCase):

    def test_render_needed_url_stays_in_plan(self) -> None:
        """A URL fetched successfully with render_needed=True must not be skipped."""
        host = _host(1, "spa.example.com")
        # 60 already-fetched obs to establish a render pattern (rate ~0.75 → render_sample)
        obs = [_uri(i, 1, f"https://spa.example.com/page/{i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        # 45/60 = 0.75 render rate → render_sample, not stop_static_get
        pts = [_page_text(i, i, render_needed=(i <= 45)) for i in range(1, 61)]

        ds = AnalysisDataset(
            uri_identities=obs, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())

        # URIs with render_needed=True (IDs 1-45) should appear in plan
        # (selected for render_sample, or deferred if budget exceeded)
        render_uri_ids = set(range(1, 46))
        planned_ids = {
            c.uri_identity_id
            for c, _ in plan.selected + plan.deferred + plan.stopped_static_get
        }
        overlap = render_uri_ids & planned_ids
        self.assertGreater(
            len(overlap), 0,
            "At least some render_needed=True URIs should remain in the plan",
        )

    def test_render_needed_leads_to_render_or_api_action(self) -> None:
        """URIs with render_needed=True should get RENDER_SAMPLE or API_DISCOVERY."""
        host = _host(1, "spa.example.com")
        # Use a language prefix + 4-digit IDs so specific and medium templates differ
        # (LANGUAGE only replaced at medium level), giving all 60 URIs the same medium
        # template key and allowing pattern stats to accumulate to the 50-sample threshold.
        obs = [_uri(i, 1, f"https://spa.example.com/en/page/{1000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=(i <= 45)) for i in range(1, 61)]
        ds = AnalysisDataset(
            uri_identities=obs, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())

        render_actions = {NextAction.RENDER_SAMPLE, NextAction.API_DISCOVERY}
        selected_actions = {d.next_action for _, d in plan.selected}
        self.assertTrue(
            selected_actions & render_actions,
            f"Expected render/API action in selected, got: {selected_actions}",
        )

    def test_render_needed_false_url_is_skipped(self) -> None:
        """A URL with outcome=success and render_needed=False must not be re-planned."""
        host = _host(1, "example.com")
        uri = _uri(1, 1, "https://example.com/page")
        attempt = _attempt(1, 1, outcome="success")
        ds = AnalysisDataset(
            uri_identities=[uri], hosts=[host], frontier_items=[],
            fetch_attempts=[attempt],
            representations=[_repr(1, 1)],
            page_texts=[_page_text(1, 1, render_needed=False)],
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        total = (
            len(plan.selected) + len(plan.deferred)
            + len(plan.rejected) + len(plan.stopped_static_get)
        )
        self.assertEqual(total, 0, "render_needed=False URL should not be re-planned")


# ---------------------------------------------------------------------------
# 4. Non-success fetch outcomes remain in candidates
# ---------------------------------------------------------------------------


class TestNonSuccessOutcomesRemainEligible(unittest.TestCase):

    def _plan_for_outcome(self, outcome: str, uri: str = "https://example.com/products/42") -> CrawlPlan:
        host = _host(1, "example.com")
        u = _uri(1, 1, uri)
        attempt = _attempt(1, 1, outcome=outcome)
        ds = AnalysisDataset(
            uri_identities=[u], hosts=[host], frontier_items=[],
            fetch_attempts=[attempt],
            representations=[_repr(1, 1)],
            page_texts=[],
            extracted_links=[], candidate_documents=[],
        )
        return plan_from_dataset(ds, _default_budget())

    def test_error_outcome_remains_eligible(self) -> None:
        plan = self._plan_for_outcome("error")
        total = len(plan.selected) + len(plan.deferred) + len(plan.stopped_static_get)
        self.assertGreater(total, 0, "outcome=error URI should still appear in plan")

    def test_timeout_outcome_remains_eligible(self) -> None:
        plan = self._plan_for_outcome("timeout")
        total = len(plan.selected) + len(plan.deferred) + len(plan.stopped_static_get)
        self.assertGreater(total, 0, "outcome=timeout URI should still appear in plan")

    def test_head_fail_outcome_remains_eligible(self) -> None:
        plan = self._plan_for_outcome("head_fail")
        total = len(plan.selected) + len(plan.deferred) + len(plan.stopped_static_get)
        self.assertGreater(total, 0, "outcome=head_fail URI should still appear in plan")

    def test_never_fetched_uri_is_in_plan(self) -> None:
        """A URI with no fetch attempt at all should appear in the plan."""
        host = _host(1, "example.com")
        u = _uri(1, 1, "https://example.com/products/new")
        ds = AnalysisDataset(
            uri_identities=[u], hosts=[host], frontier_items=[],
            fetch_attempts=[], representations=[], page_texts=[],
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        total = len(plan.selected) + len(plan.deferred) + len(plan.stopped_static_get)
        self.assertGreater(total, 0)

    def test_success_outcome_no_page_text_is_skipped(self) -> None:
        """outcome=success with no page_text row should be treated as fully done."""
        plan = self._plan_for_outcome("success")
        total = (
            len(plan.selected) + len(plan.deferred)
            + len(plan.rejected) + len(plan.stopped_static_get)
        )
        self.assertEqual(total, 0, "outcome=success (no page_text) should be skipped")


# ---------------------------------------------------------------------------
# 5. Pattern stats are fetch-method-scoped
# ---------------------------------------------------------------------------


class TestPatternStatsFetchMethodScoping(unittest.TestCase):

    def test_bad_static_get_pattern_does_not_block_fetch_document(self) -> None:
        """TDS PDFs on the same host/template as a bad static pattern are still selected."""
        host = _host(1, "mfg.example.com")
        # 60 observed pages with bad static pattern
        obs = [_uri(i, 1, f"https://mfg.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i, total_ms=400) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        # 3 TDS PDFs on the same host
        tds = [_uri(500 + i, 1, f"https://mfg.example.com/tds/Product_{i}_TDS.pdf") for i in range(1, 4)]

        ds = AnalysisDataset(
            uri_identities=obs + tds, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        budget = _default_budget(max_document_fetches=10, hard_stop_sample_size=50)
        plan = plan_from_dataset(ds, budget)

        selected_uris = {c.canonical_uri for c, _ in plan.selected}
        tds_selected = [u for u in selected_uris if "_TDS.pdf" in u]
        self.assertEqual(len(tds_selected), 3, f"Expected all 3 TDS PDFs selected, got: {tds_selected}")

    def test_tds_pdf_action_is_fetch_document(self) -> None:
        host = _host(1, "mfg.example.com")
        obs = [_uri(i, 1, f"https://mfg.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        tds = [_uri(500 + i, 1, f"https://mfg.example.com/tds/Product_{i}_TDS.pdf") for i in range(1, 4)]
        ds = AnalysisDataset(
            uri_identities=obs + tds, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget(max_document_fetches=10, hard_stop_sample_size=50))
        for candidate, decision in plan.selected:
            if "_TDS.pdf" in candidate.canonical_uri:
                self.assertEqual(decision.next_action, NextAction.FETCH_DOCUMENT)
                self.assertEqual(decision.url_role, URLRole.TECHNICAL_DOCUMENT)

    def test_bad_static_pattern_does_not_block_render_path(self) -> None:
        """When static GET is stopped, render/API paths should remain open for unrelated URIs."""
        host = _host(1, "spa.example.com")
        # Bad static pattern (render_rate=1.0)
        obs = [_uri(i, 1, f"https://spa.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        # A download center URL on the same host — different template, should still be inspected
        dl = _uri(999, 1, "https://spa.example.com/en/downloads")
        ds = AnalysisDataset(
            uri_identities=obs + [dl], hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        dl_decision = next(
            (d for c, d in plan.selected + plan.deferred if c.uri_identity_id == 999), None
        )
        self.assertIsNotNone(dl_decision, "Download center URL should appear in plan")
        if dl_decision:
            self.assertNotEqual(
                dl_decision.next_action, NextAction.STOP_STATIC_GET,
                "Download center URL on different template should not be stopped",
            )


# ---------------------------------------------------------------------------
# 6. High-inbound legal/footer links not promoted over technical documents
# ---------------------------------------------------------------------------


class TestInboundLinkNoiseNotPromoted(unittest.TestCase):

    def test_legal_url_with_many_inbound_links_not_selected_as_doc(self) -> None:
        host = _host(1, "example.com")
        source_uris = [_uri(i, 1, f"https://example.com/products/page{i}") for i in range(1, 21)]
        legal = _uri(100, 1, "https://example.com/legal/privacy-policy")
        # 20 inbound links to the legal URL
        links = [
            ExtractedLinkRow(
                id=i, source_uri_identity_id=i, target_uri_identity_id=100,
                anchor_text="Privacy Policy",
            )
            for i in range(1, 21)
        ]
        ds = AnalysisDataset(
            uri_identities=source_uris + [legal], hosts=[host], frontier_items=[],
            fetch_attempts=[], representations=[], page_texts=[],
            extracted_links=links, candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        for candidate, decision in plan.selected:
            if "privacy" in candidate.canonical_uri or "legal" in candidate.canonical_uri:
                self.assertNotEqual(decision.next_action, NextAction.FETCH_DOCUMENT)

    def test_legal_url_with_many_inbound_links_has_legal_noise_reason(self) -> None:
        host = _host(1, "example.com")
        legal = _uri(100, 1, "https://example.com/legal/privacy-policy")
        links = [
            ExtractedLinkRow(
                id=i, source_uri_identity_id=i + 200, target_uri_identity_id=100,
                anchor_text="Privacy Policy",
            )
            for i in range(1, 21)
        ]
        source_uris = [_uri(200 + i, 1, f"https://example.com/products/{i}") for i in range(1, 21)]
        ds = AnalysisDataset(
            uri_identities=[legal] + source_uris, hosts=[host], frontier_items=[],
            fetch_attempts=[], representations=[], page_texts=[],
            extracted_links=links, candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        for candidate, decision in plan.rejected + plan.deferred:
            if candidate.uri_identity_id == 100:
                self.assertIn("LEGAL_NOISE", decision.reason_codes)
                return
        self.fail("Legal URL should be in rejected or deferred")

    def test_single_inbound_tds_pdf_still_selected(self) -> None:
        """A TDS PDF with just one inbound link is still selected for FETCH_DOCUMENT."""
        host = _host(1, "example.com")
        source = _uri(1, 1, "https://example.com/products/page")
        tds = _uri(2, 1, "https://example.com/tds/Product_A_TDS.pdf")
        link = ExtractedLinkRow(
            id=1, source_uri_identity_id=1, target_uri_identity_id=2,
            anchor_text="Technical Data Sheet",
        )
        ds = AnalysisDataset(
            uri_identities=[source, tds], hosts=[host], frontier_items=[],
            fetch_attempts=[], representations=[], page_texts=[],
            extracted_links=[link], candidate_documents=[],
        )
        plan = plan_from_dataset(ds, _default_budget())
        tds_selected = any(
            c.uri_identity_id == 2 and d.next_action == NextAction.FETCH_DOCUMENT
            for c, d in plan.selected
        )
        self.assertTrue(tds_selected, "TDS PDF with one inbound link should be selected")


# ---------------------------------------------------------------------------
# 7. compare_actual_vs_planned
# ---------------------------------------------------------------------------


class TestCompareActualVsPlanned(unittest.TestCase):

    def _build_scenario(self) -> tuple[AnalysisDataset, CrawlPlan]:
        host = _host(1, "example.com")
        # 30 already-fetched static GETs on example.com
        obs = [_uri(i, 1, f"https://example.com/en/products/{i}") for i in range(1, 31)]
        attempts = [_attempt(i, i, total_ms=350) for i in range(1, 31)]
        reprs = [_repr(i, i) for i in range(1, 31)]
        # 10 with render_needed
        pts = [_page_text(i, i, render_needed=(i <= 10)) for i in range(1, 31)]

        # 5 new candidates
        cands = [_uri(100 + i, 1, f"https://example.com/en/products/{100 + i}") for i in range(5)]
        # 1 TDS PDF not yet fetched
        tds = _uri(200, 1, "https://example.com/tds/Product_TDS.pdf")

        ds = AnalysisDataset(
            uri_identities=obs + cands + [tds], hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        budget = CrawlBudget(max_static_gets=5, max_document_fetches=10)
        plan = plan_from_dataset(ds, budget)
        return ds, plan

    def test_returns_crawl_plan_comparison(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        self.assertIsInstance(comparison, CrawlPlanComparison)

    def test_actual_static_gets_counted(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        self.assertIn("example.com", comparison.actual_static_gets_by_host)
        self.assertEqual(comparison.actual_static_gets_by_host["example.com"], 30)

    def test_promoted_technical_documents_present(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        promoted_uris = {d["canonical_uri"] for d in comparison.promoted_technical_documents}
        self.assertTrue(
            any("_TDS.pdf" in u for u in promoted_uris),
            f"Expected TDS PDF in promoted_technical_documents, got: {promoted_uris}",
        )

    def test_planned_docs_not_fetched_contains_tds(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        not_fetched_uris = {d["canonical_uri"] for d in comparison.planned_docs_not_fetched}
        self.assertTrue(
            any("_TDS.pdf" in u for u in not_fetched_uris),
            f"TDS PDF should appear in planned_docs_not_fetched, got: {not_fetched_uris}",
        )

    def test_hosts_where_planner_reduces_example_com(self) -> None:
        """30 actual static GETs vs max 5 planned → planner should flag a reduction."""
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        hostnames = {r["hostname"] for r in comparison.hosts_where_planner_reduces}
        self.assertIn(
            "example.com", hostnames,
            "example.com has 30 actual vs ~5 planned — should appear in reduction list",
        )

    def test_to_dict_has_required_keys(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        d = comparison.to_dict()
        for key in (
            "actual_static_gets_by_host", "planned_static_gets_by_host",
            "stopped_static_get_templates", "planned_docs_not_fetched",
            "hosts_where_planner_reduces", "promoted_technical_documents",
        ):
            self.assertIn(key, d, f"Missing key in to_dict(): {key}")

    def test_reduction_summary_returns_dict(self) -> None:
        ds, plan = self._build_scenario()
        comparison = compare_actual_vs_planned(ds, plan)
        summary = comparison.reduction_summary()
        self.assertIn("hosts_to_reduce", summary)
        self.assertIn("docs_not_yet_fetched", summary)

    def test_empty_plan_gives_empty_comparison(self) -> None:
        ds, _ = self._build_scenario()
        empty_plan = CrawlPlan()
        comparison = compare_actual_vs_planned(ds, empty_plan)
        self.assertEqual(comparison.promoted_technical_documents, [])
        self.assertEqual(comparison.planned_docs_not_fetched, [])


# ---------------------------------------------------------------------------
# 8. CrawlPlanningReport carries stopped_static_get_summary separately
# ---------------------------------------------------------------------------


class TestReportStoppedStaticGetSummary(unittest.TestCase):

    def _report_with_bad_pattern(self) -> CrawlPlanningReport:
        host = _host(1, "spa.example.com")
        obs = [_uri(i, 1, f"https://spa.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        cands = [_uri(1000 + i, 1, f"https://spa.example.com/en/products/{20000 + i}") for i in range(10)]
        ds = AnalysisDataset(
            uri_identities=obs + cands, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        budget = _default_budget(hard_stop_sample_size=50)
        plan = plan_from_dataset(ds, budget)
        return _build_report(plan, crawl_run_id=1, crawl_run_key="test", budget=budget)

    def test_stopped_static_get_summary_is_non_empty(self) -> None:
        report = self._report_with_bad_pattern()
        self.assertGreater(
            len(report.stopped_static_get_summary), 0,
            "stopped_static_get_summary should be non-empty for a bad static pattern",
        )

    def test_stopped_static_get_summary_actions_are_correct(self) -> None:
        report = self._report_with_bad_pattern()
        for item in report.stopped_static_get_summary:
            self.assertEqual(
                item["next_action"], NextAction.STOP_STATIC_GET.value,
                f"All items in stopped_static_get_summary should have next_action=stop_static_get",
            )

    def test_rejected_summary_has_no_stop_static_get_items(self) -> None:
        report = self._report_with_bad_pattern()
        for item in report.rejected_summary:
            self.assertNotEqual(
                item["next_action"], NextAction.STOP_STATIC_GET.value,
                "rejected_summary must not contain stop_static_get items",
            )

    def test_stopped_static_get_as_dicts_returns_list(self) -> None:
        report = self._report_with_bad_pattern()
        result = report.stopped_static_get_as_dicts()
        self.assertIsInstance(result, list)
        self.assertEqual(result, report.stopped_static_get_summary)

    def test_to_summary_dict_includes_stopped_count(self) -> None:
        report = self._report_with_bad_pattern()
        summary = report.to_summary_dict()
        self.assertIn("stopped_static_get_count", summary)
        self.assertIn("globally_rejected_count", summary)
        self.assertGreater(summary["stopped_static_get_count"], 0)

    def test_report_has_plan_field_for_comparison(self) -> None:
        report = self._report_with_bad_pattern()
        self.assertIsNotNone(report.plan)
        self.assertIsInstance(report.plan, CrawlPlan)

    def test_compare_with_returns_comparison(self) -> None:
        host = _host(1, "spa.example.com")
        obs = [_uri(i, 1, f"https://spa.example.com/en/products/{10000 + i}") for i in range(1, 61)]
        attempts = [_attempt(i, i) for i in range(1, 61)]
        reprs = [_repr(i, i) for i in range(1, 61)]
        pts = [_page_text(i, i, render_needed=True) for i in range(1, 61)]
        cands = [_uri(1000 + i, 1, f"https://spa.example.com/en/products/{20000 + i}") for i in range(10)]
        ds = AnalysisDataset(
            uri_identities=obs + cands, hosts=[host], frontier_items=[],
            fetch_attempts=attempts, representations=reprs, page_texts=pts,
            extracted_links=[], candidate_documents=[],
        )
        budget = _default_budget(hard_stop_sample_size=50)
        plan = plan_from_dataset(ds, budget)
        report = _build_report(plan, crawl_run_id=1, crawl_run_key="test", budget=budget)
        comparison = report.compare_with(ds)
        self.assertIsInstance(comparison, CrawlPlanComparison)


if __name__ == "__main__":
    unittest.main()
