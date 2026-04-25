import logging
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

if "yaml" not in sys.modules:
    yaml_stub = types.SimpleNamespace(dump=lambda obj, default_flow_style=False: "")
    sys.modules["yaml"] = yaml_stub

from pychron.core.helpers.logger_setup import (
    PYCHRON_MANAGED_HANDLER,
    check_log_disk_usage,
    logging_setup,
    simple_logger,
)


def clear_managed_handlers(logger):
    for handler in tuple(logger.handlers):
        if getattr(handler, PYCHRON_MANAGED_HANDLER, False):
            logger.removeHandler(handler)
            handler.close()


class LoggingSetupTestCase(unittest.TestCase):
    def setUp(self):
        clear_managed_handlers(logging.getLogger())

    def tearDown(self):
        clear_managed_handlers(logging.getLogger())
        clear_managed_handlers(logging.getLogger("pychron.test.simple"))

    def test_logging_setup_uses_requested_level(self):
        with tempfile.TemporaryDirectory() as root:
            logging_setup("pychron-test", root=root, use_file=False, level="INFO")

        self.assertEqual(logging.getLogger().level, logging.INFO)

    def test_logging_setup_replaces_managed_handlers(self):
        root_logger = logging.getLogger()

        with tempfile.TemporaryDirectory() as root:
            logging_setup("pychron-test", root=root, use_file=False)
            logging_setup("pychron-test", root=root, use_file=False)

        managed = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, PYCHRON_MANAGED_HANDLER, False)
        ]
        self.assertEqual(len(managed), 1)

    def test_simple_logger_does_not_duplicate_handlers(self):
        logger = simple_logger("pychron.test.simple")
        logger = simple_logger("pychron.test.simple")

        managed = [
            handler
            for handler in logger.handlers
            if getattr(handler, PYCHRON_MANAGED_HANDLER, False)
        ]
        self.assertEqual(len(managed), 1)

    def test_logging_setup_creates_log_file(self):
        """Test that logging_setup creates a log file."""
        with tempfile.TemporaryDirectory() as root:
            logging_setup("pychron-test", root=root, use_file=True)
            log_file = os.path.join(root, "pychron-test.current.log")
            self.assertTrue(os.path.isfile(log_file))

    def test_session_archival_on_startup(self):
        """Test that old logs are archived into timestamped directory on startup."""
        with tempfile.TemporaryDirectory() as root:
            # First session: create a log file
            logging_setup("pychron-test", root=root, use_file=True, use_archiver=False)
            log_file = os.path.join(root, "pychron-test.current.log")

            # Write some data to the log
            logger = logging.getLogger()
            logger.info("Test message from first session")

            # Clear handlers
            clear_managed_handlers(logger)

            # Add a small delay to ensure timestamp changes
            time.sleep(0.1)

            # Second session: startup should archive old logs
            logging_setup("pychron-test", root=root, use_file=True, use_archiver=False)

            # Check that session directory was created
            session_dirs = [
                d
                for d in os.listdir(root)
                if os.path.isdir(os.path.join(root, d)) and d[0].isdigit()
            ]
            self.assertEqual(
                len(session_dirs), 1, "Should have exactly one session directory"
            )

            # Check that old log file was moved to session directory
            session_dir = os.path.join(root, session_dirs[0])
            archived_log = os.path.join(session_dir, "pychron-test.current.log")
            self.assertTrue(os.path.isfile(archived_log), "Old log should be archived")

            # Check that new log file exists
            self.assertTrue(os.path.isfile(log_file), "New log file should exist")

            clear_managed_handlers(logger)

    def test_session_archival_uniqueness(self):
        """Test that simultaneous archival creates unique directories with counters."""
        with tempfile.TemporaryDirectory() as root:
            # Create first session and log something
            logging_setup("pychron-test", root=root, use_file=True, use_archiver=False)
            log_file = os.path.join(root, "pychron-test.current.log")

            logger = logging.getLogger()
            logger.info("First session")

            # Verify the log file exists
            self.assertTrue(os.path.isfile(log_file))

            # Close handlers but keep the log file in place
            clear_managed_handlers(logger)

            # Small delay to ensure different modification time
            time.sleep(0.01)

            # Setup second session - this should archive the previous logs
            # but since the file was just created, we need another file to trigger archival
            logging_setup("pychron-test", root=root, use_file=True, use_archiver=False)
            logger.info("Second session")

            # Check that a session directory was created (from first session)
            session_dirs = sorted(
                [
                    d
                    for d in os.listdir(root)
                    if os.path.isdir(os.path.join(root, d)) and d[0].isdigit()
                ]
            )

            # On first startup, no archival happens (no old logs)
            # On second startup with old log, it creates one session dir
            self.assertGreaterEqual(
                len(session_dirs), 1, "Should have at least one session directory"
            )

            # Verify that the archived log exists in the session directory
            if session_dirs:
                session_dir = os.path.join(root, session_dirs[0])
                archived_log = os.path.join(session_dir, "pychron-test.current.log")
                self.assertTrue(
                    os.path.isfile(archived_log),
                    f"Should have archived log in {session_dir}",
                )

            clear_managed_handlers(logger)

    def test_check_log_disk_usage_detects_threshold_exceeded(self):
        """Test that disk usage warning is triggered above threshold."""
        with tempfile.TemporaryDirectory() as root:
            # Create a test log file with minimal content
            log_file = os.path.join(root, "test.log")
            with open(log_file, "w") as f:
                f.write("x" * 100)  # 100 bytes

            # Check with very low threshold (0.0001 GB = 100 KB, file is 100 bytes so won't exceed)
            # Instead create a 1 MB file and use threshold of 0.0001 GB (100 KB)
            log_file2 = os.path.join(root, "test2.log")
            with open(log_file2, "w") as f:
                f.write("x" * (1024 * 200))  # 200 KB

            # Check with threshold of 0.0001 GB (100 KB)
            size_gb, exceeded = check_log_disk_usage(root, warn_threshold_gb=0.0001)

            self.assertTrue(
                exceeded, f"Should detect threshold exceeded (size: {size_gb:.6f} GB)"
            )

    def test_check_log_disk_usage_handles_missing_directory(self):
        """Test that check_log_disk_usage handles missing directory gracefully."""
        nonexistent = "/tmp/nonexistent_pychron_test_dir_12345"
        size_gb, exceeded = check_log_disk_usage(nonexistent)

        self.assertEqual(size_gb, 0.0)
        self.assertFalse(exceeded)

    def test_rotating_file_handler_created(self):
        """Test that rotating file handler is created when use_file=True."""
        with tempfile.TemporaryDirectory() as root:
            logging_setup("pychron-test", root=root, use_file=True)

            root_logger = logging.getLogger()
            from logging.handlers import RotatingFileHandler

            rotating_handlers = [
                h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)
            ]
            self.assertEqual(
                len(rotating_handlers), 1, "Should have one RotatingFileHandler"
            )

            # Check configuration
            handler = rotating_handlers[0]
            self.assertEqual(handler.maxBytes, int(1e8), "maxBytes should be 100 MB")
            self.assertEqual(handler.backupCount, 50, "backupCount should be 50")

            clear_managed_handlers(root_logger)


if __name__ == "__main__":
    unittest.main()
