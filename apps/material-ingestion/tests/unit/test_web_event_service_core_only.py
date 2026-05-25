import json
import unittest
from unittest.mock import patch

from material_ingestion.services.web_event_service import run_web_event


class WebEventServiceCoreOnlyTest(unittest.TestCase):
    def test_discover_requested_core_only_does_not_enqueue_qualify_event(self) -> None:
        class _Event:
            id = 10
            orchestration_id = "batch_core_only"
            event_type = "discover_requested"
            payload_json = json.dumps(
                {
                    "seed_url": "https://example.com",
                    "ingest_batch_id": "batch_core_only",
                    "ingest_source_download": "web_download",
                    "download_batch_id": "batch_download",
                    "output_root": "data/incoming/web",
                    "qualify_output_path": "data/working/discovered/qualified_batch_core_only.json",
                    "min_score": 5,
                    "limit": 10,
                    "core_only": True,
                }
            )

        with (
            patch("material_ingestion.services.web_event_service.run_web_discover_pdfs") as run_discover,
            patch("material_ingestion.services.web_event_service.enqueue_web_event") as enqueue_event,
        ):
            run_web_event(_Event())

        run_discover.assert_called_once()
        enqueue_event.assert_not_called()
