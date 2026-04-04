"""Unit tests for RetryStrategy and CircuitBreaker."""

import time
import unittest

from pychron.hardware.core.watchdog.retry_strategy import (
    RetryStrategy,
    CircuitBreaker,
    CircuitBreakerOpen,
    BackoffType,
    CircuitBreakerState,
)


class TestRetryStrategy(unittest.TestCase):
    """Test RetryStrategy backoff calculations and configuration."""

    def test_fixed_backoff(self):
        """Fixed backoff returns same delay."""
        strategy = RetryStrategy(backoff_type=BackoffType.FIXED, initial_delay=0.1)
        self.assertEqual(strategy.calculate_delay(1), 0.1)
        self.assertEqual(strategy.calculate_delay(2), 0.1)
        self.assertEqual(strategy.calculate_delay(5), 0.1)

    def test_linear_backoff(self):
        """Linear backoff increases linearly."""
        strategy = RetryStrategy(backoff_type=BackoffType.LINEAR, initial_delay=0.1, max_delay=1.0)
        self.assertEqual(strategy.calculate_delay(1), 0.1)
        self.assertAlmostEqual(strategy.calculate_delay(2), 0.2, places=5)
        self.assertAlmostEqual(strategy.calculate_delay(5), 0.5, places=5)

    def test_exponential_backoff(self):
        """Exponential backoff increases exponentially."""
        strategy = RetryStrategy(
            backoff_type=BackoffType.EXPONENTIAL, initial_delay=0.1, backoff_factor=2.0
        )
        self.assertEqual(strategy.calculate_delay(1), 0.1)
        self.assertAlmostEqual(strategy.calculate_delay(2), 0.2, places=5)
        self.assertAlmostEqual(strategy.calculate_delay(3), 0.4, places=5)
        self.assertAlmostEqual(strategy.calculate_delay(4), 0.8, places=5)

    def test_fibonacci_backoff(self):
        """Fibonacci backoff follows Fibonacci sequence."""
        strategy = RetryStrategy(
            backoff_type=BackoffType.FIBONACCI, initial_delay=0.1, backoff_factor=1.0
        )
        # fib sequence: [1, 1, 2, 3, 5, ...]
        # attempt 1: 0.1 * fib[1]=1 -> 0.1
        # attempt 2: 0.1 * fib[2]=2 -> 0.2
        # attempt 3: 0.1 * fib[3]=3 -> 0.3
        # attempt 4: 0.1 * fib[4]=5 -> 0.5
        self.assertEqual(strategy.calculate_delay(1), 0.1)
        self.assertAlmostEqual(strategy.calculate_delay(2), 0.2, places=5)
        self.assertAlmostEqual(strategy.calculate_delay(3), 0.3, places=5)
        self.assertAlmostEqual(strategy.calculate_delay(4), 0.5, places=5)

    def test_backoff_clamped_to_max_delay(self):
        """Backoff is clamped to max_delay."""
        strategy = RetryStrategy(
            backoff_type=BackoffType.EXPONENTIAL,
            initial_delay=0.1,
            max_delay=0.5,
            backoff_factor=2.0,
        )
        self.assertEqual(strategy.calculate_delay(1), 0.1)
        self.assertEqual(strategy.calculate_delay(2), 0.2)
        self.assertEqual(strategy.calculate_delay(3), 0.4)
        self.assertEqual(strategy.calculate_delay(4), 0.5)  # Clamped
        self.assertEqual(strategy.calculate_delay(5), 0.5)  # Clamped

    def test_should_retry(self):
        """should_retry respects max_attempts."""
        strategy = RetryStrategy(max_attempts=3)
        self.assertTrue(strategy.should_retry(0))
        self.assertTrue(strategy.should_retry(1))
        self.assertTrue(strategy.should_retry(2))
        self.assertFalse(strategy.should_retry(3))

    def test_zero_delay_first_attempt(self):
        """First attempt (attempt=0) returns 0 delay."""
        strategy = RetryStrategy()
        self.assertEqual(strategy.calculate_delay(0), 0.0)

    def test_from_config(self):
        """Create RetryStrategy from config dict."""
        config = {
            "type": "exponential",
            "initial_delay": 0.05,
            "max_delay": 3.0,
            "max_attempts": 7,
            "backoff_factor": 1.5,
        }
        strategy = RetryStrategy.from_config(config)
        self.assertEqual(strategy.backoff_type, BackoffType.EXPONENTIAL)
        self.assertEqual(strategy.initial_delay, 0.05)
        self.assertEqual(strategy.max_delay, 3.0)
        self.assertEqual(strategy.max_attempts, 7)
        self.assertEqual(strategy.backoff_factor, 1.5)

    def test_from_config_defaults(self):
        """from_config uses defaults for missing keys."""
        strategy = RetryStrategy.from_config({})
        self.assertEqual(strategy.backoff_type, BackoffType.EXPONENTIAL)
        self.assertEqual(strategy.initial_delay, 0.025)
        self.assertEqual(strategy.max_delay, 2.0)
        self.assertEqual(strategy.max_attempts, 5)

    def test_get_config(self):
        """get_config returns configuration dict."""
        strategy = RetryStrategy(
            backoff_type=BackoffType.LINEAR,
            initial_delay=0.05,
            max_delay=1.5,
            max_attempts=4,
            backoff_factor=1.5,
        )
        config = strategy.get_config()
        self.assertEqual(config["type"], "linear")
        self.assertEqual(config["initial_delay"], 0.05)
        self.assertEqual(config["max_delay"], 1.5)
        self.assertEqual(config["max_attempts"], 4)
        self.assertEqual(config["backoff_factor"], 1.5)


class TestCircuitBreaker(unittest.TestCase):
    """Test CircuitBreaker state transitions and behavior."""

    def test_initial_state_closed(self):
        """Circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        self.assertFalse(cb.is_open())

    def test_call_passes_through_closed(self):
        """Calls pass through when CLOSED."""
        cb = CircuitBreaker()

        def success_func():
            return "success"

        result = cb.call(success_func)
        self.assertEqual(result, "success")

    def test_call_fails_when_open(self):
        """Calls fail-fast when OPEN."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)

        with self.assertRaises(CircuitBreakerOpen):
            cb.call(lambda: "should_fail")

    def test_transition_closed_to_open(self):
        """Reaches failure_threshold transitions to OPEN."""
        cb = CircuitBreaker(failure_threshold=3)
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)

    def test_success_resets_failures(self):
        """Success resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        cb.record_success()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)

    def test_transition_open_to_half_open(self):
        """Circuit transitions to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=0.1)  # 100ms timeout
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)
        time.sleep(0.15)  # Wait for timeout
        self.assertEqual(cb.get_state(), CircuitBreakerState.HALF_OPEN)

    def test_transition_half_open_to_closed(self):
        """Success in HALF_OPEN transitions to CLOSED."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=0.1, success_threshold=1)
        cb.record_failure()
        time.sleep(0.15)
        self.assertEqual(cb.get_state(), CircuitBreakerState.HALF_OPEN)
        cb.record_success()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)

    def test_transition_half_open_to_open(self):
        """Failure in HALF_OPEN transitions back to OPEN."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=0.1)
        cb.record_failure()
        time.sleep(0.15)
        self.assertEqual(cb.get_state(), CircuitBreakerState.HALF_OPEN)
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)

    def test_manual_reset(self):
        """Manual reset transitions to CLOSED."""
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)
        cb.reset()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)

    def test_call_with_exception(self):
        """Circuit breaker tracks exceptions from call."""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise ValueError("test error")

        # First call: exception recorded, failure count increases
        with self.assertRaises(ValueError):
            cb.call(failing_func)
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)

        # Second call: still raises, transitions to OPEN
        with self.assertRaises(ValueError):
            cb.call(failing_func)
        self.assertEqual(cb.get_state(), CircuitBreakerState.OPEN)

    def test_is_open_after_timeout(self):
        """is_open() returns False after timeout elapses."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=0.1)
        cb.record_failure()
        self.assertTrue(cb.is_open())
        time.sleep(0.15)
        self.assertFalse(cb.is_open())  # Transitioned to HALF_OPEN

    def test_multiple_successes_in_half_open(self):
        """Multiple successes in HALF_OPEN with threshold > 1."""
        cb = CircuitBreaker(failure_threshold=1, timeout_duration=0.1, success_threshold=2)
        cb.record_failure()
        time.sleep(0.15)
        self.assertEqual(cb.get_state(), CircuitBreakerState.HALF_OPEN)
        cb.record_success()
        self.assertEqual(cb.get_state(), CircuitBreakerState.HALF_OPEN)
        cb.record_success()
        self.assertEqual(cb.get_state(), CircuitBreakerState.CLOSED)


if __name__ == "__main__":
    unittest.main()
