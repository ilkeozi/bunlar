import unittest

from material_ingestion.services.web_crawl_worker_service import process_candidate_urls


class WebCrawlParallelWorkersTest(unittest.TestCase):
    def test_process_candidate_urls_prevents_duplicate_active_with_host_limit(self) -> None:
        urls = [
            "https://a.example.com/file1.pdf",
            "https://a.example.com/file2.pdf",
            "https://b.example.com/file3.pdf",
        ]
        accepted, deferred = process_candidate_urls(urls, per_host_limit=1)
        self.assertEqual(2, len(accepted))
        self.assertEqual(1, len(deferred))
