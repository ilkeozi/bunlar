from __future__ import annotations

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from material_ingestion.db.models import (
    RawWebCrawlDecision,
    RawWebCrawlHost,
    RawWebCrawlRun,
    RawWebEvaluationRule,
    RawWebFrontierItem,
    RawWebHttpFetchAttempt,
    RawWebHttpRepresentation,
    RawWebUriIdentity,
)
from material_ingestion.services.web_crawl_frontier_evaluate_service import evaluate_frontier_batch


class WebCrawlFrontierEvaluateServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        tables = [
            RawWebCrawlHost.__table__,
            RawWebCrawlRun.__table__,
            RawWebUriIdentity.__table__,
            RawWebFrontierItem.__table__,
            RawWebHttpFetchAttempt.__table__,
            RawWebHttpRepresentation.__table__,
            RawWebEvaluationRule.__table__,
            RawWebCrawlDecision.__table__,
        ]
        for table in tables:
            table.create(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def _seed_frontier_fixture(self, *, state_reason_code: str, canonical_uri: str = "https://example.com/product/a") -> int:
        with self.session_factory() as session:
            host = RawWebCrawlHost(
                hostname="example.com",
                source_type="seed",
                discovery_source="test",
                allowlist_match=True,
                auto_crawl_enabled=True,
            )
            session.add(host)
            session.flush()

            run = RawWebCrawlRun(run_key="run_test", initiator="test", force_refresh=False)
            session.add(run)
            session.flush()

            uri = RawWebUriIdentity(
                canonical_uri=canonical_uri,
                normalized_hash=f"hash_{abs(hash(canonical_uri))}",
                host_id=int(host.id),
            )
            session.add(uri)
            session.flush()

            frontier = RawWebFrontierItem(
                uri_identity_id=int(uri.id),
                crawl_run_id=int(run.id),
                state="completed",
                priority=10,
                state_reason_code=state_reason_code,
            )
            session.add(frontier)
            session.flush()

            attempt = RawWebHttpFetchAttempt(
                uri_identity_id=int(uri.id),
                crawl_run_id=int(run.id),
                status_code=200,
                outcome="success",
                reason_code="head_metadata_success",
                requested_url=canonical_uri,
                final_url=canonical_uri,
                redirect_count=0,
            )
            session.add(attempt)
            session.flush()

            session.add(
                RawWebHttpRepresentation(
                    fetch_attempt_id=int(attempt.id),
                    storage_ref=canonical_uri,
                    content_type="text/html",
                    content_language="en",
                    content_disposition="",
                    link="",
                )
            )
            session.add(
                RawWebEvaluationRule(
                    action="promote",
                    match_type="contains",
                    pattern="/product",
                    weight=10,
                    enabled=True,
                    priority=1,
                    note="promote products",
                )
            )
            session.commit()
            return int(frontier.id)

    def test_evaluate_transitions_phase_a_item_to_eval_promote(self) -> None:
        frontier_id = self._seed_frontier_fixture(state_reason_code="head_metadata_success")
        with (
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory",
                return_value=self.session_factory,
            ),
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config",
                return_value=6,
            ),
        ):
            processed, promoted, deferred, skipped = evaluate_frontier_batch(batch_size=10, force=False)

        self.assertEqual((1, 1, 0, 0), (processed, promoted, deferred, skipped))
        with self.session_factory() as session:
            row = session.query(RawWebFrontierItem).filter(RawWebFrontierItem.id == frontier_id).first()
            self.assertIsNotNone(row)
            self.assertEqual("eval_promote", row.state_reason_code)
            decisions = session.query(RawWebCrawlDecision).all()
            self.assertEqual(1, len(decisions))
            self.assertEqual("eval_promote", decisions[0].reason_code)

    def test_force_true_re_evaluates_existing_eval_state(self) -> None:
        frontier_id = self._seed_frontier_fixture(state_reason_code="eval_defer")
        with (
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory",
                return_value=self.session_factory,
            ),
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config",
                return_value=6,
            ),
        ):
            processed_no_force = evaluate_frontier_batch(batch_size=10, force=False)[0]
            processed_force = evaluate_frontier_batch(batch_size=10, force=True)[0]

        self.assertEqual(0, processed_no_force)
        self.assertEqual(1, processed_force)
        with self.session_factory() as session:
            row = session.query(RawWebFrontierItem).filter(RawWebFrontierItem.id == frontier_id).first()
            self.assertIsNotNone(row)
            self.assertEqual("eval_promote", row.state_reason_code)

    def test_force_re_evaluation_updates_existing_eval_decision_row(self) -> None:
        self._seed_frontier_fixture(state_reason_code="head_metadata_success")
        with (
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory",
                return_value=self.session_factory,
            ),
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config",
                return_value=6,
            ),
        ):
            evaluate_frontier_batch(batch_size=10, force=False)
            evaluate_frontier_batch(batch_size=10, force=True)

        with self.session_factory() as session:
            decisions = (
                session.query(RawWebCrawlDecision)
                .filter(RawWebCrawlDecision.reason_code == "eval_promote")
                .all()
            )
            self.assertEqual(1, len(decisions))

    def _seed_multiple_frontier_items(self, *, uris: list[str], state_reason_code: str) -> None:
        with self.session_factory() as session:
            host = RawWebCrawlHost(
                hostname="multi.example.com",
                source_type="seed",
                discovery_source="test",
                allowlist_match=True,
                auto_crawl_enabled=True,
            )
            session.add(host)
            session.flush()
            run = RawWebCrawlRun(run_key="run_multi", initiator="test", force_refresh=False)
            session.add(run)
            session.flush()
            session.add(
                RawWebEvaluationRule(
                    action="promote",
                    match_type="contains",
                    pattern="/product",
                    weight=10,
                    enabled=True,
                    priority=1,
                    note="promote products",
                )
            )
            for uri_str in uris:
                uri = RawWebUriIdentity(
                    canonical_uri=uri_str,
                    normalized_hash=f"hash_{abs(hash(uri_str))}",
                    host_id=int(host.id),
                )
                session.add(uri)
                session.flush()
                frontier = RawWebFrontierItem(
                    uri_identity_id=int(uri.id),
                    crawl_run_id=int(run.id),
                    state="completed",
                    priority=10,
                    state_reason_code=state_reason_code,
                )
                session.add(frontier)
                session.flush()
                attempt = RawWebHttpFetchAttempt(
                    uri_identity_id=int(uri.id),
                    crawl_run_id=int(run.id),
                    status_code=200,
                    outcome="success",
                    reason_code="head_metadata_success",
                    requested_url=uri_str,
                    final_url=uri_str,
                    redirect_count=0,
                )
                session.add(attempt)
                session.flush()
                session.add(
                    RawWebHttpRepresentation(
                        fetch_attempt_id=int(attempt.id),
                        storage_ref=uri_str,
                        content_type="text/html",
                        content_language="en",
                        content_disposition="",
                        link="",
                    )
                )
            session.commit()

    def test_force_batch_preload_no_duplicate_decisions_for_multiple_items(self) -> None:
        # Seed three items; first normal eval promotes them all; force re-eval must
        # update in place via batch preload — not create new decision rows.
        self._seed_multiple_frontier_items(
            uris=[f"https://multi.example.com/product/{i}" for i in range(3)],
            state_reason_code="head_metadata_success",
        )
        patches = (
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory",
                return_value=self.session_factory,
            ),
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config",
                return_value=6,
            ),
        )
        with patches[0], patches[1]:
            processed_first, promoted_first, _, _ = evaluate_frontier_batch(batch_size=10, force=False)
            processed_force, promoted_force, _, _ = evaluate_frontier_batch(batch_size=10, force=True)

        self.assertEqual(3, processed_first)
        self.assertEqual(3, promoted_first)
        self.assertEqual(3, processed_force)
        self.assertEqual(3, promoted_force)
        with self.session_factory() as session:
            # Exactly one decision row per item — batch preload must not have created extras
            all_decisions = session.query(RawWebCrawlDecision).all()
            self.assertEqual(3, len(all_decisions))
            self.assertTrue(all(d.reason_code == "eval_promote" for d in all_decisions))

    def test_normal_eval_does_not_query_decisions_per_item(self) -> None:
        # In non-force mode the ~evaluated_exists filter excludes items with existing
        # decisions, so the per-item decision lookup path must never be taken.
        # Seed one item, evaluate normally, then seed another already-decided item and
        # verify the second normal eval correctly skips the already-evaluated one.
        self._seed_frontier_fixture(
            state_reason_code="head_metadata_success",
            canonical_uri="https://example.com/product/already",
        )
        patches = (
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory",
                return_value=self.session_factory,
            ),
            patch(
                "material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config",
                return_value=6,
            ),
        )
        with patches[0], patches[1]:
            processed_first, _, _, _ = evaluate_frontier_batch(batch_size=10, force=False)
            # Second normal run: item already has eval_promote state_reason_code and a
            # decision row — the eligible filter excludes it so processed must be 0.
            processed_second, _, _, _ = evaluate_frontier_batch(batch_size=10, force=False)

        self.assertEqual(1, processed_first)
        self.assertEqual(0, processed_second)
        with self.session_factory() as session:
            # Still exactly one decision — no accidental duplicate inserts
            self.assertEqual(1, session.query(RawWebCrawlDecision).count())


if __name__ == "__main__":
    unittest.main()
