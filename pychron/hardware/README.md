# hardware

Hardware abstraction layer for noble gas mass spectrometry instrument control.
Provides device classes, communication protocols, and a simulation system for
testing without physical hardware.

## What This Package Owns

- **Device communication** -- Serial (RS-232/RS-485), Ethernet/TCP, GPIB, USB,
  Modbus, OPC, ZMQ, Telnet, and VISA protocols
- **Valves / Actuators** -- pneumatic valve control, indicator state reading,
  software locking, actuation tracking
- **Vacuum gauges** -- Granville Phillips, MKS, Pfeiffer, Varian XGS600,
  IGC100, PLC2000 controllers
- **Temperature control** -- Eurotherm, Watlow EZ Zone, Lakeshore (330/335/336),
  thermocouple transducers, PID controllers
- **Furnaces** -- temperature setpoints, process values, output readings
- **Lasers** -- Fusions CO2, UV, and diode laser control boards
- **Motion control** -- Zaber, Kinesis, Newport, MDrive, Aerotech stages
- **Spectrometer controllers** -- Thermo (Argus/Helix), Isotopx NGX, Quadera
- **ADC / Sensors** -- LabJack U3, MCC, NCD, transducers, pyrometers,
  environmental probes, chillers, ion pumps, turbo pumps
- **Simulation system** -- replay-based and protocol-based transport simulation
  with configurable fault injection

## Entry Points

The package uses a **name-to-module mapping** system rather than `__all__`:

| Registry | File | Purpose |
|----------|------|---------|
| `HW_PACKAGE_MAP` | `__init__.py` | Maps device type names to module paths |
| `PACKAGES` | `actuators/__init__.py` | Maps actuator class names to module paths |

Key device classes (instantiated by name through the registries):

| Class | Sub-package | Role |
|-------|-------------|------|
| `CoreDevice` | `core/core_device.py` | Main workhorse device (composite base) |
| `BaseCoreDevice` | `core/base_core_device.py` | Communication, scanning, alarms, scheduler |
| `ScanableDevice` | `core/scanable_device.py` | Periodic polling, CSV logging, graphing |
| `ViewableDevice` | `core/viewable_device.py` | Traits UI device with connection state display |
| `AbstractDevice` | `core/abstract_device.py` | Wrapper/delegation pattern for composite devices |
| `HardwareValve` | `valve.py` | Valve with state tracking, actuation delay |
| `Switch` | `switch.py` | Software locking, actuation tracking |
| `Actuator` | `actuators/actuator.py` | Dynamic device loader for valve actuators |
| `GPActuator` | `actuators/gp_actuator.py` | General-purpose actuator with lock/verify |
| `BaseGaugeController` | `gauges/base_controller.py` | Pressure reading, voltage-to-pressure mapping |
| `BaseFurnaceController` | `furnace/base_furnace_controller.py` | Setpoint/process/output management |
| `PychronLaser` | `lasers/pychron_laser.py` | Alias for `FusionsLogicBoard` |

## Critical Files

```
hardware/
├── __init__.py                     # HW_PACKAGE_MAP registry
├── valve.py                        # HardwareValve, DoubleActuationValve
├── switch.py                       # BaseSwitch, Switch
├── pychron_device.py               # RemoteDeviceMixin, SerialDeviceMixin
├── transducer.py                   # Transducer, AirTransducer
├── pneumatics.py                   # ADC-based pressure reading
├── core/
│   ├── core_device.py              # CoreDevice (main composite base)
│   ├── base_core_device.py         # BaseCoreDevice (ask/tell/read, scheduler)
│   ├── scanable_device.py          # ScanableDevice (polling, alarms, CSV)
│   ├── viewable_device.py          # ViewableDevice (Traits UI)
│   ├── abstract_device.py          # AbstractDevice (delegation wrapper)
│   ├── i_core_device.py            # ICoreDevice interface
│   ├── exceptions.py               # TimeoutError, CRCError
│   ├── communicators/
│   │   ├── communicator.py         # Base Communicator (lock, transport, logging)
│   │   ├── serial_communicator.py  # SerialCommunicator (pyserial)
│   │   ├── ethernet_communicator.py # EthernetCommunicator (TCP sockets)
│   │   ├── scheduler.py            # CommunicationScheduler (RS-485 bus lock)
│   │   └── ...                     # gpib, modbus, opc, rpc, telnet, visa, zmq
│   └── simulation/
│       ├── adapters.py             # ReplayTransportAdapter, SimulatorTransportAdapter
│       ├── factory.py              # build_transport_adapter()
│       ├── faults.py               # FaultPolicy (timeout, disconnect, malformed)
│       ├── protocols.py            # NGXSimulatorProtocol, PychronValveSimulatorProtocol
│       └── session.py              # TransportSession / TransportEvent (JSON recording)
├── actuators/
│   ├── actuator.py                 # Actuator (dynamic device loader)
│   ├── gp_actuator.py              # GPActuator (general-purpose, lock/verify)
│   └── ...                         # T4, U3, ProXR, PychronGP, etc.
├── gauges/
│   └── base_controller.py          # BaseGauge, BaseGaugeController
├── furnace/
│   └── base_furnace_controller.py  # BaseFurnaceController
├── lasers/                         # Fusions CO2, UV, diode laser classes
├── mass_spec/                      # Thermo, Isotopx NGX, Quadera controllers
├── motion/                         # Zaber, Kinesis, Newport, MDrive stages
└── tests/
    ├── has_communicator_test.py    # HasCommunicator mixin unit tests
    └── transport_simulation_test.py # Simulation system tests
```

## Runtime Lifecycle

### Phase 1: Configuration Loading
Device instantiated with `name` and `configuration_dir_name`. `load()` reads an
INI-style config file. The `[Communications]` section determines the communicator
type (serial, ethernet, etc.). `HasCommunicator` dynamically imports and
instantiates the appropriate communicator.

### Phase 2: Opening
`open()` calls `communicator.open()` to establish the physical connection
(serial port, TCP socket, etc.).

### Phase 3: Initialization
`initialize()` calls `communicator.initialize()` for device-specific handshake
(e.g., ID query).

### Phase 4: Post-Initialization
`post_initialize()` sets up scanning (periodic polling), alarms, and the
communication scheduler. If `auto_start` is True, scanning begins immediately.

### Communication Flow
- **`ask(cmd)`** -- Send command, wait for response. Goes through the scheduler
  if configured (for RS-485 bus arbitration).
- **`tell(cmd)`** -- Send command, no response expected.
- **`read()`** -- Read-only, no preceding write.
- All three are wrapped with `@crc_caller` to catch and log CRC errors.

### Simulation Mode
Configured via `backend = replay` or `backend = simulator` in the
`[Communications]` section:
- **Replay** -- Plays back a recorded `TransportSession` (JSON) of
  request/response pairs. Modes: `strict` (sequential) or `scripted` (match by payload).
- **Simulator** -- Uses a protocol handler to generate live responses.
- **Fault injection** -- Configurable via `faults = timeout, intermittent_disconnect`.

## Test Strategy

Tests are sparse and narrowly focused (3 test files):

| Test File | Coverage |
|-----------|----------|
| `core/tests/has_communicator_test.py` | `HasCommunicator` mixin (build, create, require, open) |
| `core/tests/transport_simulation_test.py` | Replay round-trip, recording adapter, fault injection |
| `core/tests/ethernet_communicator_test.py` | Ethernet communicator tests |

**Notable gaps**: No tests for concrete device classes (valves, gauges,
furnaces, lasers, spectrometers). No hardware-in-the-loop test harness.

## Common Failure Modes

| Failure | Symptom | Where |
|---------|---------|-------|
| CRC error | Logged warning, returns `None` (not propagated) | `@crc_caller` decorator |
| Missing communicator | Warning logged, returns `None` | `require_communicator()` |
| Config loading failure | Warning dialog, device bootstrap aborted | `load_additional_args()` |
| Dynamic class load failure | Warning dialog for unknown `klass` | `HasCommunicator._communicator_factory()` |
| Timeout | `TimeoutError` raised on `blocking_poll()` | `core/exceptions.py` |
| Not implemented | `NotImplementedError` in abstract methods | `GPActuator`, `BaseFurnaceController` |

**Known risk areas:**
- CRC errors are swallowed -- downstream code may operate on stale/`None` data
- No retry logic at the device layer (opt-in per device via `repeat_command()`)
- Dynamic class loading via `__import__` + `getattr` -- typos in config silently
  fail with a warning dialog
- Thread safety: `CommunicationScheduler` uses a simple `Lock` for RS-485 bus
  arbitration; individual communicators also use `RLock`
