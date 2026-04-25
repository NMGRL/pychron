"""Test suite for Phase 3 - Advanced Configuration Features.

Tests for config templates, import/export, and presets functionality.
Covers Phase 3.1 (Templates), 3.2 (Import/Export), and 3.3 (Presets).
"""

import unittest
import tempfile
import json
import zipfile
from pathlib import Path
from datetime import datetime, timedelta

from pychron.hardware.config_template import ConfigTemplate
from pychron.hardware.config_template_manager import ConfigTemplateManager, TemplateSearchResult
from pychron.hardware.config_import_export import ConfigExporter, ConfigImporter, ImportResult
from pychron.hardware.device_preset import DevicePreset, PresetResult
from pychron.hardware.preset_manager import PresetManager


class TestConfigTemplate(unittest.TestCase):
    """Test ConfigTemplate class."""

    def setUp(self):
        """Create test templates."""
        self.template = ConfigTemplate(
            name="test_template",
            device_class="TestDevice",
            comm_type="RS232",
            settings={"General": {"name": "test"}, "Communications": {"port": "COM1"}},
            description="Test template",
        )

    def test_create_template(self):
        """Test creating a config template."""
        self.assertEqual(self.template.name, "test_template")
        self.assertEqual(self.template.device_class, "TestDevice")
        self.assertEqual(self.template.comm_type, "RS232")

    def test_is_compatible_with(self):
        """Test device class compatibility check."""
        self.assertTrue(self.template.is_compatible_with("TestDevice"))
        self.assertFalse(self.template.is_compatible_with("OtherDevice"))

    def test_to_config_content(self):
        """Test generating config content from template."""
        content = self.template.to_config_content("my_device")
        self.assertIn("[General]", content)
        self.assertIn("my_device", content)
        self.assertIn("TestDevice", content)

    def test_to_json_from_json(self):
        """Test JSON serialization."""
        json_str = self.template.to_json()
        restored = ConfigTemplate.from_json(json_str)
        self.assertEqual(restored.name, self.template.name)
        self.assertEqual(restored.device_class, self.template.device_class)

    def test_add_tag(self):
        """Test adding tags."""
        self.template.add_tag("production")
        self.assertTrue(self.template.has_tag("production"))

    def test_remove_tag(self):
        """Test removing tags."""
        self.template.add_tag("test")
        self.template.remove_tag("test")
        self.assertFalse(self.template.has_tag("test"))

    def test_modified_timestamp_updates(self):
        """Test that modified timestamp is updated."""
        original_modified = self.template.modified
        import time

        time.sleep(0.01)
        self.template.add_tag("new_tag")
        self.assertGreater(self.template.modified, original_modified)


class TestConfigTemplateManager(unittest.TestCase):
    """Test ConfigTemplateManager class."""

    def setUp(self):
        """Create temporary directory for templates."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ConfigTemplateManager(Path(self.temp_dir.name))

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_create_manager(self):
        """Test creating a template manager."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(len(self.manager.templates), 0)

    def test_save_and_load_template(self):
        """Test saving and loading templates."""
        template = ConfigTemplate(
            name="saved_template",
            device_class="Device1",
            comm_type="RS232",
            settings={},
            description="Saved test",
        )

        # Save
        self.assertTrue(self.manager.save_template(template))

        # Load
        loaded = self.manager.load_templates()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "saved_template")

    def test_get_template(self):
        """Test retrieving a template by name."""
        template = ConfigTemplate(
            name="retrieve_test",
            device_class="Device2",
            comm_type="TCP",
            settings={},
        )
        self.manager.save_template(template)

        retrieved = self.manager.get_template("retrieve_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "retrieve_test")

    def test_delete_template(self):
        """Test deleting a template."""
        template = ConfigTemplate(
            name="delete_test",
            device_class="Device3",
            comm_type="USB",
            settings={},
        )
        self.manager.save_template(template)
        self.assertTrue(self.manager.delete_template("delete_test"))
        self.assertIsNone(self.manager.get_template("delete_test"))

    def test_get_templates_for_device_class(self):
        """Test filtering templates by device class."""
        t1 = ConfigTemplate(name="t1", device_class="DeviceA", comm_type="RS232", settings={})
        t2 = ConfigTemplate(name="t2", device_class="DeviceB", comm_type="RS232", settings={})
        self.manager.save_template(t1)
        self.manager.save_template(t2)

        results = self.manager.get_templates_for_device_class("DeviceA")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "t1")

    def test_get_templates_for_comm_type(self):
        """Test filtering templates by communication type."""
        t1 = ConfigTemplate(name="t1", device_class="Dev1", comm_type="RS232", settings={})
        t2 = ConfigTemplate(name="t2", device_class="Dev2", comm_type="TCP", settings={})
        self.manager.save_template(t1)
        self.manager.save_template(t2)

        results = self.manager.get_templates_for_comm_type("RS232")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comm_type, "RS232")

    def test_search_templates(self):
        """Test searching templates with multiple criteria."""
        t1 = ConfigTemplate(
            name="production_device",
            device_class="Device1",
            comm_type="RS232",
            settings={},
            description="Production setup",
        )
        t1.add_tag("production")
        self.manager.save_template(t1)

        # Search by name
        result = self.manager.search_templates(query="production")
        self.assertEqual(len(result.templates), 1)

        # Search by device class
        result = self.manager.search_templates(device_class="Device1")
        self.assertEqual(len(result.templates), 1)

        # Search by tag
        result = self.manager.search_templates(tag="production")
        self.assertEqual(len(result.templates), 1)

    def test_rename_template(self):
        """Test renaming a template."""
        template = ConfigTemplate(
            name="old_name", device_class="Device1", comm_type="RS232", settings={}
        )
        self.manager.save_template(template)
        self.assertTrue(self.manager.rename_template("old_name", "new_name"))
        self.assertIsNone(self.manager.get_template("old_name"))
        self.assertIsNotNone(self.manager.get_template("new_name"))

    def test_duplicate_template(self):
        """Test duplicating a template."""
        template = ConfigTemplate(
            name="original", device_class="Device1", comm_type="RS232", settings={}
        )
        self.manager.save_template(template)

        duplicate = self.manager.duplicate_template("original", "duplicate")
        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.name, "duplicate")
        self.assertEqual(duplicate.device_class, "Device1")

    def test_get_statistics(self):
        """Test getting manager statistics."""
        t1 = ConfigTemplate(name="t1", device_class="Dev1", comm_type="RS232", settings={})
        t2 = ConfigTemplate(name="t2", device_class="Dev2", comm_type="TCP", settings={})
        self.manager.save_template(t1)
        self.manager.save_template(t2)

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_templates"], 2)
        self.assertEqual(stats["device_classes"], 2)
        self.assertEqual(stats["comm_types"], 2)


class TestDevicePreset(unittest.TestCase):
    """Test DevicePreset class."""

    def setUp(self):
        """Create test presets."""
        self.preset = DevicePreset(
            name="test_preset",
            lab_name="NMGRL",
            device_configs={"Device1": {"name": "dev1", "General": {}}},
            description="Test preset",
        )

    def test_create_preset(self):
        """Test creating a device preset."""
        self.assertEqual(self.preset.name, "test_preset")
        self.assertEqual(self.preset.lab_name, "NMGRL")

    def test_is_for_lab(self):
        """Test lab membership check."""
        self.assertTrue(self.preset.is_for_lab("NMGRL"))
        self.assertFalse(self.preset.is_for_lab("USGS"))

    def test_has_device_class(self):
        """Test device class membership."""
        self.assertTrue(self.preset.has_device_class("Device1"))
        self.assertFalse(self.preset.has_device_class("Device2"))

    def test_add_device_config(self):
        """Test adding device config to preset."""
        self.preset.add_device_config("Device2", {"name": "dev2"})
        self.assertTrue(self.preset.has_device_class("Device2"))

    def test_remove_device_config(self):
        """Test removing device config from preset."""
        self.assertTrue(self.preset.remove_device_config("Device1"))
        self.assertFalse(self.preset.has_device_class("Device1"))

    def test_get_device_class_list(self):
        """Test getting device class list."""
        self.preset.add_device_config("Device2", {"name": "dev2"})
        classes = self.preset.get_device_class_list()
        self.assertIn("Device1", classes)
        self.assertIn("Device2", classes)

    def test_to_json_from_json(self):
        """Test JSON serialization."""
        json_str = self.preset.to_json()
        restored = DevicePreset.from_json(json_str)
        self.assertEqual(restored.name, self.preset.name)
        self.assertEqual(restored.lab_name, self.preset.lab_name)

    def test_add_and_remove_tags(self):
        """Test tag management."""
        self.preset.add_tag("production")
        self.assertTrue(self.preset.has_tag("production"))
        self.preset.remove_tag("production")
        self.assertFalse(self.preset.has_tag("production"))


class TestPresetManager(unittest.TestCase):
    """Test PresetManager class."""

    def setUp(self):
        """Create temporary directory for presets."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = PresetManager(Path(self.temp_dir.name))

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_create_manager(self):
        """Test creating a preset manager."""
        self.assertIsNotNone(self.manager)

    def test_save_and_load_preset(self):
        """Test saving and loading presets."""
        preset = DevicePreset(
            name="saved_preset",
            lab_name="NMGRL",
            device_configs={},
            description="Saved",
        )
        self.assertTrue(self.manager.save_preset(preset))

        loaded = self.manager.load_presets()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "saved_preset")

    def test_get_presets_for_lab(self):
        """Test filtering presets by lab."""
        p1 = DevicePreset(
            name="nmgrl_preset", lab_name="NMGRL", device_configs={}, description="NMGRL"
        )
        p2 = DevicePreset(
            name="usgs_preset", lab_name="USGS", device_configs={}, description="USGS"
        )
        self.manager.save_preset(p1)
        self.manager.save_preset(p2)

        nmgrl_presets = self.manager.get_presets_for_lab("NMGRL")
        self.assertEqual(len(nmgrl_presets), 1)
        self.assertEqual(nmgrl_presets[0].lab_name, "NMGRL")

    def test_search_presets(self):
        """Test searching presets."""
        preset = DevicePreset(
            name="production_setup",
            lab_name="NMGRL",
            device_configs={},
            description="Production configuration",
        )
        preset.add_tag("production")
        self.manager.save_preset(preset)

        results = self.manager.search_presets(query="production")
        self.assertGreater(len(results), 0)

    def test_get_statistics(self):
        """Test getting preset statistics."""
        p1 = DevicePreset(
            name="p1", lab_name="NMGRL", device_configs={"Dev1": {}}, description="P1"
        )
        p2 = DevicePreset(name="p2", lab_name="USGS", device_configs={"Dev2": {}}, description="P2")
        self.manager.save_preset(p1)
        self.manager.save_preset(p2)

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_presets"], 2)
        self.assertEqual(stats["labs"], 2)


class TestConfigExporter(unittest.TestCase):
    """Test ConfigExporter class."""

    def setUp(self):
        """Create temporary directory for exports."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_export_templates(self):
        """Test exporting templates to ZIP."""
        templates = [
            ConfigTemplate(
                name="t1", device_class="Dev1", comm_type="RS232", settings={}, version="1.0"
            )
        ]

        output_path = Path(self.temp_dir.name) / "templates.zip"
        result = ConfigExporter.export_templates(templates, output_path)

        self.assertTrue(result.success)
        self.assertTrue(output_path.exists())
        self.assertEqual(result.exported_count, 1)


class TestConfigImporter(unittest.TestCase):
    """Test ConfigImporter class."""

    def setUp(self):
        """Create temporary directory for imports."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_validate_config_content(self):
        """Test config validation."""
        valid_config = "[General]\nname = test\n"
        self.assertTrue(ConfigImporter.validate_config_content(valid_config))

    def test_validate_bundle(self):
        """Test bundle validation."""
        # Create a test bundle
        bundle_path = Path(self.temp_dir.name) / "test.zip"
        metadata = {"type": "templates", "count": 0, "templates": []}

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("metadata.json", json.dumps(metadata))

        self.assertTrue(ConfigImporter.validate_bundle(bundle_path, bundle_type="templates"))


if __name__ == "__main__":
    unittest.main()
