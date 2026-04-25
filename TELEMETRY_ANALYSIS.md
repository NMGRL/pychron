# Telemetry & Watchdog Implementation Analysis - Pychron Main Branch

**Date**: 2026-04-04  
**Scope**: Complete analysis of telemetry and watchdog implementations on main branch  
**Status**: Phase 2 complete, Phase 3-6 partially complete with critical defects  

## Quick Summary

- **Core Infrastructure**: ✅ Solid (Recorder, Context, Event, Span, Listeners)
- **Critical Defects**: 5 P1 issues blocking correlation and health visibility
- **High-Priority Defects**: 7 P2 issues breaking replay/analysis
- **Missing**: Lifecycle management, per-queue recorders, phase-level wrapping
- **Recommendation**: 5.5 hours of focused fixes to reach production-ready

---

[Full analysis follows - see sections below]

## Table of Contents

1. Part 1: Current Telemetry Infrastructure
2. Part 2: Watchdog Integration Points  
3. Part 3: P1/P2 Defects Summary
4. Part 4: Event Flow Analysis
5. Part 5: Recorder Lifecycle Issues
6. Part 6: Context Cleanup Gaps
7. Part 7: Event Correlation Patterns
8. Part 8: Replay/CLI Compatibility
9. Part 9: Implementation Status
10. Part 10: Recommended Fix Priority
11. File Location Summary

---

## Part 1: Current Telemetry Infrastructure

### 1.1 Core Components

**TelemetryRecorder** (172 lines)
- ✅ JSONL writer with thread-safe buffering
- ✅ Configurable batch size (default 100)
- ✅ Factory: for_queue(), for_run()
- ⚠️ No lifecycle management in executor

**TelemetryContext** (114 lines) 
- ✅ Thread-safe contextvars for correlation IDs
- ✅ Span stack for nesting
- ⚠️ **P1 BUG**: Span stack mutation (append in-place)
- ⚠️ **P2 BUG**: Not cleared between runs

**TelemetryEvent** (143 lines)
- ✅ Complete schema (20+ fields)
- ✅ EventType enum
- ✅ to_dict() serialization

**Span** (215 lines)
- ✅ Context manager for timing
- ✅ Parent/child nesting
- ⚠️ **P1 BUG**: parent_span_id captured after pop
- ⚠️ Result: Parent-child relationships broken

### 1.2 Listener Implementations

**StateMachineListener**
- ✅ Emits state_transition events
- ⚠️ **P1 BUG**: New span_id per event (not correlated)
- ⚠️ **P2 BUG**: ts field may be None
- ⚠️ **P2 BUG**: Incomplete run_id extraction

**DeviceIOTelemetry**
- ✅ Decorator and context manager
- ⚠️ **P2 BUG**: span_id from context (may be None)
- ⚠️ **P2 BUG**: Decorator silent no-op

**MonitorInterlockTelemetry**
- ✅ Monitor decisions and interlock evaluations
- ⚠️ **P1 BUG**: No span_id generation

**HeartbeatTelemetryListener**
- ✅ Device health events
- ⚠️ **P1 BUG**: New span_id per event
- ⚠️ **P2 BUG**: Unclear parent_span_id

### 1.3 Replay & CLI

**replay.py**
- ✅ Load JSONL, reconstruct timeline
- ⚠️ **P2 BUG**: Event type mismatch (device_io vs device_command)
- ⚠️ Device commands always empty

**cli.py**
- ✅ inspect, timeline, stats, replay commands
- ⚠️ Device section incomplete

---

## Part 2: Watchdog Integration Points

### 2.1 Where Health Checks Are Called

- **Extraction Phase**: experiment_executor.py:1618-1623
- **Measurement Phase**: experiment_executor.py:1667-1672
- **Save Phase**: experiment_executor.py:1300-1306
- ⚠️ **P1 BUG**: No telemetry events emitted
- ⚠️ Results always ignored (graceful degradation)

### 2.2 Telemetry Event Emission

ExecutorWatchdogIntegration
- ✅ Initializes service heartbeats
- ⚠️ **P1 BUG**: check_phase_device_health() doesn't emit events
- ⚠️ **P1 BUG**: record_service_operation() never called

### 2.3 Context Cleanup Issues

- ✅ Queue context set at start
- ✅ Run context set per run
- ⚠️ **P1 BUG**: Run context NOT cleared between runs
- ⚠️ **P2 BUG**: Queue context NOT cleared on completion

---

## Part 3: P1/P2 Defects Summary

### P1 DEFECTS (Breaks Correlation)

1. **Span Stack Bug** (span.py:100-124)
   - parent_span_id captured after pop
   - Inconsistent between __exit__ and record_* methods
   - Impact: Parent-child relationships broken

2. **StateMachineListener Span ID** (state_machine_listener.py:84)
   - New span_id per transition
   - Impact: Cannot trace state to phase

3. **TelemetryContext Span Stack Mutation** (context.py:75-79)
   - append() then set() pattern breaks with contextvars
   - Impact: Corruption in async/threaded scenarios

4. **ExecutorWatchdog No Telemetry** (executor_watchdog_integration.py:174)
   - Health checks don't emit events
   - Impact: Health monitoring invisible

5. **MonitorInterlock No Span ID** (monitor_interlock.py:96)
   - Uses context span_id (may be None)
   - Impact: Monitor events not correlatable

### P2 DEFECTS (Breaks Replay/Analysis)

1. **Device IO Event Type Mismatch** (device_io.py:84, replay.py:145)
   - device_io emits "device_io"
   - replay expects "device_command"
   - Impact: Device commands empty in replay

2. **StateMachineListener Timestamp** (state_machine_listener.py:78)
   - ts may be None
   - Impact: Timeline ordering broken

3. **StateMachineListener Run Context** (state_machine_listener.py:62-73)
   - Wrong run_id on queue transitions
   - Impact: Mixed context

4. **Missing Monitor/Interlock Types**
   - monitor_trip, automatic_intervention not emitted
   - Impact: Incomplete monitoring

5. **DeviceIO Decorator Silent Failure** (device_io.py:50-52)
   - Silently no-ops if no recorder
   - Impact: Dual code paths

6. **Replay Device Command Mapping** (replay.py:145-155)
   - Looks for "device_command" but events are "device_io"
   - Impact: Report shows empty commands

7. **TelemetryEvent Field Semantics**
   - state_from/state_to used for different things
   - Impact: Confusion in analysis

---

## Part 4: Event Flow Analysis

**Current Extraction Phase Flow** (BROKEN):
```
phase entry (no span) 
  → health check (no telemetry)
  → device I/O (span_id=None or wrong)
  → monitor checks (span_id=context parent)
  → state transition (NEW span_id=uuid, not correlated)
```

**Correlation Chain**:
- Queue starts: queue_id set ✓
- Run starts: run_id set ✓
- Phase enters: NO SPAN ✗
- Health check: NO TELEMETRY ✗
- Device I/O: NO PARENT ✗
- State transition: NEW SPAN ID ✗

---

## Part 5: Recorder Lifecycle Issues

### Current Lifecycle (controller.py:152-159)

```python
telemetry_dir = Path.home() / ".pychron_telemetry" / "logs"
log_file = telemetry_dir / f"telemetry_{os.getpid()}.jsonl"
self.telemetry_recorder = TelemetryRecorder(log_path=log_file)
```

Issues:
1. ⚠️ **P1 BUG**: Single recorder for entire executor
   - Expected: Per-queue recorder
   - Actual: Global log file

2. ⚠️ **P1 BUG**: No flush guarantee
   - recorder.flush() never called
   - Buffer lost on crash

3. ⚠️ **P2 BUG**: set_global_recorder() not called
   - controller.telemetry_recorder ≠ span._global_recorder
   - May use different instances

### Missing Integration Points

- Queue Start: No per-queue recorder creation
- Queue End: No flush/close
- Run Start: No context reset
- Run End: No context cleanup

---

## Part 6: Context Cleanup Gaps

### Span Stack Issues
- No try/finally pattern
- If exception between push/pop, stack corrupted

### Run Context Leakage
- Not cleared between runs in same queue
- Subsequent runs show previous run_id

### Queue Context Leakage
- Not cleared on queue completion
- Leaks to next queue execution

---

## Part 7: Event Correlation Patterns

**Good**:
- Queue span captures queue_id/trace_id ✓
- Run span inherits queue + adds run context ✓

**Bad**:
- State transitions: new span_id (not correlated to phase) ✗
- Device I/O: no parent span (span_id=context parent) ✗
- Health checks: random span_id per event ✗
- Monitor/interlock: inherit parent span_id (not own ID) ✗

---

## Part 8: Replay/CLI Compatibility Issues

### Event Type Mismatches

| Type | Emitted | Expected | Status |
|------|---------|----------|--------|
| device_io | device_io.py | device_command, command | ❌ MISMATCH |
| monitor_check | monitor_interlock.py | cli.py, replay.py | ✓ OK |
| monitor_trip | - | cli.py, replay.py | ❌ NEVER |
| interlock_check | monitor_interlock.py | cli.py, replay.py | ✓ OK |
| automatic_intervention | - | cli.py, replay.py | ❌ NEVER |

### Replay Report Issues

```python
report = replay_queue_telemetry(path)
print(report.device_commands)  # Always []!
```

Why: device_io.py emits "device_io" but replay.py filters for "device_command"

---

## Part 9: Implementation Status

### Complete
- ✅ TelemetryRecorder
- ✅ TelemetryContext
- ✅ TelemetryEvent
- ✅ Span
- ✅ StateMachineListener
- ✅ HeartbeatTelemetryListener
- ✅ Replay infrastructure
- ✅ CLI tools

### Partial
- ⚠️ TelemetryDeviceIOContext (emits but no correlation)
- ⚠️ TelemetryMonitorDecision (emits but no span_id)
- ⚠️ ExecutorController integration (wrong lifecycle)
- ⚠️ Watchdog telemetry (listeners created but checks don't emit)

### Missing
- ❌ Per-queue recorders
- ❌ Recorder flush/close
- ❌ Context cleanup between runs
- ❌ Context cleanup on queue completion
- ❌ Phase-level Span wrappers
- ❌ Event type alignment
- ❌ Documentation

---

## Part 10: Recommended Fix Priority

### Immediate (30-90 minutes)
1. Fix Span Parent Capture (span.py) - 30 min
2. Fix StateMachineListener Span ID (state_machine_listener.py) - 15 min
3. Fix TelemetryContext Stack (context.py) - 20 min

### Critical (3.5 hours)
4. Add Watchdog Health Check Telemetry (executor_watchdog_integration.py) - 1 hour
5. Fix Device IO Event Type Mismatch (device_io.py, replay.py) - 1 hour
6. Fix Run Context Cleanup (experiment_executor.py) - 30 min

### High (3.5 hours)
7. Fix Recorder Lifecycle (controller.py) - 2 hours
8. Add Phase-Level Span Wrappers (_do_extraction, _do_measurement, _do_save) - 1.5 hours

### Total: 5.5 hours for production-ready system

---

## File Location Summary

### Core Infrastructure
- `pychron/experiment/telemetry/recorder.py` (172 lines)
- `pychron/experiment/telemetry/context.py` (114 lines) **[P1 BUG]**
- `pychron/experiment/telemetry/event.py` (143 lines)
- `pychron/experiment/telemetry/span.py` (215 lines) **[P1 BUG]**

### Listeners & Wrappers
- `pychron/experiment/telemetry/state_machine_listener.py` (108 lines) **[P1, P2]**
- `pychron/experiment/telemetry/device_io.py` (211 lines) **[P2]**
- `pychron/experiment/telemetry/monitor_interlock.py` (249 lines) **[P1]**
- `pychron/hardware/core/watchdog/telemetry_integration.py` (418 lines) **[P1, P2]**

### Integration
- `pychron/experiment/state_machines/controller.py` (821 lines) **[P1: Lifecycle]**
- `pychron/experiment/experiment_executor.py` (3122 lines)
- `pychron/experiment/executor_watchdog_integration.py` (346 lines) **[P1: No telemetry]**

### Analysis
- `pychron/experiment/telemetry/replay.py` (218 lines) **[P2: Event mismatch]**
- `pychron/experiment/telemetry/cli.py` (571 lines)

### Tests
- `pychron/experiment/telemetry/tests/` (39+ tests)
- `pychron/hardware/core/watchdog/tests/test_telemetry_integration.py` (335 lines)
- `pychron/experiment/tests/test_executor_watchdog_integration.py` (395 lines)

---

## Conclusion

The telemetry infrastructure is **well-designed but incompletely integrated**. Core components are solid, but critical defects in span handling, event correlation, and lifecycle management make the system unreliable for production.

The **watchdog integration is present but invisible** - health checks happen but generate no telemetry, making health-related failures impossible to debug.

Fixing 3 P1 span issues + adding watchdog telemetry + fixing lifecycle + adding phase wrappers = **5.5 hours to production-ready**.

