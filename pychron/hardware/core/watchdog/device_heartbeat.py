"""Device heartbeat state machine for monitoring health and liveness.

Provides per-device/service health tracking with state transitions:
  HEALTHY → DEGRADED → UNAVAILABLE → RECOVERING → HEALTHY

Used by BaseCoreDevice to track communicator responsiveness and by software
services (DVC, DB, Dashboard) for connection health.
"""

import time
from enum import Enum
from typing import Optional, List


class HeartbeatState(Enum):
    """Device/service health state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"


class DeviceHeartbeat:
    """Per-device liveness contract with state machine.

    Tracks consecutive failures, time in state, and transitions through
    HEALTHY → DEGRADED → UNAVAILABLE → RECOVERING states based on
    operation success/failure patterns.

    Attributes:
        degraded_threshold: Failures before transitioning to DEGRADED (default: 2)
        unavailable_threshold: Failures before transitioning to UNAVAILABLE (default: 5)
    """

    def __init__(
        self,
        device_id: str,
        degraded_threshold: int = 2,
        unavailable_threshold: int = 5,
    ):
        """Initialize heartbeat for a device.

        Args:
            device_id: Unique identifier for device/service
            degraded_threshold: Consecutive failures before DEGRADED transition
            unavailable_threshold: Consecutive failures before UNAVAILABLE transition
        """
        self.device_id = device_id
        self.degraded_threshold = degraded_threshold
        self.unavailable_threshold = unavailable_threshold

        self._state = HeartbeatState.HEALTHY
        self._consecutive_failures = 0
        self._last_successful_op_time: Optional[float] = None
        self._last_state_change_time = time.time()
        self._recovery_attempts = 0

    def record_success(self) -> None:
        """Record successful operation, may transition to HEALTHY.

        Resets failure counter and transitions to HEALTHY state.
        """
        self._last_successful_op_time = time.time()
        old_state = self._state
        self._consecutive_failures = 0
        new_state = HeartbeatState.HEALTHY

        if old_state != new_state:
            self._transition_to(new_state)

    def record_failure(self, exc: Optional[Exception] = None) -> None:
        """Record failed operation, may transition to DEGRADED/UNAVAILABLE.

        Args:
            exc: Exception from failed operation (for logging/analysis)
        """
        self._consecutive_failures += 1
        old_state = self._state
        new_state = old_state

        # Determine next state based on failure count
        if self._consecutive_failures >= self.unavailable_threshold:
            new_state = HeartbeatState.UNAVAILABLE
        elif self._consecutive_failures >= self.degraded_threshold:
            new_state = HeartbeatState.DEGRADED

        if old_state != new_state:
            self._transition_to(new_state)

    def record_recovery_attempt(self) -> None:
        """Record recovery probe attempt.

        Transitions to RECOVERING when attempting to reconnect from
        UNAVAILABLE state.
        """
        self._recovery_attempts += 1
        if self._state != HeartbeatState.RECOVERING:
            self._transition_to(HeartbeatState.RECOVERING)

    def record_recovery_success(self) -> None:
        """Record successful recovery probe.

        Transitions from RECOVERING back to HEALTHY (short-circuits the
        failure threshold counter).
        """
        self._consecutive_failures = 0
        self._last_successful_op_time = time.time()
        self._recovery_attempts = 0
        if self._state != HeartbeatState.HEALTHY:
            self._transition_to(HeartbeatState.HEALTHY)

    def reset(self) -> None:
        """Manually reset device to HEALTHY state.

        Used when operator manually recovers device or for testing.
        """
        self._consecutive_failures = 0
        self._recovery_attempts = 0
        old_state = self._state
        if old_state != HeartbeatState.HEALTHY:
            self._transition_to(HeartbeatState.HEALTHY)

    def get_state(self) -> HeartbeatState:
        """Return current health state."""
        return self._state

    def is_healthy(self) -> bool:
        """Check if device is in HEALTHY state."""
        return self._state == HeartbeatState.HEALTHY

    def is_degraded(self) -> bool:
        """Check if device is in DEGRADED state."""
        return self._state == HeartbeatState.DEGRADED

    def is_unavailable(self) -> bool:
        """Check if device is in UNAVAILABLE state."""
        return self._state == HeartbeatState.UNAVAILABLE

    def is_recovering(self) -> bool:
        """Check if device is in RECOVERING state."""
        return self._state == HeartbeatState.RECOVERING

    def time_in_state(self) -> float:
        """Return seconds since last state change."""
        return time.time() - self._last_state_change_time

    def time_since_success(self) -> Optional[float]:
        """Return seconds since last successful operation.

        Returns None if no successful operations recorded.
        """
        if self._last_successful_op_time is None:
            return None
        return time.time() - self._last_successful_op_time

    def get_consecutive_failures(self) -> int:
        """Return count of consecutive failures."""
        return self._consecutive_failures

    def get_recovery_attempts(self) -> int:
        """Return count of recovery attempts."""
        return self._recovery_attempts

    def get_status_summary(self) -> dict:
        """Return dict with current health status.

        Returns:
            dict with keys: state, consecutive_failures, recovery_attempts,
                           time_in_state, time_since_success (or None)
        """
        return {
            "device_id": self.device_id,
            "state": self._state.value,
            "consecutive_failures": self._consecutive_failures,
            "recovery_attempts": self._recovery_attempts,
            "time_in_state": self.time_in_state(),
            "time_since_success": self.time_since_success(),
        }

    def _transition_to(self, new_state: HeartbeatState) -> None:
        """Internal: record state transition with timestamp."""
        self._state = new_state
        self._last_state_change_time = time.time()
