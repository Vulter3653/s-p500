import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

import pandas as pd

from scripts.download_10k_html import (
    INPUT_RELATIVE,
    MANIFEST_COLUMNS,
    HtmlDownloader,
    archive_url,
    validate_input,
)


class Response:
    status = 200

    def __init__(self, payload=b"<html>filing</html>"):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload

    def getcode(self):
        return self.status


class HtmlDownloadUnitTests(unittest.TestCase):
    def test_final_input_contract(self):
        frame = pd.read_csv(INPUT_RELATIVE, dtype=str, keep_default_na=False)
        validate_input(frame)
        self.assertEqual(len(frame), 100)
        self.assertEqual(frame["accession_number"].nunique(), 100)

    def test_archive_url(self):
        self.assertEqual(
            archive_url("0000049826", "0000049826-26-000008", "itw-20251231.htm"),
            "https://www.sec.gov/Archives/edgar/data/49826/000004982626000008/itw-20251231.htm",
        )

    def test_log_does_not_store_user_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / "log.jsonl"
            downloader = HtmlDownloader(
                user_agent="Unit Test test@example.invalid",
                log_path=log,
                opener=lambda *_args, **_kwargs: Response(),
                sleeper=lambda _delay: None,
            )
            payload, status, _ = downloader.download("https://www.sec.gov/test.htm")
            self.assertTrue(payload)
            self.assertEqual(status, 200)
            record = json.loads(log.read_text())
            self.assertEqual(
                set(record), {"url", "start_time", "end_time", "status_code", "retry"}
            )
            self.assertNotIn("Unit Test", log.read_text())

    def test_retryable_http_status_retries_with_backoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            calls = []

            def opener(request, timeout):
                calls.append((request.full_url, timeout))
                if len(calls) == 1:
                    raise HTTPError(request.full_url, 429, "retry", {}, None)
                return Response()

            downloader = HtmlDownloader(
                user_agent="Unit Test test@example.invalid",
                log_path=Path(temporary) / "log.jsonl",
                opener=opener,
                sleeper=lambda _delay: None,
            )
            payload, status, _ = downloader.download("https://www.sec.gov/test.htm")
            self.assertTrue(payload)
            self.assertEqual(status, 200)
            self.assertEqual(len(calls), 2)
            self.assertEqual(downloader.retry_count, 1)


class HtmlDownloadArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_path = Path("2025/pilot_100/html/manifest/html_manifest.csv")
        if not cls.manifest_path.exists():
            raise unittest.SkipTest("HTML collection artifacts are not present")
        cls.manifest = pd.read_csv(cls.manifest_path, dtype=str, keep_default_na=False)

    def test_manifest_and_html_count(self):
        self.assertEqual(list(self.manifest.columns), MANIFEST_COLUMNS)
        self.assertEqual(len(self.manifest), 100)
        paths = [Path(path) for path in self.manifest["html_path"]]
        self.assertEqual(sum(path.is_file() for path in paths), len(self.manifest))

    def test_sha_size_paths_and_accessions(self):
        self.assertEqual(self.manifest["accession_number"].nunique(), 100)
        self.assertEqual(self.manifest["sha256"].nunique(), 100)
        for row in self.manifest.to_dict("records"):
            path = Path(row["html_path"])
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)
            self.assertEqual(int(row["file_size"]), path.stat().st_size)
            self.assertEqual(
                row["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
