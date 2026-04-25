# Pychron Architecture

## Purpose

This file is a fast orientation guide for the active codebase. It is not a full
design spec. Use it to find the right subsystem before making changes.

## Top-Level Shape

Pychron is a Qt desktop application built on Enthought Envisage and TraitsUI.
The codebase combines:

- application bootstrap and plugin composition
- experiment execution and automation
- DVC-backed persistence and repository workflows
- hardware/instrument control
- processing, plotting, and review tooling

The active runtime package is `pychron/`. Legacy and experimental paths exist;
prefer the path that is currently wired into launchers, tasks, and plugins.

## Startup Flow

The main startup path is:

1. launcher script in `launchers/`
2. launcher helper entry point
3. environment/path/bootstrap setup
4. `pychron.envisage.pychron_run`
5. application object and plugin assembly
6. Envisage task application run loop

The runtime tree under `~/Pychron` is now bootstrap-managed. The supported
operator and developer setup flow uses:

- `pychron-bootstrap`
- `pychron-doctor`
- `python -m pychron doctor`

See `docs/dev_guide/running_pychron.rst` and `docs/dev_guide/installation.rst`
for the current startup and install flow.

## Major Subsystems

### Envisage / application shell

- `pychron/envisage`
- `pychron/applications`
- `launchers/`

Owns application startup, plugin registration, task panes, browser/task shell,
preferences dialogs, and shared UI wiring.

See `pychron/envisage/architecture.md`.

### Experiment execution

- `pychron/experiment`
- `pychron/pyscripts`

Owns experiment queues, execution state, automated runs, scripts, queue editors,
and run lifecycle coordination.

See `pychron/experiment/architecture.md`.

### DVC persistence

- `pychron/dvc`
- parts of `pychron/entry`, `pychron/loading`, `pychron/data_mapper`

Owns repository-backed persistence, metadata lookup, analysis save/pull/push
behavior, and DVC-facing import/export helpers.

See `pychron/dvc/architecture.md`.

### Hardware and instruments

- `pychron/hardware`
- `pychron/extraction_line`
- `pychron/lasers`
- `pychron/spectrometer`
- `pychron/furnace`

Owns device managers, controllers, remote hardware integration, and task-level
instrument UIs.

See `pychron/hardware/architecture.md`.

### Processing and review

- `pychron/pipeline`
- `pychron/processing`
- `pychron/envisage/browser`

Owns data reduction, browser tables, plotting, review tools, and many operator
analysis workflows.

## Shared Foundations

Common cross-cutting infrastructure lives in:

- `pychron/core`
- `pychron/database`
- `pychron/paths.py`
- `pychron/globals.py`

Treat these as shared dependencies. Changes here have a larger blast radius than
changes inside a task-specific package.

## Working Guidance

- Trace from the user-visible screen or command first, then narrow to the active
  plugin, task, manager, or editor.
- Check for local `architecture.md` and `AGENTS.md` files before changing a deep
  subsystem.
- Add instrumentation early when debugging cross-subsystem behavior, especially
  at plugin boundaries, queue execution boundaries, hardware I/O, and DVC save
  or load points.
- Prefer small fixes in the active path over broad cleanup across parallel
  legacy implementations.
