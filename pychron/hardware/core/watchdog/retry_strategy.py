"""Retry strategies and circuit breaker patterns for resilient communication.

Provides configurable backoff strategies (fixed, linear, exponential, fibonacci)
and circuit breaker pattern to prevent cascading failures during communication
with devices and services.
"""

import time
from enum import Enum
from typing import Callable, Any, Optional


class BackoffType(Enum):
    """Backoff strategy type."""

    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


class CircuitBreakerState(Enum):
    """Circuit breaker state."""

    CLOSED = "closed"  # Normal operation, pass through
    OPEN = "open"  # Failing, fast-fail new attempts
    HALF_OPEN = "half_open"  # Testing recovery


class RetryStrategy:
    """Configurable retry strategy with backoff.

    Attributes:
        backoff_type: Type of backoff (fixed, linear, exponential, fibonacci)
        initial_delay: Starting delay in seconds
        max_delay: Maximum delay between retries
        max_attempts: Total number of attempts before giving up
        backoff_factor: Multiplier for exponential/fibonacci backoff
    """

    def __init__(
        self,
        backoff_type: BackoffType | str = BackoffType.EXPONENTIAL,
        initial_delay: float = 0.025,
        max_delay: float = 2.0,
        max_attempts: int = 5,
        backoff_factor: float = 2.0,
    ):
        """Initialize retry strategy.

        Args:
            backoff_type: Type of backoff strategy
            initial_delay: Starting delay in seconds (default: 25ms)
            max_delay: Maximum delay between retries (default: 2s)
            max_attempts: Maximum number of attempts (default: 5)
            backoff_factor: Multiplier for exponential/fibonacci (default: 2.0)
        """
        if isinstance(backoff_type, str):
            backoff_type = BackoffType(backoff_type)
        self.backoff_type = backoff_type
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        # Cached fibonacci sequence for efficiency
        self._fib_cache = [1, 1]

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed).

        Args:
            attempt: Attempt number (0 for first attempt)

        Returns:
            Delay in seconds, clamped to [initial_delay, max_delay]
        """
        if attempt <= 0:
            return 0.0

        if self.backoff_type == BackoffType.FIXED:
            delay = self.initial_delay
        elif self.backoff_type == BackoffType.LINEAR:
            delay = self.initial_delay * attempt
        elif self.backoff_type == BackoffType.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        elif self.backoff_type == BackoffType.FIBONACCI:
            delay = self.initial_delay * self._get_fibonacci(attempt)
        else:
            delay = self.initial_delay

        # Clamp to range [initial_delay, max_delay]
        return min(max(delay, self.initial_delay), self.max_delay)

    def should_retry(self, attempt: int) -> bool:
        """Check if should retry based on attempt count.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False if max attempts exceeded
        """
        return attempt < self.max_attempts

    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number (1-indexed), with caching."""
        while len(self._fib_cache) <= n:
            self._fib_cache.append(self._fib_cache[-1] + self._fib_cache[-2])
        return self._fib_cache[n]

    @classmethod
    def from_config(cls, config: dict) -> "RetryStrategy":
        """Create RetryStrategy from configuration dict.

        Args:
            config: Dict with optional keys: type, initial_delay, max_delay,
                    max_attempts, backoff_factor

        Returns:
            RetryStrategy instance with config values or defaults
        """
        return cls(
            backoff_type=config.get("type", "exponential"),
            initial_delay=float(config.get("initial_delay", 0.025)),
            max_delay=float(config.get("max_delay", 2.0)),
            max_attempts=int(config.get("max_attempts", 5)),
            backoff_factor=float(config.get("backoff_factor", 2.0)),
        )

    def get_config(self) -> dict:
        """Return configuration as dict."""
        return {
            "type": self.backoff_type.value,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "max_attempts": self.max_attempts,
            "backoff_factor": self.backoff_factor,
        }


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures.

    States:
        CLOSED: Normal operation, all calls pass through
        OPEN: Too many failures, fail-fast for new calls
        HALF_OPEN: Testing if service recovered, allow one probe

    When OPEN, after timeout_duration seconds transitions to HALF_OPEN.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 1,
        timeout_duration: float = 30.0,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures before opening (default: 5)
            success_threshold: Consecutive successes before closing from HALF_OPEN (default: 1)
            timeout_duration: Seconds to wait in OPEN before HALF_OPEN (default: 30s)
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_duration = timeout_duration

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change_time = time.time()

    def is_open(self) -> bool:
        """Check if circuit is open (fail-fast mode)."""
        if self._state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed to transition to HALF_OPEN
            time_since_open = time.time() - self._last_state_change_time
            if time_since_open >= self.timeout_duration:
                self._transition_to(CircuitBreakerState.HALF_OPEN)
                return False  # Allow one probe attempt
            return True
        return False

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Callable to execute
            *args: Positional arguments to func
            **kwargs: Keyword arguments to func

        Returns:
            Result of func execution

        Raises:
            Exception from func if any, or CircuitBreakerOpen if circuit open
        """
        if self.is_open():
            raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def record_success(self) -> None:
        """Record successful call."""
        self._failure_count = 0
        self._success_count += 1

        if self._state == CircuitBreakerState.HALF_OPEN:
            if self._success_count >= self.success_threshold:
                self._transition_to(CircuitBreakerState.CLOSED)

    def record_failure(self) -> None:
        """Record failed call."""
        self._last_failure_time = time.time()
        self._failure_count += 1
        self._success_count = 0

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._transition_to(CircuitBreakerState.OPEN)
        elif (
            self._state == CircuitBreakerState.CLOSED
            and self._failure_count >= self.failure_threshold
        ):
            self._transition_to(CircuitBreakerState.OPEN)

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self._failure_count = 0
        self._success_count = 0
        if self._state != CircuitBreakerState.CLOSED:
            self._transition_to(CircuitBreakerState.CLOSED)

    def get_state(self) -> CircuitBreakerState:
        """Return current circuit state."""
        # Check for timeout transition while getting state
        if self._state == CircuitBreakerState.OPEN:
            time_since_open = time.time() - self._last_state_change_time
            if time_since_open >= self.timeout_duration:
                self._transition_to(CircuitBreakerState.HALF_OPEN)
        return self._state

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """Internal: record state transition."""
        self._state = new_state
        self._last_state_change_time = time.time()
        if new_state != CircuitBreakerState.HALF_OPEN:
            self._failure_count = 0
            self._success_count = 0


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass
