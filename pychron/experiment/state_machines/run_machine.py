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

# Run states
RUN_IDLE = "run_idle"
RUN_CREATED = "run_created"
RUN_STARTING = "run_starting"
RUN_PRECHECK = "run_precheck"
RUN_EXTRACTING = "run_extracting"
RUN_WAITING_OVERLAP_SIGNAL = "run_waiting_overlap_signal"
RUN_WAITING_MIN_PUMPTIME = "run_waiting_min_pumptime"
RUN_MEASURING = "run_measuring"
RUN_POST_MEASUREMENT = "run_post_measurement"
RUN_SAVING = "run_saving"
RUN_FINISHING = "run_finishing"
RUN_SUCCESS = "run_success"
RUN_FAILED = "run_failed"
RUN_TRUNCATED = "run_truncated"
RUN_CANCELED = "run_canceled"
RUN_ABORTED = "run_aborted"
RUN_INVALID = "run_invalid"

# Run events
CREATE = "create"
START = "start"
PRECHECK_PASSED = "precheck_passed"
PRECHECK_FAILED = "precheck_failed"
START_EXTRACTION = "start_extraction"
EXTRACTION_COMPLETE = "extraction_complete"
EXTRACTION_FAILED = "extraction_failed"
WAIT_OVERLAP = "wait_overlap"
OVERLAP_SIGNALLED = "overlap_signalled"
MIN_PUMPTIME_COMPLETE = "min_pumptime_complete"
START_MEASUREMENT = "start_measurement"
MEASUREMENT_COMPLETE = "measurement_complete"
MEASUREMENT_FAILED = "measurement_failed"
START_POST_MEASUREMENT = "start_post_measurement"
POST_MEASUREMENT_COMPLETE = "post_measurement_complete"
POST_MEASUREMENT_FAILED = "post_measurement_failed"
START_SAVE = "start_save"
SAVE_COMPLETE = "save_complete"
SAVE_FAILED = "save_failed"
TRUNCATE = "truncate"
CANCEL = "cancel"
ABORT = "abort"
MARK_INVALID = "mark_invalid"
FINISH = "finish"
RESET = "reset"

STATES = {
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
}

TERMINAL_STATES = {
    RUN_SUCCESS,
    RUN_FAILED,
    RUN_TRUNCATED,
    RUN_CANCELED,
    RUN_ABORTED,
    RUN_INVALID,
}

TRANSITIONS: dict[str, dict[str, str]] = {
    RUN_IDLE: {
        CREATE: RUN_CREATED,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
        MARK_INVALID: RUN_INVALID,
    },
    RUN_CREATED: {
        START: RUN_STARTING,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
        MARK_INVALID: RUN_INVALID,
    },
    RUN_STARTING: {
        PRECHECK_PASSED: RUN_PRECHECK,
        PRECHECK_FAILED: RUN_FAILED,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_PRECHECK: {
        START_EXTRACTION: RUN_EXTRACTING,
        WAIT_OVERLAP: RUN_WAITING_OVERLAP_SIGNAL,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
        MARK_INVALID: RUN_INVALID,
    },
    RUN_EXTRACTING: {
        EXTRACTION_COMPLETE: RUN_MEASURING,
        EXTRACTION_FAILED: RUN_FAILED,
        WAIT_OVERLAP: RUN_WAITING_OVERLAP_SIGNAL,
        TRUNCATE: RUN_TRUNCATED,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_WAITING_OVERLAP_SIGNAL: {
        OVERLAP_SIGNALLED: RUN_WAITING_MIN_PUMPTIME,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_WAITING_MIN_PUMPTIME: {
        MIN_PUMPTIME_COMPLETE: RUN_MEASURING,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_MEASURING: {
        MEASUREMENT_COMPLETE: RUN_POST_MEASUREMENT,
        MEASUREMENT_FAILED: RUN_FAILED,
        TRUNCATE: RUN_TRUNCATED,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_POST_MEASUREMENT: {
        POST_MEASUREMENT_COMPLETE: RUN_SAVING,
        POST_MEASUREMENT_FAILED: RUN_FAILED,
        START_SAVE: RUN_SAVING,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_SAVING: {
        SAVE_COMPLETE: RUN_FINISHING,
        SAVE_FAILED: RUN_FAILED,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_FINISHING: {
        FINISH: RUN_SUCCESS,
        CANCEL: RUN_CANCELED,
        ABORT: RUN_ABORTED,
    },
    RUN_SUCCESS: {
        RESET: RUN_IDLE,
    },
    RUN_FAILED: {
        RESET: RUN_IDLE,
    },
    RUN_TRUNCATED: {
        FINISH: RUN_SUCCESS,
        START_SAVE: RUN_SAVING,
        RESET: RUN_IDLE,
    },
    RUN_CANCELED: {
        RESET: RUN_IDLE,
    },
    RUN_ABORTED: {
        RESET: RUN_IDLE,
    },
    RUN_INVALID: {
        RESET: RUN_IDLE,
    },
}


class RunStateMachine(BaseStateMachine):
    def __init__(self, subject_id: str | None = None):
        super().__init__(
            states=STATES,
            terminal_states=TERMINAL_STATES,
            transitions=TRANSITIONS,
            initial_state=RUN_IDLE,
            subject_id=subject_id,
        )

    @property
    def is_extracting(self) -> bool:
        return self._observed_state == RUN_EXTRACTING

    @property
    def is_measuring(self) -> bool:
        return self._observed_state == RUN_MEASURING

    @property
    def is_running(self) -> bool:
        return self._observed_state not in {RUN_IDLE, *TERMINAL_STATES}

    @property
    def is_terminal(self) -> bool:
        return self._observed_state in TERMINAL_STATES

    @property
    def is_waiting_overlap(self) -> bool:
        return self._observed_state in {
            RUN_WAITING_OVERLAP_SIGNAL,
            RUN_WAITING_MIN_PUMPTIME,
        }

    @property
    def is_saving(self) -> bool:
        return self._observed_state == RUN_SAVING

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

    def map_to_legacy_state(self) -> str:
        mapping = {
            RUN_IDLE: "not run",
            RUN_CREATED: "not run",
            RUN_STARTING: "not run",
            RUN_PRECHECK: "not run",
            RUN_EXTRACTING: "extraction",
            RUN_WAITING_OVERLAP_SIGNAL: "extraction",
            RUN_WAITING_MIN_PUMPTIME: "extraction",
            RUN_MEASURING: "measurement",
            RUN_POST_MEASUREMENT: "measurement",
            RUN_SAVING: "measurement",
            RUN_FINISHING: "measurement",
            RUN_SUCCESS: "success",
            RUN_FAILED: "failed",
            RUN_TRUNCATED: "truncated",
            RUN_CANCELED: "canceled",
            RUN_ABORTED: "aborted",
            RUN_INVALID: "invalid",
        }
        return mapping.get(self._observed_state, "not run")
