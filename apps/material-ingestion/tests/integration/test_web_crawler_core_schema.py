import unittest

from material_ingestion.db.models import (
    RawWebCrawlDecision,
    RawWebCrawlHost,
    RawWebCrawlRun,
    RawWebFrontierItem,
    RawWebUriAlias,
    RawWebUriIdentity,
)


class WebCrawlerCoreSchemaTest(unittest.TestCase):
    def test_models_are_registered(self) -> None:
        self.assertEqual("raw_web_crawl_host", RawWebCrawlHost.__tablename__)
        self.assertEqual("raw_web_uri_identity", RawWebUriIdentity.__tablename__)
        self.assertEqual("raw_web_uri_alias", RawWebUriAlias.__tablename__)
        self.assertEqual("raw_web_crawl_run", RawWebCrawlRun.__tablename__)
        self.assertEqual("raw_web_frontier_item", RawWebFrontierItem.__tablename__)
        self.assertEqual("raw_web_crawl_decision", RawWebCrawlDecision.__tablename__)
