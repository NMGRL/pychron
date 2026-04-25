"""Tests for metrics exporter."""

import unittest
from unittest.mock import MagicMock, patch

from pychron.observability.config import MetricsConfig
from pychron.observability.exporter import is_exporter_started, start_exporter
from pychron.observability.metrics import configure


class TestExporterDisabled(unittest.TestCase):
    """Test exporter behavior when metrics are disabled."""

    def setUp(self) -> None:
        """Set up test with metrics disabled."""
        configure(MetricsConfig(enabled=False))
        # Reset exporter state
        import pychron.observability.exporter as exporter_module

        exporter_module._exporter_started = False

    def test_exporter_start_is_noop_when_disabled(self) -> None:
        """Test that exporter start is no-op when disabled."""
        result = start_exporter()
        self.assertTrue(result)
        # Exporter should not actually start
        self.assertFalse(is_exporter_started())


class TestExporterEnabled(unittest.TestCase):
    """Test exporter behavior when metrics are enabled."""

    def setUp(self) -> None:
        """Set up test with metrics enabled."""
        configure(MetricsConfig(enabled=True, host="127.0.0.1", port=19109))
        # Reset exporter state
        import pychron.observability.exporter as exporter_module

        exporter_module._exporter_started = False

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Reset exporter state
        import pychron.observability.exporter as exporter_module

        exporter_module._exporter_started = False

    @patch("pychron.observability.exporter.start_http_server")
    def test_exporter_start_successful(self, mock_start: MagicMock) -> None:
        """Test successful exporter start."""
        result = start_exporter()
        self.assertTrue(result)
        self.assertTrue(is_exporter_started())
        mock_start.assert_called_once()

    @patch("pychron.observability.exporter.start_http_server")
    def test_exporter_start_idempotent(self, mock_start: MagicMock) -> None:
        """Test that exporter start is idempotent."""
        result1 = start_exporter()
        result2 = start_exporter()

        self.assertTrue(result1)
        self.assertTrue(result2)
        # start_http_server should only be called once
        mock_start.assert_called_once()

    @patch("pychron.observability.exporter.start_http_server")
    def test_exporter_start_failure_is_handled(self, mock_start: MagicMock) -> None:
        """Test that exporter start failure is handled gracefully."""
        mock_start.side_effect = OSError("Port already in use")

        result = start_exporter()
        self.assertFalse(result)
        # Exporter should not be marked as started
        self.assertFalse(is_exporter_started())

    @patch("pychron.observability.exporter.start_http_server")
    def test_exporter_uses_configured_host_port(self, mock_start: MagicMock) -> None:
        """Test that exporter uses configured host and port."""
        configure(MetricsConfig(enabled=True, host="0.0.0.0", port=8888))

        start_exporter()

        # Verify called with correct parameters
        mock_start.assert_called_once()
        args, kwargs = mock_start.call_args
        self.assertEqual(kwargs.get("port"), 8888)
        self.assertEqual(kwargs.get("addr"), "0.0.0.0")


class TestExporterIntegration(unittest.TestCase):
    """Integration tests for exporter with real registry."""

    def setUp(self) -> None:
        """Set up test with clean state."""
        configure(MetricsConfig(enabled=True, host="127.0.0.1", port=19109))
        import pychron.observability.exporter as exporter_module

        exporter_module._exporter_started = False

    def tearDown(self) -> None:
        """Clean up after tests."""
        import pychron.observability.exporter as exporter_module

        exporter_module._exporter_started = False

    @patch("pychron.observability.exporter.start_http_server")
    def test_exporter_uses_custom_registry(self, mock_start: MagicMock) -> None:
        """Test that exporter uses the custom registry."""
        start_exporter()

        # Verify registry was passed to start_http_server
        args, kwargs = mock_start.call_args
        self.assertIn("registry", kwargs)
        # Registry should not be None
        self.assertIsNotNone(kwargs["registry"])


if __name__ == "__main__":
    unittest.main()
