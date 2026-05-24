import argparse
import threading
import time
import unittest
from unittest.mock import patch

from material_ingestion.services.web_event_service import run_web_run
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

    def test_run_web_run_dispatches_workers_concurrently(self) -> None:
        active = 0
        peak = 0
        lock = threading.Lock()

        def _run_worker(_args):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return 0

        args = argparse.Namespace(
            seed_url="https://example.com",
            discover_batch_id="batch_discover_parallel",
            download_batch_id="batch_download_parallel",
            max_pages=1,
            cross_domain=False,
            ingest_source_discovery="web_discovery",
            ingest_source_download="web_download",
            min_score=1,
            limit=10,
            output_root="data/incoming",
            worker_count=3,
            host_allowlist=None,
        )

        with (
            patch("material_ingestion.services.web_event_service.enqueue_web_event"),
            patch("material_ingestion.services.web_event_service.run_web_worker", side_effect=_run_worker),
        ):
            rc = run_web_run(args)

        self.assertEqual(0, rc)
        self.assertGreaterEqual(peak, 2)
