import unittest
from unittest.mock import patch

from material_ingestion.services.web_discovery_service import run_web_discover_pdfs


class WebCrawlBackwardCompatibilityTest(unittest.TestCase):
    def test_discovery_ignores_crawler_core_persistence_failures(self) -> None:
        class _Args:
            seed_url = "https://example.com"
            ingest_source = "web_discovery"
            ingest_locator = None
            ingest_batch_id = "batch_test"
            orchestration_id = "batch_test"
            max_pages = 1
            cross_domain = False
            output = None

        with (
            patch("material_ingestion.services.web_discovery_service.WebPdfDiscovery") as mock_discovery,
            patch("material_ingestion.services.web_discovery_service.RawWebDbExporter") as mock_exporter,
            patch("material_ingestion.services.web_discovery_service.ensure_uri_identity"),
            patch("material_ingestion.services.web_discovery_service.ensure_orchestration"),
            patch("material_ingestion.services.web_discovery_service.register_discovered_host", return_value=1),
            patch("material_ingestion.services.web_discovery_service.bootstrap_host_policy") as bootstrap_host_policy,
            patch("material_ingestion.services.web_discovery_service.discover_and_persist_host_sitemaps", return_value=0),
            patch("material_ingestion.services.web_discovery_service.register_discovered_uri", side_effect=RuntimeError("boom")),
        ):
            bootstrap_host_policy.return_value.robots_txt = "User-agent: *\nAllow: /"
            bootstrap_host_policy.return_value.fetch_status = "success"
            mock_discovery.return_value.discover.return_value = ([{"url": "https://example.com"}], [], [])
            mock_exporter.return_value.export_pages.return_value = 1
            mock_exporter.return_value.export_page_observations.return_value = 1
            mock_exporter.return_value.export_candidates.return_value = 0
            mock_exporter.return_value.export_fetch_xhr_observations.return_value = 0
            rc = run_web_discover_pdfs(_Args())

        self.assertEqual(0, rc)
