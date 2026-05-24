import unittest
from unittest.mock import patch

from material_ingestion.services.web_crawl_orchestrator import register_discovered_uri


class WebCrawlPolicyDecisionsTest(unittest.TestCase):
    def test_reject_when_host_not_allowlisted(self) -> None:
        with (
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_orchestration") as ensure_orchestration,
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_uri_identity") as ensure_uri_identity,
            patch("material_ingestion.services.web_crawl_orchestrator.register_discovered_host"),
            patch("material_ingestion.services.web_crawl_orchestrator.is_url_host_allowlisted", return_value=False),
            patch("material_ingestion.services.web_crawl_orchestrator.record_decision") as record_decision,
            patch("material_ingestion.services.web_crawl_orchestrator.enqueue_frontier_item") as enqueue_frontier_item,
        ):
            ensure_orchestration.return_value.crawl_run_id = 10
            ensure_uri_identity.return_value.uri_identity_id = 20
            ensure_uri_identity.return_value.canonical_uri = "https://example.com/file.pdf"

            result = register_discovered_uri(run_key="batch_1", observed_uri="https://example.com/file.pdf")

        self.assertEqual(0, result)
        enqueue_frontier_item.assert_not_called()
        record_decision.assert_called_once()

    def test_skip_when_robots_disallow(self) -> None:
        robots_txt = "User-agent: *\nDisallow: /blocked"
        with (
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_orchestration") as ensure_orchestration,
            patch("material_ingestion.services.web_crawl_orchestrator.ensure_uri_identity") as ensure_uri_identity,
            patch("material_ingestion.services.web_crawl_orchestrator.register_discovered_host", return_value=1),
            patch("material_ingestion.services.web_crawl_orchestrator.is_url_host_allowlisted", return_value=True),
            patch("material_ingestion.services.web_crawl_orchestrator.evaluate_and_persist_robots", return_value=False),
            patch("material_ingestion.services.web_crawl_orchestrator.record_decision") as record_decision,
            patch("material_ingestion.services.web_crawl_orchestrator.enqueue_frontier_item") as enqueue_frontier_item,
        ):
            ensure_orchestration.return_value.crawl_run_id = 10
            ensure_uri_identity.return_value.uri_identity_id = 20
            ensure_uri_identity.return_value.canonical_uri = "https://example.com/blocked/file.pdf"

            result = register_discovered_uri(
                run_key="batch_1",
                observed_uri="https://example.com/blocked/file.pdf",
                robots_txt=robots_txt,
            )

        self.assertEqual(0, result)
        enqueue_frontier_item.assert_not_called()
        record_decision.assert_called_once()
