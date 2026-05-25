import unittest
from unittest.mock import patch

from material_ingestion.services.web_crawl_policy_runtime_service import (
    discover_and_persist_host_sitemaps,
    extract_sitemap_urls,
    fetch_robots_txt,
)


class WebCrawlPolicyRuntimeServiceTest(unittest.TestCase):
    def test_extract_sitemap_urls_includes_robots_and_default(self) -> None:
        robots_txt = "User-agent: *\nSitemap: https://example.com/sitemap-main.xml\n"
        urls = extract_sitemap_urls(robots_txt=robots_txt, host="example.com")
        self.assertIn("https://example.com/sitemap-main.xml", urls)
        self.assertIn("https://example.com/sitemap.xml", urls)

    def test_fetch_robots_txt_returns_failed_on_errors(self) -> None:
        with patch("material_ingestion.services.web_crawl_policy_runtime_service.urlopen", side_effect=RuntimeError("boom")):
            out = fetch_robots_txt(host="example.com")
        self.assertEqual("failed", out.fetch_status)
        self.assertEqual("", out.robots_txt)

    def test_discover_and_persist_host_sitemaps_recurses_sitemapindex(self) -> None:
        sitemap_index = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/child.xml</loc></sitemap>
</sitemapindex>"""
        child_urlset = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
</urlset>"""
        by_url = {
            "https://example.com/sitemap.xml": sitemap_index,
            "https://example.com/child.xml": child_urlset,
        }

        with (
            patch("material_ingestion.services.web_crawl_policy_runtime_service.fetch_text_url", side_effect=lambda url: by_url[url]),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.persist_sitemap_entries", return_value=1) as persist_entries,
        ):
            inserted = discover_and_persist_host_sitemaps(host_id=1, host="example.com", robots_txt="")

        self.assertEqual(2, inserted)
        self.assertEqual(2, persist_entries.call_count)
