import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.delete_migrated_raw_html_from_r2 import (
    delete_manifest_keys,
    find_remaining_manifest_keys,
    load_and_validate_manifest,
)


class DeleteMigratedRawHtmlFromR2Tests(unittest.TestCase):
    def write_manifest(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "manifest.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["r2_object_key", "migration_status", "verification_status"],
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    @staticmethod
    def valid_row(key):
        return {
            "r2_object_key": key,
            "migration_status": "uploaded",
            "verification_status": "verified_size_and_sha",
        }

    def test_dry_run_validation_does_not_need_client(self):
        keys, summary = load_and_validate_manifest(
            self.write_manifest([self.valid_row("a"), self.valid_row("b")]), 2
        )
        self.assertEqual(keys, ["a", "b"])
        self.assertEqual(summary["eligible_delete_count"], 2)

    def test_expected_count_mismatch_stops(self):
        with self.assertRaisesRegex(ValueError, "expected count"):
            load_and_validate_manifest(self.write_manifest([self.valid_row("a")]), 2)

    def test_duplicate_key_stops(self):
        with self.assertRaisesRegex(ValueError, "duplicate object keys"):
            load_and_validate_manifest(
                self.write_manifest([self.valid_row("a"), self.valid_row("a")]), 2
            )

    def test_blank_key_stops(self):
        with self.assertRaisesRegex(ValueError, "blank object keys"):
            load_and_validate_manifest(self.write_manifest([self.valid_row("")]), 1)

    def test_execute_deletes_only_manifest_keys_in_batches(self):
        client = Mock()
        client.delete_objects.return_value = {}
        keys = [f"key-{index}" for index in range(1001)]
        results, batches = delete_manifest_keys(client, "bucket", keys)
        self.assertEqual(batches, 2)
        self.assertEqual(len(results), 1001)
        sent = [
            item["Key"]
            for call in client.delete_objects.call_args_list
            for item in call.kwargs["Delete"]["Objects"]
        ]
        self.assertEqual(sent, keys)

    def test_batch_api_errors_are_recorded(self):
        client = Mock()
        client.delete_objects.return_value = {
            "Errors": [{"Key": "b", "Code": "AccessDenied", "Message": "denied"}]
        }
        results, batches = delete_manifest_keys(client, "bucket", ["a", "b"])
        self.assertEqual(batches, 1)
        self.assertEqual(sum(row["delete_api_error"] for row in results), 1)
        self.assertEqual(results[1]["error_code"], "AccessDenied")

    def test_absence_check_reports_only_manifest_keys(self):
        client = Mock()
        paginator = Mock()
        paginator.paginate.return_value = [
            {"Contents": [{"Key": "target-a"}, {"Key": "unrelated"}]},
            {"Contents": [{"Key": "target-b"}]},
        ]
        client.get_paginator.return_value = paginator
        remaining = find_remaining_manifest_keys(
            client, "bucket", ["target-a", "target-b", "missing"]
        )
        self.assertEqual(remaining, ["target-a", "target-b"])


if __name__ == "__main__":
    unittest.main()
