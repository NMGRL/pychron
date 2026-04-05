# Pychron Device Failure Impact Analysis

## Executive Summary

This analysis examines how device failures affect experiment execution in Pychron, a long-running scientific laboratory automation system. The system has a multi-layered architecture with explicit state machines for executor/queue/run lifecycle management, and shows **limited resilience to device failures** with opportunities for heartbeat/watchdog integration.

---

## 1. Architecture Overview

### 1.1 Execution Flow

```
ExperimentExecutor (main orchestrator)
  ├── Executor State Machine (lifecycle control)
  ├── Queue State Machine (per experiment queue)
  ├── Run State Machine (per individual run)
  └── AutomatedRun (individual analysis execution)
```

**Key Components:**
- `ExperimentExecutor` - coordinates multi-queue execution, handles device I/O
- `ExecutorController` - owns lifecycle policy, transition sequencing
- `AutomatedRun` - delegates to extraction/measurement scripts and data collectors
- `ExtractionLineManager` - device interface, valve/pump/gauge control
- `MeasurementPyScript` / `ExtractionPyScript` - runtime script execution with device commands

### 1.2 Run Lifecycle

Each run goes through explicit states:
```
RUN_IDLE → RUN_CREATING → RUN_STARTING → RUN_PRECHECK 
  → RUN_EXTRACTING [→ RUN_WAITING_OVERLAP_SIGNAL → RUN_WAITING_MIN_PUMPTIME]
  → RUN_MEASURING → RUN_POST_MEASUREMENT → RUN_SAVING → RUN_FINISHING → RUN_SUCCESS
                                                      ↓ 
                                              RUN_FAILED (on error)
```

---

## 2. Device Access Patterns

### 2.1 Where Devices Are Accessed

#### Extraction Phase
- **File**: `pychron/experiment/experiment_executor.py:_extraction()`
- **Code Path**: 
  ```python
  AutomatedRun.start_extraction() 
    → AutomatedRun.do_extraction(syn_extractor)
    → ExtractionPyScript.execute() 
    → pyscript commands (open_valve, close_valve, lock_valve, etc.)
    → ExtractionLineManager methods
  ```

#### Measurement Phase
- **File**: `pychron/experiment/experiment_executor.py:_measurement()`
- **Code Path**:
  ```python
  AutomatedRun.start_measurement()
    → AutomatedRun.do_measurement()
    → MeasurementPyScript.execute()
    → SpectrometryManager operations
    → Data collection loops with device I/O
  ```

#### Post-Measurement Phase
- Device state checks
- Save operations
- Post-run monitoring

### 2.2 Direct Device Command Examples

From `pychron/pyscripts/commands/extractionline.py` and `valve.py`:
```python
# Valve operations (with retry logic already present)
open_valve(name, **kw)      # 3 retries on failure
close_valve(name, **kw)     # 3 retries on failure
unlock_valve(name, **kw)    
lock_valve(name, **kw)      

# Extraction line operations
acquire(name)               # Resource allocation
release(name)               # Resource deallocation
extract(value)              # Extraction device control

# Gauge/pressure operations
get_pressure(controller, name)
```

### 2.3 Device Access in AutomatedRun Pyscript Interface

Methods like:
- `py_equilibration()` - **Opens/closes valves with 3-retry logic**
- `py_position_magnet()` - **Accesses spectrometer, checks `_alive` flag**
- `py_activate_detectors()` - **Accesses spectrometer manager**
- `py_data_collection()` - **Accesses collector, checks `_alive`**
- `py_get_intensity()` - **Reads detector values**
- `py_baselines()` - **Ion optics and detector access**

---

## 3. Current Error Handling & Failure Modes

### 3.1 Retry Logic (Existing)

**Valve Operations** have limited retries:
```python
# From AutomatedRun.py_equilibration() - Lines 594-607
for i in range(3):
    ok, changed = elm.close_valve(o, mode="script")
    if ok:
        break
    else:
        time.sleep(0.1)  # 100ms between attempts
else:
    # After 3 failures, cancel the run
    invoke_in_main_thread(
        self.warning_dialog,
        'Equilibration: Failed to Close "{}"'.format(o),
    )
    self.cancel_run(do_post_equilibration=False)
    return
```

**Takeaway**: Valve ops only retry 3 times with 100ms delays - **very aggressive failure mode**.

### 3.2 No Retry Logic in Most Device Access

- Spectrometer commands: **NO RETRY**
- Gauge/pressure reads: **NO RETRY**
- Extraction line moves: **NO RETRY**
- Data collection: **NO RETRY**

### 3.3 Exception Handling Pattern

**In experiment_executor.py** (Lines 709-715):
```python
try:
    evt.do(ctx)
except BaseException as e:
    self.warning("Event {} failed. exception: {}".format(evt.id, e))
    import traceback
    self.debug(traceback.format_exc())
```

**Pattern**: Exceptions logged but often swallowed - **run may continue in degraded state**.

### 3.4 Device Availability Tracking

**Location**: `pychron/extraction_line/extraction_line_manager.py:build_canvas_state()` (Lines 426-429)
```python
if self.devices:
    degraded_devices = [
        dev.name for dev in self.devices 
        if hasattr(dev, "enabled") and not dev.enabled
    ]
```

**Current State**: 
- Devices can be marked `enabled=False`
- **NO CHECK** prevents device operations on disabled devices
- **NO BLOCKING** of runs based on degraded devices
- **VISUALIZATION ONLY** - appears in UI state but doesn't affect execution

### 3.5 Monitor-Based Failure Detection

**AutomatedRunMonitor** (Lines 112-138 in `pychron/monitors/automated_run_monitor.py`):
```python
def _fcheck_conditions(self):
    ok = True
    for ci in self.checks:
        pa = ci.parameter
        # Evaluate pressure/device parameter against rule
        if ci.check_condition(v):
            self._fatal_errors.append(ci.message)
            ok = False
            break
    return ok
```

**Usage** (in controller, Line 1233):
```python
fatal_error=bool(self.monitor and self.monitor.has_fatal_error())
```

**Current State**:
- Only checks pre-configured conditions (pressure, device values)
- **NO HEARTBEAT** of device connectivity itself
- **REACTIVE** (waits for value to go out of range, not proactive health checks)

---

## 4. Cascade Failure Analysis

### 4.1 How One Device Failure Stops the Whole Run

**Scenario 1: Valve Fails to Open During Equilibration**

```
1. AutomatedRun.py_equilibration() tries to open inlet valve
2. ExtractionLineManager.open_valve() fails 3 times (total ~300ms)
3. cancel_run() called with do_post_equilibration=False
4. Run moves to CANCELED state
5. Measurement never executes
6. Data is not saved/published
7. Queue continues to next run (if not configured to stop)
```

**Verdict**: **ONE VALVE FAILURE → ENTIRE RUN LOST**

---

**Scenario 2: Spectrometer Detector Becomes Unresponsive**

```
1. py_data_collection() → MeasurementPyScript.execute()
2. Data collection loop accesses detector → timeout/no response
3. Exception NOT caught by py_data_collection()
4. Exception propagates through pyscript runner
5. Run marked as FAILED
6. Data collection aborted mid-measurement
7. Partial/corrupted isotope data saved
```

**Verdict**: **DETECTOR FAILURE → RUN FAILS, PARTIAL DATA PERSISTED**

---

**Scenario 3: Pump Stops During Extraction**

```
1. AutomatedRun.do_extraction() executes extraction script
2. Script calls extract_pump(power=100)
3. ExtractionLineManager.set_device(pump, 100) → timeout
4. Exception logged, script execution may continue
5. Subsequent commands execute with pump off
6. Sample contaminated/insufficient extraction
7. Run continues to measurement with bad data
```

**Verdict**: **PUMP FAILURE → RUN CONTINUES WITH BAD DATA**

---

### 4.2 Current Mitigations (All Weak)

1. **`is_alive` flag**: Only set by user cancel/abort, NOT by device health
   - Location: `pychron/experiment/automated_run/automated_run.py:261`
   - Checked in: `py_position_magnet()`, `py_activate_detectors()`, `py_data_collection()`
   - **Problem**: User must manually cancel, devices don't trigger it

2. **Monitor Fatal Errors**: Only checks pre-defined conditions
   - Location: `pychron/experiment/experiment_executor.py:1233`
   - Code: `fatal_error=bool(self.monitor and self.monitor.has_fatal_error())`
   - **Problem**: No connectivity checks, config-dependent

3. **Pre-run Checks**: Before queue execution
   - Location: `pychron/experiment/experiment_executor.py:_pre_execute_check()`
   - **Problem**: Only at queue start, not continuous monitoring

4. **Valve Retry Logic**: 3 attempts then abort
   - Location: `pychron/experiment/automated_run/automated_run.py:594-608`
   - **Problem**: 300ms timeout total is too aggressive for transient issues

---

## 5. Logging & Monitoring of Device Errors

### 5.1 Where Logged

**Hardware-Level**:
- `pychron/hardware/core/base_core_device.py` - TimeoutError, CRCError
- `pychron/hardware/core/communicators/` - Communication errors
- Device-specific managers log via `self.logger`

**Application-Level**:
- `ExtractionLineManager.debug()` / `.warning()` / `.critical()`
- `AutomatedRun.warning()` / `.debug_exception()`
- Pyscript execution exceptions logged via script runner

**Telemetry** (Newer):
- `pychron/experiment/telemetry/device_io.py` - Tracks device I/O timing/success
- Device I/O context manager:
  ```python
  @contextmanager
  def device_io(name, device_name, payload=None):
      try:
          yield result  # Device operation
      except Exception as e:
          record event with error=str(e)
          raise
  ```

### 5.2 Current Gaps in Device Health Visibility

1. **No Proactive Health Heartbeat**
   - No periodic "ping" to check device is responsive
   - No pre-run device connectivity verification loop

2. **No Device State Tracking**
   - Last successful operation timestamp per device
   - No "degradation detection" (e.g., increasing timeouts)

3. **No Watchdog Timer**
   - Operations can hang indefinitely
   - No "expected max duration" enforcement

4. **No Cascading Failure Prevention**
   - One device failure doesn't quarantine related devices
   - E.g., if pump fails, extraction still proceeds

5. **No Circuit Breaker Pattern**
   - Repeated failures don't trigger device disable
   - No "fail fast" mode for known-bad devices

---

## 6. Existing Metrics & Reliability Tracking

### 6.1 What's Tracked

**Per-Run**:
- `spec.state` - Run terminal state (SUCCESS, FAILED, CANCELED, etc.)
- `run.duration` - Total execution time
- Isotope data quality metrics (in post-measurement)

**Per-Queue**:
- `stats.experiment_queues` - Active queues
- `stats.current_run_duration_f` - Current run time

**System-Level**:
- `degraded_devices` list in `CanvasSystemState`
- Monitor fatal error count

### 6.2 What's NOT Tracked

- **Device-specific success rate** (e.g., "valve X opened successfully in 95% of cases")
- **Mean time between device failures** (MTBDF)
- **Device response time distribution** (to detect degradation)
- **Correlation between device failures and run failures**
- **"Time since last successful health check" per device**
- **Cascade failure chains** (device A failed → device B failed → run canceled)

---

## 7. Gaps Where Watchdog/Heartbeat Would Add Value

### 7.1 Pre-Run Health Check

**Current**: One-time at queue start via `_pre_execute_check()`

**Gap**: No refresh between runs in a queue

**Watchdog Solution**:
```
Between each run:
  FOR each device in extraction_line_manager.devices:
    Send quick ping/read command
    IF timeout or error:
      Mark device as degraded
      IF critical device (valve, pump, spectrometer):
        Skip or abort next run
      Log event with timestamp
    ELSE:
      Update last_successful_heartbeat_time
```

### 7.2 Continuous Device Monitoring During Run Execution

**Current**: Only monitors pre-configured conditions (pressure range, etc.)

**Gap**: No detection of:
- Sudden device disconnects mid-run
- Increasing communication latency
- Partial failures (e.g., some detectors unresponsive)

**Watchdog Solution**:
```
During extraction/measurement:
  Background thread every 5-10 seconds:
    FOR each active device:
      IF device used in current phase:
        Send non-blocking health query
        IF response time > baseline_expected * 2:
          Increment degradation_count
        IF response time > baseline_expected * 5 OR no response:
          Trigger run abort + mark device as failed
        IF device hasn't responded in 30+ seconds:
          Timeout → abort run
```

### 7.3 Transient Failure Retry with Backoff

**Current**: Fixed 3 retries with 100ms delay for valves only

**Gap**: 
- Other operations (spectrometer, extraction) have NO retries
- No exponential backoff (helps with congestion)
- No transient vs. permanent failure discrimination

**Watchdog Solution**:
```
For device operations:
  attempt = 0
  backoff = 50ms
  max_backoff = 5s
  
  WHILE attempt < max_attempts:
    TRY operation with timeout
    ON timeout/transient_error:
      attempt += 1
      sleep(backoff)
      backoff *= 1.5 (up to max_backoff)
      CONTINUE
    ON permanent_error (device not found, auth fail):
      break (don't retry)
    ON success:
      reset backoff
      break
  
  IF all attempts failed:
    IF is_critical_operation (valve, pump):
      abort_run()
    ELSE:
      cancel_run()
```

### 7.4 Device Recovery/Graceful Degradation

**Current**: 
- Device marked `enabled=False` but no automatic re-enable
- No "skip non-critical" mode

**Gap**: No handling of:
- Temporarily failed device that recovers
- Partial run continuation without non-critical device
- Device quarantine period before retrying

**Watchdog Solution**:
```
After device failure:
  Mark as QUARANTINED with timestamp
  For next 5 minutes:
    Fail-fast all operations to that device
  After 5 minutes:
    Send health ping
    IF success: reanimate device
    IF fail: QUARANTINE for 5 more min (max 30 min)
  
  For non-critical devices (gauges):
    Allow run to continue with degraded monitoring
  For critical devices (valves, pump):
    Abort run immediately
```

### 7.5 Run Step Timeout Enforcement

**Current**: No explicit timeout per phase (extraction, measurement, save)

**Gap**: 
- Extraction can hang indefinitely
- Measurement loops can deadlock
- Saves can block queue for hours

**Watchdog Solution**:
```
For each run phase:
  phase_start_time = now()
  phase_timeout = configured_timeout (e.g., 30 min for extraction)
  
  DURING phase:
    IF now() - phase_start_time > phase_timeout:
      Log "Phase timeout - likely device hang"
      abort_run()
      mark_device_that_last_responded_as_suspect()
```

---

## 8. Integration Points for Heartbeat Contract

### 8.1 Controller Integration

**File**: `pychron/experiment/state_machines/controller.py`

**Integration Point**: `run_step_sequence()` method (Line 733)
```python
def run_step_sequence(self) -> tuple[str, ...]:
    return ("_start", "_extraction", "_measurement", "_post_measurement")
```

**Enhancement**:
```python
# Before each step, execute heartbeat check
def pre_run_step_health_check(self, run_id: str, step_name: str) -> bool:
    """Check device health before each run phase"""
    # Call heartbeat manager
    # Returns True if OK, False if critical device failed
    # If False, trigger run abort
```

### 8.2 Executor Integration

**File**: `pychron/experiment/experiment_executor.py`

**Integration Point**: `_do_run()` method (Line 1181+)
```python
# Line 1248 - Current step execution
if not getattr(self, step)(run):
    self.warning("{} did not complete successfully".format(step[1:]))
```

**Enhancement**:
```python
# Wrap step execution with timeout + heartbeat
def _do_run_step_with_heartbeat(self, step_name, run):
    """Execute run step with device health monitoring"""
    heartbeat_manager = self.heartbeat_manager  # new component
    
    # Start continuous health monitoring thread
    monitor_thread = heartbeat_manager.start_phase_monitor(
        phase=step_name,
        run_id=run.uuid,
        critical_devices=self._get_critical_devices_for_phase(step_name),
        timeout_seconds=self._get_phase_timeout(step_name)
    )
    
    try:
        result = getattr(self, step)(run)
    finally:
        heartbeat_manager.stop_phase_monitor(monitor_thread)
    
    return result
```

### 8.3 AutomatedRun Integration

**File**: `pychron/experiment/automated_run/automated_run.py`

**Integration Point**: `py_equilibration()` method (Line 570+)

Current (3-retry logic):
```python
for i in range(3):
    ok, changed = elm.close_valve(o, mode="script")
    if ok:
        break
    else:
        time.sleep(0.1)
else:
    invoke_in_main_thread(self.warning_dialog, ...)
    self.cancel_run(do_post_equilibration=False)
    return
```

**Enhancement**:
```python
# Use heartbeat-aware retry with backoff
result = self.extraction_line_manager.close_valve_with_retry(
    valve_name=o,
    mode="script",
    retry_strategy="exponential_backoff",  # vs. fixed
    initial_delay=50e-3,  # 50ms
    max_delay=5,  # 5s
    max_attempts=10
)
if not result:
    self.extraction_line_manager.mark_device_unavailable(o)
    self.cancel_run(do_post_equilibration=False)
    return
```

### 8.4 ExtractionLineManager Integration

**File**: `pychron/extraction_line/extraction_line_manager.py`

**Integration Point**: Device access methods

Current:
```python
def open_valve(self, name, **kw):
    return self._open_close_valve(name, "open", **kw)

def get_pressure(self, controller, name):
    if self.gauge_manager:
        return self.gauge_manager.get_pressure(controller, name)
```

**Enhancement**:
```python
def open_valve_with_heartbeat(self, name, **kw):
    """Open valve with built-in health check"""
    # Check device heartbeat first
    if not self.is_device_healthy(name):
        self.warning(f"Device {name} marked unhealthy")
        return False
    
    # Execute with timeout enforcement
    try:
        return self.open_valve(name, **kw)
    except TimeoutError:
        self.mark_device_unavailable(name)
        raise
    finally:
        # Update last_op_timestamp for this device
        self.devices[name].last_op_timestamp = time.time()
```

---

## 9. Recommendations

### Priority 1: Implement Exponential Backoff Retry
- Replace fixed 3-attempt logic with configurable backoff
- Apply to all device operations (not just valves)
- **Effort**: Medium | **Impact**: High

### Priority 2: Add Pre-Phase Device Health Checks
- Before extraction, measurement, save: quick ping all devices
- **Effort**: Medium | **Impact**: High

### Priority 3: Implement Phase Timeout Enforcement
- Configure max duration per run phase
- **Effort**: Low | **Impact**: Medium

### Priority 4: Track Device Health Metrics
- Last successful operation timestamp per device
- Operation success rate per device
- Mean response time per device
- **Effort**: Medium | **Impact**: Medium

### Priority 5: Add Circuit Breaker Pattern
- Disable devices after N consecutive failures
- Quarantine period before re-enabling
- **Effort**: Medium | **Impact**: High

### Priority 6: Continuous Background Heartbeat (Low Frequency)
- Every 30-60s during measurement, check device responsiveness
- Alert if device hasn't responded in 5 min
- **Effort**: High | **Impact**: Low-Medium

---

## 10. Key Files for Implementation

| File | Purpose | Heartbeat Role |
|------|---------|-----------------|
| `pychron/experiment/state_machines/controller.py` | Lifecycle policy | Pre-phase health check trigger |
| `pychron/experiment/experiment_executor.py` | Run orchestration | Phase timeout enforcement |
| `pychron/extraction_line/extraction_line_manager.py` | Device interface | Device health status tracking |
| `pychron/experiment/automated_run/automated_run.py` | Run logic | Device availability checks in pyscripts |
| `pychron/monitors/automated_run_monitor.py` | Run monitoring | Device health checks |
| `pychron/experiment/telemetry/device_io.py` | Telemetry | Device operation tracking |

---

## 11. Conclusion

**Current State**: 
- Pychron has good state machine architecture but **reactive device error handling**
- One device failure cascades to entire run failure with **limited mitigation**
- Retry logic is limited (3 attempts for valves only) and too aggressive
- No continuous device health monitoring or heartbeat mechanism

**Heartbeat/Watchdog Value**: 
- **High**: Pre-phase health checks would catch device disconnects early
- **High**: Exponential backoff retry would handle transient issues
- **Medium**: Continuous monitoring would detect degradation patterns
- **High**: Circuit breaker pattern would prevent thrashing

**Integration Points**: Clear and well-defined in state machine layers and device manager interfaces.

