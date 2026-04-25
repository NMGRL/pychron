# ===============================================================================
# Copyright 2024 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

"""
Unit tests for hardware device library discovery and config generation.
"""

import unittest
import tempfile
from pathlib import Path
from unittest import mock

from pychron.hardware.library import (
    LibraryEntry,
    parse_docstring_yaml,
    validate_metadata,
    slugify,
    generate_config_content,
    generate_device_config,
    ConfigGenerationResult,
)


class TestLibraryEntry(unittest.TestCase):
    """Tests for LibraryEntry dataclass."""

    def test_entry_with_complete_metadata(self):
        """Test creating entry with all required metadata."""
        metadata = {
            "name": "Test Device",
            "description": "A test device",
            "company": "Test Corp",
            "docs_url": "https://example.com/docs",
            "website": "https://example.com",
        }
        entry = LibraryEntry(
            class_name="TestClass",
            package="test.module",
            metadata=metadata,
            is_complete=True,
            missing_fields=[],
        )

        self.assertEqual(entry.name, "Test Device")
        self.assertEqual(entry.description, "A test device")
        self.assertEqual(entry.company, "Test Corp")
        self.assertEqual(entry.docs_url, "https://example.com/docs")
        self.assertTrue(entry.is_complete)

    def test_entry_with_incomplete_metadata(self):
        """Test entry with missing required fields."""
        metadata = {"name": "Test Device"}
        entry = LibraryEntry(
            class_name="TestClass",
            package="test.module",
            metadata=metadata,
            is_complete=False,
            missing_fields=["description", "company", "docs_url or website"],
        )

        self.assertFalse(entry.is_complete)
        self.assertEqual(len(entry.missing_fields), 3)

    def test_entry_default_values(self):
        """Test entry defaults to class name and ethernet."""
        entry = LibraryEntry(class_name="MyClass", package="my.package")

        self.assertEqual(entry.name, "MyClass")
        self.assertEqual(entry.default_comm_type, "ethernet")
        self.assertIsNone(entry.model)
        self.assertFalse(entry.is_complete)


class TestParseDocstringYaml(unittest.TestCase):
    """Tests for parse_docstring_yaml function."""

    def test_parse_valid_yaml_metadata(self):
        """Test parsing valid YAML metadata from docstring."""
        docstring = """
        Device description
        
        :::
        name: Test Device
        description: A test device
        company: Test Corp
        website: https://example.com
        """

        result = parse_docstring_yaml(docstring)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Test Device")
        self.assertEqual(result["company"], "Test Corp")

    def test_parse_no_metadata_block(self):
        """Test parsing docstring without ::: marker."""
        docstring = "Just a simple docstring without metadata"

        result = parse_docstring_yaml(docstring)

        self.assertIsNone(result)

    def test_parse_empty_docstring(self):
        """Test parsing empty docstring."""
        result = parse_docstring_yaml("")
        self.assertIsNone(result)

    def test_parse_none_docstring(self):
        """Test parsing None docstring."""
        result = parse_docstring_yaml(None)
        self.assertIsNone(result)

    def test_parse_malformed_yaml(self):
        """Test parsing malformed YAML gracefully returns None."""
        docstring = """
        Device description
        
        :::
        name: Test Device
        invalid: [unclosed
        """

        result = parse_docstring_yaml(docstring)

        self.assertIsNone(result)


class TestValidateMetadata(unittest.TestCase):
    """Tests for validate_metadata function."""

    def test_valid_metadata_with_docs_url(self):
        """Test validation passes with all required fields and docs_url."""
        metadata = {
            "name": "Device",
            "description": "Desc",
            "company": "Corp",
            "docs_url": "https://example.com/docs",
        }

        is_valid, missing = validate_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_valid_metadata_with_website(self):
        """Test validation passes with all required fields and website."""
        metadata = {
            "name": "Device",
            "description": "Desc",
            "company": "Corp",
            "website": "https://example.com",
        }

        is_valid, missing = validate_metadata(metadata)

        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_missing_name(self):
        """Test validation fails when name is missing."""
        metadata = {"description": "Desc", "company": "Corp", "website": "https://example.com"}

        is_valid, missing = validate_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("name", missing)

    def test_missing_link_fields(self):
        """Test validation fails when both docs_url and website are missing."""
        metadata = {"name": "Device", "description": "Desc", "company": "Corp"}

        is_valid, missing = validate_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("docs_url or website", missing)

    def test_empty_required_fields(self):
        """Test validation treats empty strings as missing."""
        metadata = {
            "name": "",
            "description": "Desc",
            "company": "Corp",
            "website": "https://example.com",
        }

        is_valid, missing = validate_metadata(metadata)

        self.assertFalse(is_valid)
        self.assertIn("name", missing)


class TestSlugify(unittest.TestCase):
    """Tests for slugify function."""

    def test_convert_to_lowercase(self):
        """Test slugify converts to lowercase."""
        result = slugify("MyDevice")
        self.assertEqual(result, "mydevice")

    def test_replace_spaces_with_underscore(self):
        """Test slugify replaces spaces with underscore."""
        result = slugify("My Device")
        self.assertEqual(result, "my_device")

    def test_remove_special_characters(self):
        """Test slugify removes special characters."""
        result = slugify("My-Device@123!")
        self.assertEqual(result, "my_device123")

    def test_multiple_spaces_to_single_underscore(self):
        """Test multiple spaces/hyphens become single underscore."""
        result = slugify("My   Device--Name")
        self.assertEqual(result, "my_device_name")


class TestGenerateConfigContent(unittest.TestCase):
    """Tests for generate_config_content function."""

    def setUp(self):
        """Set up test fixtures."""
        self.entry = LibraryEntry(
            class_name="TestDevice",
            package="test.module",
            metadata={"model": "TD-100", "vendor_part_number": "ABC-123"},
        )

    def test_generate_ethernet_config(self):
        """Test config generation for ethernet communication."""
        content = generate_config_content(self.entry, "My Device", "ethernet")

        self.assertIn("[General]", content)
        self.assertIn("[Communications]", content)
        self.assertIn("[Scan]", content)
        self.assertIn("type=ethernet", content)
        self.assertIn("host=localhost", content)
        self.assertIn("port=10001", content)

    def test_generate_serial_config(self):
        """Test config generation for serial communication."""
        content = generate_config_content(self.entry, "My Device", "serial")

        self.assertIn("type=serial", content)
        self.assertIn("port=/dev/ttyS0", content)
        self.assertIn("baudrate=9600", content)

    def test_includes_device_metadata(self):
        """Test config includes device metadata."""
        content = generate_config_content(self.entry, "Test Dev", "ethernet")

        self.assertIn("name=Test Dev", content)
        self.assertIn("klass=TestDevice", content)
        self.assertIn("model=TD-100", content)
        self.assertIn("vendor_part_number=ABC-123", content)

    def test_config_structure(self):
        """Test config has required sections in order."""
        content = generate_config_content(self.entry, "Device", "ethernet")
        lines = content.split("\n")

        general_idx = next(i for i, l in enumerate(lines) if "[General]" in l)
        comm_idx = next(i for i, l in enumerate(lines) if "[Communications]" in l)
        scan_idx = next(i for i, l in enumerate(lines) if "[Scan]" in l)

        self.assertLess(general_idx, comm_idx)
        self.assertLess(comm_idx, scan_idx)


class TestGenerateDeviceConfig(unittest.TestCase):
    """Tests for generate_device_config function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.entry = LibraryEntry(
            class_name="TestDevice",
            package="test.module",
            metadata={"name": "Test Device"},
            is_complete=True,
        )

    def tearDown(self):
        """Clean up temp directory."""
        self.temp_dir.cleanup()

    def test_successful_generation(self):
        """Test successful config generation and file creation."""
        result = generate_device_config(self.entry, "My Device", self.output_dir)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.path)
        self.assertFalse(result.backup_created)
        self.assertIsNone(result.error)

        # Verify file was created
        config_file = Path(result.path)
        self.assertTrue(config_file.exists())
        self.assertIn("My Device", config_file.read_text())

    def test_filename_slugification(self):
        """Test device name is properly slugified in filename."""
        result = generate_device_config(self.entry, "My Test Device", self.output_dir)

        self.assertTrue(result.success)
        config_file = Path(result.path)
        self.assertEqual(config_file.name, "my_test_device.cfg")

    def test_collision_detection_without_overwrite(self):
        """Test collision is detected when file exists and overwrite is False."""
        config_path = self.output_dir / "test_device.cfg"
        config_path.write_text("existing content")

        result = generate_device_config(
            self.entry, "test device", self.output_dir, allow_overwrite=False
        )

        self.assertFalse(result.success)
        self.assertIn("already exists", result.error)

    def test_overwrite_with_backup(self):
        """Test file overwrite creates backup of existing file."""
        config_path = self.output_dir / "test_device.cfg"
        original_content = "original content"
        config_path.write_text(original_content)

        result = generate_device_config(
            self.entry, "test device", self.output_dir, allow_overwrite=True
        )

        self.assertTrue(result.success)
        self.assertTrue(result.backup_created)

        # Verify backup exists
        backup_path = config_path.parent / f"{config_path.name}.backup"
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(), original_content)

        # Verify new content was written
        self.assertNotEqual(config_path.read_text(), original_content)

    def test_creates_output_directory(self):
        """Test output directory is created if it doesn't exist."""
        nested_dir = self.output_dir / "nested" / "devices"

        result = generate_device_config(self.entry, "My Device", nested_dir)

        self.assertTrue(result.success)
        self.assertTrue(nested_dir.exists())

    def test_config_generation_result_repr(self):
        """Test ConfigGenerationResult string representations."""
        result_success = ConfigGenerationResult(
            success=True, path="/path/to/device.cfg", backup_created=True
        )

        self.assertIn("Config generated", str(result_success))
        self.assertIn("backup created", str(result_success))

        result_fail = ConfigGenerationResult(success=False, error="Test error")

        self.assertIn("Generation failed", str(result_fail))
        self.assertIn("Test error", str(result_fail))


if __name__ == "__main__":
    unittest.main()

# ============= EOF =============================================
