import logging
import sys
import tempfile
import types
import unittest

if "yaml" not in sys.modules:
    yaml_stub = types.SimpleNamespace(dump=lambda obj, default_flow_style=False: "")
    sys.modules["yaml"] = yaml_stub

from pychron.core.helpers.logger_setup import (
    PYCHRON_MANAGED_HANDLER,
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


if __name__ == "__main__":
    unittest.main()
