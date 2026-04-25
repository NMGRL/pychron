# ===============================================================================
# Copyright 2026 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict

from pychron import globals as globalv
from pychron.experiment.telemetry.context import TelemetryContext
from pychron.experiment.telemetry.recorder import TelemetryRecorder
from pychron.experiment.telemetry.state_machine_listener import StateMachineListener
from pychron.experiment.state_machines.executor_machine import (
    ExecutorStateMachine,
    IDLE,
    PREPARING,
    RUNNING_QUEUE,
    STOPPING_AT_BOUNDARY,
    CANCELING,
    ABORTING,
    RECOVERING,
    FINALIZING,
    COMPLETED,
    FAILED,
    CANCELED,
    ABORTED,
    EXECUTE,
    PRECHECK_PASSED,
    PRECHECK_FAILED,
    QUEUE_SELECTED,
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
    QUEUE_RECOVERY,
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
    RUN_STARTED,
    OVERLAP_ALLOWED,
    OVERLAP_BLOCKED,
    RUN_TERMINAL,
    SAVE_PENDING,
    SAVE_COMPLETE,
    QUEUE_EMPTY,
    STOP_BOUNDARY_REACHED,
    CANCEL_QUEUE,
    ABORT_QUEUE,
    QUEUE_RECOVER,
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
from pychron.experiment.state_machines.base import TransitionRecord


class ExecutorController:
    def __init__(self, executor: Any):
        self._executor = executor
        self.executor_machine = ExecutorStateMachine(subject_id="executor")
        self.queue_machine: QueueStateMachine | None = None
        self._run_machines: dict[str, RunStateMachine] = {}
        self._active_run_ids: list[str] = []
        self._end_at_run_completion = False
        self._failure_reason: str | None = None
        self._on_transition: list[Callable[[str, TransitionRecord], None]] = []

        # Initialize telemetry (app-wide context and recorder)
        self.telemetry_context: TelemetryContext | None = None
        self.telemetry_recorder: TelemetryRecorder | None = None
        self._queue_recorders: Dict[str, TelemetryRecorder] = {}
        if getattr(globalv, "telemetry_enabled", False):
            self.telemetry_context = TelemetryContext()
            telemetry_dir = Path.home() / ".pychron_telemetry" / "logs"
            telemetry_dir.mkdir(parents=True, exist_ok=True)
            log_file = telemetry_dir / f"telemetry_{os.getpid()}.jsonl"
            self.telemetry_recorder = TelemetryRecorder(log_path=log_file)
            listener = StateMachineListener(self.telemetry_recorder)
            self.register_on_transition(listener.on_transition)

    @property
    def active_run_machines(self) -> list[tuple[str, RunStateMachine]]:
        return [
            (rid, self._run_machines[rid])
            for rid in self._active_run_ids
            if rid in self._run_machines
        ]

    @property
    def end_at_run_completion(self) -> bool:
        return self._end_at_run_completion

    @end_at_run_completion.setter
    def end_at_run_completion(self, value: bool) -> None:
        self._end_at_run_completion = value

    @property
    def failure_reason(self) -> str | None:
        return self._failure_reason

    def register_on_transition(self, callback: Callable[[str, TransitionRecord], None]) -> None:
        self._on_transition.append(callback)

    def get_queue_recorder(self, queue_name: str) -> TelemetryRecorder:
        """Get or create recorder for this queue.

        Args:
            queue_name: Name of the queue

        Returns:
            TelemetryRecorder instance for the queue
        """
        if queue_name not in self._queue_recorders:
            telemetry_dir = Path.home() / ".pychron_telemetry" / "logs"
            telemetry_dir.mkdir(parents=True, exist_ok=True)
            log_file = telemetry_dir / f"telemetry_{queue_name}_{os.getpid()}.jsonl"
            recorder = TelemetryRecorder(log_path=log_file)
            self._queue_recorders[queue_name] = recorder
        return self._queue_recorders[queue_name]

    def finalize_queue(self, queue_name: str) -> None:
        """Flush and close queue recorder.

        Args:
            queue_name: Name of the queue to finalize
        """
        recorder = self._queue_recorders.pop(queue_name, None)
        if recorder:
            recorder.flush()
            recorder.close()
        # Clear queue context
        if self.telemetry_context:
            self.telemetry_context.set_queue_id(None)

    def close_session(self) -> None:
        """Flush all recorders and close session."""
        # Flush and close all queue recorders
        for recorder in self._queue_recorders.values():
            try:
                recorder.flush()
                recorder.close()
            except Exception:
                pass
        self._queue_recorders.clear()

        # Flush and close main recorder
        if self.telemetry_recorder:
            try:
                self.telemetry_recorder.flush()
                self.telemetry_recorder.close()
            except Exception:
                pass

        # Clear all context
        if self.telemetry_context:
            self.telemetry_context.clear_all()

    def _notify(self, machine_name: str, record: TransitionRecord) -> None:
        for cb in self._on_transition:
            try:
                cb(machine_name, record)
            except Exception:
                pass

    # Executor-level transitions

    def execute(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(EXECUTE, source="controller.execute", **kwargs)
        self._notify("executor", record)
        return record

    def precheck_passed(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            PRECHECK_PASSED, source="controller.precheck_passed", **kwargs
        )
        self._notify("executor", record)
        return record

    def precheck_failed(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            PRECHECK_FAILED, source="controller.precheck_failed", **kwargs
        )
        self._notify("executor", record)
        return record

    def queue_selected(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            QUEUE_SELECTED, source="controller.queue_selected", **kwargs
        )
        self._notify("executor", record)
        return record

    def queue_finished(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            QUEUE_FINISHED, source="controller.queue_finished", **kwargs
        )
        self._notify("executor", record)
        return record

    def request_stop_at_boundary(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            REQUEST_STOP_AT_BOUNDARY, source="controller.request_stop_at_boundary", **kwargs
        )
        self._notify("executor", record)
        return record

    def request_cancel(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            REQUEST_CANCEL, source="controller.request_cancel", **kwargs
        )
        self._notify("executor", record)
        if self.queue_machine:
            self.queue_machine.transition(
                CANCEL_QUEUE, force=True, source="controller.request_cancel"
            )
        return record

    def request_abort(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            REQUEST_ABORT, source="controller.request_abort", **kwargs
        )
        self._notify("executor", record)
        if self.queue_machine:
            self.queue_machine.transition(
                ABORT_QUEUE, force=True, source="controller.request_abort"
            )
        return record

    def run_failure(self, reason: str | None = None, **kwargs: Any) -> TransitionRecord:
        reason = kwargs.pop("reason", reason)
        self._failure_reason = reason
        record = self.executor_machine.transition(
            RUN_FAILURE, source="controller.run_failure", reason=reason, **kwargs
        )
        self._notify("executor", record)
        return record

    def recovery_requested(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            RECOVERY_REQUESTED, source="controller.recovery_requested", **kwargs
        )
        self._notify("executor", record)
        return record

    def recovery_complete(self, **kwargs: Any) -> TransitionRecord:
        record = self.executor_machine.transition(
            RECOVERY_COMPLETE, source="controller.recovery_complete", **kwargs
        )
        self._notify("executor", record)
        return record

    def finalize_complete(self, result: str = "completed", **kwargs: Any) -> TransitionRecord:
        reason = kwargs.pop("reason", result)
        record = self.executor_machine.transition(
            FINALIZE_COMPLETE, source="controller.finalize_complete", reason=reason, **kwargs
        )
        self._notify("executor", record)
        return record

    def reset(self, **kwargs: Any) -> TransitionRecord:
        self.executor_machine.reset()
        self.queue_machine = None
        self._run_machines.clear()
        self._active_run_ids.clear()
        self._end_at_run_completion = False
        self._failure_reason = None
        record = self.executor_machine.transition(RESET, source="controller.reset", **kwargs)
        self._notify("executor", record)
        return record

    # Queue-level transitions

    def init_queue(self, queue_name: str | None = None) -> QueueStateMachine:
        self.queue_machine = QueueStateMachine(subject_id=queue_name)
        return self.queue_machine

    def begin_queue(self, queue_name: str | None = None) -> QueueStateMachine:
        machine = self.init_queue(queue_name)
        self.start_queue(queue_name=queue_name)
        self.queue_precheck_passed(queue_name=queue_name)
        self.start_delay_complete(queue_name=queue_name)
        return machine

    def start_queue(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            START_QUEUE, source="controller.start_queue", **kwargs
        )
        self._notify("queue", record)
        return record

    def queue_precheck_passed(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            QUEUE_PRECHECK_PASSED, source="controller.queue_precheck_passed", **kwargs
        )
        self._notify("queue", record)
        return record

    def queue_precheck_failed(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            QUEUE_PRECHECK_FAILED, source="controller.queue_precheck_failed", **kwargs
        )
        self._notify("queue", record)
        return record

    def start_delay_complete(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            START_DELAY_COMPLETE, source="controller.start_delay_complete", **kwargs
        )
        self._notify("queue", record)
        return record

    def next_run_ready(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            NEXT_RUN_READY, source="controller.next_run_ready", **kwargs
        )
        self._notify("queue", record)
        return record

    def queue_empty(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            QUEUE_EMPTY, source="controller.queue_empty", **kwargs
        )
        self._notify("queue", record)
        return record

    def stop_boundary_reached(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            STOP_BOUNDARY_REACHED, source="controller.stop_boundary_reached", **kwargs
        )
        self._notify("queue", record)
        return record

    def run_created_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            RUN_CREATED, source="controller.run_created", **kwargs
        )
        self._notify("queue", record)
        return record

    def run_started_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            RUN_STARTED, source="controller.run_started", **kwargs
        )
        self._notify("queue", record)
        return record

    def overlap_allowed_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            OVERLAP_ALLOWED, source="controller.overlap_allowed", **kwargs
        )
        self._notify("queue", record)
        return record

    def overlap_blocked_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            OVERLAP_BLOCKED, source="controller.overlap_blocked", **kwargs
        )
        self._notify("queue", record)
        return record

    def run_terminal_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            RUN_TERMINAL, source="controller.run_terminal", **kwargs
        )
        self._notify("queue", record)
        return record

    def save_pending_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            SAVE_PENDING, source="controller.save_pending", **kwargs
        )
        self._notify("queue", record)
        return record

    def save_complete_event(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            SAVE_COMPLETE, source="controller.save_complete", **kwargs
        )
        self._notify("queue", record)
        return record

    def queue_shutdown_complete(self, **kwargs: Any) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None
        record = self.queue_machine.transition(
            QUEUE_SHUTDOWN_COMPLETE, source="controller.queue_shutdown_complete", **kwargs
        )
        self._notify("queue", record)
        return record

    def prepare_next_run(self, queue_name: str | None = None) -> TransitionRecord | None:
        return self.next_run_ready(queue_name=queue_name)

    def mark_queue_overlap(
        self, allowed: bool, queue_name: str | None = None
    ) -> TransitionRecord | None:
        if allowed:
            if self.queue_machine:
                self.queue_machine.overlap_allowed = True
            return self.overlap_allowed_event(queue_name=queue_name)

        if self.queue_machine:
            self.queue_machine.overlap_allowed = False
        return self.overlap_blocked_event(queue_name=queue_name)

    def should_queue_overlap(
        self,
        run_is_last: bool,
        analysis_type: str,
        overlap_enabled: bool,
    ) -> bool:
        if self.queue_machine is None:
            return False
        allowed = (not run_is_last) and analysis_type == "unknown" and overlap_enabled
        self.queue_machine.overlap_allowed = allowed
        return allowed

    def queue_run_execution_mode(
        self,
        run_is_last: bool,
        analysis_type: str,
        overlap_enabled: bool,
    ) -> str:
        if self.should_queue_overlap(
            run_is_last=run_is_last,
            analysis_type=analysis_type,
            overlap_enabled=overlap_enabled,
        ):
            return "overlap"
        return "serial"

    def queue_overlap_launch_actions(self) -> tuple[str, ...]:
        return ("wait_extracting", "start_overlap_thread", "wait_overlap_signal")

    def queue_settle_mode(self) -> str:
        if self.should_stop_at_boundary() or self.should_end_at_run_completion():
            return "stop_at_boundary"
        return "wait_for_active_runs"

    def queue_extracting_settle_mode(
        self, has_extracting_run: bool, extracting_is_special: bool
    ) -> str:
        if not has_extracting_run:
            return "none"
        if self.queue_settle_mode() != "stop_at_boundary":
            return "wait"
        if extracting_is_special:
            return "cancel_special"
        return "wait"

    def queue_settle_actions(
        self,
        has_extracting_run: bool,
        extracting_is_special: bool,
        has_measuring_run: bool,
    ) -> tuple[str, ...]:
        settle_mode = self.queue_settle_mode()
        if settle_mode != "stop_at_boundary":
            if has_extracting_run or has_measuring_run:
                return ("wait_active_runs",)
            return ()

        actions: list[str] = []
        extracting_mode = self.queue_extracting_settle_mode(
            has_extracting_run=has_extracting_run,
            extracting_is_special=extracting_is_special,
        )
        if extracting_mode == "wait":
            actions.append("wait_extracting")
        elif extracting_mode == "cancel_special":
            actions.append("cancel_special_extracting")

        if has_measuring_run:
            actions.append("wait_measuring")
        return tuple(actions)

    def queue_terminal_result(
        self,
        failure_reason: str | None = None,
    ) -> str:
        if self.should_abort():
            return "aborted"
        if self.should_cancel():
            return "canceled"
        if failure_reason:
            return "failed"
        return "completed"

    def queue_completion_actions(self) -> tuple[str, ...]:
        return (
            "stop_stats_timer",
            "clear_extract_state",
            "set_queue_message",
            "sync_compatibility_state",
        )

    def queue_completion_message(
        self,
        queue_name: str,
        stop_at_boundary: bool,
        canceled: bool,
    ) -> tuple[str, str]:
        if stop_at_boundary:
            color = "orange"
            status = "Stopped"
        elif canceled:
            color = "red"
            status = "Canceled"
        else:
            color = "green"
            status = "Finished"

        return "{} {}".format(queue_name, status), color

    def should_save_run(self, run_state: str, save_all_runs: bool) -> bool:
        return save_all_runs or run_state in ("success", "truncated")

    def run_post_save_actions(
        self,
        run_state: str,
        use_autoplot: bool,
        experiment_type: str,
    ) -> tuple[str, ...]:
        actions: list[str] = ["set_run_completed", "remove_backup", "post_run_check"]
        actions.append("log_run_duration")
        actions.append("finish_run")
        if experiment_type == "Ar/Ar" and run_state in ("success", "truncated"):
            actions.append("update_arar_values")
        if use_autoplot:
            actions.append("publish_autoplot")
        actions.extend(
            (
                "pop_wait_group",
                "finish_stats_run",
                "update_stats",
                "write_queue_files",
                "end_run_event",
                "remove_root_handler",
                "post_finish",
                "remove_run_machine",
                "refresh_queue_table",
            )
        )
        return tuple(actions)

    def queue_run_saved(
        self, queue_name: str | None = None, waiting: bool = False
    ) -> TransitionRecord | None:
        if self.queue_machine:
            self.queue_machine.save_in_progress = waiting
        if waiting:
            return self.save_pending_event(queue_name=queue_name)
        return self.save_complete_event(queue_name=queue_name)

    def mark_queue_run_terminal(
        self,
        queue_name: str | None = None,
        stop_at_boundary: bool = False,
        waiting_for_save: bool = False,
    ) -> TransitionRecord | None:
        if self.queue_machine is None:
            return None

        if waiting_for_save:
            return self.queue_run_saved(queue_name=queue_name, waiting=True)
        if stop_at_boundary:
            return self.stop_boundary_reached(queue_name=queue_name)
        return self.run_terminal_event(queue_name=queue_name)

    def finish_queue(
        self,
        result: str,
        queue_name: str | None = None,
        reason: str | None = None,
    ) -> None:
        if self.queue_machine is None:
            return
        self.queue_shutdown_complete(queue_name=queue_name, reason=reason)
        self.queue_machine.finalize_with_result(result, reason=reason)

    # Run-level transitions

    def create_run_machine(self, run_id: str) -> RunStateMachine:
        machine = RunStateMachine(subject_id=run_id)
        self._run_machines[run_id] = machine
        self._active_run_ids.append(run_id)
        return machine

    def remove_run_machine(self, run_id: str) -> None:
        if run_id in self._active_run_ids:
            self._active_run_ids.remove(run_id)
        self._run_machines.pop(run_id, None)

    def get_run_machine(self, run_id: str) -> RunStateMachine | None:
        return self._run_machines.get(run_id)

    def transition_run(
        self, run_id: str, event: str, force: bool = False, **kwargs: Any
    ) -> TransitionRecord | None:
        machine = self._run_machines.get(run_id)
        if machine is None:
            return None
        record = machine.transition(
            event, force=force, source=f"controller.transition_run:{run_id}", **kwargs
        )
        self._notify(f"run:{run_id}", record)
        return record

    def begin_run(self, run_id: str, queue_name: str | None = None) -> RunStateMachine:
        machine = self.create_run_machine(run_id)
        self.run_created_event(run_id=run_id, queue_name=queue_name)
        self.transition_run(run_id, CREATE)
        self.transition_run(run_id, START)
        return machine

    def mark_run_started(
        self, run_id: str, queue_name: str | None = None, failed: bool = False
    ) -> TransitionRecord | None:
        if failed:
            return self.transition_run(run_id, RUN_PRECHECK_FAILED, force=True)
        record = self.transition_run(run_id, RUN_PRECHECK_PASSED)
        self.run_started_event(run_id=run_id, queue_name=queue_name)
        return record

    def start_run_extraction(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, START_EXTRACTION)

    def complete_run_extraction(
        self, run_id: str, failed: bool = False, reason: str | None = None
    ) -> TransitionRecord | None:
        event = EXTRACTION_FAILED if failed else EXTRACTION_COMPLETE
        return self.transition_run(run_id, event, force=failed, reason=reason)

    def enter_run_overlap_wait(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, WAIT_OVERLAP)

    def signal_run_overlap(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, OVERLAP_SIGNALLED)

    def complete_run_min_pumptime(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, MIN_PUMPTIME_COMPLETE)

    def start_run_measurement(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, START_MEASUREMENT)

    def complete_run_measurement(
        self, run_id: str, failed: bool = False, reason: str | None = None
    ) -> TransitionRecord | None:
        event = MEASUREMENT_FAILED if failed else MEASUREMENT_COMPLETE
        return self.transition_run(run_id, event, force=failed, reason=reason)

    def start_run_post_measurement(self, run_id: str) -> TransitionRecord | None:
        return self.transition_run(run_id, START_POST_MEASUREMENT)

    def complete_run_post_measurement(
        self, run_id: str, failed: bool = False, reason: str | None = None
    ) -> TransitionRecord | None:
        event = POST_MEASUREMENT_FAILED if failed else POST_MEASUREMENT_COMPLETE
        return self.transition_run(run_id, event, force=failed, reason=reason)

    def start_run_save(self, run_id: str, queue_name: str | None = None) -> TransitionRecord | None:
        record = self.transition_run(run_id, START_SAVE)
        self.queue_run_saved(queue_name=queue_name, waiting=True)
        return record

    def complete_run_save(
        self,
        run_id: str,
        queue_name: str | None = None,
        failed: bool = False,
        reason: str | None = None,
    ) -> TransitionRecord | None:
        event = SAVE_FAILED if failed else RUN_SAVE_COMPLETE
        record = self.transition_run(run_id, event, force=failed, reason=reason)
        if not failed:
            self.transition_run(run_id, FINISH)
            self.mark_queue_run_terminal(queue_name=queue_name)
            self.queue_run_saved(queue_name=queue_name, waiting=False)
        return record

    def run_step_sequence(self) -> tuple[str, ...]:
        return ("_start", "_extraction", "_measurement", "_post_measurement")

    def should_continue_run(self, alive: bool, aborting: bool, fatal_error: bool) -> str:
        if not alive:
            return "stop"
        if aborting:
            return "abort"
        if fatal_error:
            return "fatal"
        return "continue"

    def handle_run_step_failure(
        self,
        run_id: str,
        step_name: str,
        reason: str | None = None,
    ) -> None:
        if step_name == "_start":
            self.mark_run_started(run_id, failed=True)

    def complete_run_execution(
        self,
        run_id: str,
        run_state: str | None = None,
    ) -> None:
        if run_state not in ("truncated", "canceled", "failed"):
            self.transition_run(run_id, FINISH)

    def truncate_run(self, run_id: str, reason: str | None = None) -> TransitionRecord | None:
        return self.transition_run(run_id, TRUNCATE, force=True, reason=reason)

    def cancel_run(self, run_id: str, reason: str | None = None) -> TransitionRecord | None:
        return self.transition_run(run_id, CANCEL, force=True, reason=reason)

    def abort_run(self, run_id: str, reason: str | None = None) -> TransitionRecord | None:
        return self.transition_run(run_id, ABORT, force=True, reason=reason)

    def invalidate_run(self, run_id: str, reason: str | None = None) -> TransitionRecord | None:
        return self.transition_run(run_id, MARK_INVALID, force=True, reason=reason)

    # Derived compatibility properties

    @property
    def is_alive(self) -> bool:
        return self.executor_machine.is_alive

    @property
    def is_running(self) -> bool:
        return self.executor_machine.is_running

    @property
    def is_canceling(self) -> bool:
        return self.executor_machine.is_canceling

    @property
    def is_terminal(self) -> bool:
        return self.executor_machine.is_terminal

    def can_execute(self) -> bool:
        return self.executor_machine.can_execute()

    def should_reset_before_execute(self) -> bool:
        return self.is_terminal or (not self.can_execute() and not self.is_running)

    @property
    def extracting(self) -> bool:
        for _, rm in self.active_run_machines:
            if rm.is_extracting:
                return True
        return False

    @property
    def measuring(self) -> bool:
        for _, rm in self.active_run_machines:
            if rm.is_measuring:
                return True
        return False

    def should_stop_at_boundary(self) -> bool:
        return self.executor_machine._observed_state == STOPPING_AT_BOUNDARY

    def should_cancel(self) -> bool:
        return self.executor_machine._observed_state in {CANCELING, ABORTING}

    def should_abort(self) -> bool:
        return self.executor_machine._observed_state == ABORTING

    def should_end_at_run_completion(self) -> bool:
        return self._end_at_run_completion

    def finalize_with_result(self, result: str, **kwargs: Any) -> None:
        self.executor_machine.finalize_with_result(result, **kwargs)
        if self.queue_machine:
            self.queue_machine.finalize_with_result(result, **kwargs)
