import unittest
from unittest.mock import patch

from material_ingestion.services.web_crawl_orchestrator import register_discovered_uri


class WebCrawlFrontierLifecycleTest(unittest.TestCase):
    def test_register_discovered_uri_calls_foundational_services(self) -> None:
        with (
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_orchestration") as ensure_orchestration,
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_uri_identity") as ensure_uri_identity,
            patch("material_ingestion.services.web_crawl_orchestrator.register_discovered_host"),
            patch("material_ingestion.services.web_crawl_orchestrator.is_url_host_allowlisted", return_value=True),
            patch("material_ingestion.services.web_crawl_orchestrator.enqueue_frontier_item") as enqueue_frontier_item,
            patch("material_ingestion.services.web_crawl_orchestrator.record_decision") as record_decision,
        ):
            ensure_orchestration.return_value.crawl_run_id = 11
            ensure_uri_identity.return_value.uri_identity_id = 22
            ensure_uri_identity.return_value.canonical_uri = "https://example.com/a.pdf"
            enqueue_frontier_item.return_value = 33

            frontier_id = register_discovered_uri(run_key="batch_test", observed_uri="https://example.com/a.pdf")

        self.assertEqual(33, frontier_id)
        ensure_orchestration.assert_called_once()
        ensure_uri_identity.assert_called_once()
        enqueue_frontier_item.assert_called_once()
        record_decision.assert_called_once()
