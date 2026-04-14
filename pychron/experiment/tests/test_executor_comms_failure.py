import unittest


class _FakeRunSpec:
    def __init__(self) -> None:
        self.state = "measurement"

    def transition(self, action: str, force: bool = False, source: str | None = None) -> None:
        if action == "fail":
            self.state = "failed"


class _FakeRun:
    def __init__(self) -> None:
        self.runid = "10001-01"
        self.uuid = "run-uuid-1"
        self.spec = _FakeRunSpec()


from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.experiment.state_machines import ExecutorController


class _FakeWaitGroup:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class _ExecutorHarness:
    _get_run_subject_id = ExperimentExecutor._get_run_subject_id
    _transition_run_failure = ExperimentExecutor._transition_run_failure
    _handle_device_communication_failure = ExperimentExecutor._handle_device_communication_failure

    def __init__(self) -> None:
        self._controller = ExecutorController(self)
        self.wait_group = _FakeWaitGroup()
        self.alive = True
        self._err_message = ""
        self.warning_messages: list[str] = []
        self.extract_state_changes: list[bool] = []

    def warning(self, msg: str) -> None:
        self.warning_messages.append(msg)

    def set_extract_state(self, state, *args, **kw) -> None:
        self.extract_state_changes.append(state)

    def current_terminal_result(self) -> str:
        return self._controller.queue_terminal_result(self._err_message or None)


class ExperimentExecutorCommsFailureTestCase(unittest.TestCase):
    def _make_executor(self) -> _ExecutorHarness:
        executor = _ExecutorHarness()
        executor._controller.execute()
        executor._controller.precheck_passed()
        executor._controller.init_queue("queue-1")
        executor._controller.start_queue()
        return executor

    def test_handle_device_communication_failure_marks_execution_failed(self) -> None:
        executor = self._make_executor()
        run = _FakeRun()
        run_id = run.uuid
        executor._controller.begin_run(run_id, queue_name="queue-1")
        executor._controller.mark_run_started(run_id, queue_name="queue-1")
        executor._controller.start_run_measurement(run_id)

        result = executor._handle_device_communication_failure(
            "Communication failure: spectrometer unavailable", run=run
        )

        self.assertFalse(result)
        self.assertFalse(executor.alive)
        self.assertEqual(executor._err_message, "Communication failure: spectrometer unavailable")
        self.assertEqual(executor.current_terminal_result(), "failed")
        self.assertEqual(
            executor._controller.failure_reason, "Communication failure: spectrometer unavailable"
        )
        self.assertEqual(run.spec.state, "failed")
        self.assertFalse(executor._controller.should_save_run(run.spec.state, False))


if __name__ == "__main__":
    unittest.main()
