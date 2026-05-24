import unittest

from material_ingestion.services.web_crawl_robots_service import evaluate_robots_allow


class WebCrawlRobotsPolicyTest(unittest.TestCase):
    def test_robots_disallow_is_enforced(self) -> None:
        robots_txt = """
User-agent: *
Disallow: /private
Allow: /
"""
        self.assertFalse(evaluate_robots_allow(robots_txt, "https://example.com/private/a.pdf"))
        self.assertTrue(evaluate_robots_allow(robots_txt, "https://example.com/public/a.pdf"))
