import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from material_ingestion import cli
from material_ingestion.db.models import RawWebDownloadedFile, RawWebPdfCandidate
from material_ingestion.sources.web.web_file_downloader import DownloadedFile
from material_ingestion.sources.web.web_pdf_discovery import PdfCandidate


class WebCliIntegrationTest(unittest.TestCase):
    def test_web_status_command_reports_counts(self) -> None:
        class _Event:
            def __init__(self, id_: int, status: str, event_type: str, error_text: str = ""):
                self.id = id_
                self.status = status
                self.event_type = event_type
                self.error_text = error_text
                self.next_retry_at = None

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def all(self):
                return self.rows

        class _FakeSession:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                return _FakeQuery(
                    [
                        _Event(1, "queued", "discover_requested"),
                        _Event(2, "done", "qualify_requested"),
                        _Event(3, "failed", "download_requested", "boom"),
                    ]
                )

        def _fake_session_factory():
            return _FakeSession()

        with (
            patch("sys.argv", ["cli.py", "web", "status", "--orchestration-id", "orch_1"]),
            patch("material_ingestion.services.web_event_service.create_session_factory", return_value=_fake_session_factory),
        ):
            rc = cli.main()
        self.assertEqual(0, rc)

    def test_discover_pdfs_command_persists_and_writes_output(self) -> None:
        fake_pages = [{"url": "https://example.com", "status_code": 200, "content_type": "text/html", "crawl_ok": True}]
        fake_candidates = [
            PdfCandidate(
                source_page_url="https://example.com",
                pdf_url="https://example.com/tds.pdf",
                anchor_text="TDS",
                score=7,
                reason="url_pdf_suffix,url_keyword",
            )
        ]

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "discovered.json"

            with (
                patch("sys.argv", [
                    "cli.py",
                    "web",
                    "discover-pdfs",
                    "--seed-url",
                    "https://example.com",
                    "--ingest-batch-id",
                    "batch_test_discovery",
                    "--output",
                    str(out),
                ]),
                patch("material_ingestion.services.web_discovery_service.WebPdfDiscovery") as mock_discovery_cls,
                patch("material_ingestion.services.web_discovery_service.RawWebDbExporter") as mock_exporter_cls,
            ):
                mock_discovery = mock_discovery_cls.return_value
                mock_discovery.discover.return_value = (fake_pages, fake_candidates, [])

                mock_exporter = mock_exporter_cls.return_value
                mock_exporter.export_pages.return_value = 1
                mock_exporter.export_candidates.return_value = 1
                mock_exporter.export_fetch_xhr_observations.return_value = 0

                rc = cli.main()

            self.assertEqual(0, rc)
            self.assertTrue(out.exists())
            content = out.read_text(encoding="utf-8")
            self.assertIn("https://example.com/tds.pdf", content)

    def test_fetch_pdfs_command_downloads_and_persists(self) -> None:
        class _FakeCandidate:
            def __init__(self, pdf_url: str, score: int, id_: int):
                self.pdf_url = pdf_url
                self.score = score
                self.id = id_

        fake_candidates = [_FakeCandidate("https://example.com/tds.pdf", 7, 1)]

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def limit(self, *args, **kwargs):
                return self

            def all(self):
                return self.rows

        class _FakeSession:
            def __init__(self, rows):
                self.rows = rows

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                if model is RawWebPdfCandidate:
                    return _FakeQuery(self.rows)
                if model is RawWebDownloadedFile.canonical_source_url:
                    return _FakeQuery([])
                return _FakeQuery([])

        def _fake_session_factory():
            return _FakeSession(fake_candidates)

        downloaded = DownloadedFile(
            source_url="https://example.com/tds.pdf",
            stored_path="data/incoming/web/example.com/fake.pdf",
            sha256="a" * 64,
            size_bytes=123,
            content_type="application/pdf",
            status_code=200,
        )

        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "fetch-pdfs",
                "--ingest-batch-id",
                "batch_test_discovery",
                "--download-batch-id",
                "batch_test_download",
            ]),
            patch("material_ingestion.services.web_qualification_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.WebFileDownloader") as mock_downloader_cls,
            patch("material_ingestion.services.web_download_service.RawWebDbExporter") as mock_exporter_cls,
        ):
            mock_downloader = mock_downloader_cls.return_value
            mock_downloader.download_pdf.return_value = downloaded

            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_downloaded_files.return_value = 1
            mock_exporter.export_fetch_xhr_observations.return_value = 0

            rc = cli.main()

        self.assertEqual(0, rc)

    def test_fetch_pdfs_skips_non_pdf_like_candidates(self) -> None:
        class _FakeCandidate:
            def __init__(self, pdf_url: str, score: int, id_: int, reason: str):
                self.pdf_url = pdf_url
                self.score = score
                self.id = id_
                self.reason = reason
                self.anchor_text = "doc"
                self.source_page_url = "https://example.com"

        fake_candidates = [
            _FakeCandidate("https://example.com/file", 7, 1, "anchor_keyword"),
            _FakeCandidate("https://example.com/spec-sheet", 8, 2, "url_pdf_suffix,anchor_keyword"),
            _FakeCandidate("https://example.com/tds.pdf", 9, 3, "url_pdf_suffix"),
            _FakeCandidate("https://cdn.example.com/documents/12345", 9, 4, "api_json_url,api_document_hint"),
        ]

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def limit(self, *args, **kwargs):
                return self

            def all(self):
                return self.rows

        class _FakeSession:
            def __init__(self, rows):
                self.rows = rows

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def query(self, model):
                if model is RawWebPdfCandidate:
                    return _FakeQuery(self.rows)
                if model is RawWebDownloadedFile.canonical_source_url:
                    return _FakeQuery([])
                return _FakeQuery([])

        def _fake_session_factory():
            return _FakeSession(fake_candidates)

        downloaded = DownloadedFile(
            source_url="https://example.com/tds.pdf",
            stored_path="data/incoming/web/example.com/fake.pdf",
            sha256="a" * 64,
            size_bytes=123,
            content_type="application/pdf",
            status_code=200,
        )

        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "fetch-pdfs",
                "--ingest-batch-id",
                "batch_test_discovery",
                "--download-batch-id",
                "batch_test_download",
            ]),
            patch("material_ingestion.services.web_qualification_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.WebFileDownloader") as mock_downloader_cls,
            patch("material_ingestion.services.web_download_service.RawWebDbExporter") as mock_exporter_cls,
        ):
            mock_downloader = mock_downloader_cls.return_value
            mock_downloader.download_pdf.return_value = downloaded

            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_downloaded_files.return_value = 3
            mock_exporter.export_fetch_xhr_observations.return_value = 0

            rc = cli.main()

        self.assertEqual(0, rc)
        self.assertEqual(3, mock_downloader.download_pdf.call_count)


    def test_fetch_pdfs_uses_deepseek_for_ambiguous_candidates(self) -> None:
        class _FakeCandidate:
            def __init__(self, pdf_url: str, score: int, id_: int, reason: str):
                self.pdf_url = pdf_url
                self.score = score
                self.id = id_
                self.reason = reason
                self.anchor_text = "download"
                self.source_page_url = "https://example.com"

        fake_candidates = [_FakeCandidate("https://example.com/doc/123", 9, 9, "anchor_keyword")]

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return self.rows

        class _FakeSession:
            def __init__(self, rows):
                self.rows = rows
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def query(self, model):
                if model is RawWebPdfCandidate:
                    return _FakeQuery(self.rows)
                if model is RawWebDownloadedFile.canonical_source_url:
                    return _FakeQuery([])
                return _FakeQuery([])

        def _fake_session_factory():
            return _FakeSession(fake_candidates)

        downloaded = DownloadedFile(
            source_url="https://example.com/doc/123",
            stored_path="data/incoming/web/example.com/fake.pdf",
            sha256="a" * 64,
            size_bytes=123,
            content_type="application/pdf",
            status_code=200,
        )

        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "fetch-pdfs",
                "--ingest-batch-id",
                "batch_test_discovery",
                "--download-batch-id",
                "batch_test_download",
            ]),
            patch("material_ingestion.services.web_qualification_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.WebFileDownloader") as mock_downloader_cls,
            patch("material_ingestion.services.web_download_service.RawWebDbExporter") as mock_exporter_cls,
            patch("material_ingestion.services.web_qualification_service.DeepseekPdfClassifier") as mock_classifier_cls,
            patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}, clear=False),
        ):
            mock_downloader = mock_downloader_cls.return_value
            mock_downloader.download_pdf.return_value = downloaded

            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_downloaded_files.return_value = 1

            mock_classifier = mock_classifier_cls.return_value
            mock_classifier.is_likely_pdf.return_value = True

            rc = cli.main()

        self.assertEqual(0, rc)
        self.assertEqual(1, mock_classifier.is_likely_pdf.call_count)
        self.assertEqual(1, mock_downloader.download_pdf.call_count)

    def test_web_run_runs_discovery_then_fetch(self) -> None:
        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "run",
                "--seed-url",
                "https://example.com",
                "--discover-batch-id",
                "batch_discover",
                "--download-batch-id",
                "batch_download",
            ]),
            patch("material_ingestion.services.web_event_service.enqueue_web_event") as mock_enqueue,
            patch("material_ingestion.services.web_event_service.run_web_worker", return_value=0) as mock_run_worker,
        ):
            rc = cli.main()

        self.assertEqual(0, rc)
        self.assertEqual(1, mock_enqueue.call_count)
        self.assertEqual(1, mock_run_worker.call_count)

    def test_web_worker_requeues_stale_events_before_polling(self) -> None:
        with (
            patch("sys.argv", ["cli.py", "web", "worker", "--once"]),
            patch("material_ingestion.services.web_event_service.requeue_stale_running_events", return_value=2) as mock_requeue,
            patch("material_ingestion.services.web_event_service.get_next_queued_web_event", return_value=None),
        ):
            rc = cli.main()
        self.assertEqual(0, rc)
        self.assertEqual(1, mock_requeue.call_count)

    def test_fetch_pdfs_skips_already_downloaded_urls_for_resume(self) -> None:
        class _FakeCandidate:
            def __init__(self, pdf_url: str, score: int, id_: int, reason: str):
                self.pdf_url = pdf_url
                self.score = score
                self.id = id_
                self.reason = reason
                self.anchor_text = "doc"
                self.source_page_url = "https://example.com"

        fake_candidates = [
            _FakeCandidate("https://example.com/a.pdf", 9, 1, "url_pdf_suffix"),
            _FakeCandidate("https://example.com/b.pdf", 8, 2, "url_pdf_suffix"),
        ]
        downloaded_rows = [("https://example.com/a.pdf",)]

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return self.rows

        class _FakeSession:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def query(self, model):
                if model is RawWebPdfCandidate:
                    return _FakeQuery(fake_candidates)
                if model is RawWebDownloadedFile.canonical_source_url:
                    return _FakeQuery(downloaded_rows)
                return _FakeQuery([])

        def _fake_session_factory():
            return _FakeSession()

        downloaded = DownloadedFile(
            source_url="https://example.com/b.pdf",
            stored_path="data/incoming/web/example.com/fake.pdf",
            sha256="a" * 64,
            size_bytes=123,
            content_type="application/pdf",
            status_code=200,
        )

        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "fetch-pdfs",
                "--ingest-batch-id",
                "batch_test_discovery",
                "--download-batch-id",
                "batch_test_download",
            ]),
            patch("material_ingestion.services.web_qualification_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.WebFileDownloader") as mock_downloader_cls,
            patch("material_ingestion.services.web_download_service.RawWebDbExporter") as mock_exporter_cls,
        ):
            mock_downloader = mock_downloader_cls.return_value
            mock_downloader.download_pdf.return_value = downloaded
            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_downloaded_files.return_value = 1
            rc = cli.main()

        self.assertEqual(0, rc)
        self.assertEqual(1, mock_downloader.download_pdf.call_count)

    def test_fetch_pdfs_skips_non_preferred_language_candidates(self) -> None:
        class _FakeCandidate:
            def __init__(self, pdf_url: str, score: int, id_: int, reason: str):
                self.pdf_url = pdf_url
                self.score = score
                self.id = id_
                self.reason = reason
                self.anchor_text = "doc"
                self.source_page_url = "https://example.com"

        fake_candidates = [
            _FakeCandidate("https://download.example.com/en/file-a.pdf", 9, 1, "url_pdf_suffix,lang_en"),
            _FakeCandidate("https://download.example.com/nl/file-b.pdf", 9, 2, "url_pdf_suffix,lang_nl"),
        ]

        class _FakeQuery:
            def __init__(self, rows):
                self.rows = rows
            def filter(self, *args, **kwargs):
                return self
            def order_by(self, *args, **kwargs):
                return self
            def limit(self, *args, **kwargs):
                return self
            def all(self):
                return self.rows

        class _FakeSession:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def query(self, model):
                if model is RawWebPdfCandidate:
                    return _FakeQuery(fake_candidates)
                if model is RawWebDownloadedFile.canonical_source_url:
                    return _FakeQuery([])
                return _FakeQuery([])

        def _fake_session_factory():
            return _FakeSession()

        downloaded = DownloadedFile(
            source_url="https://download.example.com/en/file-a.pdf",
            stored_path="data/incoming/web/example.com/fake.pdf",
            sha256="a" * 64,
            size_bytes=123,
            content_type="application/pdf",
            status_code=200,
        )

        with (
            patch("sys.argv", [
                "cli.py",
                "web",
                "fetch-pdfs",
                "--ingest-batch-id",
                "batch_test_discovery",
                "--download-batch-id",
                "batch_test_download",
            ]),
            patch("material_ingestion.services.web_qualification_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.create_session_factory", return_value=_fake_session_factory),
            patch("material_ingestion.services.web_download_service.WebFileDownloader") as mock_downloader_cls,
            patch("material_ingestion.services.web_download_service.RawWebDbExporter") as mock_exporter_cls,
            patch.dict("os.environ", {"MATERIAL_INGESTION_PREFERRED_LANGUAGES": "en,english"}, clear=False),
        ):
            mock_downloader = mock_downloader_cls.return_value
            mock_downloader.download_pdf.return_value = downloaded
            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_downloaded_files.return_value = 1
            rc = cli.main()

        self.assertEqual(0, rc)
        self.assertEqual(1, mock_downloader.download_pdf.call_count)


if __name__ == "__main__":
    unittest.main()
