import unittest

try:
    from pychron.experiment.tasks.experiment_editor import ExperimentEditor
except ModuleNotFoundError as exc:
    ExperimentEditor = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _FakeQueue:
    def __init__(self, n):
        self.automated_runs = [object() for _ in range(n)]


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class ExperimentEditorPerformanceTestCase(unittest.TestCase):
    def test_row_titles_disabled_for_large_tables(self):
        editor = ExperimentEditor()
        editor.queue = _FakeQueue(500)
        self.assertFalse(editor._use_row_titles())

    def test_row_titles_enabled_for_smaller_tables(self):
        editor = ExperimentEditor()
        editor.queue = _FakeQueue(25)
        self.assertTrue(editor._use_row_titles())


if __name__ == "__main__":
    unittest.main()
