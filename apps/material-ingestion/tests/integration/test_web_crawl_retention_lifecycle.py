import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from material_ingestion.services.web_crawl_retention_service import (
    apply_decision_event_retention,
    apply_representation_retention,
)


class WebCrawlRetentionLifecycleTest(unittest.TestCase):
    def test_retention_transitions_full_representation_to_metadata_only(self) -> None:
        class _Row:
            def __init__(self):
                self.expires_full_at = datetime(2020, 1, 1, tzinfo=UTC)
                self.storage_ref = "blob/path"
                self.metadata_only_since = None

        row = _Row()

        class _Query:
            def filter(self, *args, **kwargs):
                return self

            def all(self):
                return [row]

        class _Session:
            committed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                return _Query()

            def commit(self):
                self.committed = True

        def _factory():
            return _Session()

        with patch("material_ingestion.services.web_crawl_retention_service.create_session_factory", return_value=_factory):
            moved = apply_representation_retention(now=datetime(2026, 5, 24, tzinfo=UTC))

        self.assertEqual(1, moved)
        self.assertEqual("", row.storage_ref)
        self.assertIsNotNone(row.metadata_only_since)

    def test_decision_event_retention_deletes_old_rows(self) -> None:
        class _DeleteQuery:
            def __init__(self, count: int):
                self._count = count

            def filter(self, *args, **kwargs):
                return self

            def delete(self, synchronize_session=False):
                return self._count

        class _Session:
            committed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                name = getattr(model, "__name__", "")
                if name == "RawWebCrawlDecision":
                    return _DeleteQuery(3)
                if name == "RawWebIngestionEvent":
                    return _DeleteQuery(2)
                return _DeleteQuery(0)

            def commit(self):
                self.committed = True

        session = _Session()

        def _factory():
            return session

        with patch("material_ingestion.services.web_crawl_retention_service.create_session_factory", return_value=_factory):
            deleted_decisions, deleted_events = apply_decision_event_retention(
                decision_retention_days=14,
                event_retention_days=14,
                now=datetime(2026, 5, 24, tzinfo=UTC),
            )

        self.assertEqual(3, deleted_decisions)
        self.assertEqual(2, deleted_events)
        self.assertTrue(session.committed)

    def test_decision_event_retention_skips_commit_when_nothing_deleted(self) -> None:
        class _DeleteQuery:
            def filter(self, *args, **kwargs):
                return self

            def delete(self, synchronize_session=False):
                return 0

        class _Session:
            committed = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                return _DeleteQuery()

            def commit(self):
                self.committed = True

        session = _Session()

        def _factory():
            return session

        with patch("material_ingestion.services.web_crawl_retention_service.create_session_factory", return_value=_factory):
            deleted_decisions, deleted_events = apply_decision_event_retention(
                decision_retention_days=14,
                event_retention_days=14,
                now=datetime(2026, 5, 24, tzinfo=UTC),
            )

        self.assertEqual(0, deleted_decisions)
        self.assertEqual(0, deleted_events)
        self.assertFalse(session.committed)
