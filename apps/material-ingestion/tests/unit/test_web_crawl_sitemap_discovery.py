import unittest

from material_ingestion.services.web_crawl_sitemap_service import parse_sitemap_urls


class WebCrawlSitemapDiscoveryTest(unittest.TestCase):
    def test_parse_sitemap_urls_extracts_loc_and_lastmod(self) -> None:
        xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
  <url>
    <loc>https://example.com/a</loc>
    <lastmod>2026-05-01T10:00:00Z</lastmod>
  </url>
  <url>
    <loc>https://example.com/b</loc>
  </url>
</urlset>
"""
        rows = parse_sitemap_urls(xml)
        self.assertEqual(2, len(rows))
        self.assertEqual("https://example.com/a", rows[0][0])
        self.assertIsNotNone(rows[0][1])
        self.assertEqual("https://example.com/b", rows[1][0])
