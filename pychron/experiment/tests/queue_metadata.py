from __future__ import absolute_import

import unittest

from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.queue.experiment_queue import ExperimentQueue


class QueueMetadataPropagationTestCase(unittest.TestCase):
    def setUp(self):
        self.queue = ExperimentQueue()
        self.queue.username = "nmgrl"
        self.queue.mass_spectrometer = "jan"
        self.queue.extract_device = "Fusions CO2"
        self.queue.tray = "221-hole"
        self.queue.load_name = "Load-007"
        self.queue.queue_conditionals_name = "default_conditionals"
        self.queue.repository_identifier = "Repo-1"

    def test_add_runs_applies_missing_queue_metadata(self):
        run = AutomatedRunSpec(labnumber="10001")

        self.queue.add_runs([run])

        self.assertEqual(run.username, "nmgrl")
        self.assertEqual(run.mass_spectrometer, "jan")
        self.assertEqual(run.extract_device, "Fusions CO2")
        self.assertEqual(run.tray, "221-hole")
        self.assertEqual(run.load_holder, "221-hole")
        self.assertEqual(run.load_name, "Load-007")
        self.assertEqual(run.queue_conditionals_name, "default_conditionals")
        self.assertEqual(run.repository_identifier, "Repo-1")

    def test_sync_queue_meta_force_updates_existing_runs(self):
        run = AutomatedRunSpec(
            labnumber="10001",
            username="old-user",
            load_name="old-load",
            queue_conditionals_name="old-conditionals",
            repository_identifier="old-repo",
        )
        self.queue.automated_runs = [run]

        self.queue.username = "new-user"
        self.queue.load_name = "new-load"
        self.queue.queue_conditionals_name = "new-conditionals"
        self.queue.repository_identifier = "new-repo"
        self.queue.tray = "new-tray"
        self.queue.sync_queue_meta(
            attrs=(
                "username",
                "load_name",
                "queue_conditionals_name",
                "repository_identifier",
                "tray",
            ),
            force=True,
        )

        self.assertEqual(run.username, "new-user")
        self.assertEqual(run.load_name, "new-load")
        self.assertEqual(run.queue_conditionals_name, "new-conditionals")
        self.assertEqual(run.repository_identifier, "new-repo")
        self.assertEqual(run.tray, "new-tray")
        self.assertEqual(run.load_holder, "new-tray")


if __name__ == "__main__":
    unittest.main()
