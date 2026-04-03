# extraction_line

Extraction line control system for noble gas mass spectrometry. Manages pneumatic
valves, vacuum gauges, cryogenic controllers, heaters, pumps, and sample changer
workflows on a physical gas-processing manifold.

## What This Package Owns

- **Valves / Switches** -- pneumatic valve actuation, interlock checking, ownership,
  software locks, and state persistence
- **Vacuum hardware** -- ion gauges, convection gauges, pumps, manometers
- **Cryo / Heaters** -- temperature control and response recording
- **Pipette tracking** -- shot-count persistence for precision sample delivery
- **Sample changer** -- three-step isolate / evacuate / finish workflow
- **Canvas visualization** -- 2D diagram of the extraction line showing live valve states
- **Graph / topology** -- node-edge representation for volume calculations and path traversal
- **Status monitor** -- background thread that polls hardware state for multi-client setups

## Entry Points

| Class | File | Role |
|-------|------|------|
| `ExtractionLineManager` | `extraction_line_manager.py` | Primary orchestrator; all public APIs |
| `ClientExtractionLineManager` | `client_extraction_line_manager.py` | Network client variant with `StatusMonitor` |
| `SwitchManager` | `switch_manager.py` | Core valve/switch controller |
| `ClientSwitchManager` | `client_switch_manager.py` | Network client; reads state words remotely |
| `StatusMonitor` | `status_monitor.py` | Background polling thread |
| `ExtractionLineGraph` | `graph/extraction_line_graph.py` | Topological graph of the line |
| `SampleChanger` | `sample_changer.py` | Chamber change workflow |
| `ExtractionLinePlugin` | `tasks/extraction_line_plugin.py` | Envisage plugin (service registration) |
| `ExtractionLineTask` | `tasks/extraction_line_task.py` | Envisage task (UI integration) |

## Critical Files

```
extraction_line/
├── extraction_line_manager.py      # Central orchestrator (~1100 lines)
├── switch_manager.py               # Valve control engine (~1300 lines)
├── client_extraction_line_manager.py  # Client variant with StatusMonitor
├── client_switch_manager.py        # Remote state-word reading
├── status_monitor.py               # Background polling thread
├── section.py                      # Valve grouping and state tests
├── sample_changer.py               # Three-step chamber workflow
├── device_manager.py               # Base class for threaded device scanning
├── gauge_manager.py                # Vacuum gauge readings
├── cryo_manager.py                 # Cryogenic temperature control
├── switch_parser.py                # XML/YAML valve config parser
├── graph/
│   ├── extraction_line_graph.py    # Graph builder and volume calculator
│   ├── nodes.py                    # Node types (ValveNode, PumpNode, etc.)
│   └── traverse.py                 # BFS traversal, stops at closed valves
├── pipettes/
│   └── tracking.py                 # Shot-count persistence (JSON/pickle)
└── tasks/
    ├── extraction_line_plugin.py   # Envisage plugin
    └── extraction_line_task.py     # Envisage task
```

## Runtime Lifecycle

1. **Plugin instantiation** -- `ExtractionLinePlugin._factory()` creates an
   `ExtractionLineManager` (or `ClientExtractionLineManager`) and registers it
   as an Envisage service.
2. **Task activation** -- `ExtractionLineTask.activated()` calls
   `manager.activate()`.
3. **Manager activation** -- binds preferences, reloads canvas scene, discovers
   hardware devices via `ICoreDevice` service.
4. **Activate hook** -- starts `StatusMonitor`, begins gauge/heater/pump scan
   threads, optionally schedules periodic hardware state polling.
5. **SwitchManager loading** -- parses valve definitions from XML/YAML, creates
   `HardwareValve` / `ManualSwitch` objects, loads initial states from hardware,
   restores soft locks from pickle, creates `PipetteTracker` instances.
6. **Valve control flow** -- public API (`open_valve` / `close_valve`) → ownership
   check → interlock check → hardware actuation → canvas update → state propagation
   via trait events.

## Test Strategy

**No unit tests exist** for this package. The `tests/` directory is empty.
Runtime communication tests exist as methods on managers (e.g. `test_valve_communication`)
but are not automated test cases.

Recommended test targets:
- `switch_manager.py` -- interlock logic, checksum validation, state-word parsing
- `section.py` -- valve grouping and state-test evaluation
- `graph/traverse.py` -- BFS correctness with closed-valve stopping
- `pipettes/tracking.py` -- persistence round-trips

## Common Failure Modes

| Failure | Symptom | Where |
|---------|---------|-------|
| Missing actuator | Warning dialog, valve inoperable | `switch_manager.py:1095` |
| Invalid valve file | Warning dialog, no valves loaded | `switch_manager.py:992` |
| Checksum mismatch | State not updated, warning logged | `switch_manager.py:676` |
| Software interlock | Valve will not open, warning logged | `switch_manager.py:844` |
| Positive interlock failure | Valve will not open | `switch_manager.py:853` |
| Ownership conflict | Operation silently blocked | `extraction_line_manager.py:916` |
| Pickle/JSON load failure | State silently lost, defaults used | `switch_manager.py`, `pipettes/tracking.py` |
| Hostname resolution failure | Ownership defaults to `"localhost"` | `extraction_line_manager.py:909` |

**Known code-quality concerns:**
- Bare `except BaseException` in several places
- Debug `print()` statements left in `switch_manager.py` (lines 529, 547)
- Dead code: `readback.py` (fully commented out), `programmer/valve_programmer.py`
  (fully commented out), `valve_manager.py.orig` (legacy backup)
- No type hints; mixed Python 2/3 import artifacts
