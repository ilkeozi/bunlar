"""Tests for planning report cleanup: URL dedup and grouped stopped templates (Issues 2 & 3)."""
from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.planning_report import (
    _group_stopped_static_templates,
    _strip_tracking_params,
)
from material_ingestion.services.url_intelligence.models import NextAction, URLRole, ScoreBreakdown
from material_ingestion.services.url_intelligence.planner import (
    CrawlBudget,
    CrawlPlan,
    PlanCandidate,
    _allocate,
)
from material_ingestion.services.url_intelligence.decision import URLDecision


def _make_decision(action: NextAction = NextAction.STOP_STATIC_GET) -> URLDecision:
    return URLDecision(
        canonical_url="https://example.com/page",
        url_role=URLRole.GENERIC_HTML,
        templates=[],
        selected_template="",
        scores=ScoreBreakdown(
            url_score=0, source_score=0, pattern_score=0, final_score=0,
            url_reasons=[], source_reasons=[], pattern_reasons=[],
        ),
        next_action=action,
        reason_codes=["PATTERN_RENDER_HEAVY", "STOP_PATTERN"],
        debug={},
    )


def _make_candidate(
    uid: int,
    url: str,
    host: str = "example.com",
    template: str = "/en/{numeric_id}",
) -> PlanCandidate:
    return PlanCandidate(
        uri_identity_id=uid,
        canonical_uri=url,
        source_type="frontier",
        host=host,
        inferred_templates=[template],
    )


class TestStripTrackingParams(unittest.TestCase):

    def test_strips_vid_param(self) -> None:
        url = "https://example.com/doc.pdf?vid=abc123"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_utm_source(self) -> None:
        url = "https://example.com/doc.pdf?utm_source=email&utm_medium=newsletter"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_fbclid(self) -> None:
        url = "https://example.com/doc.pdf?fbclid=xyz"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_gclid(self) -> None:
        url = "https://example.com/doc.pdf?gclid=xyz"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_session_param(self) -> None:
        url = "https://example.com/doc.pdf?session=s123"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_token_param(self) -> None:
        url = "https://example.com/doc.pdf?token=abc"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_strips_cache_prefixed_param(self) -> None:
        url = "https://example.com/doc.pdf?cache-buster=123"
        self.assertEqual(_strip_tracking_params(url), "https://example.com/doc.pdf")

    def test_preserves_non_tracking_params(self) -> None:
        url = "https://example.com/doc.pdf?lang=en&format=pdf"
        result = _strip_tracking_params(url)
        self.assertIn("lang=en", result)
        self.assertIn("format=pdf", result)

    def test_url_without_query_unchanged(self) -> None:
        url = "https://example.com/doc.pdf"
        self.assertEqual(_strip_tracking_params(url), url)

    def test_mixed_tracking_and_real_params_preserved(self) -> None:
        url = "https://example.com/doc.pdf?lang=en&vid=abc&utm_source=x"
        result = _strip_tracking_params(url)
        self.assertIn("lang=en", result)
        self.assertNotIn("vid", result)
        self.assertNotIn("utm_source", result)

    def test_vid_and_base_url_are_same_canonical(self) -> None:
        base = "https://example.com/brochure.pdf"
        with_vid = "https://example.com/brochure.pdf?vid=abc123"
        self.assertEqual(_strip_tracking_params(base), _strip_tracking_params(with_vid))


class TestGroupStoppedStaticTemplates(unittest.TestCase):

    def test_twenty_urls_same_template_produce_one_row(self) -> None:
        template = "/{language}/{numeric_id}/page"
        pairs = [
            (
                _make_candidate(i, f"https://example.com/en/{10000 + i}/page", template=template),
                _make_decision(),
            )
            for i in range(20)
        ]
        groups = _group_stopped_static_templates(pairs)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["stopped_count"], 20)

    def test_group_contains_host_and_template(self) -> None:
        template = "/{language}/{numeric_id}/page"
        pairs = [
            (
                _make_candidate(i, f"https://example.com/en/{10000 + i}/page", template=template),
                _make_decision(),
            )
            for i in range(5)
        ]
        groups = _group_stopped_static_templates(pairs)
        self.assertEqual(groups[0]["host"], "example.com")
        self.assertEqual(groups[0]["template"], template)

    def test_representative_urls_capped_at_three(self) -> None:
        template = "/{language}/{numeric_id}"
        pairs = [
            (
                _make_candidate(i, f"https://example.com/en/{10000 + i}", template=template),
                _make_decision(),
            )
            for i in range(20)
        ]
        groups = _group_stopped_static_templates(pairs)
        self.assertLessEqual(len(groups[0]["representative_urls"]), 3)

    def test_two_templates_produce_two_groups(self) -> None:
        pairs = [
            (
                _make_candidate(i, f"https://example.com/en/{10000 + i}", template="/en/{numeric_id}"),
                _make_decision(),
            )
            for i in range(10)
        ] + [
            (
                _make_candidate(100 + i, f"https://other.com/en/{20000 + i}", host="other.com", template="/en/{numeric_id}"),
                _make_decision(),
            )
            for i in range(5)
        ]
        groups = _group_stopped_static_templates(pairs)
        self.assertEqual(len(groups), 2)

    def test_groups_sorted_by_stopped_count_descending(self) -> None:
        pairs_large = [
            (
                _make_candidate(i, f"https://big.com/en/{10000 + i}", host="big.com", template="/en/{numeric_id}"),
                _make_decision(),
            )
            for i in range(15)
        ]
        pairs_small = [
            (
                _make_candidate(100 + i, f"https://small.com/en/{20000 + i}", host="small.com", template="/en/{numeric_id}"),
                _make_decision(),
            )
            for i in range(3)
        ]
        groups = _group_stopped_static_templates(pairs_small + pairs_large)
        self.assertEqual(groups[0]["stopped_count"], 15)
        self.assertEqual(groups[1]["stopped_count"], 3)

    def test_empty_stopped_list_produces_empty_groups(self) -> None:
        groups = _group_stopped_static_templates([])
        self.assertEqual(groups, [])

    def test_group_contains_next_action(self) -> None:
        template = "/{language}/{numeric_id}"
        pairs = [
            (
                _make_candidate(i, f"https://example.com/en/{10000 + i}", template=template),
                _make_decision(NextAction.STOP_STATIC_GET),
            )
            for i in range(3)
        ]
        groups = _group_stopped_static_templates(pairs)
        self.assertEqual(groups[0]["next_action"], NextAction.STOP_STATIC_GET.value)


def _make_fetch_doc_decision(url: str, score: int = 100, role: URLRole = URLRole.TECHNICAL_DOCUMENT) -> URLDecision:
    return URLDecision(
        canonical_url=url,
        url_role=role,
        templates=[],
        selected_template="",
        scores=ScoreBreakdown(
            url_score=score, source_score=0, pattern_score=0, final_score=score,
            url_reasons=["TECH_DOC_FILE_URL"], source_reasons=[], pattern_reasons=[],
        ),
        next_action=NextAction.FETCH_DOCUMENT,
        reason_codes=["TECH_DOC_FILE_URL"],
        debug={},
    )


def _make_doc_candidate(uid: int, url: str, host: str = "example.com") -> PlanCandidate:
    return PlanCandidate(
        uri_identity_id=uid,
        canonical_uri=url,
        source_type="frontier",
        host=host,
        inferred_templates=[],
    )


class TestPlannerDocumentDedup(unittest.TestCase):

    def test_tds_and_vid_variant_deduped_to_one_selected(self) -> None:
        base = "https://example.com/tds/Product_TDS.pdf"
        vid = "https://example.com/tds/Product_TDS.pdf?vid=abc123"
        ranked = [
            (_make_doc_candidate(1, base), _make_fetch_doc_decision(base)),
            (_make_doc_candidate(2, vid), _make_fetch_doc_decision(vid)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 1)
        selected_urls = [c.canonical_uri for c, _ in plan.selected]
        self.assertEqual(len(selected_urls), 1)

    def test_vid_duplicate_goes_to_deferred(self) -> None:
        base = "https://example.com/tds/Product_TDS.pdf"
        vid = "https://example.com/tds/Product_TDS.pdf?vid=abc123"
        ranked = [
            (_make_doc_candidate(1, base), _make_fetch_doc_decision(base)),
            (_make_doc_candidate(2, vid), _make_fetch_doc_decision(vid)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        deferred_urls = [c.canonical_uri for c, _ in plan.deferred]
        self.assertIn(vid, deferred_urls)

    def test_utm_variant_deduped(self) -> None:
        base = "https://example.com/docs/SDS.pdf"
        utm = "https://example.com/docs/SDS.pdf?utm_source=email&utm_campaign=q1"
        ranked = [
            (_make_doc_candidate(1, base), _make_fetch_doc_decision(base)),
            (_make_doc_candidate(2, utm), _make_fetch_doc_decision(utm)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 1)

    def test_distinct_documents_not_deduped(self) -> None:
        url_a = "https://example.com/docs/TDS_A.pdf"
        url_b = "https://example.com/docs/TDS_B.pdf"
        ranked = [
            (_make_doc_candidate(1, url_a), _make_fetch_doc_decision(url_a)),
            (_make_doc_candidate(2, url_b), _make_fetch_doc_decision(url_b)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 2)
        self.assertEqual(len(plan.selected), 2)

    def test_real_query_param_not_stripped(self) -> None:
        # lang=en is not a tracking param — two different language variants
        # are NOT the same doc and should each be selected
        url_en = "https://example.com/docs/report.pdf?lang=en"
        url_de = "https://example.com/docs/report.pdf?lang=de"
        ranked = [
            (_make_doc_candidate(1, url_en), _make_fetch_doc_decision(url_en)),
            (_make_doc_candidate(2, url_de), _make_fetch_doc_decision(url_de)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 2)

    def test_generic_pdf_vid_duplicate_also_deduped(self) -> None:
        base = "https://example.com/downloads/brochure.pdf"
        vid = "https://example.com/downloads/brochure.pdf?vid=xyz"
        decision_base = _make_fetch_doc_decision(base, score=60, role=URLRole.DOCUMENT)
        decision_vid = _make_fetch_doc_decision(vid, score=60, role=URLRole.DOCUMENT)
        ranked = [
            (_make_doc_candidate(1, base), decision_base),
            (_make_doc_candidate(2, vid), decision_vid),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 1)

    def test_dedup_vid_first_then_base(self) -> None:
        # Even when the vid variant comes first in the ranked list, dedup fires
        base = "https://example.com/tds/Product_TDS.pdf"
        vid = "https://example.com/tds/Product_TDS.pdf?vid=abc123"
        ranked = [
            (_make_doc_candidate(1, vid), _make_fetch_doc_decision(vid)),
            (_make_doc_candidate(2, base), _make_fetch_doc_decision(base)),
        ]
        plan = _allocate(ranked, CrawlBudget(max_document_fetches=10), {})
        self.assertEqual(plan.budget_usage.document_fetches, 1)
        self.assertEqual(len(plan.selected), 1)


if __name__ == "__main__":
    unittest.main()
