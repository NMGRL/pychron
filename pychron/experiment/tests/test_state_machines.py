import unittest

from pychron.experiment.state_machines.base import BaseStateMachine, TransitionRecord
from pychron.experiment.state_machines.executor_machine import (
    ExecutorStateMachine,
    IDLE,
    PREPARING,
    RUNNING_QUEUE,
    STOPPING_AT_BOUNDARY,
    CANCELING,
    ABORTING,
    FINALIZING,
    COMPLETED,
    FAILED,
    CANCELED,
    ABORTED,
    RECOVERING,
    EXECUTE,
    PRECHECK_PASSED,
    PRECHECK_FAILED,
    QUEUE_FINISHED,
    REQUEST_STOP_AT_BOUNDARY,
    REQUEST_CANCEL,
    REQUEST_ABORT,
    RUN_FAILURE,
    RECOVERY_REQUESTED,
    RECOVERY_COMPLETE,
    FINALIZE_COMPLETE,
    RESET,
)
from pychron.experiment.state_machines.queue_machine import (
    QueueStateMachine,
    QUEUE_IDLE,
    QUEUE_PRECHECK,
    QUEUE_START_DELAY,
    QUEUE_READY_NEXT_RUN,
    QUEUE_PREPARING_RUN,
    QUEUE_RUNNING_SERIAL,
    QUEUE_RUNNING_OVERLAP,
    QUEUE_WAITING_OVERLAP_BOUNDARY,
    QUEUE_WAITING_SAVE,
    QUEUE_SHUTDOWN,
    QUEUE_COMPLETED,
    QUEUE_FAILED,
    QUEUE_CANCELED,
    QUEUE_ABORTED,
    START_QUEUE,
    QUEUE_PRECHECK_PASSED,
    QUEUE_PRECHECK_FAILED,
    START_DELAY_COMPLETE,
    NEXT_RUN_READY,
    RUN_CREATED,
    RUN_TERMINAL,
    SAVE_PENDING,
    SAVE_COMPLETE,
    QUEUE_EMPTY,
    STOP_BOUNDARY_REACHED,
    CANCEL_QUEUE,
    ABORT_QUEUE,
    QUEUE_SHUTDOWN_COMPLETE,
)
from pychron.experiment.state_machines.run_machine import (
    RunStateMachine,
    RUN_IDLE,
    RUN_CREATED,
    RUN_STARTING,
    RUN_PRECHECK,
    RUN_EXTRACTING,
    RUN_WAITING_OVERLAP_SIGNAL,
    RUN_WAITING_MIN_PUMPTIME,
    RUN_MEASURING,
    RUN_POST_MEASUREMENT,
    RUN_SAVING,
    RUN_FINISHING,
    RUN_SUCCESS,
    RUN_FAILED,
    RUN_TRUNCATED,
    RUN_CANCELED,
    RUN_ABORTED,
    RUN_INVALID,
    CREATE,
    START,
    PRECHECK_PASSED as RUN_PRECHECK_PASSED,
    PRECHECK_FAILED as RUN_PRECHECK_FAILED,
    START_EXTRACTION,
    EXTRACTION_COMPLETE,
    EXTRACTION_FAILED,
    WAIT_OVERLAP,
    OVERLAP_SIGNALLED,
    MIN_PUMPTIME_COMPLETE,
    START_MEASUREMENT,
    MEASUREMENT_COMPLETE,
    MEASUREMENT_FAILED,
    START_POST_MEASUREMENT,
    POST_MEASUREMENT_COMPLETE,
    POST_MEASUREMENT_FAILED,
    START_SAVE,
    SAVE_COMPLETE as RUN_SAVE_COMPLETE,
    SAVE_FAILED,
    TRUNCATE,
    CANCEL,
    ABORT,
    MARK_INVALID,
    FINISH,
)


class TestBaseStateMachine(unittest.TestCase):
    def test_transition_record(self):
        record = TransitionRecord(
            old_state="a",
            new_state="b",
            event="go",
            accepted=True,
            source="test",
            reason="because",
            subject_id="sub1",
        )
        self.assertEqual(record.old_state, "a")
        self.assertEqual(record.new_state, "b")
        self.assertTrue(record.accepted)
        self.assertEqual(record.subject_id, "sub1")

    def test_base_machine_transitions(self):
        machine = BaseStateMachine(
            states={"a", "b", "c"},
            terminal_states={"c"},
            transitions={
                "a": {"go": "b"},
                "b": {"finish": "c"},
                "c": {},
            },
            initial_state="a",
            subject_id="test",
        )
        self.assertEqual(machine.observed_state, "a")
        self.assertFalse(machine.is_terminal())

        record = machine.transition("go", source="test")
        self.assertTrue(record.accepted)
        self.assertEqual(machine.observed_state, "b")

        record = machine.transition("finish", source="test")
        self.assertTrue(record.accepted)
        self.assertEqual(machine.observed_state, "c")
        self.assertTrue(machine.is_terminal())

        record = machine.transition("go", source="test")
        self.assertFalse(record.accepted)
        self.assertEqual(machine.observed_state, "c")

    def test_base_machine_force_transition(self):
        machine = BaseStateMachine(
            states={"a", "b"},
            terminal_states=set(),
            transitions={"a": {}, "b": {}},
            initial_state="a",
        )
        record = machine.transition("go", force=True, source="test")
        self.assertFalse(record.accepted)

    def test_base_machine_guards(self):
        machine = BaseStateMachine(
            states={"a", "b"},
            terminal_states=set(),
            transitions={"a": {"go": "b"}},
            initial_state="a",
        )
        machine.register_guard("go", lambda: False)
        record = machine.transition("go", source="test")
        self.assertFalse(record.accepted)
        self.assertEqual(machine.observed_state, "a")

        machine.register_guard("go", lambda: True)
        record = machine.transition("go", source="test")
        self.assertTrue(record.accepted)
        self.assertEqual(machine.observed_state, "b")

    def test_base_machine_history(self):
        machine = BaseStateMachine(
            states={"a", "b"},
            terminal_states=set(),
            transitions={"a": {"go": "b"}},
            initial_state="a",
        )
        machine.transition("go", source="test")
        machine.transition("go", source="test2")
        self.assertEqual(len(machine.history), 2)
        self.assertEqual(machine.history[0].new_state, "b")
        self.assertEqual(machine.history[1].accepted, False)

    def test_base_machine_reset(self):
        machine = BaseStateMachine(
            states={"a", "b"},
            terminal_states=set(),
            transitions={"a": {"go": "b"}, "__initial__": "a"},
            initial_state="a",
        )
        machine.transition("go", source="test")
        self.assertEqual(machine.observed_state, "b")
        machine.reset()
        self.assertEqual(machine.observed_state, "a")
        self.assertEqual(len(machine.history), 0)

    def test_set_observed_state(self):
        machine = BaseStateMachine(
            states={"a", "b"},
            terminal_states=set(),
            transitions={"a": {"go": "b"}},
            initial_state="a",
        )
        record = machine.set_observed_state("b", source="direct", reason="test")
        self.assertEqual(machine.observed_state, "b")
        self.assertTrue(record.accepted)


class TestExecutorStateMachine(unittest.TestCase):
    def test_initial_state(self):
        machine = ExecutorStateMachine()
        self.assertEqual(machine.observed_state, IDLE)
        self.assertTrue(machine.can_execute())

    def test_nominal_path(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        self.assertEqual(machine.observed_state, PREPARING)
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertEqual(machine.observed_state, RUNNING_QUEUE)
        machine.transition(QUEUE_FINISHED, source="test")
        self.assertEqual(machine.observed_state, FINALIZING)
        machine.transition(FINALIZE_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, COMPLETED)
        self.assertTrue(machine.is_terminal)

    def test_precheck_failure_path(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_FAILED, source="test")
        self.assertEqual(machine.observed_state, FINALIZING)

    def test_stop_at_boundary(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertEqual(machine.observed_state, RUNNING_QUEUE)
        machine.transition(REQUEST_STOP_AT_BOUNDARY, source="test")
        self.assertEqual(machine.observed_state, STOPPING_AT_BOUNDARY)

    def test_cancel_from_running(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(REQUEST_CANCEL, source="test")
        self.assertEqual(machine.observed_state, CANCELING)

    def test_abort_from_running(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(REQUEST_ABORT, source="test")
        self.assertEqual(machine.observed_state, ABORTING)

    def test_run_failure_goes_to_finalizing(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(RUN_FAILURE, source="test", reason="step failed")
        self.assertEqual(machine.observed_state, FINALIZING)

    def test_recovery_path(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(RUN_FAILURE, source="test")
        machine.transition(FINALIZE_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, COMPLETED)
        machine.finalize_with_result("failed")
        machine.transition(RECOVERY_REQUESTED, source="test")
        self.assertEqual(machine.observed_state, RECOVERING)
        machine.transition(RECOVERY_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, PREPARING)

    def test_reset_from_terminal(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(QUEUE_FINISHED, source="test")
        machine.transition(FINALIZE_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, COMPLETED)
        machine.transition(RESET, source="test")
        self.assertEqual(machine.observed_state, IDLE)

    def test_is_alive_derived(self):
        machine = ExecutorStateMachine()
        self.assertFalse(machine.is_alive)
        machine.transition(EXECUTE, source="test")
        self.assertTrue(machine.is_alive)
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertTrue(machine.is_alive)
        machine.transition(QUEUE_FINISHED, source="test")
        machine.transition(FINALIZE_COMPLETE, source="test")
        self.assertFalse(machine.is_alive)

    def test_cancel_from_preparing(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        self.assertEqual(machine.observed_state, PREPARING)
        machine.transition(REQUEST_CANCEL, source="test")
        self.assertEqual(machine.observed_state, CANCELING)

    def test_abort_from_preparing(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(REQUEST_ABORT, source="test")
        self.assertEqual(machine.observed_state, ABORTING)

    def test_is_alive_false_in_canceling_state(self):
        """is_alive should return False when canceling to stop queue immediately"""
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertTrue(machine.is_alive)
        machine.transition(REQUEST_CANCEL, source="test")
        self.assertEqual(machine.observed_state, CANCELING)
        self.assertFalse(machine.is_alive)

    def test_is_alive_false_in_aborting_state(self):
        """is_alive should return False when aborting to stop queue immediately"""
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertTrue(machine.is_alive)
        machine.transition(REQUEST_ABORT, source="test")
        self.assertEqual(machine.observed_state, ABORTING)
        self.assertFalse(machine.is_alive)

    def test_history_records_transitions(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test", reason="start")
        machine.transition(PRECHECK_PASSED, source="test")
        self.assertEqual(len(machine.history), 2)
        self.assertEqual(machine.history[0].event, EXECUTE)
        self.assertEqual(machine.history[0].reason, "start")

    def test_finalize_with_result(self):
        machine = ExecutorStateMachine()
        machine.transition(EXECUTE, source="test")
        machine.transition(PRECHECK_PASSED, source="test")
        machine.transition(QUEUE_FINISHED, source="test")
        machine.finalize_with_result("failed")
        self.assertEqual(machine.observed_state, FAILED)


class TestQueueStateMachine(unittest.TestCase):
    def test_initial_state(self):
        machine = QueueStateMachine()
        self.assertEqual(machine.observed_state, QUEUE_IDLE)

    def test_nominal_serial_path(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        self.assertEqual(machine.observed_state, QUEUE_PRECHECK)
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_START_DELAY)
        machine.transition(START_DELAY_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, QUEUE_READY_NEXT_RUN)
        machine.transition(NEXT_RUN_READY, source="test")
        self.assertEqual(machine.observed_state, QUEUE_PREPARING_RUN)
        machine.transition(RUN_CREATED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_RUNNING_SERIAL)
        machine.transition(RUN_TERMINAL, source="test")
        self.assertEqual(machine.observed_state, QUEUE_READY_NEXT_RUN)

    def test_precheck_failure(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_FAILED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_SHUTDOWN)

    def test_cancel_from_running(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(RUN_CREATED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_RUNNING_SERIAL)
        machine.transition(CANCEL_QUEUE, source="test")
        self.assertEqual(machine.observed_state, QUEUE_CANCELED)

    def test_abort_from_running(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(RUN_CREATED, source="test")
        machine.transition(ABORT_QUEUE, source="test")
        self.assertEqual(machine.observed_state, QUEUE_ABORTED)

    def test_overlap_path(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(RUN_CREATED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_RUNNING_SERIAL)
        machine.overlap_allowed = True
        machine.transition(OVERLAP_ALLOWED, source="test")
        self.assertEqual(machine.observed_state, QUEUE_RUNNING_OVERLAP)

    def test_save_wait_path(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(RUN_CREATED, source="test")
        machine.transition(SAVE_PENDING, source="test")
        self.assertEqual(machine.observed_state, QUEUE_WAITING_SAVE)
        machine.transition(SAVE_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, QUEUE_READY_NEXT_RUN)

    def test_queue_empty(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(QUEUE_EMPTY, source="test")
        self.assertEqual(machine.observed_state, QUEUE_SHUTDOWN)

    def test_terminal_states(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(QUEUE_EMPTY, source="test")
        machine.transition(QUEUE_SHUTDOWN_COMPLETE, source="test")
        self.assertTrue(machine.is_terminal())

    def test_finalize_with_result(self):
        machine = QueueStateMachine()
        machine.transition(START_QUEUE, source="test")
        machine.transition(QUEUE_PRECHECK_PASSED, source="test")
        machine.transition(START_DELAY_COMPLETE, source="test")
        machine.transition(NEXT_RUN_READY, source="test")
        machine.transition(QUEUE_EMPTY, source="test")
        machine.finalize_with_result("failed")
        self.assertEqual(machine.observed_state, QUEUE_FAILED)


class TestRunStateMachine(unittest.TestCase):
    def test_initial_state(self):
        machine = RunStateMachine()
        self.assertEqual(machine.observed_state, RUN_IDLE)

    def test_nominal_path(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        self.assertEqual(machine.observed_state, RUN_CREATED)
        machine.transition(START, source="test")
        self.assertEqual(machine.observed_state, RUN_STARTING)
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        self.assertEqual(machine.observed_state, RUN_PRECHECK)
        machine.transition(START_EXTRACTION, source="test")
        self.assertEqual(machine.observed_state, RUN_EXTRACTING)
        machine.transition(EXTRACTION_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, RUN_MEASURING)
        machine.transition(MEASUREMENT_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, RUN_POST_MEASUREMENT)
        machine.transition(POST_MEASUREMENT_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, RUN_SAVING)
        machine.transition(RUN_SAVE_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, RUN_FINISHING)
        machine.transition(FINISH, source="test")
        self.assertEqual(machine.observed_state, RUN_SUCCESS)

    def test_extraction_failure(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_FAILED, source="test")
        self.assertEqual(machine.observed_state, RUN_FAILED)

    def test_measurement_failure(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(MEASUREMENT_FAILED, source="test")
        self.assertEqual(machine.observed_state, RUN_FAILED)

    def test_cancel_during_extraction(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(CANCEL, source="test")
        self.assertEqual(machine.observed_state, RUN_CANCELED)

    def test_abort_during_measurement(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(ABORT, source="test")
        self.assertEqual(machine.observed_state, RUN_ABORTED)

    def test_truncate_during_measurement(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(TRUNCATE, source="test")
        self.assertEqual(machine.observed_state, RUN_TRUNCATED)

    def test_overlap_wait_path(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(WAIT_OVERLAP, source="test")
        self.assertEqual(machine.observed_state, RUN_WAITING_OVERLAP_SIGNAL)
        machine.transition(OVERLAP_SIGNALLED, source="test")
        self.assertEqual(machine.observed_state, RUN_WAITING_MIN_PUMPTIME)
        machine.transition(MIN_PUMPTIME_COMPLETE, source="test")
        self.assertEqual(machine.observed_state, RUN_MEASURING)

    def test_save_failure(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(MEASUREMENT_COMPLETE, source="test")
        machine.transition(POST_MEASUREMENT_COMPLETE, source="test")
        machine.transition(START_SAVE, source="test")
        machine.transition(SAVE_FAILED, source="test")
        self.assertEqual(machine.observed_state, RUN_FAILED)

    def test_is_extracting_derived(self):
        machine = RunStateMachine()
        self.assertFalse(machine.is_extracting)
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        self.assertTrue(machine.is_extracting)

    def test_is_measuring_derived(self):
        machine = RunStateMachine()
        self.assertFalse(machine.is_measuring)
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        self.assertTrue(machine.is_measuring)

    def test_map_to_legacy_state(self):
        machine = RunStateMachine()
        self.assertEqual(machine.map_to_legacy_state(), "not run")
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        self.assertEqual(machine.map_to_legacy_state(), "extraction")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        self.assertEqual(machine.map_to_legacy_state(), "measurement")
        machine.transition(MEASUREMENT_COMPLETE, source="test")
        machine.transition(POST_MEASUREMENT_COMPLETE, source="test")
        machine.transition(START_SAVE, source="test")
        machine.transition(RUN_SAVE_COMPLETE, source="test")
        machine.transition(FINISH, source="test")
        self.assertEqual(machine.map_to_legacy_state(), "success")

    def test_mark_invalid(self):
        machine = RunStateMachine()
        machine.transition(MARK_INVALID, source="test")
        self.assertEqual(machine.observed_state, RUN_INVALID)

    def test_post_measurement_failure(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(MEASUREMENT_COMPLETE, source="test")
        machine.transition(POST_MEASUREMENT_FAILED, source="test")
        self.assertEqual(machine.observed_state, RUN_FAILED)

    def test_terminal_state_rejects_transitions(self):
        machine = RunStateMachine()
        machine.transition(CREATE, source="test")
        machine.transition(START, source="test")
        machine.transition(RUN_PRECHECK_PASSED, source="test")
        machine.transition(START_EXTRACTION, source="test")
        machine.transition(EXTRACTION_COMPLETE, source="test")
        machine.transition(MEASUREMENT_COMPLETE, source="test")
        machine.transition(POST_MEASUREMENT_COMPLETE, source="test")
        machine.transition(START_SAVE, source="test")
        machine.transition(RUN_SAVE_COMPLETE, source="test")
        machine.transition(FINISH, source="test")
        self.assertEqual(machine.observed_state, RUN_SUCCESS)
        record = machine.transition(START_EXTRACTION, source="test")
        self.assertFalse(record.accepted)


if __name__ == "__main__":
    unittest.main()
