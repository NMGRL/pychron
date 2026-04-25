# Pychron Testing Patterns Search Results

## Overview

This directory contains comprehensive documentation on testing patterns and regression risk analysis for the pychron codebase, specifically focused on understanding how to safely implement device heartbeat and watchdog functionality.

## Documentation Files

### 1. TESTING_PATTERNS.md
**Comprehensive guide to testing patterns used in pychron**

Contains:
- 5 core test patterns with code examples and use cases
- Integration test structure for device/communicator testing
- Regression test suite information
- Device manager implementation details
- Existing test fixtures and mocks available for reuse
- Recommendations for minimizing regression risk
- Quick test reference table

**Best for:** Understanding HOW to write tests following pychron conventions

### 2. TESTING_SUMMARY.txt
**Detailed reference with absolute file paths and analysis**

Contains:
- Absolute file paths for all 10 key test files
- Core device classes with line counts and key methods
- Communicators with retry logic details
- Simulation framework components
- 4-phase testing strategy for watchdog implementation
- Regression test commands
- Risk areas analysis
- Migration path from baseline to full implementation
- Reusable test fixtures with descriptions
- Key insights and findings

**Best for:** Finding WHERE things are and WHAT the risks are

## Quick Navigation

### By Task

**I want to understand device testing:**
→ TESTING_PATTERNS.md → "Integration Test Structure" section

**I want to find a specific test file:**
→ TESTING_SUMMARY.txt → "ABSOLUTE FILE PATHS FOR KEY TEST FILES"

**I want to know what patterns to follow:**
→ TESTING_PATTERNS.md → "Test Patterns to Follow" section

**I want to understand regression risks:**
→ TESTING_SUMMARY.txt → "RISK AREAS FOR WATCHDOG IMPLEMENTATION"

**I want to run existing tests:**
→ TESTING_SUMMARY.txt → "REGRESSION TEST COMMAND" section

**I want to understand device lifecycle:**
→ TESTING_SUMMARY.txt → "CORE DEVICE CLASSES TO UNDERSTAND"

### By File Type

**Test Files:**
- Device bootstrap: `/pychron/core/tests/device_bootstrap_test.py`
- Communicator: `/pychron/hardware/core/tests/has_communicator_test.py`
- Ethernet: `/pychron/hardware/core/tests/ethernet_communicator_test.py`
- Simulation: `/pychron/hardware/core/tests/simulation_core_test.py`
- Transport: `/pychron/hardware/core/tests/transport_simulation_test.py`
- State Machine: `/pychron/experiment/tests/executor_state_machine_test.py`
- Telemetry: `/pychron/experiment/telemetry/tests/test_device_io_telemetry.py`

**Core Classes:**
- BaseCoreDevice: `/pychron/hardware/core/base_core_device.py`
- ScanableDevice: `/pychron/hardware/core/scanable_device.py`
- HasCommunicator: `/pychron/has_communicator.py`
- DeviceManager: `/pychron/extraction_line/device_manager.py`

**Communicators with Retry Logic:**
- EthernetCommunicator: `/pychron/hardware/core/communicators/ethernet_communicator.py`
- SerialCommunicator: `/pychron/hardware/core/communicators/serial_communicator.py`

**Simulation Framework:**
- Location: `/pychron/hardware/core/simulation/`
- Key classes: SimulatorTransportAdapter, FaultPolicy, TransportSession

## Key Findings Summary

### 1. Testing Infrastructure Maturity
- **Comprehensive**: 10+ major test files, 50+ test classes, 200+ test methods
- **Well-layered**: Unit tests → Integration tests → End-to-end tests
- **Isolation-focused**: Simulation adapters avoid real hardware
- **Dependency-conscious**: Tests can be run without Qt/Traits

### 2. Error Recovery Patterns Exist
- **EthernetCommunicator**: 2-3 retries with 25ms backoff
- **SerialCommunicator**: 1 retry on exception
- **Fault Framework**: 5 types of injectable faults (timeout, disconnect, etc.)
- **Gap**: No health tracking, no device state aggregation

### 3. Test Patterns Available
- **Lightweight harnesses**: Zero-dependency test doubles
- **Fake communicators**: Minimal interface for unit testing
- **Simulation adapters**: Full protocol simulation with fault injection
- **Telemetry recording**: Structured operation logging

### 4. Regression Risk Factors
**HIGH RISK:**
- DeviceManager._scan() loop currently has no error handling
- Must coordinate with existing retry logic at 3 levels
- Bootstrap initialization timing critical

**MEDIUM RISK:**
- Telemetry system integration
- Device lock contention
- Error categorization (operational vs. device health)

**LOW RISK:**
- Configuration loading isolated
- UI display independent
- Database operations unaffected

### 5. Recommended Implementation Path
1. **Phase 1**: Add heartbeat to BaseCoreDevice (unit tests with _FakeCommunicator)
2. **Phase 2**: Integrate with DeviceManager._scan() (tests with SimulatorTransportAdapter)
3. **Phase 3**: Add recovery logic (tests with fault injection)
4. **Phase 4**: Verify executor state machine (tests with controller stub)

## Running Tests

### Quick Smoke Test (no dependencies)
```bash
python -m unittest pychron.core.tests.device_bootstrap_test
```

### Core Hardware Tests (requires Traits)
```bash
python -m unittest pychron.hardware.core.tests.has_communicator_test
python -m unittest pychron.hardware.core.tests.ethernet_communicator_test
python -m unittest pychron.hardware.core.tests.simulation_core_test
python -m unittest pychron.hardware.core.tests.transport_simulation_test
```

### Executor Tests
```bash
python -m unittest pychron.experiment.tests.executor_state_machine_test
```

### Telemetry Tests
```bash
python -m unittest pychron.experiment.telemetry.tests.test_device_io_telemetry
```

### Full Suite
```bash
python -m unittest pychron.test_suite
```

## Test Pattern Recommendations

### For Watchdog Unit Tests
**Pattern**: Use `_FakeCommunicator` from `has_communicator_test.py`
- Lightweight, zero dependencies
- Fast execution
- Easy to track calls and verify behavior
- Example: `extraction_line/tests/device_watchdog_test.py` (to create)

### For Watchdog Integration Tests
**Pattern**: Use `SimulatorTransportAdapter` from `hardware/core/simulation/`
- Full protocol simulation
- Fault injection support
- Session recording/replay
- Example: `hardware/core/tests/transport_simulation_test.py`

### For Manager Integration Tests
**Pattern**: Use harness from `device_bootstrap_test.py`
- Track execution sequence
- Verify error handling
- Test state transitions
- Example: New file in `extraction_line/tests/`

### For State Machine Tests
**Pattern**: Use stub executor from `executor_state_machine_test.py`
- Minimal setup, no Qt/Traits required
- Verify transitions
- Test policy decision methods
- Example: `experiment/tests/executor_state_machine_test.py`

## Critical Integration Points

1. **DeviceManager._scan()**: Main entry point for periodic updates
   - Currently no error handling
   - Loops through devices calling scan_func/update
   - Must not break on device communication errors

2. **BaseCoreDevice.ask()**: Communication point
   - Has built-in retries (2-3 attempts)
   - Decorated with @crc_caller for error handling
   - Watchdog should not interfere with active operations

3. **Device.lock_scan()**: Synchronization point
   - Context manager for thread-safe device access
   - Watchdog health checks may contend here
   - Need to consider locking strategy

4. **TelemetryContext**: Instrumentation capture
   - Captures operation timing and status
   - Propagates context IDs (queue_id, run_id, etc.)
   - Useful for health operation tracking

5. **ExecutorController**: State machine
   - Controls experiment execution
   - Must remain unaffected by watchdog operations
   - State transitions must continue correctly

## Files to Monitor

**High Priority (Direct Impact):**
- `pychron/hardware/core/base_core_device.py`
- `pychron/hardware/core/scanable_device.py`
- `pychron/extraction_line/device_manager.py`
- `pychron/hardware/core/communicators/communicator.py`

**Medium Priority (Coordination Needed):**
- `pychron/hardware/core/communicators/ethernet_communicator.py`
- `pychron/hardware/core/communicators/serial_communicator.py`
- `pychron/experiment/experiment_executor.py`
- `pychron/extraction_line/extraction_line_manager.py`

## Key Insights

1. **Error Coverage Gap**: Retry logic exists but not extensively tested for sustained failures
2. **Test Isolation Critical**: Hardware tests can be optional, enables safe local development
3. **Few Integration Points**: Main entry through DeviceManager._scan(), clear boundaries
4. **Minimal Footprint**: Heartbeat logic can live in BaseCoreDevice, manager integration is 5-10 lines
5. **Regression Risk Mitigated**: By comprehensive test suite and clear separation of concerns

## Next Steps

1. Read TESTING_PATTERNS.md for pattern descriptions and examples
2. Read TESTING_SUMMARY.txt for absolute paths and detailed analysis
3. Review target files:
   - `pychron/extraction_line/device_manager.py` (integration point)
   - `pychron/hardware/core/base_core_device.py` (where watchdog logic lives)
   - `pychron/hardware/core/tests/has_communicator_test.py` (test pattern example)
4. Create unit tests for watchdog logic
5. Create integration tests with fault injection
6. Run regression tests to establish baseline
7. Implement watchdog following recommended pattern

## Additional Resources

- Repo Map: See AGENTS.md for subsystem layout
- Experiment Execution: See `docs/dev_guide/automated_analysis.rst`
- Hardware Control: See `docs/architecture/` for hardware subsystem docs
- Development Guide: See `docs/dev_guide/` for workflow and setup

---

**Generated**: 2025-04-03
**Scope**: Testing patterns for BaseCoreDevice, ScanableDevice, and device manager watchdog implementation
**Status**: Complete - ready for watchdog development

