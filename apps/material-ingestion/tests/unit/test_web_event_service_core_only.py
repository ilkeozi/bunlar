import json
import unittest
from unittest.mock import patch

from material_ingestion.services.web_event_service import enqueue_core_discover_event, run_web_event


class WebEventServiceCoreOnlyTest(unittest.TestCase):
    def test_core_discover_requested_enqueues_frontier_build_event(self) -> None:
        class _Event:
            id = 10
            orchestration_id = "batch_core_only"
            event_type = "core_discover_requested"
            payload_json = json.dumps(
                {
                    "seed_url": "https://example.com",
                    "ingest_batch_id": "batch_core_only",
                }
            )

        with (
            patch("material_ingestion.services.web_event_service.run_web_discover_pdfs") as run_discover,
            patch("material_ingestion.services.web_event_service.enqueue_web_event") as enqueue_event,
        ):
            run_web_event(_Event())

        run_discover.assert_called_once()
        enqueue_event.assert_called_once()
        kwargs = enqueue_event.call_args.kwargs
        self.assertEqual("frontier_build_requested", kwargs["event_type"])
        self.assertEqual("batch_core_only", kwargs["orchestration_id"])

    def test_frontier_build_requested_runs_builder(self) -> None:
        class _Event:
            id = 11
            orchestration_id = "batch_core_only"
            event_type = "frontier_build_requested"
            payload_json = json.dumps({"run_key": "batch_core_only", "batch_size": 1000})

        with (
            patch("material_ingestion.services.web_event_service.build_frontier_from_sitemaps", return_value=42) as build_frontier,
            patch("material_ingestion.services.web_event_service.enqueue_web_event") as enqueue_event,
        ):
            run_web_event(_Event())
        build_frontier.assert_called_once()
        enqueue_event.assert_called_once()
        self.assertEqual("frontier_fetch_requested", enqueue_event.call_args.kwargs["event_type"])

    def test_frontier_fetch_requested_runs_fetcher(self) -> None:
        class _Event:
            id = 12
            orchestration_id = "batch_core_only"
            event_type = "frontier_fetch_requested"
            payload_json = json.dumps({"run_key": "batch_core_only", "batch_size": 10})

        with patch("material_ingestion.services.web_event_service.fetch_frontier_batch", return_value=(10, 8, 2)) as fetch_batch:
            run_web_event(_Event())
        fetch_batch.assert_called_once()

    def test_enqueue_core_discover_event_uses_core_event_type(self) -> None:
        with patch("material_ingestion.services.web_event_service.enqueue_web_event", return_value=99) as enqueue_event:
            event_id = enqueue_core_discover_event(run_key="run_1", seed_url="https://example.com")
        self.assertEqual(99, event_id)
        enqueue_event.assert_called_once()
        kwargs = enqueue_event.call_args.kwargs
        self.assertEqual("core_discover_requested", kwargs["event_type"])
        self.assertEqual("run_1", kwargs["orchestration_id"])
