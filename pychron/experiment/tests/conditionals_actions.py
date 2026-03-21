import unittest

try:
    from pychron.experiment.automated_run.spec import AutomatedRunSpec, MEASUREMENT
    from pychron.experiment.conditional.conditional import (
        QueueModificationConditional,
    )
except ModuleNotFoundError as exc:
    AutomatedRunSpec = None
    QueueModificationConditional = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _FakeExecutor:
    def __init__(self, queue):
        self.experiment_queue = queue
        self.queue_modified = False

    def set_queue_modified(self):
        self.queue_modified = True


class _FakeQueue:
    def __init__(self, runs):
        self.automated_runs = list(runs)
        self.mass_spectrometer = "jan"
        self.extract_device = "Fusions CO2"
        self.username = "test-user"
        self.tray = "221-hole"
        self.load_name = "Load001"
        self.queue_conditionals_name = "default"
        self.repository_identifier = "laboratory"
        self.refresh_table_needed = False
        self.invalidated = False

    @property
    def cleaned_automated_runs(self):
        return [
            run for run in self.automated_runs if not run.skip and run.state == "not run"
        ]

    @property
    def load_holder(self):
        return self.tray

    def sync_queue_meta(self, runs=None, attrs=None, force=False):
        if runs is None:
            runs = self.automated_runs

        for run in runs:
            run.apply_queue_metadata(self, force=force)

    def invalidate_stats(self):
        self.invalidated = True


class _FakeRun:
    def __init__(self, spec, executor):
        self.spec = spec
        self.experiment_executor = executor


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class ConditionalQueueActionTestCase(unittest.TestCase):
    def _make_queue(self, current_labnumber="10000", next_labnumber="10001"):
        current = AutomatedRunSpec(
            labnumber=current_labnumber,
            measurement_script="jan_measure.py",
            extraction_script="jan_extract.py",
        )
        current.mass_spectrometer = "jan"
        current.state = MEASUREMENT

        nxt = AutomatedRunSpec(labnumber=next_labnumber)
        queue = _FakeQueue([current, nxt])
        executor = _FakeExecutor(queue)
        return current, nxt, queue, executor

    def test_repeat_run_inserts_copy_after_current(self):
        current, nxt, queue, executor = self._make_queue()
        cond = QueueModificationConditional(action="Repeat Run")

        changed = cond.do_modifications(_FakeRun(current, executor), executor, queue)

        self.assertIsNone(changed)
        self.assertTrue(executor.queue_modified)
        self.assertTrue(queue.refresh_table_needed)
        self.assertTrue(queue.invalidated)
        self.assertEqual(len(queue.automated_runs), 3)
        inserted = queue.automated_runs[1]
        self.assertEqual(inserted.labnumber, current.labnumber)
        self.assertIsNot(inserted, current)

    def test_run_blank_inserts_blank_reference(self):
        current, nxt, queue, executor = self._make_queue()
        cond = QueueModificationConditional(action="Run Blank")

        cond.do_modifications(_FakeRun(current, executor), executor, queue)

        inserted = queue.automated_runs[1]
        self.assertEqual(inserted.analysis_type, "blank_unknown")
        self.assertEqual(inserted.labnumber, "bu")
        self.assertTrue(inserted.repository_identifier.startswith("jan_blank"))


if __name__ == "__main__":
    unittest.main()
