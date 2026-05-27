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
    RawWebRuntimeConfig,
    RawWebUriIdentity,
)
from material_ingestion.services import shared_cache_service
from material_ingestion.services.shared_cache_service import (
    local_cache_delete,
    local_cache_get,
    local_cache_invalidate_prefix,
    local_cache_set,
)
from material_ingestion.services.web_crawl_frontier_evaluate_service import (
    _EVAL_RULES_CACHE_KEY,
    evaluate_frontier_batch,
)
from material_ingestion.services.web_runtime_config_service import (
    create_runtime_config,
    delete_runtime_config,
    get_runtime_int_config,
    replace_runtime_configs,
    update_runtime_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clear_local_cache() -> None:
    shared_cache_service._local_ttl.clear()


class LocalTTLCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        _clear_local_cache()

    def test_set_and_get_within_ttl(self) -> None:
        local_cache_set("k", "hello", 60)
        self.assertEqual("hello", local_cache_get("k"))

    def test_get_returns_none_for_missing_key(self) -> None:
        self.assertIsNone(local_cache_get("no_such_key"))

    def test_get_returns_none_after_expiry(self) -> None:
        with patch("material_ingestion.services.shared_cache_service.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            local_cache_set("k", "val", 10)
            mock_time.monotonic.return_value = 1011.0  # past TTL
            self.assertIsNone(local_cache_get("k"))

    def test_get_returns_value_just_before_expiry(self) -> None:
        with patch("material_ingestion.services.shared_cache_service.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            local_cache_set("k", 42, 10)
            mock_time.monotonic.return_value = 1009.9
            self.assertEqual(42, local_cache_get("k"))

    def test_delete_removes_entry(self) -> None:
        local_cache_set("k", "v", 60)
        local_cache_delete("k")
        self.assertIsNone(local_cache_get("k"))

    def test_invalidate_prefix_removes_matching_keys(self) -> None:
        local_cache_set("foo:a", 1, 60)
        local_cache_set("foo:b", 2, 60)
        local_cache_set("bar:c", 3, 60)
        local_cache_invalidate_prefix("foo:")
        self.assertIsNone(local_cache_get("foo:a"))
        self.assertIsNone(local_cache_get("foo:b"))
        self.assertEqual(3, local_cache_get("bar:c"))

    def test_set_overwrites_existing_entry(self) -> None:
        local_cache_set("k", "first", 60)
        local_cache_set("k", "second", 60)
        self.assertEqual("second", local_cache_get("k"))


class RuntimeConfigCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        _clear_local_cache()
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        RawWebRuntimeConfig.__table__.create(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def _patch(self):
        return patch(
            "material_ingestion.services.web_runtime_config_service.create_session_factory",
            return_value=self.session_factory,
        )

    def _seed(self, key: str, value: str) -> int:
        with self.session_factory() as session:
            row = RawWebRuntimeConfig(config_key=key, config_value=value, enabled=True, note="")
            session.add(row)
            session.commit()
            return int(row.id)

    def test_first_call_hits_db_and_caches(self) -> None:
        self._seed("my_key", "99")
        with self._patch():
            v1 = get_runtime_int_config(key="my_key", default=0)
            v2 = get_runtime_int_config(key="my_key", default=0)
        self.assertEqual(99, v1)
        self.assertEqual(99, v2)

    def test_cached_value_returned_without_db(self) -> None:
        self._seed("my_key", "10")
        with self._patch() as mock_factory:
            get_runtime_int_config(key="my_key", default=0)
            # Update the DB directly — cache should still return the old value
            with self.session_factory() as s:
                s.query(RawWebRuntimeConfig).filter_by(config_key="my_key").update({"config_value": "99"})
                s.commit()
            cached_value = get_runtime_int_config(key="my_key", default=0)
        self.assertEqual(10, cached_value)

    def test_cache_expires_and_re_reads_db(self) -> None:
        self._seed("my_key", "10")
        with self._patch():
            with patch("material_ingestion.services.shared_cache_service.time") as mock_time:
                mock_time.monotonic.return_value = 1000.0
                get_runtime_int_config(key="my_key", default=0)
                # Expire the cache
                mock_time.monotonic.return_value = 1000.0 + 31
                with self.session_factory() as s:
                    s.query(RawWebRuntimeConfig).filter_by(config_key="my_key").update({"config_value": "55"})
                    s.commit()
                refreshed = get_runtime_int_config(key="my_key", default=0)
        self.assertEqual(55, refreshed)

    def test_missing_key_returns_default_and_caches_it(self) -> None:
        with self._patch():
            v = get_runtime_int_config(key="no_such_key", default=42)
        self.assertEqual(42, v)
        # Second call should return cached default without hitting DB
        with self._patch():
            v2 = get_runtime_int_config(key="no_such_key", default=99)
        self.assertEqual(42, v2)

    def test_create_invalidates_cache(self) -> None:
        self._seed("ck", "1")
        with self._patch():
            get_runtime_int_config(key="ck", default=0)  # warm cache
            with self.session_factory() as s:
                s.query(RawWebRuntimeConfig).filter_by(config_key="ck").update({"config_value": "2"})
                s.commit()
            create_runtime_config(config_key="other_key", config_value="5")
            # Cache for "ck" should be invalidated by the create
            v = get_runtime_int_config(key="ck", default=0)
        self.assertEqual(2, v)

    def test_update_invalidates_cache(self) -> None:
        row_id = self._seed("uk", "7")
        with self._patch():
            get_runtime_int_config(key="uk", default=0)
            update_runtime_config(config_id=row_id, config_value="8")
            v = get_runtime_int_config(key="uk", default=0)
        self.assertEqual(8, v)

    def test_delete_invalidates_cache(self) -> None:
        row_id = self._seed("dk", "3")
        with self._patch():
            get_runtime_int_config(key="dk", default=0)
            delete_runtime_config(config_id=row_id)
            v = get_runtime_int_config(key="dk", default=99)
        self.assertEqual(99, v)

    def test_replace_invalidates_cache(self) -> None:
        self._seed("rk", "1")
        with self._patch():
            get_runtime_int_config(key="rk", default=0)
            replace_runtime_configs(rows=[{"config_key": "rk", "config_value": "9", "enabled": True}])
            v = get_runtime_int_config(key="rk", default=0)
        self.assertEqual(9, v)


class EvalRulesCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        _clear_local_cache()
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

    def _seed_minimal_fixture(self) -> None:
        with self.session_factory() as session:
            host = RawWebCrawlHost(hostname="example.com", source_type="seed", discovery_source="t", allowlist_match=True, auto_crawl_enabled=True)
            session.add(host)
            session.flush()
            run = RawWebCrawlRun(run_key="run1", initiator="t", force_refresh=False)
            session.add(run)
            session.flush()
            uri = RawWebUriIdentity(canonical_uri="https://example.com/product/a", normalized_hash="h1", host_id=int(host.id))
            session.add(uri)
            session.flush()
            session.add(RawWebFrontierItem(uri_identity_id=int(uri.id), crawl_run_id=int(run.id), state="completed", priority=10, state_reason_code="head_metadata_success"))
            attempt = RawWebHttpFetchAttempt(uri_identity_id=int(uri.id), crawl_run_id=int(run.id), status_code=200, outcome="success", reason_code="head_metadata_success", requested_url="https://example.com/product/a", final_url="https://example.com/product/a", redirect_count=0)
            session.add(attempt)
            session.flush()
            session.add(RawWebHttpRepresentation(fetch_attempt_id=int(attempt.id), storage_ref="https://example.com/product/a", content_type="text/html", content_language="en", content_disposition="", link=""))
            session.add(RawWebEvaluationRule(action="promote", match_type="contains", pattern="/product", weight=10, enabled=True, priority=1, note=""))
            session.commit()

    def _patches(self):
        return (
            patch("material_ingestion.services.web_crawl_frontier_evaluate_service.create_session_factory", return_value=self.session_factory),
            patch("material_ingestion.services.web_crawl_frontier_evaluate_service.get_runtime_int_config", return_value=6),
        )

    def test_rules_are_cached_after_first_evaluate(self) -> None:
        self._seed_minimal_fixture()
        p1, p2 = self._patches()
        with p1, p2:
            evaluate_frontier_batch(batch_size=10, force=False)
        self.assertIsNotNone(local_cache_get(_EVAL_RULES_CACHE_KEY))

    def test_second_evaluate_uses_cached_rules(self) -> None:
        self._seed_minimal_fixture()
        p1, p2 = self._patches()
        with p1, p2:
            evaluate_frontier_batch(batch_size=10, force=False)
            # Delete rules from DB — second call must still work from cache
            with self.session_factory() as s:
                s.query(RawWebEvaluationRule).delete()
                s.commit()
            # Reset frontier item so it can be re-evaluated
            with self.session_factory() as s:
                s.query(RawWebFrontierItem).update({"state_reason_code": "head_metadata_success"})
                s.query(RawWebCrawlDecision).delete()
                s.commit()
            processed, promoted, _, _ = evaluate_frontier_batch(batch_size=10, force=False)
        # Rules were cached so the item is still promoted despite DB rules being gone
        self.assertEqual(1, processed)
        self.assertEqual(1, promoted)

    def test_rules_cache_expires_and_reloads(self) -> None:
        self._seed_minimal_fixture()
        p1, p2 = self._patches()
        with p1, p2:
            with patch("material_ingestion.services.shared_cache_service.time") as mock_time:
                mock_time.monotonic.return_value = 500.0
                evaluate_frontier_batch(batch_size=10, force=False)
                # Expire the cache
                mock_time.monotonic.return_value = 500.0 + 31
                self.assertIsNone(local_cache_get(_EVAL_RULES_CACHE_KEY))


if __name__ == "__main__":
    unittest.main()
