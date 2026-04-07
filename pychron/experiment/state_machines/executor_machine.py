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

# Executor states
IDLE = "idle"
PREPARING = "preparing"
RUNNING_QUEUE = "running_queue"
STOPPING_AT_BOUNDARY = "stopping_at_boundary"
CANCELING = "canceling"
ABORTING = "aborting"
RECOVERING = "recovering"
FINALIZING = "finalizing"
COMPLETED = "completed"
FAILED = "failed"
CANCELED = "canceled"
ABORTED = "aborted"

# Executor events
EXECUTE = "execute"
PRECHECK_PASSED = "precheck_passed"
PRECHECK_FAILED = "precheck_failed"
QUEUE_SELECTED = "queue_selected"
QUEUE_FINISHED = "queue_finished"
REQUEST_STOP_AT_BOUNDARY = "request_stop_at_boundary"
REQUEST_CANCEL = "request_cancel"
REQUEST_ABORT = "request_abort"
RUN_FAILURE = "run_failure"
RECOVERY_REQUESTED = "recovery_requested"
RECOVERY_COMPLETE = "recovery_complete"
FINALIZE_COMPLETE = "finalize_complete"
RESET = "reset"

STATES = {
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
}

TERMINAL_STATES = {COMPLETED, FAILED, CANCELED, ABORTED}

# transitions[state][event] -> target_state
TRANSITIONS: dict[str, dict[str, str]] = {
    IDLE: {
        EXECUTE: PREPARING,
        RECOVERY_REQUESTED: RECOVERING,
        RESET: IDLE,
    },
    PREPARING: {
        PRECHECK_PASSED: RUNNING_QUEUE,
        PRECHECK_FAILED: FINALIZING,
        REQUEST_CANCEL: CANCELING,
        REQUEST_ABORT: ABORTING,
    },
    RUNNING_QUEUE: {
        QUEUE_SELECTED: RUNNING_QUEUE,
        QUEUE_FINISHED: FINALIZING,
        REQUEST_STOP_AT_BOUNDARY: STOPPING_AT_BOUNDARY,
        REQUEST_CANCEL: CANCELING,
        REQUEST_ABORT: ABORTING,
        RUN_FAILURE: FINALIZING,
    },
    STOPPING_AT_BOUNDARY: {
        QUEUE_FINISHED: FINALIZING,
        REQUEST_CANCEL: CANCELING,
        REQUEST_ABORT: ABORTING,
        RUN_FAILURE: FINALIZING,
    },
    CANCELING: {
        QUEUE_FINISHED: FINALIZING,
        RUN_FAILURE: FINALIZING,
    },
    ABORTING: {
        QUEUE_FINISHED: FINALIZING,
        RUN_FAILURE: FINALIZING,
    },
    RECOVERING: {
        RECOVERY_COMPLETE: PREPARING,
        REQUEST_CANCEL: CANCELING,
        REQUEST_ABORT: ABORTING,
    },
    FINALIZING: {
        FINALIZE_COMPLETE: COMPLETED,
    },
    COMPLETED: {
        RESET: IDLE,
    },
    FAILED: {
        RECOVERY_REQUESTED: RECOVERING,
        RESET: IDLE,
    },
    CANCELED: {
        RESET: IDLE,
    },
    ABORTED: {
        RESET: IDLE,
    },
}


class ExecutorStateMachine(BaseStateMachine):
    def __init__(self, subject_id: str | None = None):
        super().__init__(
            states=STATES,
            terminal_states=TERMINAL_STATES,
            transitions=TRANSITIONS,
            initial_state=IDLE,
            subject_id=subject_id,
        )

    @property
    def is_alive(self) -> bool:
        return self._observed_state not in {IDLE, COMPLETED, FAILED, CANCELED, ABORTED, CANCELING, ABORTING}

    @property
    def is_running(self) -> bool:
        return self._observed_state in {RUNNING_QUEUE, STOPPING_AT_BOUNDARY}

    @property
    def is_canceling(self) -> bool:
        return self._observed_state in {CANCELING, ABORTING}

    @property
    def is_terminal(self) -> bool:
        return self._observed_state in TERMINAL_STATES

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

    def can_execute(self) -> bool:
        return self._observed_state == IDLE

    def can_stop_at_boundary(self) -> bool:
        return self._observed_state == RUNNING_QUEUE

    def can_cancel(self) -> bool:
        return self._observed_state not in {IDLE, *TERMINAL_STATES}

    def can_abort(self) -> bool:
        return self._observed_state not in {IDLE, *TERMINAL_STATES}

    def can_recover(self) -> bool:
        return self._observed_state in {FAILED, IDLE}

    def finalize_with_result(self, result: str, **kwargs: Any) -> None:
        target_map = {
            "completed": COMPLETED,
            "failed": FAILED,
            "canceled": CANCELED,
            "aborted": ABORTED,
        }
        target = target_map.get(result, COMPLETED)
        reason = kwargs.pop("reason", result)
        self.transition(
            FINALIZE_COMPLETE,
            source="finalize_with_result",
            reason=reason,
            **kwargs,
        )
        if self._observed_state == COMPLETED and target != COMPLETED:
            self.set_observed_state(target, source="finalize_with_result", reason=reason)
