import unittest

from material_ingestion.sources.web.web_pdf_discovery import WebPdfDiscovery


class WebPdfDiscoveryTest(unittest.TestCase):
    def test_discovers_pdf_candidates_and_respects_same_domain(self) -> None:
        discovery = WebPdfDiscovery()

        pages_by_url = {
            "https://example.com": """
                <html><body>
                  <a href='/docs/tds-a.pdf'>TDS A</a>
                  <a href='https://example.com/catalog'>Catalog</a>
                  <a href='https://other.com/files/x.pdf'>External PDF</a>
                </body></html>
            """,
            "https://example.com/catalog": """
                <html><body>
                  <a href='/downloads/specification-sheet.pdf'>Specification Sheet</a>
                </body></html>
            """,
        }

        def fake_fetch_html(url: str):
            html = pages_by_url.get(url, "")
            return html, 200, "text/html"

        discovery._fetch_html = fake_fetch_html  # type: ignore[method-assign]

        pages, candidates, observations = discovery.discover(seed_url="https://example.com", same_domain_only=True, max_pages=10)

        self.assertEqual(2, len(pages))
        self.assertEqual(0, len(observations))
        urls = [c.pdf_url for c in candidates]
        self.assertIn("https://example.com/docs/tds-a.pdf", urls)
        self.assertIn("https://example.com/downloads/specification-sheet.pdf", urls)
        self.assertNotIn("https://other.com/files/x.pdf", urls)

    def test_allows_cross_domain_when_enabled(self) -> None:
        discovery = WebPdfDiscovery()

        def fake_fetch_html(url: str):
            return (
                "<html><body><a href='https://other.com/files/external.pdf'>External PDF</a></body></html>",
                200,
                "text/html",
            )

        discovery._fetch_html = fake_fetch_html  # type: ignore[method-assign]

        _, candidates, _ = discovery.discover(seed_url="https://example.com", same_domain_only=False, max_pages=5)

        self.assertEqual(1, len(candidates))
        self.assertEqual("https://other.com/files/external.pdf", candidates[0].pdf_url)

    def test_auto_strategy_keeps_html_result_without_js_fallback(self) -> None:
        discovery = WebPdfDiscovery()

        def fake_fetch_html(url: str):
            return (
                "<html><body><a href='/files/tds.pdf'>TDS</a></body></html>",
                200,
                "text/html",
            )

        def fail_if_js_called(_url: str):
            raise AssertionError("JS renderer should not be called when HTML already found candidates")

        discovery._fetch_html = fake_fetch_html  # type: ignore[method-assign]
        discovery._fetch_html_rendered = fail_if_js_called  # type: ignore[method-assign]

        _, candidates, _ = discovery.discover(seed_url="https://example.com", same_domain_only=True, max_pages=5)
        self.assertEqual(1, len(candidates))
        self.assertEqual("https://example.com/files/tds.pdf", candidates[0].pdf_url)

    def test_auto_strategy_falls_back_to_js_when_html_has_no_candidates(self) -> None:
        discovery = WebPdfDiscovery()

        def fake_fetch_html(_url: str):
            return ("<html><body><a href='/catalog'>Catalog</a></body></html>", 200, "text/html")

        def fake_fetch_html_rendered(_url: str, **_kwargs):
            return ("<html><body><a href='/files/rendered.pdf'>Rendered PDF</a></body></html>", 200, "text/html")

        discovery._fetch_html = fake_fetch_html  # type: ignore[method-assign]
        discovery._fetch_html_rendered = fake_fetch_html_rendered  # type: ignore[method-assign]

        _, candidates, _ = discovery.discover(seed_url="https://example.com", same_domain_only=True, max_pages=5)
        self.assertEqual(1, len(candidates))
        self.assertEqual("https://example.com/files/rendered.pdf", candidates[0].pdf_url)

    def test_extract_urls_from_json_payload(self) -> None:
        payload = {
            "items": [
                {"downloadUrl": "https://cdn.example.com/documents/abc"},
                {"href": "https://cdn.example.com/files/spec.pdf"},
            ],
            "nested": {"text": "mirror https://cdn.example.com/files/spec.pdf and https://a.example.org/dl/123"},
        }
        urls = WebPdfDiscovery._extract_urls_from_json_payload(payload)
        self.assertIn("https://cdn.example.com/documents/abc", urls)
        self.assertIn("https://cdn.example.com/files/spec.pdf", urls)
        self.assertIn("https://a.example.org/dl/123", urls)

    def test_score_pdf_candidate_with_api_marker(self) -> None:
        score, reason = WebPdfDiscovery._score_pdf_candidate(
            "https://cdn.example.com/documents/abc",
            "__api_json_url__",
        )
        self.assertGreater(score, 0)
        self.assertIn("api_json_url", reason)


if __name__ == "__main__":
    unittest.main()
