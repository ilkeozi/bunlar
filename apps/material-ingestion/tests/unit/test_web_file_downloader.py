import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message

from material_ingestion.sources.web.web_file_downloader import WebFileDownloader


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/pdf", status: int = 200):
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class WebFileDownloaderTest(unittest.TestCase):
    @patch("material_ingestion.sources.web.web_file_downloader.urlopen")
    def test_download_pdf_saves_file_and_hash(self, mock_urlopen) -> None:
        body = b"%PDF-1.4 fake pdf body"
        mock_urlopen.return_value = _FakeResponse(body)

        downloader = WebFileDownloader()
        with tempfile.TemporaryDirectory() as tmp:
            result = downloader.download_pdf(
                source_url="https://example.com/files/datasheet.pdf",
                output_root=Path(tmp),
            )

            saved = Path(result.stored_path)
            self.assertTrue(saved.exists())
            self.assertEqual(body, saved.read_bytes())
            self.assertEqual(len(body), result.size_bytes)
            self.assertEqual("application/pdf", result.content_type)
            self.assertTrue(result.stored_path.endswith(".pdf"))

    @patch("material_ingestion.sources.web.web_file_downloader.time.sleep")
    @patch("material_ingestion.sources.web.web_file_downloader.urlopen")
    def test_download_pdf_retries_on_429_then_succeeds(self, mock_urlopen, mock_sleep) -> None:
        body = b"%PDF-1.4 fake pdf body"
        err = HTTPError(
            url="https://example.com/files/datasheet.pdf",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )
        mock_urlopen.side_effect = [err, _FakeResponse(body)]

        downloader = WebFileDownloader(max_retries=2, backoff_base_seconds=0.0, jitter_seconds=0.0)
        with tempfile.TemporaryDirectory() as tmp:
            result = downloader.download_pdf(
                source_url="https://example.com/files/datasheet.pdf",
                output_root=Path(tmp),
            )

        self.assertEqual(2, mock_urlopen.call_count)
        self.assertEqual(1, mock_sleep.call_count)
        self.assertEqual(len(body), result.size_bytes)

    @patch("material_ingestion.sources.web.web_file_downloader.time.sleep")
    @patch("material_ingestion.sources.web.web_file_downloader.urlopen")
    def test_download_pdf_uses_retry_after_header(self, mock_urlopen, mock_sleep) -> None:
        body = b"%PDF-1.4 fake pdf body"
        headers = Message()
        headers["Retry-After"] = "3"
        err = HTTPError(
            url="https://example.com/files/datasheet.pdf",
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=None,
        )
        mock_urlopen.side_effect = [err, _FakeResponse(body)]

        downloader = WebFileDownloader(max_retries=2, backoff_base_seconds=0.1, jitter_seconds=0.0)
        with tempfile.TemporaryDirectory() as tmp:
            downloader.download_pdf(
                source_url="https://example.com/files/datasheet.pdf",
                output_root=Path(tmp),
            )

        self.assertEqual(2, mock_urlopen.call_count)
        self.assertEqual(1, mock_sleep.call_count)
        self.assertGreaterEqual(mock_sleep.call_args[0][0], 3.0)

    @patch("material_ingestion.sources.web.web_file_downloader.urlopen")
    def test_download_pdf_encodes_spaces_in_url(self, mock_urlopen) -> None:
        body = b"%PDF-1.4 fake pdf body"
        mock_urlopen.return_value = _FakeResponse(body)

        downloader = WebFileDownloader()
        with tempfile.TemporaryDirectory() as tmp:
            result = downloader.download_pdf(
                source_url="https://example.com/files/My File.pdf",
                output_root=Path(tmp),
            )

        request_arg = mock_urlopen.call_args[0][0]
        self.assertIn("My%20File.pdf", request_arg.full_url)
        self.assertIn("My%20File.pdf", result.source_url)


if __name__ == "__main__":
    unittest.main()
