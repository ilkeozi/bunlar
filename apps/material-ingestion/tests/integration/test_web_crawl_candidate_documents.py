import unittest
from unittest.mock import patch

from material_ingestion.services.web_crawl_freshness_service import build_freshness_request


class WebCrawlCandidateDocumentsTest(unittest.TestCase):
    def test_freshness_uses_conditional_headers_when_validators_present(self) -> None:
        decision = build_freshness_request(etag='"abc"', last_modified="Mon, 20 May 2026 10:00:00 GMT")
        self.assertTrue(decision.conditional)
        self.assertIn("If-None-Match", decision.headers)
        self.assertIn("If-Modified-Since", decision.headers)

    def test_force_refresh_disables_conditional_headers(self) -> None:
        decision = build_freshness_request(etag='"abc"', force_refresh=True)
        self.assertFalse(decision.conditional)
        self.assertEqual({}, decision.headers)

    def test_candidate_persistence_path_invoked_from_discovery(self) -> None:
        class _Args:
            seed_url = "https://example.com"
            ingest_source = "web_discovery"
            ingest_locator = None
            ingest_batch_id = "batch_test"
            orchestration_id = "batch_test"
            max_pages = 1
            cross_domain = False
            output = None

        class _Candidate:
            source_page_url = "https://example.com"
            pdf_url = "https://example.com/tds.pdf"
            anchor_text = "TDS"
            score = 8
            reason = "url_pdf_suffix"

        with (
            patch("material_ingestion.services.web_discovery_service.WebPdfDiscovery") as mock_discovery,
            patch("material_ingestion.services.web_discovery_service.RawWebDbExporter") as mock_exporter,
            patch("material_ingestion.services.web_discovery_service.ensure_uri_identity") as ensure_uri_identity,
            patch("material_ingestion.services.web_discovery_service.register_discovered_uri"),
            patch("material_ingestion.services.web_discovery_service.persist_extracted_link"),
            patch("material_ingestion.services.web_discovery_service.persist_candidate_document") as persist_candidate,
            patch("material_ingestion.services.web_discovery_service.persist_structured_data_record") as persist_structured_data,
        ):
            mock_discovery.return_value.discover.return_value = (
                [
                    {
                        "url": "https://example.com",
                        "raw_html": '<script type="application/ld+json">{"@type":"Dataset","name":"TDS"}</script>',
                    }
                ],
                [_Candidate()],
                [],
            )
            mock_exporter.return_value.export_pages.return_value = 1
            mock_exporter.return_value.export_page_observations.return_value = 1
            mock_exporter.return_value.export_candidates.return_value = 1
            mock_exporter.return_value.export_fetch_xhr_observations.return_value = 0
            ensure_uri_identity.return_value.uri_identity_id = 1
            ensure_uri_identity.return_value.canonical_uri = "https://example.com/tds.pdf"

            from material_ingestion.services.web_discovery_service import run_web_discover_pdfs

            rc = run_web_discover_pdfs(_Args())

        self.assertEqual(0, rc)
        persist_candidate.assert_called()
        persist_structured_data.assert_called()
