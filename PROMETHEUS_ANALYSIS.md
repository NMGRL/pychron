# Prometheus Observability Implementation - Code Analysis Report

**Analysis Date:** April 5, 2026  
**Codebase:** Pychron  
**Files Analyzed:** ~1,319 lines across 9 files  
**Test Coverage:** 54 tests, all passing (except executor_watchdog_integration tests with 3 failures)

---

## Executive Summary

The Prometheus observability implementation in Pychron is **well-structured and production-ready** with **minor edge cases and one critical compatibility issue**. The code demonstrates:

- Strong defensive programming with try-except blocks and graceful degradation
- Good separation of concerns between metrics, exporter, and registry
- Comprehensive test coverage for core functionality
- Clean API design for metrics recording

**Critical Finding:** ExecutorWatchdogIntegration has incompatible API calls with the actual DeviceQuorumChecker implementation (3 test failures).

---

## Detailed Analysis

### 1. CRITICAL ISSUES

#### [CRITICAL-1] Incorrect DeviceQuorumChecker Constructor Call
**Location:** `pychron/experiment/executor_watchdog_integration.py`, lines 78-84  
**Severity:** CRITICAL - Will crash at runtime  
**Issue:**
```python
def device_quorum_checker(self):
    """Lazy-load DeviceQuorumChecker."""
    if self._device_quorum_checker is None:
        from pychron.hardware.core.watchdog import DeviceQuorumChecker
        self._device_quorum_checker = DeviceQuorumChecker(logger=self.logger)  # ❌ WRONG
        return self._device_quorum_checker
```

**Actual API:** DeviceQuorumChecker.__init__(phase_requirements=None)  
**Expected:** No logger parameter accepted  
**Impact:** Any code accessing `watchdog.device_quorum_checker` will fail with TypeError

**Fix:**
```python
self._device_quorum_checker = DeviceQuorumChecker()
# Or if phase_requirements are needed:
self._device_quorum_checker = DeviceQuorumChecker(phase_requirements={})
```

---

#### [CRITICAL-2] Accessing Private prometheus_client Registry Attributes
**Location:** `pychron/observability/registry.py`, lines 46, 75, 109  
**Severity:** CRITICAL - Fragile and unsupported API  
**Issue:**
```python
except ValueError:
    # Metric already registered, retrieve it
    return registry._names_to_collectors[name]  # ❌ PRIVATE API
```

**Problem:**
- `_names_to_collectors` is a private attribute (underscore prefix convention)
- Not documented in prometheus_client API
- Could break with library version updates
- Violates the library's intended interface

**Impact:** Metrics deduplication is unreliable; could cause KeyError or AttributeError

**Fix:** Use the library's public API or document the internal dependency:
```python
except ValueError as e:
    # Metric already registered, attempt retrieval
    if "Duplicated timeseries" in str(e):
        # Log warning and return a no-op metric wrapper
        logger.warning(f"Metric {name} already registered, using existing")
        # Attempt safe retrieval with fallback
        try:
            return registry._names_to_collectors[name]
        except (AttributeError, KeyError):
            # Fall back to creating a new instance with forced registry
            return Metric(name, description, labelnames=labelnames, registry=registry)
```

Or better solution: Document prometheus_client version requirement and add unit test for this specific scenario.

---

### 2. MAJOR ISSUES

#### [MAJOR-1] Thread Safety - Unsynchronized Global State
**Location:** `pychron/observability/metrics.py`, lines 13-14, 23-24, 33, 55-57  
**Severity:** MAJOR - Race condition in multi-threaded context  
**Issue:**
```python
_config: MetricsConfig | None = None
_init_errors_logged: set[str] = set()

def configure(config: MetricsConfig) -> None:
    global _config
    _config = config  # ❌ NOT THREAD-SAFE

def _log_once(error_key: str, message: str) -> None:
    if error_key not in _init_errors_logged:  # ❌ RACE CONDITION
        logger.warning(message)
        _init_errors_logged.add(error_key)  # ❌ NON-ATOMIC
```

**Problem:**
- No locks protecting global state
- Two threads could both log the "same" error
- Configuration could be changed mid-metric-recording
- Set modification during iteration (if iteration happens)

**Impact:** 
- Duplicate error logs in concurrent scenarios
- Potential configuration inconsistency
- May cause issues with Prometheus metric name conflicts

**Fix:**
```python
import threading

_config_lock = threading.RLock()
_error_lock = threading.Lock()
_config: MetricsConfig | None = None
_init_errors_logged: set[str] = set()

def configure(config: MetricsConfig) -> None:
    global _config
    with _config_lock:
        _config = config

def get_config() -> MetricsConfig:
    global _config
    with _config_lock:
        if _config is None:
            _config = MetricsConfig(enabled=False)
        return _config

def _log_once(error_key: str, message: str) -> None:
    with _error_lock:
        if error_key not in _init_errors_logged:
            logger.warning(message)
            _init_errors_logged.add(error_key)
```

---

#### [MAJOR-2] Thread Safety - Global Registry Access
**Location:** `pychron/observability/registry.py`, lines 14-17  
**Severity:** MAJOR - Non-atomic singleton creation  
**Issue:**
```python
_registry: CollectorRegistry | None = None

def get_registry() -> CollectorRegistry:
    global _registry
    if _registry is None:
        _registry = CollectorRegistry()  # ❌ DOUBLE-CHECK LOCKING NEEDED
    return _registry
```

**Problem:**
- Double-checked locking without actual locking
- Two concurrent threads could create two different registries
- Metrics would be recorded to different registries, losing data
- prometheus_client might also have internal locking, but it's not guaranteed

**Impact:** In multi-threaded experiment execution, metrics could be split across multiple registries

**Fix:**
```python
import threading

_registry: CollectorRegistry | None = None
_registry_lock = threading.Lock()

def get_registry() -> CollectorRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:  # Double-check after acquiring lock
                _registry = CollectorRegistry()
    return _registry
```

---

#### [MAJOR-3] Missing Error Context in Device IO Metrics Recording
**Location:** `pychron/experiment/telemetry/device_io.py`, lines 77-79, 248-254  
**Severity:** MAJOR - Silent failures hide problems  
**Issue:**
```python
except Exception:
    # Silently ignore any metrics recording failures
    pass
```

**Problem:**
- Errors are completely silent - no logging
- Makes debugging difficult
- Could hide corruption or configuration issues
- Different from metrics.py which uses _log_once()

**Impact:** 
- Prometheus metrics silently fail to record
- No visibility into why metrics aren't appearing
- Makes troubleshooting in production difficult

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)
_metrics_error_logged = set()

def _record_prometheus_device_io_metrics(...) -> None:
    try:
        # ... existing code ...
    except Exception as e:
        error_key = f"device_io_{device_name}_{operation_type}"
        if error_key not in _metrics_error_logged:
            logger.warning(
                f"Failed to record device I/O metrics for {device_name}/{operation_type}: {e}"
            )
            _metrics_error_logged.add(error_key)
```

---

#### [MAJOR-4] Label Validation Not Enforced
**Location:** `pychron/observability/metrics.py`, lines 60-88, 90-120, 122-159  
**Severity:** MAJOR - Silent label mismatches  
**Issue:**
```python
def inc_counter(
    name: str,
    description: str,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
) -> None:
    # No validation that labelvalues keys match labels
    labelvalues = labelvalues or {}
    full_name = f"{get_config().namespace}_{name}"
    labels = labels or []
    counter = registry.counter(full_name, description, labelnames=labels)
    if labelvalues:
        counter.labels(**labelvalues).inc()  # ❌ Prometheus will raise KeyError if mismatch
```

**Problem:**
- If caller passes labels=["a", "b"] but labelvalues={"a": "1"}, prometheus_client raises KeyError
- No defensive check before calling .labels(**labelvalues)
- Error message could be confusing to users
- Different labelvalues across calls to same metric could cause hidden conflicts

**Impact:**
- Unexpected KeyErrors in production
- Inconsistent metrics recording across calls
- Difficult to debug label mismatch issues

**Fix:**
```python
def inc_counter(
    name: str,
    description: str,
    labels: list[str] | None = None,
    labelvalues: dict[str, str] | None = None,
) -> None:
    if not is_enabled():
        return
    
    labelvalues = labelvalues or {}
    labels = labels or []
    
    # Validate label consistency
    if labels and labelvalues:
        missing_labels = set(labels) - set(labelvalues.keys())
        if missing_labels:
            logger.warning(
                f"Counter {name}: Missing label values for {missing_labels}. "
                f"Expected {labels}, got {list(labelvalues.keys())}"
            )
            return
        
        extra_labels = set(labelvalues.keys()) - set(labels)
        if extra_labels:
            logger.warning(
                f"Counter {name}: Extra label values {extra_labels}. "
                f"Expected {labels}, got {list(labelvalues.keys())}"
            )
            # Filter to matching labels only
            labelvalues = {k: v for k, v in labelvalues.items() if k in labels}
    
    try:
        full_name = f"{get_config().namespace}_{name}"
        counter = registry.counter(full_name, description, labelnames=labels)
        if labelvalues:
            counter.labels(**labelvalues).inc()
        else:
            counter.inc()
    except Exception as e:
        _log_once(f"counter_{name}", f"Failed to increment counter {name}: {e}")
```

---

#### [MAJOR-5] Incomplete Test for ExecutorWatchdogIntegration
**Location:** `pychron/experiment/tests/test_executor_watchdog_integration.py`  
**Severity:** MAJOR - 3 failing tests  
**Issues:**
1. Line 98: Attempts to access non-existent `watchdog.device_quorum_checker` property with wrong API
2. Line 223: Tests access private `_successes` attribute that may not exist
3. Line 349: Tests non-existent `watchdog.watchdog` property

**Impact:** Test suite shows failures; indicates untested code paths

**Fix:** Update tests to match actual implementation:
```python
def test_lazy_load_device_quorum_checker(self):
    """Test lazy-loading of device quorum checker."""
    with patch("pychron.experiment.executor_watchdog_integration.globalv") as mock_globalv:
        mock_globalv.watchdog_enabled = True
        watchdog = ExecutorWatchdogIntegration(self.executor)
        
        # First access should create the checker
        checker1 = watchdog.device_quorum_checker
        checker2 = watchdog.device_quorum_checker
        
        # Should return the same instance
        self.assertIs(checker1, checker2)
```

---

### 3. MINOR ISSUES

#### [MINOR-1] Inconsistent Error Handling Styles
**Location:** Multiple files  
**Severity:** MINOR - Code consistency  
**Issue:**
- `metrics.py`: Uses `_log_once()` with controlled error logging
- `device_io.py`: Uses silent `except Exception: pass`
- `executor_watchdog_integration.py`: Uses `logger.warning()`

**Problem:** Inconsistent patterns make codebase harder to maintain

**Fix:** Standardize on the `_log_once()` pattern across all modules:
```python
# In device_io.py - add logger like metrics.py
import logging
from . import _metrics_errors

logger = logging.getLogger(__name__)
_metrics_error_logged = set()  # or import from metrics module

def _log_once_metric_error(error_key: str, message: str):
    if error_key not in _metrics_error_logged:
        logger.warning(message)
        _metrics_error_logged.add(error_key)
```

---

#### [MINOR-2] Type Annotations Missing from Some Functions
**Location:** `pychron/observability/tasks/plugin.py`, line 96 (return type missing)  
**Severity:** MINOR - Type hint coverage  
**Issue:**
```python
def check(self) -> bool:  # ✓ Has return type
    # ...

def _configure_observability(self) -> None:  # ✓ Has return type
    # ...

def __init__(self, *args, **kw):  # ❌ Missing return type annotation
    # Should be: def __init__(self, *args: Any, **kw: Any) -> None:
```

**Impact:** Minimal; mostly affects IDE autocompletion

**Fix:**
```python
from typing import Any

def __init__(self, *args: Any, **kw: Any) -> None:
    super().__init__(*args, **kw)
    self._exporter_started = False
```

---

#### [MINOR-3] Magic Number 50 for Label Truncation
**Location:** `pychron/experiment/executor_watchdog_integration.py`, lines 441, 465  
**Location:** `pychron/experiment/telemetry/device_io.py`, lines 47-48  
**Severity:** MINOR - Undocumented behavior  
**Issue:**
```python
phase = str(phase_name).lower().replace(" ", "_")[:50]  # ❌ Magic number
device = str(device_name).lower().replace(" ", "_")[:50]
```

**Problem:**
- Magic number 50 with no explanation
- Prometheus label length limits not documented
- Truncation could cause collisions

**Fix:**
```python
# Add constant at module level
MAX_LABEL_LENGTH = 50  # Prometheus label limit

# Or document the magic number
phase = str(phase_name).lower().replace(" ", "_")[:50]  # Prometheus label length limit
```

---

#### [MINOR-4] Incomplete Instrumentation Module Functions
**Location:** `pychron/experiment/instrumentation.py`, lines 173-180  
**Severity:** MINOR - Dead code  
**Issue:**
```python
def _record_phase_started(phase_name: str) -> None:
    """Record that a phase has started.
    
    Args:
        phase_name: Name of the phase (e.g., 'extraction', 'measurement').
    """
    # Phase metrics are tracked via context managers by the user
    pass  # ❌ NO-OP FUNCTION
```

**Problem:**
- Function is defined but does nothing
- Comment says "context managers by the user" but no such guidance
- Creates API confusion

**Fix:** Either remove or implement:
```python
def _record_phase_started(phase_name: str) -> None:
    """Record that a phase has started.
    
    Note: Phase tracking should use observe_duration() context manager for timing.
    This function is reserved for future enhancement.
    
    Args:
        phase_name: Name of the phase (e.g., 'extraction', 'measurement').
    """
    pass  # Intentionally no-op; use context managers for timing
```

Or add an actual counter:
```python
def _record_phase_started(phase_name: str) -> None:
    """Record that a phase has started."""
    try:
        from pychron.observability import inc_counter
        phase = str(phase_name).lower().replace(" ", "_")[:50]
        inc_counter(
            "phase_starts_total",
            "Total phase starts",
            labels=["phase"],
            labelvalues={"phase": phase},
        )
    except Exception:
        pass
```

---

#### [MINOR-5] Possible Resource Leak with Exception in Context Manager
**Location:** `pychron/experiment/telemetry/device_io.py`, lines 207-254  
**Severity:** MINOR - Edge case  
**Issue:**
```python
def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    """Exit context; record device I/O end with timing."""
    if not self.recorder:
        return  # ❌ Early return doesn't suppress exception

    if exc_type is not None:
        self.success = False
        self.error = str(exc_val)
    
    # ... record metrics ...
    
    # ✓ Good: Doesn't suppress exceptions (returns None implicitly)
```

**Problem:** While the code doesn't suppress exceptions (which is good), it could fail if `recorder.record_event()` or metrics recording raises an exception while handling an original exception, which would mask the original error.

**Impact:** Very minor; only affects error diagnostics in edge cases

**Fix:**
```python
def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
    """Exit context; record device I/O end with timing."""
    if not self.recorder:
        return False  # Explicitly don't suppress exceptions
    
    if exc_type is not None:
        self.success = False
        self.error = str(exc_val)
    
    try:
        # ... existing recording code ...
        self.recorder.record_event(event)
        _record_prometheus_device_io_metrics(...)
    except Exception as e:
        # Log but don't suppress the original exception
        logger.warning(f"Failed to record telemetry event: {e}", exc_info=True)
    
    return False  # Don't suppress exceptions
```

---

### 4. ARCHITECTURE & DESIGN ISSUES

#### [ARCH-1] Inconsistent Label Normalization
**Location:** Multiple files  
**Severity:** MINOR - Consistency issue  
**Issue:**

Device I/O metrics normalization:
```python
device = str(device_name).lower().replace(" ", "_")[:50]
operation = str(operation_type).lower().replace(" ", "_")[:50]
```

But executor watchdog:
```python
phase = str(phase_name).lower().replace(" ", "_")[:50]
```

And instrumentation:
```python
phase = str(phase_name).lower().replace(" ", "_")[:50]
```

**Problem:** No centralized normalization function; duplicated logic

**Fix:** Create a utility function:
```python
# In pychron/observability/metrics.py or new utils.py

def normalize_label_value(value: str, max_length: int = 50) -> str:
    """Normalize a label value for Prometheus.
    
    Prometheus label values should:
    - Be lowercase
    - Have spaces replaced with underscores
    - Be limited in length
    
    Args:
        value: The label value to normalize
        max_length: Maximum label length (default 50 for safety)
    
    Returns:
        Normalized label value
    """
    return str(value).lower().replace(" ", "_")[:max_length]
```

Then use everywhere:
```python
from pychron.observability.metrics import normalize_label_value

device = normalize_label_value(device_name)
operation = normalize_label_value(operation_type)
```

---

#### [ARCH-2] Configuration Management Could Be More Flexible
**Location:** `pychron/observability/config.py`  
**Severity:** MINOR - Design improvement  
**Issue:**

MetricsConfig is a simple data class with no validation:
```python
class MetricsConfig:
    def __init__(
        self,
        enabled: bool = False,
        host: str = "127.0.0.1",
        port: int = 9109,
        namespace: str = "pychron",
    ) -> None:
        self.enabled = enabled
        self.host = host
        self.port = port
        self.namespace = namespace
```

**Problems:**
- No validation of host/port
- No environment variable support
- No config file loading
- Port validation happens in plugin, not in config

**Fix:**
```python
import os
from typing import Optional

class MetricsConfig:
    """Configuration for Prometheus metrics export."""
    
    def __init__(
        self,
        enabled: Optional[bool] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """Initialize metrics configuration.
        
        Reads from environment variables if not provided:
        - PYCHRON_METRICS_ENABLED (default: false)
        - PYCHRON_METRICS_HOST (default: 127.0.0.1)
        - PYCHRON_METRICS_PORT (default: 9109)
        - PYCHRON_METRICS_NAMESPACE (default: pychron)
        """
        self.enabled = enabled if enabled is not None else os.getenv('PYCHRON_METRICS_ENABLED', 'false').lower() == 'true'
        self.host = host or os.getenv('PYCHRON_METRICS_HOST', '127.0.0.1')
        self.port = port or int(os.getenv('PYCHRON_METRICS_PORT', '9109'))
        self.namespace = namespace or os.getenv('PYCHRON_METRICS_NAMESPACE', 'pychron')
        
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}. Must be 1-65535.")
        if not isinstance(self.namespace, str) or not self.namespace:
            raise ValueError(f"Invalid namespace: {self.namespace}. Must be non-empty string.")
        if not isinstance(self.host, str) or not self.host:
            raise ValueError(f"Invalid host: {self.host}. Must be non-empty string.")
```

---

### 5. DOCUMENTATION & COMPLETENESS

#### [DOC-1] Missing Docstring for registry._names_to_collectors Access
**Location:** `pychron/observability/registry.py`, lines 44-46  
**Severity:** MINOR - Documentation  
**Issue:**
```python
except ValueError:
    # Metric already registered, retrieve it
    return registry._names_to_collectors[name]  # ❌ No explanation of why we access private API
```

**Fix:**
```python
except ValueError:
    # Metric already registered; retrieve from internal registry
    # NOTE: Uses private _names_to_collectors API from prometheus_client.
    # This is fragile and should be replaced when prometheus_client provides
    # a public API for deduplication. See: https://github.com/prometheus/client_python/issues/XXX
    return registry._names_to_collectors[name]
```

---

#### [DOC-2] Missing README for Observability Module
**Location:** `pychron/observability/`  
**Severity:** MINOR - Documentation  
**Issue:** No README explaining:
- How to enable Prometheus metrics
- What metrics are available
- How to configure the exporter
- Example dashboard queries

**Fix:** Create `pychron/observability/README.md` with:
- Configuration instructions
- Metric list and descriptions
- Example Prometheus scrape configuration
- Example Grafana dashboard setup

---

### 6. TEST COVERAGE ANALYSIS

#### Tests Passing: 54/54 (Observability + Device IO)
#### Tests Failing: 3/30 (Executor Watchdog)

**Good Coverage:**
- ✓ Metrics disabled/enabled scenarios
- ✓ Label handling
- ✓ Duration context manager
- ✓ Exporter idempotency
- ✓ Plugin initialization
- ✓ Device I/O decorator and context manager

**Missing Coverage:**
- ❌ Concurrent metric recording
- ❌ Label validation edge cases
- ❌ Prometheus HTTP server actual startup
- ❌ Error handling in real exception scenarios
- ❌ Large metric values (overflow scenarios)
- ❌ Custom bucket validation for histograms

---

## Summary of Issues by Category

| Category | Critical | Major | Minor |
|----------|----------|-------|-------|
| Code Quality | 1 | 1 | 5 |
| Thread Safety | 0 | 2 | 0 |
| Test Coverage | 0 | 1 | 0 |
| Documentation | 0 | 0 | 2 |
| Architecture | 0 | 0 | 2 |
| **TOTAL** | **1** | **4** | **9** |

---

## Recommendations by Priority

### P0 - Must Fix Before Merge
1. **Fix DeviceQuorumChecker API call** - Will crash at runtime
2. **Replace private API access** - Use public prometheus_client API
3. **Fix 3 executor watchdog tests** - Currently failing

### P1 - Should Fix for Quality
1. **Add thread safety locks** - Critical for multi-threaded experiment execution
2. **Add label validation** - Prevent silent metric recording failures
3. **Add error logging** - Make metrics failures visible for debugging

### P2 - Nice to Have
1. Standardize error handling patterns
2. Extract normalization utilities
3. Create observability README
4. Add environment variable config support
5. Expand test coverage for edge cases

---

## Style & Consistency Notes

### PEP 8 Compliance
- ✓ Imports properly organized (top-level, then relative)
- ✓ Line lengths reasonable (~90-100 chars)
- ✓ Docstrings follow Google style
- ✓ Type hints present on public functions
- ❌ Missing some type hints on __init__ methods
- ⚠ Magic numbers without constants

### Import Organization
- ✓ Lazy imports used appropriately to avoid circular dependencies
- ✓ Top-level imports kept minimal
- ✓ Relative imports clean

### Naming Conventions
- ✓ Consistent use of snake_case for functions/variables
- ✓ CONSTANT_CASE not used (no module-level constants)
- ✓ Private methods use leading underscore

---

## Performance Considerations

1. **Metric Recording Overhead:** Minimal - try-except blocks only on failures
2. **Registry Access:** Could benefit from local caching in tight loops
3. **Label Normalization:** Performed on every call - could be cached if label values are static
4. **Thread Contention:** Current implementation has no locks - potential bottleneck under high concurrency

---

## Next Steps

1. **Immediately:** Fix the 3 critical/major issues before merge
2. **Short-term:** Add thread-safe wrappers
3. **Medium-term:** Improve test coverage for edge cases
4. **Long-term:** Consider replacing private prometheus_client API access with documented public API

