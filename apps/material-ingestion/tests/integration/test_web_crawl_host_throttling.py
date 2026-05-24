import unittest

from material_ingestion.services.web_crawl_scheduler_service import HostThrottleScheduler


class WebCrawlHostThrottlingTest(unittest.TestCase):
    def test_per_host_throttle_cap(self) -> None:
        scheduler = HostThrottleScheduler(per_host_limit=1)
        d1 = scheduler.try_acquire("https://x.example.com/a")
        d2 = scheduler.try_acquire("https://x.example.com/b")
        self.assertTrue(d1.allowed)
        self.assertFalse(d2.allowed)
        self.assertEqual("host_concurrency_limit", d2.reason)
