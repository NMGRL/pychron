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

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


@dataclass
class TransitionRecord:
    old_state: str
    new_state: str
    event: str
    accepted: bool
    forced: bool = False
    source: str | None = None
    reason: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    subject_id: str | None = None


class BaseStateMachine:
    def __init__(
        self,
        states: set[str],
        terminal_states: set[str],
        transitions: dict[str, dict[str, str]],
        initial_state: str,
        subject_id: str | None = None,
    ):
        self._states = states
        self._terminal_states = terminal_states
        self._transitions = transitions
        self._initial_state = initial_state
        self._commanded_state: str = initial_state
        self._observed_state: str = initial_state
        self._subject_id = subject_id
        self.history: list[TransitionRecord] = []
        self._guards: dict[str, Callable[..., bool]] = {}
        self._effects: dict[str, Callable[..., None]] = {}
        self._compat_updates: dict[str, Callable[..., None]] = {}

    @property
    def commanded_state(self) -> str:
        return self._commanded_state

    @property
    def observed_state(self) -> str:
        return self._observed_state

    @property
    def subject_id(self) -> str | None:
        return self._subject_id

    def is_terminal(self, state: str | None = None) -> bool:
        s = state if state is not None else self._observed_state
        return s in self._terminal_states

    def register_guard(self, event: str, func: Callable[..., bool]) -> None:
        self._guards[event] = func

    def register_effect(self, event: str, func: Callable[..., None]) -> None:
        self._effects[event] = func

    def register_compat_update(self, event: str, func: Callable[..., None]) -> None:
        self._compat_updates[event] = func

    def transition(
        self,
        event: str,
        force: bool = False,
        source: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> TransitionRecord:
        current = self._observed_state
        state_map = self._transitions.get(current, {})
        target = state_map.get(event)

        if target is None:
            record = TransitionRecord(
                old_state=current,
                new_state=current,
                event=event,
                accepted=False,
                forced=force,
                source=source,
                reason=reason or "no transition defined",
                subject_id=self._subject_id,
            )
            self.history.append(record)
            return record

        if not force and event in self._guards:
            guard = self._guards[event]
            if not guard(**kwargs):
                record = TransitionRecord(
                    old_state=current,
                    new_state=current,
                    event=event,
                    accepted=False,
                    forced=force,
                    source=source,
                    reason="guard rejected",
                    subject_id=self._subject_id,
                )
                self.history.append(record)
                return record

        self._commanded_state = target
        if event in self._effects:
            self._effects[event](**kwargs)

        self._observed_state = target

        if event in self._compat_updates:
            self._compat_updates[event](**kwargs)

        record = TransitionRecord(
            old_state=current,
            new_state=target,
            event=event,
            accepted=True,
            forced=force,
            source=source,
            reason=reason,
            subject_id=self._subject_id,
        )
        self.history.append(record)
        return record

    def set_observed_state(
        self,
        state: str,
        source: str | None = None,
        reason: str | None = None,
    ) -> TransitionRecord:
        current = self._observed_state
        if state == current:
            return TransitionRecord(
                old_state=current,
                new_state=current,
                event="noop",
                accepted=True,
                source=source,
                reason=reason,
                subject_id=self._subject_id,
            )
        self._observed_state = state
        record = TransitionRecord(
            old_state=current,
            new_state=state,
            event="set_observed",
            accepted=True,
            source=source,
            reason=reason,
            subject_id=self._subject_id,
        )
        self.history.append(record)
        return record

    def reset(self, state: str | None = None) -> None:
        s = state if state is not None else self._initial_state
        self._commanded_state = s
        self._observed_state = s
        self.history.clear()
