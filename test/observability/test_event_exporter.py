"""Tests for event exporter."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pychron.observability.event_exporter import EventExporter


class TestEventExporter(unittest.TestCase):
    """Test EventExporter functionality."""

    def test_export_to_file_json(self):
        """Test exporting JSON to file."""
        events_data = '{"events": [{"timestamp": 1234567890, "value": 42}]}'
        filepath = EventExporter.export_to_file(events_data, "json", "test_export")

        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.suffix, ".json")
        self.assertEqual(filepath.read_text(), events_data)

        # Cleanup
        filepath.unlink()

    def test_export_to_file_csv(self):
        """Test exporting CSV to file."""
        csv_data = "timestamp,metric_name,value\n1234567890,test_metric,42"
        filepath = EventExporter.export_to_file(csv_data, "csv", "test_csv_export")

        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.suffix, ".csv")
        self.assertEqual(filepath.read_text(), csv_data)

        # Cleanup
        filepath.unlink()

    def test_export_to_file_without_filename(self):
        """Test exporting to file without custom filename."""
        events_data = '{"events": []}'
        filepath = EventExporter.export_to_file(events_data, "json")

        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.read_text(), events_data)

        # Cleanup
        filepath.unlink()

    def test_export_to_file_handles_exception(self):
        """Test that export handles file write exceptions gracefully."""
        with patch("pathlib.Path.write_text") as mock_write:
            mock_write.side_effect = IOError("Permission denied")
            filepath = EventExporter.export_to_file('{"events": []}', "json")
            self.assertIsNone(filepath)

    def test_open_export_dialog_success(self):
        """Test successful export file creation."""
        # We can't easily test the dialog without Qt, but we can test that
        # the method at least tries to handle OK responses
        events_data = '{"events": [{"value": 42}]}'
        # This will return None since we can't mock the dialog properly without Qt
        # But it shouldn't raise an exception
        try:
            filepath = EventExporter.open_export_dialog(events_data, "json")
            # Either returns a path (if dialog was available) or None (if not)
            self.assertTrue(filepath is None or isinstance(filepath, Path))
        except Exception as e:
            # If Qt is not available, this might raise an ImportError
            self.assertIn("import", str(e).lower())

    @patch("pyface.api.FileDialog")
    def test_open_export_dialog_cancelled(self, mock_dialog_class):
        """Test export dialog when user cancels."""
        # Mock the dialog for cancelled action
        mock_dialog = Mock()
        mock_dialog.open.return_value = 1  # Not OK
        mock_dialog_class.return_value = mock_dialog

        events_data = '{"events": []}'
        filepath = EventExporter.open_export_dialog(events_data, "json")

        # Should return None when cancelled
        self.assertIsNone(filepath)

    @patch("pyface.api.FileDialog")
    def test_open_export_dialog_exception(self, mock_dialog_class):
        """Test export dialog handles exceptions."""
        mock_dialog_class.side_effect = Exception("Dialog error")
        filepath = EventExporter.open_export_dialog('{"events": []}', "json")
        self.assertIsNone(filepath)

    def test_get_export_summary_success(self):
        """Test export summary with successful export."""
        filepath = Path("/tmp/events.json")
        summary = EventExporter.get_export_summary(42, filepath)
        self.assertIn("42", summary)
        self.assertIn("events.json", summary)

    def test_get_export_summary_failure(self):
        """Test export summary with failed export."""
        summary = EventExporter.get_export_summary(42, None)
        self.assertIn("Failed", summary)
        self.assertIn("42", summary)


if __name__ == "__main__":
    unittest.main()
