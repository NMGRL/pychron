"""Test suite for Phase 5 - Integration Features.

Tests for device lifecycle, usage analytics, and registry integration.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from pychron.hardware.device_lifecycle import (
    DeviceVersion,
    VersionStatus,
    DeviceLifecycle,
    LifecycleManager,
)
from pychron.hardware.usage_analytics import (
    DeviceUsageEvent,
    DeviceUsageStats,
    UsageAnalytics,
)
from pychron.hardware.registry_client import RegistryMetadata, SyncResult, RegistryClient


class TestDeviceVersion(unittest.TestCase):
    """Test DeviceVersion class."""

    def setUp(self):
        """Create test version."""
        self.version = DeviceVersion(
            version="1.0.0",
            release_date=datetime.now() - timedelta(days=10),
            status=VersionStatus.CURRENT,
            changelog="Initial release",
            compatible_with=["0.9.0"],
        )

    def test_create_version(self):
        """Test creating a device version."""
        self.assertEqual(self.version.version, "1.0.0")
        self.assertEqual(self.version.status, VersionStatus.CURRENT)

    def test_is_current(self):
        """Test checking if version is current."""
        self.assertTrue(self.version.is_current())

    def test_is_deprecated(self):
        """Test checking if version is deprecated."""
        self.assertFalse(self.version.is_deprecated())

    def test_is_compatible_with(self):
        """Test checking compatibility."""
        self.assertTrue(self.version.is_compatible_with("0.9.0"))
        self.assertFalse(self.version.is_compatible_with("2.0.0"))

    def test_days_since_release(self):
        """Test calculating days since release."""
        days = self.version.days_since_release()
        self.assertGreater(days, 0)
        self.assertLess(days, 30)

    def test_is_recent(self):
        """Test checking if version is recent."""
        self.assertTrue(self.version.is_recent(days=30))
        self.assertFalse(self.version.is_recent(days=5))


class TestDeviceLifecycle(unittest.TestCase):
    """Test DeviceLifecycle class."""

    def setUp(self):
        """Create test lifecycle."""
        self.lifecycle = DeviceLifecycle(device_class="TestDevice")
        v1 = DeviceVersion(
            version="1.0.0",
            release_date=datetime.now() - timedelta(days=30),
            status=VersionStatus.LEGACY,
            changelog="Legacy version",
        )
        v2 = DeviceVersion(
            version="2.0.0",
            release_date=datetime.now() - timedelta(days=10),
            status=VersionStatus.CURRENT,
            changelog="Current version",
            compatible_with=["1.0.0"],
        )
        self.lifecycle.add_version(v1)
        self.lifecycle.add_version(v2)
        self.lifecycle.current_version = "2.0.0"
        self.lifecycle.installed_version = "1.0.0"

    def test_needs_update(self):
        """Test checking if update is needed."""
        self.assertTrue(self.lifecycle.needs_update)

    def test_is_deprecated(self):
        """Test checking if device is deprecated."""
        self.assertFalse(self.lifecycle.is_deprecated)

    def test_latest_version(self):
        """Test getting latest version."""
        latest = self.lifecycle.latest_version
        self.assertIsNotNone(latest)
        self.assertEqual(latest.version, "2.0.0")

    def test_mark_deprecated(self):
        """Test marking device as deprecated."""
        self.lifecycle.mark_deprecated()
        self.assertTrue(self.lifecycle.is_deprecated)

    def test_mark_installed(self):
        """Test marking version as installed."""
        result = self.lifecycle.mark_installed("2.0.0")
        self.assertTrue(result)
        self.assertEqual(self.lifecycle.installed_version, "2.0.0")

    def test_get_update_path(self):
        """Test getting update path."""
        path = self.lifecycle.get_update_path()
        self.assertIsNotNone(path)
        self.assertIn("1.0.0", path)
        self.assertIn("2.0.0", path)


class TestLifecycleManager(unittest.TestCase):
    """Test LifecycleManager class."""

    def setUp(self):
        """Create test manager."""
        self.manager = LifecycleManager()

    def test_register_device(self):
        """Test registering a device."""
        lifecycle = self.manager.register_device("TestDevice")
        self.assertIsNotNone(lifecycle)
        self.assertEqual(lifecycle.device_class, "TestDevice")

    def test_get_lifecycle(self):
        """Test retrieving a lifecycle."""
        self.manager.register_device("TestDevice")
        lifecycle = self.manager.get_lifecycle("TestDevice")
        self.assertIsNotNone(lifecycle)

    def test_add_version(self):
        """Test adding a version."""
        self.manager.register_device("TestDevice")
        version = DeviceVersion(
            version="1.0.0",
            release_date=datetime.now(),
            status=VersionStatus.CURRENT,
            changelog="Initial",
        )
        result = self.manager.add_version("TestDevice", version)
        self.assertTrue(result)

    def test_check_for_updates(self):
        """Test checking for updates."""
        lifecycle = self.manager.register_device("TestDevice")
        v1 = DeviceVersion(
            version="1.0.0",
            release_date=datetime.now(),
            status=VersionStatus.LEGACY,
            changelog="Legacy",
        )
        v2 = DeviceVersion(
            version="2.0.0",
            release_date=datetime.now(),
            status=VersionStatus.CURRENT,
            changelog="Current",
        )
        lifecycle.add_version(v1)
        lifecycle.add_version(v2)
        lifecycle.current_version = "2.0.0"
        lifecycle.installed_version = "1.0.0"

        updates = self.manager.check_for_updates()
        self.assertEqual(len(updates), 1)

    def test_get_deprecated_devices(self):
        """Test getting deprecated devices."""
        lifecycle = self.manager.register_device("TestDevice")
        lifecycle.mark_deprecated()

        deprecated = self.manager.get_deprecated_devices()
        self.assertEqual(len(deprecated), 1)
        self.assertIn("TestDevice", deprecated)

    def test_get_update_statistics(self):
        """Test getting update statistics."""
        self.manager.register_device("Device1")
        self.manager.register_device("Device2")

        stats = self.manager.get_update_statistics()
        self.assertEqual(stats["total_devices"], 2)


class TestDeviceUsageEvent(unittest.TestCase):
    """Test DeviceUsageEvent class."""

    def setUp(self):
        """Create test event."""
        self.event = DeviceUsageEvent(
            device_class="TestDevice",
            timestamp=datetime.now(),
            duration=timedelta(seconds=10),
            success=True,
        )

    def test_create_event(self):
        """Test creating an event."""
        self.assertEqual(self.event.device_class, "TestDevice")
        self.assertTrue(self.event.success)

    def test_to_dict(self):
        """Test converting to dictionary."""
        data = self.event.to_dict()
        self.assertEqual(data["device_class"], "TestDevice")
        self.assertTrue(data["success"])


class TestDeviceUsageStats(unittest.TestCase):
    """Test DeviceUsageStats class."""

    def setUp(self):
        """Create test stats."""
        self.stats = DeviceUsageStats(device_class="TestDevice")
        self.stats.total_runs = 100
        self.stats.successful_runs = 95
        self.stats.total_runtime = timedelta(hours=50)
        self.stats.error_count = 5
        self.stats.error_types = {"timeout": 3, "connection": 2}

    def test_success_rate(self):
        """Test success rate calculation."""
        self.assertAlmostEqual(self.stats.success_rate, 95.0)

    def test_failure_rate(self):
        """Test failure rate calculation."""
        self.assertAlmostEqual(self.stats.failure_rate, 5.0)

    def test_average_runtime(self):
        """Test average runtime calculation."""
        avg = self.stats.average_runtime
        self.assertAlmostEqual(avg.total_seconds(), 1800)  # 50 hours / 100 runs

    def test_reliability_score(self):
        """Test reliability score."""
        self.assertAlmostEqual(self.stats.reliability_score, 95.0)

    def test_to_dict(self):
        """Test converting to dictionary."""
        data = self.stats.to_dict()
        self.assertEqual(data["device_class"], "TestDevice")
        self.assertEqual(data["total_runs"], 100)


class TestUsageAnalytics(unittest.TestCase):
    """Test UsageAnalytics class."""

    def setUp(self):
        """Create test analytics."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.analytics = UsageAnalytics(Path(self.temp_dir.name))

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_record_event_success(self):
        """Test recording a successful event."""
        event = DeviceUsageEvent(
            device_class="TestDevice",
            timestamp=datetime.now(),
            duration=timedelta(seconds=10),
            success=True,
        )
        self.analytics.record_event(event)

        stats = self.analytics.get_device_stats("TestDevice")
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_runs, 1)
        self.assertEqual(stats.successful_runs, 1)

    def test_record_event_failure(self):
        """Test recording a failed event."""
        event = DeviceUsageEvent(
            device_class="TestDevice",
            timestamp=datetime.now(),
            duration=timedelta(seconds=10),
            success=False,
            error_type="timeout",
        )
        self.analytics.record_event(event)

        stats = self.analytics.get_device_stats("TestDevice")
        self.assertEqual(stats.error_count, 1)
        self.assertEqual(stats.error_types["timeout"], 1)

    def test_get_top_devices(self):
        """Test getting top devices."""
        for i in range(3):
            event = DeviceUsageEvent(
                device_class=f"Device{i}",
                timestamp=datetime.now(),
                duration=timedelta(seconds=10 * (i + 1)),
                success=True,
            )
            self.analytics.record_event(event)

        top = self.analytics.get_top_devices(limit=2, by="runs")
        self.assertEqual(len(top), 2)

    def test_get_reliability_report(self):
        """Test getting reliability report."""
        event = DeviceUsageEvent(
            device_class="TestDevice",
            timestamp=datetime.now(),
            duration=timedelta(seconds=10),
            success=True,
        )
        self.analytics.record_event(event)

        report = self.analytics.get_reliability_report()
        self.assertIn("TestDevice", report)
        self.assertEqual(report["TestDevice"], 100.0)

    def test_get_summary_statistics(self):
        """Test getting summary statistics."""
        event = DeviceUsageEvent(
            device_class="TestDevice",
            timestamp=datetime.now(),
            duration=timedelta(seconds=10),
            success=True,
        )
        self.analytics.record_event(event)

        summary = self.analytics.get_summary_statistics()
        self.assertEqual(summary["total_devices"], 1)
        self.assertEqual(summary["total_runs"], 1)


class TestRegistryClient(unittest.TestCase):
    """Test RegistryClient class."""

    def setUp(self):
        """Create test client."""
        self.client = RegistryClient()

    def test_create_client(self):
        """Test creating a registry client."""
        self.assertIsNotNone(self.client)

    def test_is_available(self):
        """Test checking registry availability."""
        available = self.client.is_available()
        self.assertTrue(available)

    def test_fetch_device_metadata(self):
        """Test fetching device metadata."""
        metadata = self.client.fetch_device_metadata("TestDevice")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.class_name, "TestDevice")

    def test_submit_device(self):
        """Test submitting device metadata."""
        device_data = {"manufacturer": "TestMfg", "model": "Model1", "version": "1.0.0"}
        result = self.client.submit_device("TestDevice", device_data)
        self.assertTrue(result)

    def test_get_device_versions(self):
        """Test getting device versions."""
        versions = self.client.get_device_versions("TestDevice")
        self.assertIsNotNone(versions)
        self.assertGreater(len(versions), 0)

    def test_check_updates(self):
        """Test checking for updates."""
        updates = self.client.check_updates()
        self.assertIsNotNone(updates)

    def test_get_similar_devices(self):
        """Test searching for similar devices."""
        similar = self.client.get_similar_devices("TestDevice")
        self.assertIsNotNone(similar)

    def test_clear_cache(self):
        """Test clearing cache."""
        self.client.fetch_device_metadata("TestDevice")
        initial_size = self.client.get_cache_size()
        self.client.clear_cache()
        final_size = self.client.get_cache_size()
        self.assertEqual(final_size, 0)

    def test_export_to_registry_format(self):
        """Test exporting to registry format."""
        entry_data = {
            "class_name": "TestDevice",
            "company": "TestMfg",
            "model": "Model1",
            "description": "Test",
        }
        result = self.client.export_to_registry_format(entry_data)
        self.assertIsNotNone(result)
        self.assertIn("TestDevice", result)


if __name__ == "__main__":
    unittest.main()
