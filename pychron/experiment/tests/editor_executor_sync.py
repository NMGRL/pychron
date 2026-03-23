import unittest

try:
    from pychron.experiment.experiment_executor import ExperimentExecutor
except ModuleNotFoundError as exc:
    ExperimentExecutor = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _FakeStats:
    def __init__(self):
        self.refreshed = False

    def refresh_on_queue_change(self):
        self.refreshed = True


class _FakeQueue:
    def __init__(self):
        self.refresh_table_needed = False
        self.refresh_info_needed = False
        self.selected = []


class _FakeEditor:
    def __init__(self, queue):
        self.queue = queue


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class ExperimentExecutorSyncTestCase(unittest.TestCase):
    def _make_executor(self):
        ex = ExperimentExecutor()
        ex.stats = _FakeStats()
        ex.experiment_queues = []
        return ex

    def test_set_queue_modified_marks_queue_refresh_flags(self):
        ex = self._make_executor()
        queue = _FakeQueue()

        ex.set_queue_modified(queue)

        self.assertTrue(ex.queue_modified)
        self.assertTrue(ex.stats.refreshed)
        self.assertTrue(queue.refresh_table_needed)
        self.assertTrue(queue.refresh_info_needed)

    def test_sync_active_context_updates_selected_run(self):
        ex = self._make_executor()
        queue = _FakeQueue()
        selected = object()
        queue.selected = [selected]
        editor = _FakeEditor(queue)

        ex.sync_active_context(editor=editor, queue=queue, queues=[queue])

        self.assertIs(ex.active_editor, editor)
        self.assertIs(ex.experiment_queue, queue)
        self.assertEqual(ex.experiment_queues, [queue])
        self.assertIs(ex.selected_run, selected)


if __name__ == "__main__":
    unittest.main()
