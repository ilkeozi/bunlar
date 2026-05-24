import unittest

from material_ingestion.services.web_crawl_identity_service import canonicalize_uri


class WebCrawlUriIdentityTest(unittest.TestCase):
    def test_canonicalize_uri_normalizes_scheme_and_host(self) -> None:
        uri = "HTTP://Example.COM/path//to/file?x=1"
        self.assertEqual("http://example.com/path/to/file?x=1", canonicalize_uri(uri))

    def test_canonicalize_uri_adds_default_path(self) -> None:
        self.assertEqual("https://example.com/", canonicalize_uri("https://example.com"))
