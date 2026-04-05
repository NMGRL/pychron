# Pychron Testing Patterns and Regression Risk Analysis

## Test File Locations and Structure

### Core Hardware/Device Tests
- **Device Bootstrap Tests**: `/pychron/core/tests/device_bootstrap_test.py`
  - Tests bootstrap lifecycle: load → open → initialize → post_initialize
  - Tests error handling during bootstrap phases
  - Uses lightweight harness class (_BootstrapHarness) with no external dependencies

- **Communicator Tests**: `/pychron/hardware/core/tests/`
  - `has_communicator_test.py` - HasCommunicator mixin tests
  - `ethernet_communicator_test.py` - Network communication tests
  - `simulation_core_test.py` - Fault injection and simulation
  - `transport_simulation_test.py` - End-to-end communicator tests

- **Simulation/Fault Injection**: `/pychron/hardware/core/simulation/`
  - Comprehensive fault injection framework supporting:
    - Timeout faults
    - Disconnect faults
    - Malformed packet faults
    - Out-of-range value faults
    - Stale status faults

### Experiment/Execution Tests
- **Executor State Machine Tests**: `/pychron/experiment/tests/executor_state_machine_test.py`
  - Minimal stub setup (_ExecutorStub)
  - Tests state transitions without external dependencies
  - No device interaction testing

- **Device I/O Telemetry Tests**: `/pychron/experiment/telemetry/tests/test_device_io_telemetry.py`
  - Tests decorator and context manager patterns
  - Uses Mock objects from unittest.mock
  - Tests timing, success/failure capture, context propagation

- **Extraction Line Tests**: `/pychron/extraction_line/tests/network_state_test.py`
  - Network state computation tests
  - No device or communicator interaction

### Pyscript Integration Tests
- **Extraction Script Tests**: `/pychron/pyscripts/tests/extraction_script.py`
  - Uses simple Dummy classes (DummyDevice, DummyManager, DummyApplication)
  - Tests waitfor() functionality with mock device return values
  - Tests timing behavior

## Current Coverage of Error Paths

### Existing Retry Logic
1. **EthernetCommunicator.ask()** (~line 491-506):
   - Retries 2-3 times on None response
   - 25ms sleep between retries
   - Controlled via `use_error_mode` parameter

2. **EthernetCommunicator.read()** (~line 565-579):
   - Retries 3 times on timeout
   - Handles socket.timeout exceptions
   - Sets error_mode flag

3. **SerialCommunicator._write()**:
   - Has `retry_on_exception` parameter
   - Retries failed writes once with exception handling

### Error Conditions Tested
- Timeout faults (TransportTimeoutError)
- Disconnect faults (TransportDisconnectError)
- Malformed packets
- Out-of-range values
- Stale status (repeated previous state)

### Missing Coverage
- Device health check/heartbeat patterns
- Recovery from sustained disconnections
- Error modes persisting across commands
- Device operation success/failure tracking
- Aggregate failure metrics
- Recovery decision-making logic

## Test Patterns to Follow

### Pattern 1: Lightweight Harness Classes
```python
class _FakeCommunicator:
    def __init__(self):
        self.open_calls = []
        self.closed = False
    
    def open(self, **kw):
        self.open_calls.append(kw)
        return True
```
**When to use**: Unit tests that don't require Qt, Traits, or full lifecycle
**Benefit**: Fast, no dependencies, easy to inspect

### Pattern 2: Mock Objects from unittest.mock
```python
from unittest.mock import Mock

obj = Mock()
result = test_func(obj)
```
**When to use**: Decorator/context manager tests, method call verification
**Benefit**: Automatic tracking, flexible attribute/method mocking

### Pattern 3: Simulation Adapters with Fault Injection
```python
adapter = SimulatorTransportAdapter(
    "serial",
    PychronValveSimulatorProtocol(),
    fault_policy=FaultPolicy([
        {"fault": "timeout", "match": "GetValveState"}
    ])
)
```
**When to use**: End-to-end integration tests, error condition testing
**Benefit**: Records sessions, replays for deterministic testing, injects faults

### Pattern 4: Bootstrap Harness with Event Tracking
```python
class _BootstrapHarness:
    def __init__(self):
        self.events = []
    
    def load(self, *args, **kw):
        self.events.append("load")
        return True
```
**When to use**: Lifecycle and state transition tests
**Benefit**: Verifies call sequence, minimal overhead

### Pattern 5: Context Managers for Telemetry
```python
with TelemetryDeviceIOContext("device", "operation", recorder) as ctx:
    ctx.set_payload("key", value)
    # operation code
```
**When to use**: Tests of instrumentation, timing capture
**Benefit**: Automatic timing, exception capture, context propagation

## Integration Test Structure

### Transport Simulation Tests
- Create adapter with simulator protocol
- Optionally wrap with recorder for session capture
- Optionally add fault policies
- Call ask/write/read methods
- Verify responses match simulator behavior

### End-to-End Device Tests
- Instantiate device class (e.g., PychronGPActuator)
- Create communicator with SimulatorTransportAdapter
- Assign communicator to device
- Call device methods (e.g., open_channel, get_channel_state)
- Verify state changes correctly

Example from transport_simulation_test.py:
```python
def test_pychron_valve_simulator_end_to_end(self):
    actuator = PychronGPActuator(name="sim-actuator")
    communicator = SerialCommunicator()
    communicator.set_transport_adapter(
        SimulatorTransportAdapter("serial", PychronValveSimulatorProtocol())
    )
    communicator.open()
    actuator.communicator = communicator
    
    self.assertTrue(actuator.open_channel(valve))
    self.assertTrue(actuator.get_channel_state(valve))
```

## Regression Test Suite

### Included in Main Suite (test_suite.py)
- DeviceBootstrapTestCase
- Executor state machine tests (executor_state_machine_test.py)
- Telemetry tests (test_device_io_telemetry.py)

### Not Yet in Suite
- Hardware communicator tests (hardcoded imports, may require traits)
- Transport simulation tests (marked @skipIf for missing traits)
- Extraction line tests (marked @skipIf for yaml stub)

### Running Regression Tests
```bash
# Full test suite
python -m unittest pychron.test_suite

# Device-specific tests
python -m unittest pychron.core.tests.device_bootstrap_test
python -m unittest pychron.hardware.core.tests.has_communicator_test
python -m unittest pychron.hardware.core.tests.ethernet_communicator_test

# Executor state machine tests
python -m unittest pychron.experiment.tests.executor_state_machine_test

# Telemetry tests
python -m unittest pychron.experiment.telemetry.tests.test_device_io_telemetry
```

## Device Manager Implementation

### Current DeviceManager Pattern (/extraction_line/device_manager.py)
```python
class DeviceManager(Manager):
    def _scan(self):
        self.is_alive = True
        while self.is_alive:
            for h in self.devices:
                if h.is_scanable and h.should_update():
                    func = h.scan_func or "update"
                    if isinstance(func, str):
                        func = getattr(h, func)
                    with h.lock_scan():
                        func()
            time.sleep(self.period)
```
- No error handling in scan loop
- No retry logic
- No device state tracking
- Thread spawned in start_scans()
- Thread stopped via is_alive flag

### Key Integration Points for Watchdog
1. _scan() loop - where periodic update happens
2. lock_scan() context manager - synchronizes device access
3. DeviceManager.devices list - all managed devices
4. Each device's scan_func/update method
5. should_update() gate - rate limiting check

## Existing Test Fixtures and Mocks We Can Reuse

### FakeCommunicator Pattern
```python
class _FakeCommunicator:
    def __init__(self):
        self.open_calls = []
        self.sent = []
        self.recv_chunks = []
    
    def ask(self, *args, **kw):
        return args, kw
```
**File**: `pychron/hardware/core/tests/has_communicator_test.py`
**Reusable**: Yes - implement basic communicator interface

### SimulatorTransportAdapter
```python
adapter = SimulatorTransportAdapter(
    "serial",
    PychronValveSimulatorProtocol(),
    fault_policy=FaultPolicy([...])
)
```
**File**: `pychron/hardware/core/simulation/`
**Reusable**: Yes - inject failure scenarios
**Patterns**: timeout, disconnect, malformed, out_of_range, stale_status

### TelemetryRecorder
```python
recorder = TelemetryRecorder(log_path)
# ... operations ...
recorder.flush()
```
**File**: `pychron/experiment/telemetry/recorder.py`
**Reusable**: Yes - capture operation timings and status

## Recommendations for Minimizing Regression Risk

### 1. Test Isolation
- **Use lightweight harnesses**: Avoid full Traits/Qt initialization
- **Separate layers**: Unit test logic, integration test behavior
- **Simulation over reality**: Use adapters instead of real hardware

### 2. Incremental Addition
- Add heartbeat tests first (no device state change)
- Add health check tests next (read-only operations)
- Add recovery logic tests last (state-changing operations)

### 3. Error Path Coverage
- **Happy path**: Ensure baseline tests pass
- **Timeout scenarios**: Use TransportTimeoutError injection
- **Disconnect scenarios**: Use TransportDisconnectError injection
- **Stale data**: Use stale_status fault policy
- **Recovery success**: Verify retry logic succeeds after N attempts

### 4. Device Manager Integration
- Mock DeviceManager.devices list
- Mock device.lock_scan() context manager
- Track update() call counts and timing
- Verify scan loop continues after errors

### 5. State Machine Testing
- Verify state transitions don't break executor controller
- Test that watchdog doesn't interfere with active operations
- Verify error events are captured by telemetry system

### 6. Performance Testing
- Measure overhead of health check operations
- Verify scanning loop latency with monitoring
- Test contention on lock_scan() with multiple devices

### 7. Bootstrap Testing
- Ensure devices still bootstrap correctly
- Verify post_initialize runs after new watchdog init
- Test error recovery during device load phase

## Files to Monitor for Regression

### High Priority
- `pychron/hardware/core/base_core_device.py` - Device base class
- `pychron/hardware/core/scanable_device.py` - Scanning interface
- `pychron/extraction_line/device_manager.py` - Update loop
- `pychron/hardware/core/communicators/communicator.py` - Communication base

### Medium Priority
- `pychron/hardware/core/communicators/ethernet_communicator.py` - Retry logic
- `pychron/hardware/core/communicators/serial_communicator.py` - Retry logic
- `pychron/experiment/experiment_executor.py` - Executor integration
- `pychron/extraction_line/extraction_line_manager.py` - Device manager setup

### Integration Points to Test
1. Device bootstrap still completes successfully
2. Device update loop continues after errors
3. Executor doesn't hang on device I/O errors
4. State machines maintain consistency with device health
5. Telemetry captures all device operations
6. Experiment cleanup still occurs properly

## Quick Test Reference

| Test Type | File | Pattern | Skip Condition |
|-----------|------|---------|-----------------|
| Bootstrap | `core/tests/device_bootstrap_test.py` | Harness class | PyYAML not installed |
| Communicator | `hardware/core/tests/has_communicator_test.py` | Fake class | None |
| Ethernet | `hardware/core/tests/ethernet_communicator_test.py` | Fake sockets | Traits not available |
| Simulation | `hardware/core/tests/simulation_core_test.py` | Transport adapter | Traits not available |
| Integration | `hardware/core/tests/transport_simulation_test.py` | Full device + adapter | Traits not available |
| State Machine | `experiment/tests/executor_state_machine_test.py` | Stub executor | None |
| Telemetry | `experiment/telemetry/tests/test_device_io_telemetry.py` | Mock + recorder | None |

