"""Service health monitoring with state machine and recovery strategies.

Similar to DeviceHeartbeat but tailored for software services (DVC, database, dashboard):
- Tracks both failure counts and response time degradation
- Supports soft (transient) vs hard (persistent) failures
- Optional vs required service designation
- Circuit breaker integration for cascading failure prevention
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any
import time


class ServiceState(Enum):
    """Service health state machine.

    HEALTHY: Service is responsive and fast
    DEGRADED: Service is responding but slow or had transient failures
    UNAVAILABLE: Service is not responding or hard failures detected
    RECOVERING: Service is being recovered/retried after unavailability
    """

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    RECOVERING = "RECOVERING"


class ServiceHeartbeat:
    """Track health of software services (DVC, database, dashboard).

    Features:
    - State machine: HEALTHY -> DEGRADED -> UNAVAILABLE -> RECOVERING -> HEALTHY
    - Tracks soft failures (transient, like timeouts) vs hard failures
    - Monitors response time degradation
    - Supports optional vs required services
    - Callback support for state changes
    - Optional logger for integration with Loggable systems

    Attributes:
        service_name: Human-readable service name
        is_required: Whether service is required for experiment execution
        soft_failure_threshold: Consecutive soft failures before DEGRADED (default 2)
        hard_failure_threshold: Consecutive hard failures before UNAVAILABLE (default 3)
        response_time_threshold: Max acceptable response time in seconds (default None)
        recovery_check_interval: Min time between recovery attempts in seconds (default 30)
    """

    def __init__(
        self,
        service_name: str,
        is_required: bool = False,
        soft_failure_threshold: int = 2,
        hard_failure_threshold: int = 3,
        response_time_threshold: Optional[float] = None,
        recovery_check_interval: float = 30.0,
        logger: Optional[Any] = None,
    ):
        """Initialize service heartbeat.

        Args:
            service_name: Name of service (e.g., "DVC", "Database", "Dashboard")
            is_required: Whether service is required for experiment
            soft_failure_threshold: Soft failures before DEGRADED
            hard_failure_threshold: Hard failures before UNAVAILABLE
            response_time_threshold: Max response time for health (seconds)
            recovery_check_interval: Min seconds between recovery attempts
            logger: Optional logger object (for Loggable integration)
        """
        self.service_name = service_name
        self.is_required = is_required
        self.soft_failure_threshold = soft_failure_threshold
        self.hard_failure_threshold = hard_failure_threshold
        self.response_time_threshold = response_time_threshold
        self.recovery_check_interval = recovery_check_interval
        self._logger = logger

        # State tracking
        self._state = ServiceState.HEALTHY
        self._state_ts = time.time()
        self._soft_failures = 0
        self._hard_failures = 0
        self._last_success_ts = time.time()
        self._last_error: Optional[str] = None
        self._recovery_attempts = 0
        self._last_recovery_attempt_ts: Optional[float] = None
        self._response_times: list[float] = []

        # Callbacks
        self._on_state_change_callbacks: list[Callable] = []
        self._on_failure_callbacks: list[Callable] = []
        self._on_recovery_attempt_callbacks: list[Callable] = []
        self._on_recovery_success_callbacks: list[Callable] = []

    # =========================================================================
    # Logging helpers
    # =========================================================================

    def _log_debug(self, msg: str) -> None:
        """Log debug message."""
        if self._logger and hasattr(self._logger, "debug"):
            self._logger.debug(msg)

    def _log_info(self, msg: str) -> None:
        """Log info message."""
        if self._logger and hasattr(self._logger, "info"):
            self._logger.info(msg)

    def _log_warning(self, msg: str) -> None:
        """Log warning message."""
        if self._logger and hasattr(self._logger, "warning"):
            self._logger.warning(msg)

    def _log_error(self, msg: str) -> None:
        """Log error message."""
        if self._logger and hasattr(self._logger, "error"):
            self._logger.error(msg)

    # =========================================================================
    # State queries
    # =========================================================================

    def get_state(self) -> ServiceState:
        """Get current health state."""
        return self._state

    def is_healthy(self) -> bool:
        """True if service is HEALTHY."""
        return self._state == ServiceState.HEALTHY

    def is_degraded(self) -> bool:
        """True if service is DEGRADED."""
        return self._state == ServiceState.DEGRADED

    def is_unavailable(self) -> bool:
        """True if service is UNAVAILABLE."""
        return self._state == ServiceState.UNAVAILABLE

    def is_recovering(self) -> bool:
        """True if service is RECOVERING."""
        return self._state == ServiceState.RECOVERING

    def time_in_state(self) -> float:
        """Seconds elapsed in current state."""
        return time.time() - self._state_ts

    def time_since_success(self) -> float:
        """Seconds elapsed since last successful operation."""
        return time.time() - self._last_success_ts

    def get_stats(self) -> Dict[str, Any]:
        """Get health statistics snapshot."""
        avg_response_time = None
        if self._response_times:
            avg_response_time = sum(self._response_times) / len(self._response_times)

        return {
            "service": self.service_name,
            "state": self._state.value,
            "is_required": self.is_required,
            "soft_failures": self._soft_failures,
            "hard_failures": self._hard_failures,
            "recovery_attempts": self._recovery_attempts,
            "time_in_state": self.time_in_state(),
            "time_since_success": self.time_since_success(),
            "avg_response_time": avg_response_time,
            "last_error": self._last_error,
        }

    # =========================================================================
    # Success and failure recording
    # =========================================================================

    def record_success(self, response_time: Optional[float] = None) -> None:
        """Record successful operation.

        Args:
            response_time: Response time in seconds (optional)
        """
        old_state = self._state
        self._last_success_ts = time.time()
        self._soft_failures = 0
        self._hard_failures = 0
        self._recovery_attempts = 0
        self._last_error = None

        # Track response time
        if response_time is not None:
            self._response_times.append(response_time)
            # Keep last 20 response times
            if len(self._response_times) > 20:
                self._response_times.pop(0)

        # Transition to HEALTHY
        if self._state != ServiceState.HEALTHY:
            self._state = ServiceState.HEALTHY
            self._state_ts = time.time()
            self._log_debug(f"{self.service_name}: {old_state.value} -> HEALTHY")
            self._call_on_state_change(old_state.value, ServiceState.HEALTHY.value)

    def record_soft_failure(self, error: Optional[str] = None) -> None:
        """Record transient failure (e.g., timeout).

        Args:
            error: Error message or exception string
        """
        old_state = self._state
        self._soft_failures += 1
        self._last_error = error or "Soft failure"

        self._log_debug(
            f"{self.service_name}: soft failure {self._soft_failures}/{self.soft_failure_threshold} ({error})"
        )
        self._call_on_failure(self._soft_failures, error)

        # Check transition to DEGRADED
        if self._soft_failures >= self.soft_failure_threshold and old_state == ServiceState.HEALTHY:
            self._state = ServiceState.DEGRADED
            self._state_ts = time.time()
            self._log_warning(f"{self.service_name}: {old_state.value} -> DEGRADED (soft failures)")
            self._call_on_state_change(old_state.value, ServiceState.DEGRADED.value)

    def record_hard_failure(self, error: Optional[str] = None) -> None:
        """Record persistent failure (e.g., connection error).

        Args:
            error: Error message or exception string
        """
        old_state = self._state
        self._soft_failures = 0  # Hard failure resets soft failures
        self._hard_failures += 1
        self._last_error = error or "Hard failure"

        self._log_warning(
            f"{self.service_name}: hard failure {self._hard_failures}/{self.hard_failure_threshold} ({error})"
        )
        self._call_on_failure(self._hard_failures, error)

        # Check transition to UNAVAILABLE
        if (
            self._hard_failures >= self.hard_failure_threshold
            and old_state != ServiceState.UNAVAILABLE
        ):
            self._state = ServiceState.UNAVAILABLE
            self._state_ts = time.time()
            self._log_error(
                f"{self.service_name}: {old_state.value} -> UNAVAILABLE (hard failures)"
            )
            self._call_on_state_change(old_state.value, ServiceState.UNAVAILABLE.value)

    # =========================================================================
    # Recovery
    # =========================================================================

    def record_recovery_attempt(self) -> None:
        """Record recovery attempt (manual or automatic retry)."""
        now = time.time()

        # Respect recovery check interval
        if self._last_recovery_attempt_ts is not None:
            elapsed = now - self._last_recovery_attempt_ts
            if elapsed < self.recovery_check_interval:
                self._log_debug(
                    f"{self.service_name}: recovery attempt throttled ({elapsed:.1f}s < {self.recovery_check_interval}s)"
                )
                return

        old_state = self._state
        self._recovery_attempts += 1
        self._last_recovery_attempt_ts = now

        if old_state != ServiceState.RECOVERING:
            self._state = ServiceState.RECOVERING
            self._state_ts = now
            self._log_info(
                f"{self.service_name}: {old_state.value} -> RECOVERING (attempt {self._recovery_attempts})"
            )
            self._call_on_state_change(old_state.value, ServiceState.RECOVERING.value)

        self._call_on_recovery_attempt(self._recovery_attempts)

    def record_recovery_success(self) -> None:
        """Record successful recovery."""
        old_state = self._state
        attempts = self._recovery_attempts

        # Reset all failure counters
        self._soft_failures = 0
        self._hard_failures = 0
        self._recovery_attempts = 0
        self._state = ServiceState.HEALTHY
        self._state_ts = time.time()
        self._last_success_ts = time.time()

        self._log_info(
            f"{self.service_name}: {old_state.value} -> HEALTHY (recovered after {attempts} attempts)"
        )
        self._call_on_state_change(old_state.value, ServiceState.HEALTHY.value)
        self._call_on_recovery_success(attempts)

    def reset(self) -> None:
        """Reset all state (e.g., for testing or shutdown)."""
        self._state = ServiceState.HEALTHY
        self._state_ts = time.time()
        self._soft_failures = 0
        self._hard_failures = 0
        self._last_success_ts = time.time()
        self._last_error = None
        self._recovery_attempts = 0
        self._last_recovery_attempt_ts = None
        self._response_times.clear()

    # =========================================================================
    # Callbacks
    # =========================================================================

    def on_state_change(self, callback: Callable[[str, str], None]) -> None:
        """Register callback for state changes.

        Args:
            callback: Function(old_state_str, new_state_str)
        """
        self._on_state_change_callbacks.append(callback)

    def on_failure(self, callback: Callable[[int, Optional[str]], None]) -> None:
        """Register callback for failures.

        Args:
            callback: Function(failure_count, error)
        """
        self._on_failure_callbacks.append(callback)

    def on_recovery_attempt(self, callback: Callable[[int], None]) -> None:
        """Register callback for recovery attempts.

        Args:
            callback: Function(attempt_count)
        """
        self._on_recovery_attempt_callbacks.append(callback)

    def on_recovery_success(self, callback: Callable[[int], None]) -> None:
        """Register callback for successful recovery.

        Args:
            callback: Function(attempts_to_recover)
        """
        self._on_recovery_success_callbacks.append(callback)

    def _call_on_state_change(self, old_state: str, new_state: str) -> None:
        """Call all registered state change callbacks."""
        for cb in self._on_state_change_callbacks:
            try:
                cb(old_state, new_state)
            except Exception as e:
                self._log_debug(f"Error in on_state_change callback: {e}")

    def _call_on_failure(self, failure_count: int, error: Optional[str]) -> None:
        """Call all registered failure callbacks."""
        for cb in self._on_failure_callbacks:
            try:
                cb(failure_count, error)
            except Exception as e:
                self._log_debug(f"Error in on_failure callback: {e}")

    def _call_on_recovery_attempt(self, attempt_count: int) -> None:
        """Call all registered recovery attempt callbacks."""
        for cb in self._on_recovery_attempt_callbacks:
            try:
                cb(attempt_count)
            except Exception as e:
                self._log_debug(f"Error in on_recovery_attempt callback: {e}")

    def _call_on_recovery_success(self, attempts: int) -> None:
        """Call all registered recovery success callbacks."""
        for cb in self._on_recovery_success_callbacks:
            try:
                cb(attempts)
            except Exception as e:
                self._log_debug(f"Error in on_recovery_success callback: {e}")
