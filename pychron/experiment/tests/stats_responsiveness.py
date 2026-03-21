import unittest

try:
    from pychron.experiment.stats import StatsGroup
except ModuleNotFoundError as exc:
    StatsGroup = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _FakeQueueStats:
    def __init__(self, duration):
        self.duration = duration
        self._dirty = False

    def calculate_duration(self, runs=None):
        return self.duration


class _FakeRun:
    def __init__(self, runid, state="not run", skip=False, executable=True):
        self.runid = runid
        self.state = state
        self.skip = skip
        self.executable = executable
        self._changed = False


class _FakeQueue:
    def __init__(self, duration, runs, delay_before=0, delay_between=0, delay_blank=0, delay_air=0):
        self.stats = _FakeQueueStats(duration)
        self.automated_runs = list(runs)
        self.cleaned_automated_runs = list(runs)
        self.delay_before_analyses = delay_before
        self.delay_between_analyses = delay_between
        self.delay_after_blank = delay_blank
        self.delay_after_air = delay_air


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment stats dependencies not available")
class StatsResponsivenessTestCase(unittest.TestCase):
    def test_recalculate_when_queue_stats_marked_dirty(self):
        queue = _FakeQueue(10, [_FakeRun("a")])
        stats = StatsGroup(experiment_queues=[queue], active_queue=queue)

        stats.calculate(force=True)
        self.assertEqual(stats._total_time, 10)

        queue.stats.duration = 25
        queue.stats._dirty = True
        stats.calculate()

        self.assertEqual(stats._total_time, 25)
        self.assertFalse(queue.stats._dirty)

    def test_recalculate_when_queue_signature_changes(self):
        queue = _FakeQueue(10, [_FakeRun("a")])
        stats = StatsGroup(experiment_queues=[queue], active_queue=queue)

        stats.calculate(force=True)
        self.assertEqual(stats.nruns, 1)

        queue.automated_runs.append(_FakeRun("b"))
        queue.cleaned_automated_runs.append(queue.automated_runs[-1])
        stats.calculate()

        self.assertEqual(stats.nruns, 2)


if __name__ == "__main__":
    unittest.main()
