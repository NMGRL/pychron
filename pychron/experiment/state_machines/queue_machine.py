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

from typing import Any, Callable

from pychron.experiment.state_machines.base import BaseStateMachine

# Queue states
QUEUE_IDLE = "queue_idle"
QUEUE_PRECHECK = "queue_precheck"
QUEUE_START_DELAY = "queue_start_delay"
QUEUE_READY_NEXT_RUN = "queue_ready_next_run"
QUEUE_PREPARING_RUN = "queue_preparing_run"
QUEUE_RUNNING_SERIAL = "queue_running_serial"
QUEUE_RUNNING_OVERLAP = "queue_running_overlap"
QUEUE_WAITING_OVERLAP_BOUNDARY = "queue_waiting_overlap_boundary"
QUEUE_WAITING_SAVE = "queue_waiting_save"
QUEUE_RECOVERY = "queue_recovery"
QUEUE_SHUTDOWN = "queue_shutdown"
QUEUE_COMPLETED = "queue_completed"
QUEUE_FAILED = "queue_failed"
QUEUE_CANCELED = "queue_canceled"
QUEUE_ABORTED = "queue_aborted"

# Queue events
START_QUEUE = "start_queue"
QUEUE_PRECHECK_PASSED = "queue_precheck_passed"
QUEUE_PRECHECK_FAILED = "queue_precheck_failed"
START_DELAY_COMPLETE = "start_delay_complete"
NEXT_RUN_READY = "next_run_ready"
RUN_CREATED = "run_created"
RUN_STARTED = "run_started"
OVERLAP_ALLOWED = "overlap_allowed"
OVERLAP_BLOCKED = "overlap_blocked"
RUN_TERMINAL = "run_terminal"
SAVE_PENDING = "save_pending"
SAVE_COMPLETE = "save_complete"
QUEUE_EMPTY = "queue_empty"
STOP_BOUNDARY_REACHED = "stop_boundary_reached"
CANCEL_QUEUE = "cancel_queue"
ABORT_QUEUE = "abort_queue"
QUEUE_RECOVER = "queue_recover"
QUEUE_SHUTDOWN_COMPLETE = "queue_shutdown_complete"

STATES = {
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
}

TERMINAL_STATES = {
    QUEUE_COMPLETED,
    QUEUE_FAILED,
    QUEUE_CANCELED,
    QUEUE_ABORTED,
}

TRANSITIONS: dict[str, dict[str, str]] = {
    QUEUE_IDLE: {
        START_QUEUE: QUEUE_PRECHECK,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_PRECHECK: {
        QUEUE_PRECHECK_PASSED: QUEUE_START_DELAY,
        QUEUE_PRECHECK_FAILED: QUEUE_SHUTDOWN,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_START_DELAY: {
        START_DELAY_COMPLETE: QUEUE_READY_NEXT_RUN,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_READY_NEXT_RUN: {
        NEXT_RUN_READY: QUEUE_PREPARING_RUN,
        QUEUE_EMPTY: QUEUE_SHUTDOWN,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_PREPARING_RUN: {
        RUN_CREATED: QUEUE_RUNNING_SERIAL,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_RUNNING_SERIAL: {
        RUN_TERMINAL: QUEUE_READY_NEXT_RUN,
        SAVE_PENDING: QUEUE_WAITING_SAVE,
        OVERLAP_ALLOWED: QUEUE_RUNNING_OVERLAP,
        STOP_BOUNDARY_REACHED: QUEUE_SHUTDOWN,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_RUNNING_OVERLAP: {
        RUN_TERMINAL: QUEUE_WAITING_OVERLAP_BOUNDARY,
        SAVE_PENDING: QUEUE_WAITING_SAVE,
        STOP_BOUNDARY_REACHED: QUEUE_WAITING_OVERLAP_BOUNDARY,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_WAITING_OVERLAP_BOUNDARY: {
        RUN_TERMINAL: QUEUE_READY_NEXT_RUN,
        SAVE_PENDING: QUEUE_WAITING_SAVE,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_WAITING_SAVE: {
        SAVE_COMPLETE: QUEUE_READY_NEXT_RUN,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_RECOVERY: {
        QUEUE_RECOVER: QUEUE_PRECHECK,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_SHUTDOWN: {
        QUEUE_SHUTDOWN_COMPLETE: QUEUE_COMPLETED,
        CANCEL_QUEUE: QUEUE_CANCELED,
        ABORT_QUEUE: QUEUE_ABORTED,
    },
    QUEUE_COMPLETED: {},
    QUEUE_FAILED: {},
    QUEUE_CANCELED: {},
    QUEUE_ABORTED: {},
}


class QueueStateMachine(BaseStateMachine):
    def __init__(self, subject_id: str | None = None):
        super().__init__(
            states=STATES,
            terminal_states=TERMINAL_STATES,
            transitions=TRANSITIONS,
            initial_state=QUEUE_IDLE,
            subject_id=subject_id,
        )
        self._overlap_allowed = False
        self._has_next_run = False
        self._save_in_progress = False

    @property
    def overlap_allowed(self) -> bool:
        return self._overlap_allowed

    @overlap_allowed.setter
    def overlap_allowed(self, value: bool) -> None:
        self._overlap_allowed = value

    @property
    def has_next_run(self) -> bool:
        return self._has_next_run

    @has_next_run.setter
    def has_next_run(self, value: bool) -> None:
        self._has_next_run = value

    @property
    def save_in_progress(self) -> bool:
        return self._save_in_progress

    @save_in_progress.setter
    def save_in_progress(self, value: bool) -> None:
        self._save_in_progress = value

    @property
    def is_running(self) -> bool:
        return self._observed_state in {
            QUEUE_RUNNING_SERIAL,
            QUEUE_RUNNING_OVERLAP,
            QUEUE_WAITING_OVERLAP_BOUNDARY,
            QUEUE_WAITING_SAVE,
        }

    @property
    def is_preparing(self) -> bool:
        return self._observed_state in {
            QUEUE_PRECHECK,
            QUEUE_START_DELAY,
            QUEUE_READY_NEXT_RUN,
            QUEUE_PREPARING_RUN,
        }

    def register_all(
        self,
        guards: dict[str, Callable[..., bool]] | None = None,
        effects: dict[str, Callable[..., None]] | None = None,
        compat_updates: dict[str, Callable[..., None]] | None = None,
    ) -> None:
        if guards:
            for event, func in guards.items():
                self.register_guard(event, func)
        if effects:
            for event, func in effects.items():
                self.register_effect(event, func)
        if compat_updates:
            for event, func in compat_updates.items():
                self.register_compat_update(event, func)

    def should_overlap(self) -> bool:
        return self._observed_state == QUEUE_RUNNING_SERIAL and self._overlap_allowed

    def should_wait_for_save(self) -> bool:
        return self._save_in_progress

    def finalize_with_result(self, result: str, **kwargs: Any) -> None:
        target_map = {
            "completed": QUEUE_COMPLETED,
            "failed": QUEUE_FAILED,
            "canceled": QUEUE_CANCELED,
            "aborted": QUEUE_ABORTED,
        }
        target = target_map.get(result, QUEUE_COMPLETED)
        reason = kwargs.pop("reason", result)
        current = self._observed_state
        if current in TERMINAL_STATES:
            return
        if current == QUEUE_SHUTDOWN:
            self.transition(
                QUEUE_SHUTDOWN_COMPLETE,
                source="finalize_with_result",
                reason=reason,
                **kwargs,
            )
            if self._observed_state == QUEUE_COMPLETED and target != QUEUE_COMPLETED:
                self.set_observed_state(target, source="finalize_with_result", reason=reason)
        else:
            self.set_observed_state(target, source="finalize_with_result", reason=reason)
