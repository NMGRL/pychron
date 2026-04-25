# experiment

Experiment orchestration engine for automated Ar/Ar geochronology analyses.
Manages the full lifecycle of running samples through an extraction line and
mass spectrometer -- from queue setup through data persistence.

## What This Package Owns

- **Experiment queues** -- tabular lists of analyses loaded from tab-delimited
  files with YAML metadata headers
- **Automated runs** -- individual analysis executions with a formal state machine
  and controller-owned lifecycle policy
- **Python scripts** -- per-run PyScripts that program extraction, measurement,
  and post-measurement behavior
- **Conditionals** -- runtime rules that can truncate, terminate, cancel, or
  modify the queue based on live data (isotope signals, pressures, ages, ratios)
- **Overlap mode** -- concurrent execution where extraction of run N+1 starts
  in a thread while measurement of run N is still running
- **Data persistence** -- saving results to database, DVC, and Excel
- **Statistics** -- run timing, weighted means, MSWD, ETF tracking
- **Scheduling** -- delayed start and scheduled stop

This package **orchestrates** hardware subsystems; it does **not** own hardware
communication (see `extraction_line/`, `spectrometer/`, `lasers/`) or data
reduction (see `processing/`).

## Entry Points

| Class | File | Role |
|-------|------|------|
| `Experimentor` | `experimentor.py` | Top-level facade; owns factory, queue, executor |
| `ExperimentFactory` | `factory.py` | Builds queues and run specs from UI input |
| `ExperimentQueue` | `queue/experiment_queue.py` | Main queue class; manages run list |
| `ExperimentExecutor` | `experiment_executor.py` | Executor adapter for UI/state/effects |
| `ExecutorController` | `state_machines/controller.py` | Lifecycle controller for executor/queue/run policy |
| `AutomatedRun` | `automated_run/automated_run.py` (~3350 lines) | Executes a single analysis |
| `AutomatedRunSpec` | `automated_run/spec.py` | Data model for a queued run |
| `BaseScript` | `script/script.py` | Per-run PyScript management |
| `Datahub` | `datahub.py` | Central data store manager (DVC, MassSpec DB) |
| `ExperimentEditorTask` | `tasks/experiment_task.py` | Envisage task (UI integration) |

## Critical Files

```
experiment/
├── experimentor.py                   # Top-level manager / facade
├── experiment_executor.py            # Core execution engine (~2900 lines)
├── factory.py                        # ExperimentFactory / AutomatedRunFactory
├── experiment_queue/
│   ├── experiment_queue.py           # Main queue class
│   ├── base_queue.py                 # Load/dump tab-delimited files
│   ├── run_block.py                  # Groups runs into blocks
│   ├── parser.py                     # RunParser / UVRunParser
│   └── factory.py                    # ExperimentQueueFactory
├── automated_run/
│   ├── automated_run.py              # Single analysis executor (~3350 lines)
│   ├── spec.py                       # Run data model
│   ├── state_machine.py              # Formal state machine
│   ├── multi_collector.py            # Data collector (multi-collector)
│   ├── peak_hop_collector.py         # Data collector (peak-hopping)
│   └── persistence.py                # Save to DB / DVC / Excel
├── state_machines/
│   ├── controller.py                 # Executor/queue/run lifecycle controller
│   ├── executor_machine.py           # Top-level executor states
│   ├── queue_machine.py              # Queue states and transitions
│   ├── run_machine.py                # Run states and transitions
│   └── base.py                       # Shared machine base + transition records
├── conditional/
│   ├── conditional.py                # All conditional types (~900 lines)
│   └── utilities.py                  # Tokenizer for conditional expressions
├── script/
│   └── script.py                     # PyScript loading and validation
├── datahub.py                        # Central data store manager
├── experiment_status.py              # UI status display
├── experiment_scheduler.py           # Delayed start / scheduled stop
├── conflict_resolver.py              # Repository identifier conflicts
├── events.py                         # Hook system (5 event levels)
├── stats.py                          # Run timing and statistics
├── utilities/
│   ├── identifier.py                 # Labnumber parsing and formatting
│   ├── runid.py                      # Run ID manipulation
│   ├── position_regex.py             # Position expression parsing
│   ├── conditionals.py               # Conditional constants
│   └── comment_template.py           # Comment templating
└── tasks/
    └── experiment_task.py            # Envisage task (UI panes)
```

## Runtime Lifecycle

The runtime is no longer only a procedural loop in `ExperimentExecutor`.
Execution policy is split across:

- `ExperimentExecutor` for Traits/UI compatibility, service lookups, threads,
  and concrete side effects
- `ExecutorController` for lifecycle decisions
- explicit executor, queue, and run state machines under `state_machines/`

### Phase 0: Setup
User configures an `ExperimentQueue` via `ExperimentFactory` UI, adding
`AutomatedRunSpec` entries. Each spec has: labnumber, aliquot, position,
scripts (extraction, measurement, post-equilibration, post-measurement),
and parameters (duration, extract value, cleanup times, etc.).

### Phase 1: Execute
`ExperimentExecutor.execute()` runs pre-execute checks (hardware connectivity,
script existence), updates the executor state machine through the controller,
then starts a new thread `"Execute Queues"`.

### Phase 2: Queue Loop
Iterates over all open experiment queues. Queue lifecycle setup, next-run
preparation, overlap mode, save waits, settle mode, and terminal result
selection are now controller/state-machine responsibilities even though
`ExperimentExecutor` still performs the concrete waits and side effects.

### Phase 3: Run Loop
Gets a run generator yielding `AutomatedRunSpec` objects. For each spec:
pre-run check → `_make_run()` → controller selects serial vs overlap execution
mode → executor performs the selected side effect.

### Phase 4: Individual Run
Each run executes major phases in controller-defined order:
```
_start → _extraction → _measurement → _post_measurement
```
- **`_start`**: Sets integration time, calls `run.start()`
- **`_extraction`**: Runs extraction PyScript, monitors extraction line
- **`_measurement`**: Runs measurement PyScript with data collection
  (multi-collector or peak-hop). Equilibration scripts run concurrently.
- **`_post_measurement`**: Runs post-measurement PyScript

The controller now owns:

- run step order
- continue/stop/abort/fatal step-loop policy
- overlap eligibility
- queue settle policy
- save policy
- queue terminal result selection
- queue completion and post-save action plans

After steps: `run.save()` → post-run check → `run.finish()` → `run.teardown()`

### Phase 5: Completion
`_end_runs()` stops stats timer, `END_QUEUE` event fires, and executor/queue
terminal states are finalized through the controller.

### Overlap Mode
If a run's `overlap` flag is set, extraction runs in a separate thread while
the next run's measurement can begin. Critical for throughput when laser
heating takes longer than measurement setup.

### Event System
Five event levels allow external hooks:
`START_QUEUE` → `START_RUN` → `SAVE_RUN` → `END_RUN` → `END_QUEUE`

## Test Strategy

Tests live in `pychron/experiment/tests/` (21 test files). Uses standard
`unittest` framework.

| Test File | Coverage |
|-----------|----------|
| `state_machine.py` | State machine transitions (nominal, terminal, abort, reset) |
| `identifier.py` | `get_analysis_type()` for all special identifiers |
| `conditionals.py` | Conditional parsing, tokenization, evaluation |
| `conditionals_actions.py` | Conditional action execution |
| `pyscript_integration.py` | Script name resolution, loading validation |
| `frequency_test.py` | Frequency run generation |
| `position_regex_test.py` | Position regex matching |
| `analysis_grouping_test.py` | Analysis grouping logic |
| `editor_executor_sync.py` | Editor-executor synchronization |
| `repository_identifier.py` | Repository identifier handling |

**Notable gaps**: No unit tests for `ExperimentExecutor`, `AutomatedRun`,
`ExperimentQueue`, or `RunParser` -- too tightly coupled to hardware and Qt.

## Common Failure Modes

| Failure | Symptom | Where |
|---------|---------|-------|
| Pre-execute check failure | Warning dialog, `alive=False` | `experiment_executor.py` |
| Pre-run check failure | Run skipped, logged | `experiment_executor.py` |
| Step failure | Run transitions to FAILED, queue stops | `experiment_executor.py` |
| Monitor fatal error | Run canceled and failed | `automated_run/` |
| DVC save timeout (>5 min) | Run canceled, marked FAILED | `experiment_executor.py` |
| Post-run check failure | `_err_message` set, queue stops | `experiment_executor.py` |
| User cancel/stop/abort | Three levels of intervention | `experiment_executor.py` |
| Repository conflicts | Same labnumber, different identifiers | `conflict_resolver.py` |
| Database errors | `DatabaseError` caught, logged | `experiment_executor.py` |

### Exception Classes
- `ExtractionException` -- extraction hardware failures
- `PreExecuteCheckException` -- pre-execute validation failures
- `PreExtractionCheckException` -- pre-extraction check failures
- `CheckException` -- base for check failures with tag
- `MessageException` -- generic message+error exception

### User Intervention Levels
- **Stop**: Sets `alive=False`, waits for current run to finish
- **Cancel**: Sets `_canceled=True`, cancels current run (30s confirmation timeout)
- **Abort**: Sets `_aborted=True`, immediately aborts running extraction/measurement
