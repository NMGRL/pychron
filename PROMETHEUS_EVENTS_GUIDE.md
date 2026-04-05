# Prometheus Events in Pychron

This document explains what operations trigger Prometheus observability events and where they occur in the codebase.

## Overview

The Prometheus observability system in Pychron captures events when:
1. Experiments start, complete, fail, or are canceled
2. Device I/O operations occur (extraction line, spectrometer, lasers, hardware)
3. Health checks fail
4. Specific phases complete (extraction, measurement, post-measurement)

## Event Trigger Categories

### 1. Experiment Lifecycle Events

**Location:** `pychron/experiment/instrumentation.py`

These events track the lifecycle of experiment queues and runs:

#### Queue Events
- **Queue Start**: When an experiment queue begins processing
  - Metric: `pychron_queue_starts_total` (counter)
  - Calls: `_record_queue_started()`
  - Line: 11-29

- **Queue Complete**: When all experiments in a queue finish
  - Metric: `pychron_queue_completions_total` (counter)
  - Metric: `pychron_active_queues` (gauge)
  - Calls: `_record_queue_completed()`
  - Line: 34-54

#### Run Events
- **Run Start**: When a single experiment run begins
  - Metric: `pychron_runs_started_total` (counter)
  - Metric: `pychron_active_runs` (gauge)
  - Calls: `_record_run_started()`
  - Line: 57-77

- **Run Complete**: When an experiment finishes successfully
  - Metric: `pychron_runs_completed_total` (counter)
  - Metric: `pychron_run_duration_seconds` (histogram)
  - Metric: `pychron_active_runs` (gauge)
  - Calls: `_record_run_completed()`
  - Line: 80-108

- **Run Failed**: When an experiment fails with an error
  - Metric: `pychron_runs_failed_total` (counter)
  - Metric: `pychron_run_duration_seconds` (histogram)
  - Metric: `pychron_active_runs` (gauge)
  - Calls: `_record_run_failed()`
  - Line: 111-139

- **Run Canceled**: When an experiment is manually canceled
  - Metric: `pychron_runs_canceled_total` (counter)
  - Metric: `pychron_run_duration_seconds` (histogram)
  - Metric: `pychron_active_runs` (gauge)
  - Calls: `_record_run_canceled()`
  - Line: 142-170

#### Phase Duration Events
- **Phase Complete**: When extraction, measurement, or post-measurement phases finish
  - Metric: `pychron_phase_duration_seconds` (histogram with phase label)
  - Calls: `_record_phase_duration(phase_name, duration)`
  - Line: 183-204
  - Phases: "extraction", "measurement", "post_measurement"

---

### 2. Device I/O Events

**Location:** `pychron/experiment/telemetry/device_io.py`

These events track hardware device operations like extraction line valve controls, spectrometer readings, laser operations, etc.

#### Device I/O Operation Events
- **Operation Start/End**: When a device I/O operation occurs
  - Metric: `pychron_device_io_operations_total` (counter)
  - Labels: `device`, `operation`, `result` (success/failure)
  - Recorded automatically by `@telemetry_device_io` decorator
  - Line: 85-169

#### Device I/O Duration Events
- **Operation Duration**: Time taken for a device I/O operation
  - Metric: `pychron_device_io_duration_seconds` (histogram)
  - Labels: `device`, `operation`
  - Recorded automatically by `@telemetry_device_io` decorator
  - Line: 85-169

#### Device Success Timestamp
- **Last Success**: Timestamp of last successful device operation
  - Metric: `pychron_device_last_success_timestamp_seconds` (gauge)
  - Label: `device`
  - Updated by `TelemetryDeviceIOContext`
  - Line: 172-286

**Example Device Operations:**
- Extraction line: valve open/close, pump on/off, pressure read, temperature read
- Spectrometer: intensity measurement, peak center, detector reading
- Lasers: fire operation, power adjustment, temperature control
- Hardware: motion, temperature monitoring, gauge readings

---

### 3. Health Check Events

**Location:** `pychron/experiment/executor_watchdog_integration.py`

These events track system health and failures.

#### Health Check Failures
- **Device Health Check Failure**: When a device health check fails
  - Metric: `pychron_phase_healthcheck_failures_total` (counter)
  - Labels: `phase`, `kind` (device)
  - Line: 430-452

- **Service Health Check Failure**: When a service health check fails
  - Metric: `pychron_phase_healthcheck_failures_total` (counter)
  - Labels: `phase`, `kind` (service)
  - Line: 454-476

---

## Current Integration Status

### ✅ Implemented and Integrated
- Device I/O telemetry via `@telemetry_device_io` decorator
- Health check monitoring
- Configuration system

### ⚠️  Implemented but Not Yet Integrated
- Experiment lifecycle metrics in `instrumentation.py`
  - Status: Ready to be called from `experiment_executor.py`
  - Impact: Would capture queue and run events
  - Priority: HIGH

### ❌ Not Yet Implemented
- Database operation metrics
- DVC operation metrics
- Pipeline operation metrics
- Direct integration in hardware operation sites

---

## How Events Flow to the UI

```
1. Operation occurs (e.g., run completes)
   ↓
2. Call instrumentation function (e.g., _record_run_completed())
   ↓
3. Function calls metrics.inc_counter() or metrics.set_gauge()
   ↓
4. Metrics operation (if enabled) performs Prometheus operation
   ↓
5. [In future] Event captured by event_capture.add_event()
   ↓
6. Event propagated to ObservabilityModel via callback
   ↓
7. UI components (StatusPane, EventPane) receive event update
   ↓
8. Displays event in UI and updates metrics preview
```

## Testing Events

To test event capture, use the integration tests:

```bash
# Run live event integration tests
pytest test/observability/test_integration_live_events.py -xvs

# Tests simulate metric operations and verify UI updates
```

---

## Future Work

### Phase 1: Complete Experiment Lifecycle Integration
- Integrate `instrumentation.py` functions into `experiment_executor.py`
- Expected to capture 100s of events per experiment run
- High visibility into experiment progress

### Phase 2: Expand Device Operations
- Add metrics at actual hardware operation points
- Capture device-specific success/failure rates
- Enable performance profiling of device operations

### Phase 3: Database and DVC Metrics
- Track database query performance
- Monitor DVC repository operations
- Measure data pipeline throughput

### Phase 4: Metrics-to-Events Integration
- Integrate `metrics.inc_counter()` calls with `event_capture.add_event()`
- Automatically capture all metric operations as observable events
- Enable complete audit trail of system operations

---

## Metrics Reference

### Counters (Incrementing)
- `pychron_queue_starts_total`
- `pychron_queue_completions_total`
- `pychron_runs_started_total`
- `pychron_runs_completed_total`
- `pychron_runs_failed_total`
- `pychron_runs_canceled_total`
- `pychron_device_io_operations_total`
- `pychron_phase_healthcheck_failures_total`

### Gauges (Current Value)
- `pychron_active_queues`
- `pychron_active_runs`
- `pychron_device_last_success_timestamp_seconds`

### Histograms (Distribution)
- `pychron_run_duration_seconds`
- `pychron_device_io_duration_seconds`
- `pychron_phase_duration_seconds`

---

## Summary

**Currently Triggering Events:**
- Device I/O operations (via `@telemetry_device_io` decorator)
- Health check failures

**Ready to Trigger Events (pending integration):**
- Experiment queue start/complete
- Run start/complete/fail/cancel
- Phase completions

**Total Potential Events:**
- ~5-10 events per device I/O operation
- ~7-10 events per experiment run
- ~1-3 events per health check failure

With proper integration, a single experiment run could trigger 50-100+ observable events across device I/O, phases, and run lifecycle.
