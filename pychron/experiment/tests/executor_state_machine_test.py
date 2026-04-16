import unittest

from pychron.experiment.state_machines import ExecutorController
from pychron.experiment.state_machines.executor_machine import FINALIZING, PREPARING
from pychron.experiment.state_machines.queue_machine import (
    QUEUE_COMPLETED,
    QUEUE_RUNNING_OVERLAP,
)
from pychron.experiment.state_machines.run_machine import (
    RUN_SUCCESS,
    RUN_WAITING_MIN_PUMPTIME,
    PRECHECK_PASSED,
    RUN_WAITING_OVERLAP_SIGNAL,
)


class _ExecutorStub:
    pass


class ExecutorControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.controller = ExecutorController(_ExecutorStub())

    def test_executor_nominal_lifecycle_reaches_completed(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.init_queue("queue-1")
        self.controller.start_queue()
        self.controller.queue_precheck_passed()
        self.controller.start_delay_complete()
        self.controller.queue_empty()
        self.controller.queue_shutdown_complete()
        self.controller.queue_finished()
        self.controller.finalize_with_result("completed")

        self.assertEqual(self.controller.executor_machine.history[-2].new_state, FINALIZING)
        self.assertEqual(self.controller.executor_machine.observed_state, "completed")
        self.assertFalse(self.controller.is_alive)
        self.assertEqual(self.controller.executor_machine.history[0].new_state, PREPARING)

    def test_queue_overlap_and_save_transitions_are_explicit(self):
        self.controller.begin_queue("queue-1")
        self.controller.prepare_next_run("queue-1")
        self.controller.run_created_event()
        self.controller.mark_queue_overlap(True, "queue-1")

        self.assertEqual(self.controller.queue_machine.observed_state, QUEUE_RUNNING_OVERLAP)

        self.controller.queue_run_saved("queue-1", waiting=True)
        self.controller.queue_run_saved("queue-1", waiting=False)
        self.controller.queue_empty()
        self.controller.finish_queue("completed", "queue-1")

        self.assertEqual(self.controller.queue_machine.observed_state, QUEUE_COMPLETED)

    def test_queue_overlap_decision_is_controller_owned(self):
        self.controller.begin_queue("queue-1")

        self.assertTrue(
            self.controller.should_queue_overlap(
                run_is_last=False, analysis_type="unknown", overlap_enabled=True
            )
        )
        self.assertFalse(
            self.controller.should_queue_overlap(
                run_is_last=True, analysis_type="unknown", overlap_enabled=True
            )
        )
        self.assertFalse(
            self.controller.should_queue_overlap(
                run_is_last=False, analysis_type="air", overlap_enabled=True
            )
        )
        self.assertEqual(
            self.controller.queue_run_execution_mode(
                run_is_last=False, analysis_type="unknown", overlap_enabled=True
            ),
            "overlap",
        )
        self.assertEqual(
            self.controller.queue_run_execution_mode(
                run_is_last=True, analysis_type="unknown", overlap_enabled=True
            ),
            "serial",
        )

    def test_queue_settle_mode_reflects_stop_boundary(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.assertEqual(self.controller.queue_settle_mode(), "wait_for_active_runs")
        self.assertEqual(
            self.controller.queue_settle_actions(
                has_extracting_run=True,
                extracting_is_special=False,
                has_measuring_run=True,
            ),
            ("wait_active_runs",),
        )

        self.controller.request_stop_at_boundary()
        self.assertEqual(self.controller.queue_settle_mode(), "stop_at_boundary")
        self.assertEqual(
            self.controller.queue_extracting_settle_mode(
                has_extracting_run=True, extracting_is_special=False
            ),
            "wait",
        )
        self.assertEqual(
            self.controller.queue_extracting_settle_mode(
                has_extracting_run=True, extracting_is_special=True
            ),
            "cancel_special",
        )
        self.assertEqual(
            self.controller.queue_settle_actions(
                has_extracting_run=True,
                extracting_is_special=True,
                has_measuring_run=True,
            ),
            ("cancel_special_extracting", "wait_measuring"),
        )

    def test_queue_terminal_result_comes_from_controller_state(self):
        self.assertEqual(self.controller.queue_terminal_result(), "completed")
        self.assertEqual(
            self.controller.queue_terminal_result(
                "Communication failure: spectrometer unavailable"
            ),
            "failed",
        )
        self.assertTrue(self.controller.should_save_run("success", False))
        self.assertTrue(self.controller.should_save_run("truncated", False))
        self.assertFalse(self.controller.should_save_run("failed", False))
        self.assertEqual(
            self.controller.queue_completion_actions(),
            (
                "stop_stats_timer",
                "clear_extract_state",
                "set_queue_message",
                "sync_compatibility_state",
            ),
        )
        self.assertEqual(
            self.controller.queue_completion_message(
                queue_name="queue-1",
                stop_at_boundary=False,
                canceled=False,
            ),
            ("queue-1 Finished", "green"),
        )
        self.assertEqual(
            self.controller.queue_completion_message(
                queue_name="queue-1",
                stop_at_boundary=True,
                canceled=False,
            ),
            ("queue-1 Stopped", "orange"),
        )
        self.assertEqual(
            self.controller.queue_completion_message(
                queue_name="queue-1",
                stop_at_boundary=False,
                canceled=True,
            ),
            ("queue-1 Canceled", "red"),
        )

        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.request_cancel()
        self.assertEqual(self.controller.queue_terminal_result(), "canceled")

    def test_run_step_policy_is_controller_owned(self):
        self.assertEqual(
            self.controller.run_step_sequence(),
            ("_start", "_extraction", "_measurement", "_post_measurement"),
        )
        self.assertEqual(
            self.controller.should_continue_run(alive=True, aborting=False, fatal_error=False),
            "continue",
        )
        self.assertEqual(
            self.controller.should_continue_run(alive=False, aborting=False, fatal_error=False),
            "stop",
        )
        self.assertEqual(
            self.controller.should_continue_run(alive=True, aborting=True, fatal_error=False),
            "abort",
        )
        self.assertEqual(
            self.controller.should_continue_run(alive=True, aborting=False, fatal_error=True),
            "fatal",
        )

    def test_stop_at_boundary_uses_explicit_executor_state(self):
        self.controller.execute()
        self.controller.precheck_passed()

        self.controller.request_stop_at_boundary()

        self.assertTrue(self.controller.should_stop_at_boundary())
        self.assertEqual(self.controller.executor_machine.observed_state, "stopping_at_boundary")

    def test_cancel_path_finalizes_as_canceled(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.init_queue("queue-1")
        self.controller.start_queue()
        self.controller.request_cancel()
        self.assertTrue(self.controller.should_cancel())
        self.controller.queue_finished()
        self.controller.finalize_with_result("canceled")

        self.assertEqual(self.controller.executor_machine.observed_state, "canceled")

    def test_abort_path_finalizes_as_aborted(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.init_queue("queue-1")
        self.controller.start_queue()
        self.controller.request_abort()
        self.assertTrue(self.controller.should_abort())
        self.controller.queue_finished()
        self.controller.finalize_with_result("aborted")

        self.assertEqual(self.controller.executor_machine.observed_state, "aborted")

    def test_execute_can_reset_from_canceled_state(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.request_cancel()
        self.controller.queue_finished()
        self.controller.finalize_with_result("canceled")

        self.assertTrue(self.controller.should_reset_before_execute())
        self.controller.reset()

        self.assertTrue(self.controller.can_execute())
        self.assertFalse(self.controller.should_reset_before_execute())

    def test_execute_can_reset_from_canceling_state(self):
        self.controller.execute()
        self.controller.precheck_passed()
        self.controller.request_cancel()

        self.assertTrue(self.controller.should_reset_before_execute())
        self.controller.reset()

        self.assertTrue(self.controller.can_execute())
        self.assertFalse(self.controller.should_reset_before_execute())

    def test_execute_does_not_reset_while_running(self):
        self.controller.execute()
        self.controller.precheck_passed()

        self.assertFalse(self.controller.should_reset_before_execute())
        self.assertFalse(self.controller.can_execute())

    def test_run_overlap_and_save_flow_reaches_success(self):
        run_id = "run-1"
        self.controller.begin_run(run_id, queue_name="queue-1")
        self.controller.mark_run_started(run_id, queue_name="queue-1")
        self.controller.start_run_extraction(run_id)
        self.controller.enter_run_overlap_wait(run_id)
        self.assertEqual(
            self.controller.get_run_machine(run_id).observed_state,
            RUN_WAITING_OVERLAP_SIGNAL,
        )

        self.controller.signal_run_overlap(run_id)
        self.assertEqual(
            self.controller.get_run_machine(run_id).observed_state,
            RUN_WAITING_MIN_PUMPTIME,
        )

        self.controller.complete_run_min_pumptime(run_id)
        self.controller.complete_run_measurement(run_id)
        self.controller.start_run_post_measurement(run_id)
        self.controller.complete_run_post_measurement(run_id)
        self.controller.start_run_save(run_id, queue_name="queue-1")
        self.controller.complete_run_save(run_id, queue_name="queue-1")

        self.assertEqual(self.controller.get_run_machine(run_id).observed_state, RUN_SUCCESS)


if __name__ == "__main__":
    unittest.main()
