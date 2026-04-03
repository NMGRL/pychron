# Experiment Architecture

## Purpose

This package owns automated experiment construction and execution. It is the
center of queue editing, automated run lifecycle management, and coordination
with hardware, scripts, and persistence.

## Core Flow

The high-level execution path described in the developer guide is:

1. user builds or opens an experiment queue
2. `ExperimentExecutor.execute` begins execution
3. pre-execute checks run
4. queue execution runs on a worker thread
5. each queue is processed in order
6. each automated run moves through extraction, measurement, and persistence

See `docs/dev_guide/automated_analysis.rst` for the current lifecycle notes.

## Important Areas

- `tasks/`
  - queue editor, executor panes, preferences, and task-level UX
- `queue/`
  - queue models and queue file handling
- `automated_run/`
  - per-run execution logic and tabular adapters
- `script/`
  - experiment-side script coordination
- `conditional/`
  - conditional execution logic and related adapters

## Main Dependencies

Experiment execution sits at the intersection of several other systems:

- hardware services from instrument and extraction-line plugins
- pyscripts in `pychron/pyscripts`
- DVC/database persistence
- task UI and shared editors from Envisage/TraitsUI

Because of this, debugging often requires instrumentation at subsystem
boundaries rather than only inside one class.

## Change Guidance

- Prefer changes in the smallest layer that explains the bug:
  queue model, executor, automated run, or UI editor.
- Keep queue editor behavior and executor behavior aligned when they share the
  same tables or adapters.
- Be cautious with changes to shared run state, threading, and event ordering.
- Validate both editable queue tables and executed-run displays when touching
  shared experiment tabular code.
