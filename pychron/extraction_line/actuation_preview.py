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
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActuationPreview:
    """Preview of what would happen if a valve actuation is executed."""

    requested_action: str  # "open" or "close"
    valve_name: str
    allowed: bool = True
    reasons_blocking: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    interlocks: List[str] = field(default_factory=list)
    affected_children: List[str] = field(default_factory=list)
    state_changes: List[str] = field(default_factory=list)
    network_region_changes: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    warning_level: str = "none"  # "none", "info", "warning", "error"
    is_soft_locked: bool = False
    is_enabled: bool = True
    current_state: Optional[bool] = None

    @property
    def summary(self) -> str:
        if not self.allowed:
            return "Blocked: {}".format("; ".join(self.reasons_blocking))
        parts = []
        if self.interlocks:
            parts.append("Interlocks: {}".format(", ".join(self.interlocks)))
        if self.affected_children:
            parts.append("Affects: {}".format(", ".join(self.affected_children)))
        if self.network_region_changes:
            parts.append("Region changes: {}".format(", ".join(self.network_region_changes)))
        return " | ".join(parts) if parts else "No side effects"
