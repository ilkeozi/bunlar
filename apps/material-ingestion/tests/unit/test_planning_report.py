from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from material_ingestion.db.models import (
    RawWebCandidateDocument,
    RawWebCrawlDecision,
    RawWebCrawlHost,
    RawWebCrawlRun,
    RawWebExtractedLink,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebPageText,
    RawWebRobotsPolicy,
    RawWebSitemapAlternate,
    RawWebSitemapEntry,
    RawWebSitemapSource,
    RawWebUriIdentity,
)
from material_ingestion.services.url_intelligence.planning_report import (
    CrawlPlanningReport,
    run_planning_from_db,
)
from material_ingestion.services.url_intelligence.planner import CrawlBudget
from material_ingestion.services.url_intelligence.models import NextAction


_TABLES = [
    RawWebCrawlHost.__table__,
    RawWebCrawlRun.__table__,
    RawWebUriIdentity.__table__,
    RawWebFrontierItem.__table__,
    RawWebHttpFetchAttempt.__table__,
    RawWebHttpRepresentation.__table__,
    RawWebPageText.__table__,
    RawWebExtractedLink.__table__,
    RawWebCandidateDocument.__table__,
    RawWebCrawlDecision.__table__,
    RawWebSitemapSource.__table__,
    RawWebSitemapEntry.__table__,
    RawWebSitemapAlternate.__table__,
    RawWebRobotsPolicy.__table__,
]


class PlanningReportTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        for table in _TABLES:
            table.create(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    def _seed_run(self, session, run_key: str = "run_test") -> int:
        run = RawWebCrawlRun(run_key=run_key, initiator="test", force_refresh=False)
        session.add(run)
        session.flush()
        return int(run.id)

    def _seed_host(self, session, hostname: str = "example.com") -> int:
        host = RawWebCrawlHost(
            hostname=hostname,
            source_type="seed",
            discovery_source="test",
            allowlist_match=True,
            auto_crawl_enabled=True,
        )
        session.add(host)
        session.flush()
        return int(host.id)

    def _seed_uri(self, session, host_id: int, uri: str) -> int:
        u = RawWebUriIdentity(
            canonical_uri=uri,
            normalized_hash=f"hash_{abs(hash(uri))}",
            host_id=host_id,
        )
        session.add(u)
        session.flush()
        return int(u.id)

    def _seed_frontier(self, session, uri_id: int, run_id: int, state: str = "pending") -> int:
        fi = RawWebFrontierItem(
            uri_identity_id=uri_id,
            crawl_run_id=run_id,
            state=state,
            priority=5,
            state_reason_code="test",
        )
        session.add(fi)
        session.flush()
        return int(fi.id)

    def _seed_attempt(
        self, session, uri_id: int, run_id: int, outcome: str = "success", total_ms: int = 300
    ) -> int:
        a = RawWebHttpFetchAttempt(
            uri_identity_id=uri_id,
            crawl_run_id=run_id,
            status_code=200,
            outcome=outcome,
            reason_code="ok",
            requested_url=f"https://example.com/{uri_id}",
            final_url=f"https://example.com/{uri_id}",
            redirect_count=0,
            total_ms=total_ms,
        )
        session.add(a)
        session.flush()
        return int(a.id)

    def _seed_repr(self, session, attempt_id: int, content_type: str = "text/html") -> int:
        r = RawWebHttpRepresentation(
            fetch_attempt_id=attempt_id,
            storage_ref="",
            content_type=content_type,
            content_language="en",
            content_disposition="",
            link="",
        )
        session.add(r)
        session.flush()
        return int(r.id)

    def _seed_page_text(
        self, session, attempt_id: int, render_needed: bool = False
    ) -> int:
        pt = RawWebPageText(
            fetch_attempt_id=attempt_id,
            title="Page",
            text_length=400,
            text_ratio=0.3,
            render_needed=render_needed,
        )
        session.add(pt)
        session.flush()
        return int(pt.id)

    def _default_budget(self) -> CrawlBudget:
        return CrawlBudget(
            max_static_gets=50,
            max_renders=5,
            max_document_fetches=20,
            max_static_gets_per_host=20,
            max_renders_per_host=2,
            max_static_gets_per_template=10,
            hard_stop_sample_size=50,
        )


# ---------------------------------------------------------------------------
# F: run_planning_from_db returns a valid CrawlPlanningReport
# ---------------------------------------------------------------------------


class TestRunPlanningFromDb(PlanningReportTestBase):
    def test_returns_planning_report_instance(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session, "run_basic")
            host_id = self._seed_host(session)
            for i in range(5):
                uid = self._seed_uri(session, host_id, f"https://example.com/products/{i}")
                self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session, crawl_run_key="run_basic", budget=self._default_budget()
            )

        self.assertIsInstance(report, CrawlPlanningReport)
        total = (
            len(report.selected_summary)
            + len(report.deferred_summary)
            + len(report.rejected_summary)
        )
        self.assertGreater(total, 0)

    def test_selected_deferred_rejected_are_disjoint(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            for i in range(10):
                uid = self._seed_uri(
                    session, host_id, f"https://example.com/items/{i}"
                )
                self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session, crawl_run_id=run_id, budget=self._default_budget()
            )

        sel_ids = {d["uri_identity_id"] for d in report.selected_summary}
        def_ids = {d["uri_identity_id"] for d in report.deferred_summary}
        rej_ids = {d["uri_identity_id"] for d in report.rejected_summary}
        self.assertFalse(sel_ids & def_ids, "selected and deferred overlap")
        self.assertFalse(sel_ids & rej_ids, "selected and rejected overlap")
        self.assertFalse(def_ids & rej_ids, "deferred and rejected overlap")

    def test_budget_usage_does_not_exceed_caps(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            for i in range(100):
                uid = self._seed_uri(
                    session, host_id, f"https://example.com/p/{i}"
                )
                self._seed_frontier(session, uid, run_id)
            session.commit()

        budget = CrawlBudget(max_static_gets=10, max_renders=3, max_document_fetches=5)
        with self.session_factory() as session:
            report = run_planning_from_db(session, crawl_run_id=run_id, budget=budget)

        self.assertLessEqual(report.budget_usage["static_gets"], budget.max_static_gets)
        self.assertLessEqual(report.budget_usage["renders"], budget.max_renders)
        self.assertLessEqual(
            report.budget_usage["document_fetches"], budget.max_document_fetches
        )


# ---------------------------------------------------------------------------
# G: to_summary_dict includes budget_usage, reason_summary, host_summary,
#    template_summary
# ---------------------------------------------------------------------------


class TestSummaryDictStructure(PlanningReportTestBase):
    def test_summary_dict_has_required_keys(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session, "docs.example.com")
            for i in range(5):
                uid = self._seed_uri(
                    session, host_id, f"https://docs.example.com/en/products/{i}"
                )
                self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session, crawl_run_id=run_id, budget=self._default_budget()
            )

        summary = report.to_summary_dict()
        for key in ("budget_usage", "reason_summary", "host_summary", "template_summary"):
            self.assertIn(key, summary, f"Missing key: {key}")

        self.assertIn("static_gets", summary["budget_usage"])
        self.assertIsInstance(summary["host_summary"], list)
        self.assertIsInstance(summary["template_summary"], list)

    def test_convenience_methods_return_lists(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            uid = self._seed_uri(session, host_id, "https://example.com/x")
            self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session, crawl_run_id=run_id, budget=self._default_budget()
            )

        self.assertIsInstance(report.selected_as_dicts(), list)
        self.assertIsInstance(report.deferred_as_dicts(), list)
        self.assertIsInstance(report.rejected_as_dicts(), list)
        self.assertIsInstance(report.template_stats_as_dicts(), list)
        self.assertIsInstance(report.host_stats_as_dicts(), list)

    def test_top_lists_are_capped_at_twenty(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            for i in range(100):
                uid = self._seed_uri(
                    session, host_id, f"https://example.com/products/{i}"
                )
                self._seed_frontier(session, uid, run_id)
            session.commit()

        budget = CrawlBudget(max_static_gets=200, max_renders=5, max_document_fetches=50)
        with self.session_factory() as session:
            report = run_planning_from_db(session, crawl_run_id=run_id, budget=budget)

        self.assertLessEqual(len(report.top_selected), 20)
        self.assertLessEqual(len(report.top_deferred), 20)
        self.assertLessEqual(len(report.top_rejected), 20)


# ---------------------------------------------------------------------------
# H: technical document URIs (TDS PDFs) appear in top_document_fetches
# ---------------------------------------------------------------------------


class TestTechnicalDocumentsFetched(PlanningReportTestBase):
    def test_tds_pdfs_in_document_fetches(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session, "mfg.example.com")

            # 60 observed pages creating a bad static pattern
            for i in range(60):
                uid = self._seed_uri(
                    session, host_id, f"https://mfg.example.com/en/products/{10000 + i}"
                )
                aid = self._seed_attempt(session, uid, run_id)
                self._seed_repr(session, aid)
                self._seed_page_text(session, aid, render_needed=True)

            # 5 TDS PDF candidates
            for i in range(1, 6):
                uid = self._seed_uri(
                    session, host_id, f"https://mfg.example.com/tds/Product_{i}_TDS.pdf"
                )
                self._seed_frontier(session, uid, run_id)

            session.commit()

        budget = CrawlBudget(
            max_static_gets=10,
            max_renders=5,
            max_document_fetches=20,
            hard_stop_sample_size=50,
        )
        with self.session_factory() as session:
            report = run_planning_from_db(session, crawl_run_id=run_id, budget=budget)

        doc_uris = {d["canonical_uri"] for d in report.top_document_fetches}
        tds_in_docs = [u for u in doc_uris if "_TDS.pdf" in u]
        self.assertGreater(len(tds_in_docs), 0, "Expected TDS PDFs in top_document_fetches")

        for item in report.selected_summary:
            if "_TDS.pdf" in item["canonical_uri"]:
                self.assertEqual(item["next_action"], NextAction.FETCH_DOCUMENT.value)


# ---------------------------------------------------------------------------
# I: low-yield static template is stopped (STOP_STATIC_GET in report)
# ---------------------------------------------------------------------------


class TestLowYieldTemplateStoppedInReport(PlanningReportTestBase):
    def test_low_yield_template_produces_stop_static_get_entries(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session, "spa.example.com")

            # 60 fetched URIs on the same template, 59 render_needed, 0 candidate docs
            for i in range(60):
                uid = self._seed_uri(
                    session, host_id, f"https://spa.example.com/en/products/{10000 + i}"
                )
                aid = self._seed_attempt(session, uid, run_id)
                self._seed_repr(session, aid)
                self._seed_page_text(session, aid, render_needed=(i < 59))

            # 20 new candidate URIs on same bad template
            for i in range(20):
                uid = self._seed_uri(
                    session, host_id, f"https://spa.example.com/en/products/{20000 + i}"
                )
                self._seed_frontier(session, uid, run_id)

            session.commit()

        budget = CrawlBudget(
            max_static_gets=50,
            max_renders=5,
            max_document_fetches=10,
            hard_stop_sample_size=50,
        )
        with self.session_factory() as session:
            report = run_planning_from_db(session, crawl_run_id=run_id, budget=budget)

        # Evidence of STOP_STATIC_GET: either in top_stopped_static_templates
        # or in reason_summary
        has_stop_evidence = (
            len(report.top_stopped_static_templates) > 0
            or "STOP_STATIC_GET" in report.reason_summary
            or any(
                d.get("next_action") == NextAction.STOP_STATIC_GET.value
                for d in report.rejected_summary
            )
        )
        self.assertTrue(
            has_stop_evidence,
            "Expected evidence of STOP_STATIC_GET in the report for a bad static pattern",
        )


# ---------------------------------------------------------------------------
# J: legal/footer high-inbound extracted link is not selected
# ---------------------------------------------------------------------------


class TestLegalHighInboundNotSelected(PlanningReportTestBase):
    def test_legal_url_not_in_selected_as_fetch_document(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)

            # Many source pages
            source_ids = [
                self._seed_uri(
                    session, host_id, f"https://example.com/products/page{i}"
                )
                for i in range(20)
            ]
            for sid in source_ids:
                self._seed_frontier(session, sid, run_id)

            # Legal URL linked from all source pages
            legal_id = self._seed_uri(
                session, host_id, "https://example.com/legal/privacy-policy"
            )
            for sid in source_ids:
                lnk = RawWebExtractedLink(
                    source_uri_identity_id=sid,
                    target_uri_identity_id=legal_id,
                    rel="",
                    anchor_text="Privacy Policy",
                )
                session.add(lnk)
            session.flush()

            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session, crawl_run_id=run_id, budget=self._default_budget()
            )

        # Legal URL must not be selected for FETCH_DOCUMENT
        for item in report.selected_summary:
            if "privacy" in item["canonical_uri"] or "legal" in item["canonical_uri"]:
                self.assertNotEqual(
                    item["next_action"],
                    NextAction.FETCH_DOCUMENT.value,
                    "Legal/privacy URL must not be selected as a document fetch",
                )

        # It should appear in rejected or deferred, not selected
        legal_in_rejected_or_deferred = any(
            "privacy" in d["canonical_uri"] or "legal" in d["canonical_uri"]
            for d in report.rejected_summary + report.deferred_summary
        )
        self.assertTrue(
            legal_in_rejected_or_deferred,
            "Legal/privacy URL should be rejected or deferred",
        )

    def test_run_key_lookup_also_works_for_report(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session, run_key="report_run_001")
            host_id = self._seed_host(session, "report.example.com")
            uid = self._seed_uri(
                session, host_id, "https://report.example.com/en/products/42"
            )
            self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            report = run_planning_from_db(
                session,
                crawl_run_key="report_run_001",
                budget=self._default_budget(),
            )

        self.assertEqual(report.crawl_run_key, "report_run_001")
        self.assertIsNotNone(report.crawl_run_id)


if __name__ == "__main__":
    unittest.main()
