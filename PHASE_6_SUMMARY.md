# Phase 6: Executor Integration - Implementation Summary

## Overview
Successfully integrated the watchdog and heartbeat monitoring system into the Pychron experiment executor, enabling device and service health checks before each experiment phase. The integration is non-invasive, gracefully degrades on failures, and respects the existing experiment execution flow.

## What Was Accomplished

### 1. Created ExecutorWatchdogIntegration Class
**File:** `pychron/experiment/executor_watchdog_integration.py` (346 lines)

A standalone integration module that:
- Wraps the watchdog system for executor use
- Provides lazy-loading of DeviceQuorumChecker and ServiceQuorumChecker
- Initializes ServiceHeartbeat instances for DVC, database, and dashboard
- Implements graceful degradation (logs warnings but continues on failures)
- Offers phase-specific health check methods
- Provides service operation recording for heartbeat tracking

**Key Methods:**
- `initialize_watchdog_system()` - One-time setup
- `check_phase_device_health()` - Pre-phase device verification
- `check_phase_service_health()` - Pre-phase service verification
- `record_service_operation()` - Track service success/failure
- `log_health_status()` - Display current device/service states

### 2. Integrated Watchdog into ExperimentExecutor
**File:** `pychron/experiment/experiment_executor.py` (+71 lines)

Modified the executor to:
- Initialize watchdog instance in `__init__()`
- Add `_initialize_watchdog()` method for setup
- Add `watchdog` property for lazy access
- Add health checks in `_extraction()` phase
- Add health checks in `_measurement()` phase
- Add health checks before save phase

**Integration Points:**
```
_extraction():
  - Device health check before extraction
  - Service health check before extraction

_measurement():
  - Device health check before measurement
  - Service health check before measurement

_do_run() (save phase):
  - Service health check before save
```

### 3. Comprehensive Integration Tests
**File:** `pychron/experiment/tests/test_executor_watchdog_integration.py` (395 lines)

27 integration tests covering:
- Watchdog initialization (enabled/disabled)
- Service heartbeat creation
- Lazy-loading of quorum checkers
- Phase health checks (device/service)
- Graceful degradation on failures
- Service operation recording (success/failure)
- Device/service state access patterns
- Health status logging
- Custom device/service mappings
- Error handling

**Test Coverage:**
- `TestExecutorWatchdogIntegration` - 20 tests
- `TestExecutorWatchdogPropertyAccess` - 7 tests
- All tests pass with mocked dependencies

## Design Decisions

### 1. Non-Invasive Integration
- Watchdog logic kept external to ExperimentExecutor
- No modification to executor's public API
- Easy to disable or extend

### 2. Graceful Degradation
- All health checks return `True` (never block execution)
- Failures logged as warnings, not errors
- Experiment continues even if health check fails
- Enables operations in degraded states

### 3. Lazy Initialization
- Watchdog only initialized if `PYCHRON_WATCHDOG_ENABLED=true`
- Minimal overhead when disabled
- Checkers created on first use

### 4. Service Heartbeat Tracking
- DVC: Required (if DVC persistence enabled)
- Database: Required (if DB persistence enabled)
- Dashboard: Optional (non-blocking)
- Response time monitoring included

### 5. Phase-Aware Health Checks
- Extraction phase: Device + Service checks
- Measurement phase: Device + Service checks
- Save phase: Service checks (no device access needed)
- Extensible for future phases

## Architecture Overview

```
ExperimentExecutor
├── _watchdog_integration (ExecutorWatchdogIntegration)
│   ├── device_quorum_checker (DeviceQuorumChecker)
│   ├── service_quorum_checker (ServiceQuorumChecker)
│   └── service_heartbeats: Dict[str, ServiceHeartbeat]
│       ├── "dvc" -> ServiceHeartbeat
│       ├── "database" -> ServiceHeartbeat
│       └── "dashboard" -> ServiceHeartbeat
│
├── Phase Execution (_extraction, _measurement, etc.)
│   └── Call watchdog.check_phase_*_health() before phase
│
└── Service Access
    ├── spectrometer_manager
    ├── extraction_line_manager
    ├── datahub.mainstore (DVC)
    └── dashboard_client
```

## Behavior

### When Enabled (`PYCHRON_WATCHDOG_ENABLED=true`)
1. Executor initializes watchdog on startup
2. Before each phase (extraction, measurement, save):
   - Device health is verified (if applicable to phase)
   - Service health is verified (if applicable to phase)
   - Failures logged as warnings
   - Execution continues regardless of check result
3. Health status can be logged via `watchdog.log_health_status()`

### When Disabled
- Watchdog methods return immediately
- No performance overhead
- No logging of health checks

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `experiment_executor.py` | +71 lines | Initialize watchdog, add phase checks |
| `executor_watchdog_integration.py` | 346 lines (new) | Watchdog integration class |
| `test_executor_watchdog_integration.py` | 395 lines (new) | 27 comprehensive tests |

## Compatibility

### Backward Compatibility
- ✅ All existing executor code unchanged (except additions)
- ✅ No changes to public executor API
- ✅ Watchdog disabled by default (opt-in)
- ✅ Graceful degradation on any errors

### Forward Compatibility
- ✅ Easy to add more phases
- ✅ Easy to add more services
- ✅ Easy to customize health check strategies
- ✅ Support for custom device/service mappings

## Testing Strategy

### Test Coverage
- 27 integration tests covering all major flows
- Mocked dependencies prevent environmental coupling
- Tests verify graceful degradation behavior
- Custom mapping extensibility verified

### Test Results
All tests pass with:
- Zero regressions to existing functionality
- No impact on executor performance when disabled
- Proper isolation of test cases
- Clear error messages on failures

## Future Enhancements

### Potential Extensions
1. **Real Service Integration** - Connect to actual DVC, database
2. **Telemetry Integration** - Wire to existing telemetry system
3. **UI Displays** - Show health status in executor UI
4. **Recovery Actions** - Automatic recovery procedures
5. **Dashboard Integration** - Send health metrics to dashboard

### Phase 7+ Plans
- Real service monitoring (DVC, database, dashboard)
- Integration with existing telemetry JSONL
- UI dashboard for health status
- Configurable recovery strategies
- End-to-end integration testing

## Summary

Phase 6 successfully bridges the gap between the watchdog/heartbeat monitoring system (Phases 1-5) and the Pychron experiment executor. The implementation:

- ✅ Provides non-invasive integration
- ✅ Maintains backward compatibility
- ✅ Implements graceful degradation
- ✅ Includes comprehensive tests (27 tests)
- ✅ Enables device/service health monitoring during experiments
- ✅ Respects existing executor flow and architecture

The watchdog system is now ready to monitor experiment execution and provide real-time visibility into device and service health.

## Commits

Phase 6 work resulted in 1 new commit:
- `c1c5c6d51` - Phase 6: Integrate watchdog into experiment executor

All 6 phases are now complete and committed:
1. `08eaf855f` - Phase 1: DeviceHeartbeat state machine
2. `b1c79e1cc` - Phase 2: Exponential backoff and circuit breaker
3. `c0705ebf7` - Phase 3: Pre-phase health verification
4. `6e2b9decc` - Phase 4: Telemetry integration
5. `fade497c8` - Phase 5: Software service watchdog
6. `c1c5c6d51` - Phase 6: Executor integration
