import unittest
from unittest.mock import patch
import logging

from material_ingestion.services.web_crawl_policy_runtime_service import (
    _UspInvalidSitemapCollector,
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
        class _Page:
            def __init__(self, url: str):
                self.url = url

        class _Tree:
            def all_pages(self):
                return [_Page("https://example.com/a"), _Page("https://example.com/b")]

        with (
            patch("material_ingestion.services.web_crawl_policy_runtime_service.has_successful_sitemap_source", return_value=False),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.sitemap_tree_for_homepage", return_value=_Tree()),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.persist_sitemap_urls", return_value=2) as persist_urls,
        ):
            inserted = discover_and_persist_host_sitemaps(host_id=1, host="example.com", robots_txt="")

        self.assertEqual(2, inserted)
        persist_urls.assert_called_once()
        called = persist_urls.call_args.kwargs
        self.assertEqual("usp_homepage_discovery", called["discovered_via"])

    def test_discover_and_persist_host_sitemaps_calls_usp_without_known_paths(self) -> None:
        class _Tree:
            def all_pages(self):
                return []

        with (
            patch("material_ingestion.services.web_crawl_policy_runtime_service.has_successful_sitemap_source", return_value=False),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.sitemap_tree_for_homepage", return_value=_Tree()) as sitemap_tree,
            patch("material_ingestion.services.web_crawl_policy_runtime_service.persist_sitemap_urls", return_value=0),
        ):
            discover_and_persist_host_sitemaps(host_id=1, host="example.com", robots_txt="", max_depth=2, max_sitemaps=3)

        kwargs = sitemap_tree.call_args.kwargs
        self.assertFalse(kwargs["use_known_paths"])
        self.assertTrue(kwargs["use_robots"])

    def test_discover_and_persist_host_sitemaps_excludes_usp_invalid_sitemap_urls(self) -> None:
        class _Page:
            def __init__(self, url: str):
                self.url = url

        class _Tree:
            def all_pages(self):
                return [_Page("https://example.com/a"), _Page("https://example.com/tr/en")]

        def _fake_tree(_homepage: str, **_kwargs):
            logger = logging.getLogger("usp.objects.sitemap")
            logger.warning(
                "Invalid sitemap: https://example.com/tr/en, reason: No parsers support sitemap from https://example.com/tr/en"
            )
            return _Tree()

        with (
            patch("material_ingestion.services.web_crawl_policy_runtime_service.has_successful_sitemap_source", return_value=False),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.sitemap_tree_for_homepage", side_effect=_fake_tree),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.persist_sitemap_urls", return_value=1) as persist_urls,
        ):
            inserted = discover_and_persist_host_sitemaps(host_id=1, host="example.com", robots_txt="")

        self.assertEqual(1, inserted)
        entries = persist_urls.call_args.kwargs["entries"]
        self.assertEqual(["https://example.com/a"], [str(e["url"]) for e in entries])

    def test_usp_invalid_sitemap_collector_parses_invalid_message(self) -> None:
        collector = _UspInvalidSitemapCollector()
        record = logging.LogRecord(
            name="usp.objects.sitemap",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Invalid sitemap: https://example.com/bad, reason: parse error",
            args=(),
            exc_info=None,
        )
        collector.emit(record)
        self.assertIn("https://example.com/bad", collector.invalid_urls)

    def test_discover_and_persist_host_sitemaps_skips_when_already_successful(self) -> None:
        with (
            patch("material_ingestion.services.web_crawl_policy_runtime_service.has_successful_sitemap_source", return_value=True),
            patch("material_ingestion.services.web_crawl_policy_runtime_service.sitemap_tree_for_homepage") as sitemap_tree,
            patch("material_ingestion.services.web_crawl_policy_runtime_service.persist_sitemap_urls") as persist_urls,
        ):
            inserted = discover_and_persist_host_sitemaps(host_id=1, host="example.com", robots_txt="")
        self.assertEqual(0, inserted)
        sitemap_tree.assert_not_called()
        persist_urls.assert_not_called()
