from __future__ import annotations

import csv
import os
import tempfile
import unittest
from contextlib import contextmanager

from pychron.entry.tasks.sample.importer import SampleImportService


class _SampleRecord:
    pass


class _FakeDVC:
    def __init__(self):
        self.existing = set()

    @contextmanager
    def session_ctx(self, *args, **kw):
        yield

    def get_sample(self, sample, project, pi, material, grainsize=None):
        key = (
            sample.lower(),
            project.lower(),
            pi.lower(),
            material.lower(),
            (grainsize or "").lower(),
        )
        if key in self.existing:
            return _SampleRecord()


class SampleCSVImportTestCase(unittest.TestCase):
    def setUp(self):
        self.dvc = _FakeDVC()
        self.service = SampleImportService(self.dvc)

    def _write_csv(self, headers, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", encoding="utf-8", newline="") as wfile:
            writer = csv.writer(wfile)
            writer.writerow(headers)
            writer.writerows(rows)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_parse_canonical_template_csv(self):
        path = self._write_csv(
            ["sample", "material", "project", "principal_investigator"],
            [["A-1", "Sanidine", "Proj", "Ross"]],
        )
        preview = self.service.preview(path)
        self.assertEqual(preview.row_count, 1)
        self.assertEqual(preview.create_count, 1)

    def test_parse_alias_headers(self):
        path = self._write_csv(
            ["name", "mineral", "project_name", "pi"],
            [["A-1", "Sanidine", "Proj", "Ross"]],
        )
        preview = self.service.preview(path)
        row = preview.rows[0]
        self.assertEqual(row.sample, "A-1")
        self.assertEqual(row.material, "Sanidine")
        self.assertEqual(row.project, "Proj")
        self.assertEqual(row.principal_investigator, "Ross")

    def test_reject_missing_required_fields(self):
        path = self._write_csv(["sample", "material"], [["A-1", "Sanidine"]])
        preview = self.service.preview(path)
        self.assertEqual(preview.error_count, 1)
        self.assertIn("project is required", preview.rows[0].error_messages)

    def test_validate_bad_numeric_values(self):
        path = self._write_csv(
            ["sample", "material", "project", "principal_investigator", "elevation"],
            [["A-1", "Sanidine", "Proj", "Ross", "abc"]],
        )
        preview = self.service.preview(path)
        self.assertEqual(preview.error_count, 1)
        self.assertIn("Elevation must be numeric", preview.rows[0].error_messages)

    def test_convert_valid_utm_inputs(self):
        path = self._write_csv(
            [
                "sample",
                "material",
                "project",
                "principal_investigator",
                "easting",
                "northing",
                "utm",
            ],
            [["A-1", "Sanidine", "Proj", "Ross", "500000", "3873043", "12N"]],
        )
        preview = self.service.preview(path)
        row = preview.rows[0]
        self.assertEqual(preview.create_count, 1)
        self.assertIsNotNone(row.latitude)
        self.assertIsNotNone(row.longitude)

    def test_classify_duplicate_rows_in_file(self):
        path = self._write_csv(
            ["sample", "material", "project", "principal_investigator"],
            [
                ["A-1", "Sanidine", "Proj", "Ross"],
                ["A-1", "Sanidine", "Proj", "Ross"],
            ],
        )
        preview = self.service.preview(path)
        self.assertEqual(preview.error_count, 2)
        self.assertIn("Duplicate sample identity", preview.rows[0].error_messages)

    def test_classify_existing_database_match_as_skip(self):
        self.dvc.existing.add(("a-1", "proj", "ross", "sanidine", ""))
        path = self._write_csv(
            ["sample", "material", "project", "principal_investigator"],
            [["A-1", "Sanidine", "Proj", "Ross"]],
        )
        preview = self.service.preview(path)
        self.assertEqual(preview.skip_count, 1)
        self.assertEqual(preview.rows[0].action, "skip")

    def test_export_error_csv(self):
        path = self._write_csv(["sample", "material"], [["A-1", "Sanidine"]])
        preview = self.service.preview(path)
        fd, export_path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(export_path) and os.remove(export_path))
        self.service.export_rows(export_path, preview.error_rows(), preview.headers)

        with open(export_path, "r", encoding="utf-8") as rfile:
            text = rfile.read()
        self.assertIn("row_action", text)
        self.assertIn("error_messages", text)


if __name__ == "__main__":
    unittest.main()
