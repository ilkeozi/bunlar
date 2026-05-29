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
from material_ingestion.services.url_intelligence.db_loader import (
    load_analysis_dataset_from_db,
)


# ---------------------------------------------------------------------------
# Tables needed for these tests (in dependency order so SQLite is happy)
# ---------------------------------------------------------------------------

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


class DbLoaderTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        for table in _TABLES:
            table.create(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    # ------------------------------------------------------------------
    # Seed helpers
    # ------------------------------------------------------------------

    def _seed_run(self, session, run_key: str = "run_test_001") -> int:
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

    def _seed_uri(
        self, session, host_id: int, uri: str, hash_suffix: str = ""
    ) -> int:
        u = RawWebUriIdentity(
            canonical_uri=uri,
            normalized_hash=f"hash_{abs(hash(uri))}{hash_suffix}",
            host_id=host_id,
        )
        session.add(u)
        session.flush()
        return int(u.id)

    def _seed_frontier(
        self, session, uri_id: int, run_id: int, state: str = "pending"
    ) -> int:
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
        self,
        session,
        uri_id: int,
        run_id: int,
        outcome: str = "success",
        status_code: int = 200,
        total_ms: int = 300,
    ) -> int:
        a = RawWebHttpFetchAttempt(
            uri_identity_id=uri_id,
            crawl_run_id=run_id,
            status_code=status_code,
            outcome=outcome,
            reason_code="ok",
            requested_url=f"https://example.com/page/{uri_id}",
            final_url=f"https://example.com/page/{uri_id}",
            redirect_count=0,
            total_ms=total_ms,
        )
        session.add(a)
        session.flush()
        return int(a.id)

    def _seed_repr(
        self, session, attempt_id: int, content_type: str = "text/html"
    ) -> int:
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
            title="Test Page",
            text_length=500,
            text_ratio=0.3,
            render_needed=render_needed,
        )
        session.add(pt)
        session.flush()
        return int(pt.id)

    def _seed_link(
        self, session, source_id: int, target_id: int, anchor: str = "click here"
    ) -> int:
        lnk = RawWebExtractedLink(
            source_uri_identity_id=source_id,
            target_uri_identity_id=target_id,
            rel="",
            anchor_text=anchor,
        )
        session.add(lnk)
        session.flush()
        return int(lnk.id)

    def _seed_candidate(
        self, session, uri_id: int, source_id: int, mime: str = "application/pdf"
    ) -> int:
        doc = RawWebCandidateDocument(
            uri_identity_id=uri_id,
            source_uri_identity_id=source_id,
            mime_type=mime,
            classification="technical",
            decision_state="new",
            decision_reason_code="",
            score=80,
            distinct_source_count=1,
            score_reason_json="{}",
        )
        session.add(doc)
        session.flush()
        return int(doc.id)


# ---------------------------------------------------------------------------
# A: resolves crawl_run_key → loads frontier and fetch attempt data
# ---------------------------------------------------------------------------


class TestResolveCrawlRunKey(DbLoaderTestBase):
    def test_resolves_run_key_to_id(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session, run_key="my_run_2026")
            host_id = self._seed_host(session, "example.com")
            uri_id = self._seed_uri(session, host_id, "https://example.com/page/1")
            self._seed_frontier(session, uri_id, run_id)
            self._seed_attempt(session, uri_id, run_id)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_key="my_run_2026")

        self.assertEqual(len(ds.frontier_items), 1)
        self.assertEqual(len(ds.fetch_attempts), 1)
        self.assertEqual(ds.frontier_items[0].uri_identity_id, uri_id)

    def test_unknown_run_key_raises(self) -> None:
        with self.session_factory() as session:
            with self.assertRaises(ValueError):
                load_analysis_dataset_from_db(session, crawl_run_key="nonexistent")

    def test_neither_key_nor_id_raises(self) -> None:
        with self.session_factory() as session:
            with self.assertRaises(ValueError):
                load_analysis_dataset_from_db(session)

    def test_both_key_and_id_raises(self) -> None:
        with self.session_factory() as session:
            with self.assertRaises(ValueError):
                load_analysis_dataset_from_db(
                    session, crawl_run_key="x", crawl_run_id=1
                )


# ---------------------------------------------------------------------------
# B: normalized row loading — no row multiplication
# ---------------------------------------------------------------------------


class TestNormalizedRowCounts(DbLoaderTestBase):
    """One URI with 3 extracted links and 3 candidate docs must not multiply rows."""

    def test_row_counts_are_not_multiplied(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            source_id = self._seed_uri(session, host_id, "https://example.com/source")
            self._seed_frontier(session, source_id, run_id)
            attempt_id = self._seed_attempt(session, source_id, run_id)

            # 3 target URIs linked from source
            target_ids = [
                self._seed_uri(
                    session, host_id, f"https://example.com/target/{i}"
                )
                for i in range(1, 4)
            ]
            for tid in target_ids:
                self._seed_link(session, source_id, tid, f"anchor {tid}")

            # 3 candidate docs pointing back to source as source page
            doc_uri_ids = [
                self._seed_uri(
                    session, host_id, f"https://example.com/doc/{i}.pdf"
                )
                for i in range(1, 4)
            ]
            for duid in doc_uri_ids:
                self._seed_candidate(session, duid, source_id)

            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_id=run_id)

        self.assertEqual(len(ds.extracted_links), 3)
        self.assertEqual(len(ds.candidate_documents), 3)
        # 1 source + 3 link targets + 3 doc URIs = 7 URI identities
        self.assertEqual(len(ds.uri_identities), 7)


# ---------------------------------------------------------------------------
# C: loader includes linked URI identities not in frontier/fetch
# ---------------------------------------------------------------------------


class TestLinkedUriIdentitiesIncluded(DbLoaderTestBase):
    def test_target_uri_from_extracted_link_is_included(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            source_id = self._seed_uri(session, host_id, "https://example.com/source")
            # Source is in the frontier; target is NOT
            target_id = self._seed_uri(session, host_id, "https://example.com/linked-only")
            self._seed_frontier(session, source_id, run_id)
            self._seed_link(session, source_id, target_id)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(
                session, crawl_run_id=run_id, include_all_uri_identities=True
            )

        loaded_ids = {u.id for u in ds.uri_identities}
        self.assertIn(source_id, loaded_ids)
        self.assertIn(target_id, loaded_ids)

    def test_target_uri_excluded_when_flag_false(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            source_id = self._seed_uri(session, host_id, "https://example.com/source")
            target_id = self._seed_uri(session, host_id, "https://example.com/linked-only")
            self._seed_frontier(session, source_id, run_id)
            self._seed_link(session, source_id, target_id)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(
                session, crawl_run_id=run_id, include_all_uri_identities=False
            )

        loaded_ids = {u.id for u in ds.uri_identities}
        self.assertIn(source_id, loaded_ids)
        self.assertNotIn(target_id, loaded_ids)

    def test_candidate_document_uri_included(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            source_id = self._seed_uri(session, host_id, "https://example.com/source")
            doc_uri_id = self._seed_uri(
                session, host_id, "https://example.com/doc.pdf"
            )
            self._seed_frontier(session, source_id, run_id)
            self._seed_candidate(session, doc_uri_id, source_id)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(
                session, crawl_run_id=run_id, include_all_uri_identities=True
            )

        loaded_ids = {u.id for u in ds.uri_identities}
        self.assertIn(doc_uri_id, loaded_ids)


# ---------------------------------------------------------------------------
# D: fetch attempt, representation, and page_text are mapped correctly
# ---------------------------------------------------------------------------


class TestFetchPageTextRepresentationMapping(DbLoaderTestBase):
    def test_all_three_are_loaded_and_linked(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            uri_id = self._seed_uri(session, host_id, "https://example.com/page")
            self._seed_frontier(session, uri_id, run_id)
            attempt_id = self._seed_attempt(
                session, uri_id, run_id, total_ms=450
            )
            self._seed_repr(session, attempt_id, content_type="text/html; charset=utf-8")
            self._seed_page_text(session, attempt_id, render_needed=True)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_id=run_id)

        self.assertEqual(len(ds.fetch_attempts), 1)
        self.assertEqual(ds.fetch_attempts[0].total_ms, 450)
        self.assertEqual(ds.fetch_attempts[0].uri_identity_id, uri_id)

        self.assertEqual(len(ds.representations), 1)
        self.assertIn("text/html", ds.representations[0].content_type)
        self.assertEqual(ds.representations[0].fetch_attempt_id, attempt_id)

        self.assertEqual(len(ds.page_texts), 1)
        self.assertTrue(ds.page_texts[0].render_needed)
        self.assertEqual(ds.page_texts[0].fetch_attempt_id, attempt_id)

    def test_empty_run_returns_empty_dataset(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_id=run_id)

        self.assertEqual(ds.frontier_items, [])
        self.assertEqual(ds.fetch_attempts, [])
        self.assertEqual(ds.uri_identities, [])
        self.assertEqual(ds.hosts, [])


# ---------------------------------------------------------------------------
# E: loader is read-only (no session mutations after the call)
# ---------------------------------------------------------------------------


class TestLoaderIsReadOnly(DbLoaderTestBase):
    def test_no_pending_changes_after_load(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            uri_id = self._seed_uri(session, host_id, "https://example.com/page")
            self._seed_frontier(session, uri_id, run_id)
            self._seed_attempt(session, uri_id, run_id)
            session.commit()

        # Open a fresh session, load the dataset, then inspect session state
        with self.session_factory() as session:
            load_analysis_dataset_from_db(session, crawl_run_id=run_id)
            # Session must have no pending inserts, updates, or deletes
            self.assertFalse(
                session.new, "session.new must be empty — loader must not add objects"
            )
            self.assertFalse(
                session.dirty, "session.dirty must be empty — loader must not modify objects"
            )
            self.assertFalse(
                session.deleted, "session.deleted must be empty — loader must not delete objects"
            )

    def test_limit_caps_frontier_items(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            for i in range(10):
                uid = self._seed_uri(
                    session, host_id, f"https://example.com/page/{i}"
                )
                self._seed_frontier(session, uid, run_id)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(
                session, crawl_run_id=run_id, limit=3
            )

        self.assertEqual(len(ds.frontier_items), 3)


# ---------------------------------------------------------------------------
# Sitemap and robots policy loading
# ---------------------------------------------------------------------------


class TestSitemapAndRobotsPolicyLoading(DbLoaderTestBase):
    def test_sitemap_entries_and_alternates_are_loaded(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            uri_id = self._seed_uri(session, host_id, "https://example.com/sitemap-page")
            self._seed_frontier(session, uri_id, run_id)

            sitemap_source = RawWebSitemapSource(
                host_id=host_id,
                sitemap_url="https://example.com/sitemap.xml",
                discovered_via="robots",
                last_fetch_status="ok",
            )
            session.add(sitemap_source)
            session.flush()

            entry = RawWebSitemapEntry(
                sitemap_source_id=int(sitemap_source.id),
                uri_identity_id=uri_id,
                changefreq="weekly",
            )
            session.add(entry)
            session.flush()

            alt = RawWebSitemapAlternate(
                sitemap_entry_id=int(entry.id),
                hreflang="en",
                href="https://example.com/sitemap-page",
            )
            session.add(alt)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_id=run_id)

        self.assertEqual(len(ds.sitemap_entries), 1)
        self.assertEqual(ds.sitemap_entries[0].uri_identity_id, uri_id)
        self.assertEqual(len(ds.sitemap_alternates), 1)
        self.assertEqual(ds.sitemap_alternates[0].hreflang, "en")

    def test_robots_policy_is_loaded(self) -> None:
        with self.session_factory() as session:
            run_id = self._seed_run(session)
            host_id = self._seed_host(session)
            uri_id = self._seed_uri(session, host_id, "https://example.com/page")
            self._seed_frontier(session, uri_id, run_id)

            policy = RawWebRobotsPolicy(
                host_id=host_id,
                fetch_status="ok",
                policy_blob="User-agent: *\nDisallow: /private/",
                evaluation_summary_json="{}",
            )
            session.add(policy)
            session.commit()

        with self.session_factory() as session:
            ds = load_analysis_dataset_from_db(session, crawl_run_id=run_id)

        self.assertEqual(len(ds.robots_policies), 1)
        self.assertEqual(ds.robots_policies[0].host_id, host_id)
        self.assertIn("Disallow", ds.robots_policies[0].policy_blob)


if __name__ == "__main__":
    unittest.main()
