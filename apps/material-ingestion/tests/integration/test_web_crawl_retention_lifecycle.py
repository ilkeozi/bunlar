import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from material_ingestion.services.web_crawl_retention_service import apply_representation_retention


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
