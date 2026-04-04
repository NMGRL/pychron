# Telemetry Implementation Status

## ✅ COMPLETED: Phase 1-2 (Core Infrastructure & State Machines)

### Phase 1: Core Telemetry Infrastructure
- **TelemetryEvent** schema with correlation IDs (queue_id, trace_id, span_id, parent_span_id)
- **TelemetryRecorder** with JSONL output and buffering (batch writes for performance)
- **TelemetryContext** using contextvars for thread-safe propagation
- **Span** context manager for timing operations with parent/child nesting
- **39 comprehensive tests** covering all components

### Phase 2: State Machine Telemetry  
- **StateMachineListener** callback for executor/queue/run transitions
- Emits structured events with:
  - state_from, state_to, reason, accepted flag
  - queue_id, trace_id, span_id correlation
  - machine name and full TransitionRecord payload

**Total Tests: 39/39 PASSING ✓**

---

## 📋 PENDING: Phase 3-6

### Phase 3: Span and Timing Telemetry
**Goal:** Wrap queue/run/save operations for timing and success/failure tracking

Tasks:
1. Find and wrap queue execution entry point
2. Find and wrap run execution (_do_run) with phase spans
3. Find and wrap save pipeline calls
4. Find and wrap overlap wait/launch/settle operations
5. Add 15-20 integration tests

**Estimated:** 3-4 days

### Phase 4: Device and Monitor Telemetry
**Goal:** Add hardware I/O and monitor/interlock decision events

Tasks:
1. Wrap extraction line manager calls
2. Wrap spectrometer configuration calls
3. Add monitor check/trip events
4. Add interlock decision events
5. Add automatic intervention (cancel/abort) events
6. Add 20-25 integration tests

**Estimated:** 3-4 days

### Phase 5: Replay and Persistence
**Goal:** Finalize JSONL persistence and add incident report generation

Tasks:
1. Integrate telemetry into ExecutorController startup/shutdown
2. Initialize TelemetryContext at queue start
3. Extend replay module with full timeline reconstruction
4. Add replay tests for state progression, device commands, monitor history
5. Create directory structure ~/.pychron.{APP_ID}/logs/telemetry/
6. Add 15-20 replay/persistence tests

**Estimated:** 2-3 days

### Phase 6: Integration and Documentation
**Goal:** End-to-end testing and user documentation

Tasks:
1. Create integration test suite (5-10 tests)
2. Run existing test suites to verify no regressions
3. Add docstrings to new APIs
4. Create user guide: `docs/user_guide/telemetry.md`
5. Create developer guide: `docs/dev_guide/telemetry_extension.md`
6. Update README with telemetry features

**Estimated:** 2-3 days

---

## Architecture Overview

```
TelemetryRecorder (JSONL writer)
        ↑
        │ emits events to
        │
    TelemetryContext (thread-local IDs)
        ↑
        │ propagated by
        │
    Span (operation timing)        StateMachineListener (state transitions)
        ↑                                    ↑
        │ created by                        │ registered with
        │                                   │
    Executor/Queue/Run code     ExecutorController._notify()
        ↑                                    ↑
        │                                   │
        └────────────────────────────────────┘
                        │
                   File: queue_QUEUENAME_TIMESTAMP.jsonl
                   Format: JSON Lines
                   Replay: load_telemetry_log() → TelemetryEvent[]
```

## Quick Start for Phase 3+

1. **To wrap an operation in telemetry:**
   ```python
   from pychron.experiment.telemetry import Span
   
   with Span("my_span", "component", "action", payload={"key": "value"}):
       # Do work
       pass  # Auto-recorded as success
   # OR
   with Span("my_span", "component", "action") as span:
       try:
           # Do work
           span.record_success(payload={"result": result})
       except Exception as e:
           span.record_failure(reason="operation_failed", error=str(e))
   ```

2. **To initialize telemetry in a queue:**
   ```python
   from pychron.experiment.telemetry import (
       TelemetryRecorder, TelemetryContext, 
       StateMachineListener, set_global_recorder
   )
   
   recorder = TelemetryRecorder.for_queue("queue_id")
   set_global_recorder(recorder)
   TelemetryContext.set_queue_id("queue_id")
   TelemetryContext.set_trace_id("trace_123")
   
   # Register state machine listener
   listener = StateMachineListener(recorder)
   controller.register_on_transition(listener.on_transition)
   ```

3. **To replay a telemetry log:**
   ```python
   from pychron.experiment.telemetry import replay_queue_telemetry
   
   report = replay_queue_telemetry("/path/to/queue_experiment_2026-04-03.jsonl")
   print(report.summary)
   print(report.state_machine_history)
   ```

## Testing Commands

**Phase 1-2 tests:**
```bash
python -m unittest discover -s pychron/experiment/telemetry/tests -p "test_*.py" -v
```

**Individual test modules:**
```bash
python -m unittest pychron.experiment.telemetry.tests.test_event
python -m unittest pychron.experiment.telemetry.tests.test_context
python -m unittest pychron.experiment.telemetry.tests.test_recorder
python -m unittest pychron.experiment.telemetry.tests.test_span
python -m unittest pychron.experiment.telemetry.tests.test_replay
python -m unittest pychron.experiment.telemetry.tests.test_state_machine_listener
```

**Syntax check:**
```bash
python -m py_compile pychron/experiment/telemetry/*.py
```

---

## Design Decisions (Per AGENTS.md)

✅ **Conservative, low-regression changes**
- Callback-based only; no changes to public APIs
- Isolated new package under `pychron/experiment/telemetry/`
- Existing logging and events unchanged

✅ **Additive, not rewriting**
- Structured telemetry is a second channel parallel to existing logs
- Human-readable logging preserved
- No forced refactoring of legacy code

✅ **Focused edits**
- Telemetry hooks at high-value boundaries (state machines, manager calls)
- Not instrumenting every function
- Device telemetry starts at manager/service level, not deep in hardware

✅ **Testable layers**
- Each component unit tested independently
- 39 tests with good coverage
- Ready for integration tests in Phase 3+

---

## Notes for Phases 3-6

1. **Span ID generation:** Use `str(uuid.uuid4())[:8]` for short unique IDs
2. **Context propagation:** Use `TelemetryContext.{push,pop,get_current}_span_id()` for nesting
3. **Payload design:** Keep payloads concise; avoid deeply nested structures
4. **Error handling:** Recorder silently ignores errors to avoid impacting experiment
5. **Performance:** JSONL buffering minimizes I/O; typical overhead < 1ms per event
6. **Thread safety:** contextvars handles async/threading automatically

---

Last updated: 2026-04-03
