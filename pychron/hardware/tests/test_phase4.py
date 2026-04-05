"""Test suite for Phase 4 - Developer Tools & Validation.

Tests for validation dashboard, metadata editor, and driver generation.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from pychron.hardware.validation_reporter import ValidationReport, MetadataValidator
from pychron.hardware.metadata_editor import MetadataEditor, EditSession
from pychron.hardware.driver_generator import DriverSpec, DriverGenerator, DriverWizard


# Mock LibraryEntry for testing
class MockLibraryEntry:
    """Mock LibraryEntry for testing."""

    def __init__(
        self,
        name="TestDevice",
        class_name="TestClass",
        description="Test Description",
        company="TestCo",
        default_comm_type="RS232",
        metadata=None,
    ):
        self.name = name
        self.class_name = class_name
        self.description = description
        self.company = company
        self.default_comm_type = default_comm_type
        self.metadata = metadata or {}
        self.is_complete = all(
            [self.name, self.class_name, self.description, self.company, self.default_comm_type]
        )


class TestValidationReport(unittest.TestCase):
    """Test ValidationReport class."""

    def setUp(self):
        """Create test report."""
        self.report = ValidationReport(
            total_entries=10,
            complete_entries=8,
            incomplete_entries=2,
            missing_fields_by_entry={"Device1": ["docs_url"], "Device2": ["company"]},
        )

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        self.assertAlmostEqual(self.report.completion_percentage, 80.0)

    def test_most_missing_field(self):
        """Test finding most missing field."""
        # Both fields appear once
        self.assertIn(self.report.most_missing_field, ["docs_url", "company"])

    def test_incomplete_entries_sorted(self):
        """Test sorting incomplete entries."""
        sorted_entries = self.report.incomplete_entries_sorted
        self.assertEqual(len(sorted_entries), 2)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        data = self.report.to_dict()
        self.assertEqual(data["total_entries"], 10)
        self.assertEqual(data["complete_entries"], 8)
        self.assertAlmostEqual(data["completion_percentage"], 80.0)

    def test_to_html(self):
        """Test HTML generation."""
        html = self.report.to_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("80.0%", html)
        self.assertIn("Device1", html)

    def test_to_csv(self):
        """Test CSV generation."""
        csv = self.report.to_csv()
        self.assertIn("Entry Name", csv)
        self.assertIn("Device1", csv)
        self.assertIn("docs_url", csv)


class TestMetadataValidator(unittest.TestCase):
    """Test MetadataValidator class."""

    def setUp(self):
        """Create test entries."""
        self.complete_entry = MockLibraryEntry(
            name="CompleteDevice",
            class_name="CompleteClass",
            description="Complete Description",
            company="TestCo",
            default_comm_type="RS232",
        )

        self.incomplete_entry = MockLibraryEntry(
            name="IncompleteDevice",
            class_name="",
            description="Incomplete Description",
            company="TestCo",
            default_comm_type="RS232",
        )

    def test_validate_complete_entry(self):
        """Test validating a complete entry."""
        is_valid, missing = MetadataValidator.validate_entry(self.complete_entry)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_validate_incomplete_entry(self):
        """Test validating an incomplete entry."""
        is_valid, missing = MetadataValidator.validate_entry(self.incomplete_entry)
        self.assertFalse(is_valid)
        self.assertIn("class_name", missing)

    def test_generate_report_empty(self):
        """Test generating report with empty entries."""
        report = MetadataValidator.generate_report([])
        self.assertEqual(report.total_entries, 0)
        self.assertEqual(report.complete_entries, 0)

    def test_generate_report_mixed(self):
        """Test generating report with mixed entries."""
        entries = [self.complete_entry, self.incomplete_entry]
        report = MetadataValidator.generate_report(entries)
        self.assertEqual(report.total_entries, 2)
        self.assertEqual(report.complete_entries, 1)
        self.assertEqual(report.incomplete_entries, 1)

    def test_export_report_html(self):
        """Test exporting report as HTML."""
        report = MetadataValidator.generate_report([self.complete_entry])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report"
            result = MetadataValidator.export_report(report, output_path, format="html")

            self.assertTrue(result)
            self.assertTrue((output_path.parent / "report.html").exists())

    def test_get_missing_fields_summary(self):
        """Test getting missing fields summary."""
        report = MetadataValidator.generate_report([self.incomplete_entry])
        summary = MetadataValidator.get_missing_fields_summary(report)

        self.assertIn("class_name", summary)
        self.assertGreater(summary["class_name"], 0)

    def test_suggest_improvements(self):
        """Test improvement suggestions."""
        # Low completion
        report = ValidationReport(
            total_entries=10, complete_entries=3, incomplete_entries=7, missing_fields_by_entry={}
        )

        suggestions = MetadataValidator.suggest_improvements(report)
        self.assertGreater(len(suggestions), 0)


class TestMetadataEditor(unittest.TestCase):
    """Test MetadataEditor class."""

    def setUp(self):
        """Create test editor and entry."""
        self.editor = MetadataEditor()
        self.entry = MockLibraryEntry()

    def test_begin_edit(self):
        """Test beginning an edit session."""
        session = self.editor.begin_edit(self.entry)
        self.assertIsNotNone(session)
        self.assertEqual(session.entry_name, "TestDevice")

    def test_set_field(self):
        """Test setting a field."""
        self.editor.begin_edit(self.entry)
        result = self.editor.set_field("name", "NewName")
        self.assertTrue(result)
        self.assertEqual(self.editor.get_field("name"), "NewName")

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        self.editor.begin_edit(self.entry)
        self.editor.set_field("name", "")
        is_valid, errors = self.editor.validate()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_cancel_edit(self):
        """Test cancelling edit session."""
        self.editor.begin_edit(self.entry)
        self.editor.set_field("name", "NewName")
        self.editor.cancel_edit()
        self.assertIsNone(self.editor.current_session)

    def test_get_changes_summary(self):
        """Test getting changes summary."""
        self.editor.begin_edit(self.entry)
        self.editor.set_field("name", "NewName")
        summary = self.editor.get_changes_summary()
        self.assertIn("NewName", summary)

    def test_field_display_names(self):
        """Test field display names."""
        display = MetadataEditor.get_field_display_name("vendor_part_number")
        self.assertEqual(display, "Part Number")


class TestDriverSpec(unittest.TestCase):
    """Test DriverSpec class."""

    def setUp(self):
        """Create test spec."""
        self.spec = DriverSpec(
            class_name="TestDriver",
            manufacturer="TestMfg",
            model="Model-X",
            comm_type="RS232",
            description="Test device driver",
        )

    def test_create_spec(self):
        """Test creating a driver spec."""
        self.assertEqual(self.spec.class_name, "TestDriver")
        self.assertEqual(self.spec.manufacturer, "TestMfg")

    def test_is_serial(self):
        """Test serial communication detection."""
        self.assertTrue(self.spec.is_serial())
        self.assertFalse(self.spec.is_tcp())

    def test_is_tcp(self):
        """Test TCP communication detection."""
        tcp_spec = DriverSpec(
            class_name="TcpDriver",
            manufacturer="Mfg",
            model="Model",
            comm_type="TCP",
            description="TCP device",
        )
        self.assertTrue(tcp_spec.is_tcp())
        self.assertFalse(tcp_spec.is_serial())


class TestDriverGenerator(unittest.TestCase):
    """Test DriverGenerator class."""

    def setUp(self):
        """Create test spec."""
        self.spec = DriverSpec(
            class_name="TestDriver",
            manufacturer="TestMfg",
            model="Model-X",
            comm_type="RS232",
            description="Test device driver",
            website="https://example.com",
            docs_url="https://docs.example.com",
        )

    def test_generate_driver_class(self):
        """Test generating driver class code."""
        code = DriverGenerator.generate_driver_class(self.spec)
        self.assertIn("class TestDriver", code)
        self.assertIn("CoreDevice", code)
        self.assertIn("TestMfg", code)

    def test_generate_config_file_serial(self):
        """Test generating config for serial device."""
        config = DriverGenerator.generate_config_file(self.spec, "test_device")
        self.assertIn("[Communications]", config)
        self.assertIn("type = rs232", config)
        self.assertIn("baudrate = 9600", config)

    def test_generate_config_file_tcp(self):
        """Test generating config for TCP device."""
        tcp_spec = DriverSpec(
            class_name="TcpDriver",
            manufacturer="Mfg",
            model="Model",
            comm_type="TCP",
            description="TCP device",
        )
        config = DriverGenerator.generate_config_file(tcp_spec, "test_device")
        self.assertIn("kind = TCP", config)

    def test_generate_test_class(self):
        """Test generating test class."""
        test_code = DriverGenerator.generate_test_class(self.spec)
        self.assertIn("unittest", test_code)
        self.assertIn("TestDriver", test_code)

    def test_generate_readme(self):
        """Test generating README."""
        readme = DriverGenerator.generate_readme(self.spec)
        self.assertIn("TestDriver", readme)
        self.assertIn("TestMfg", readme)
        self.assertIn("https://example.com", readme)


class TestDriverWizard(unittest.TestCase):
    """Test DriverWizard class."""

    def setUp(self):
        """Create test wizard."""
        self.wizard = DriverWizard()

    def test_create_wizard(self):
        """Test creating wizard."""
        self.assertIsNotNone(self.wizard)
        self.assertEqual(self.wizard.current_step, 0)

    def test_step1_basic_info(self):
        """Test wizard step 1."""
        result = self.wizard.step1_basic_info("TestDriver", "Mfg", "Model", "RS232", "Description")
        self.assertTrue(result)
        self.assertIsNotNone(self.wizard.spec)

    def test_step2_communications(self):
        """Test wizard step 2."""
        self.wizard.step1_basic_info("TestDriver", "Mfg", "Model", "RS232", "Description")
        result = self.wizard.step2_communications(
            website="https://example.com", port="COM1", baudrate="9600"
        )
        self.assertTrue(result)
        self.assertEqual(self.wizard.spec.website, "https://example.com")

    def test_wizard_generate_all(self):
        """Test wizard generating all files."""
        self.wizard.step1_basic_info("TestDriver", "Mfg", "Model", "RS232", "Description")
        self.wizard.step2_communications()
        self.wizard.step3_metadata()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = self.wizard.generate_all(output_dir)

            self.assertIn("driver", files)
            self.assertIn("config", files)
            self.assertIn("test", files)
            self.assertIn("readme", files)

            self.assertTrue(files["driver"].exists())
            self.assertTrue(files["config"].exists())


if __name__ == "__main__":
    unittest.main()
