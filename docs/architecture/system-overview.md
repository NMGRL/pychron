# System Overview

## Purpose

Describe the active top-level shape of Pychron: launcher startup, Envisage plugin wiring, task-based UI, and the major domain subsystems that handle experiments, hardware, extraction-line control, DVC persistence, and data reduction.

## Main modules

- `launchers/`: application entrypoints such as `pyexperiment` and `pyvalve`
- `pychron/applications/pychron_application.py`: concrete `PychronApplication`
- `pychron/envisage/`: shared plugin, task, startup, and application infrastructure
- `pychron/experiment/`: queue construction and automated run execution
- `pychron/extraction_line/`: valve network control and visualization
- `pychron/hardware/`: shared device and communication layer
- `pychron/dvc/`: repository-backed persistence and metadata services
- `pychron/pipeline/` and `pychron/processing/`: data reduction, plotting, and export

## Key classes

- `PychronApplication` in `pychron/applications/pychron_application.py`
- `BaseTaskPlugin` in `pychron/envisage/tasks/base_task_plugin.py`
- `PychronTasksPlugin` in `pychron/envisage/tasks/tasks_plugin.py`
- subsystem plugins such as `ExperimentPlugin`, `ExtractionLinePlugin`, `HardwarePlugin`, and `DVCPlugin`

## Dependency boundaries

- Launchers and startup code should assemble plugins, not contain domain logic.
- Plugins should register services/tasks and hand off to subsystem managers.
- Task/UI code should depend on managers, factories, and services rather than device drivers directly.
- Shared layers flow inward in this order: `core`/`envisage` -> subsystem managers -> domain workflows -> UI tasks.
- `hardware` is shared infrastructure; domain packages such as `extraction_line`, `lasers`, `spectrometer`, and `furnace` should own instrument-specific behavior.

## Common extension points

- Add or remove plugins through the application initialization path and plugin definitions.
- Register new task factories, task extensions, preferences panes, and service offers in `BaseTaskPlugin` subclasses.
- Contribute subsystem-specific actions and dock panes through Envisage extension points.
- Add new hardware-backed workflows by combining a plugin, manager/service, and task.

## Known sharp edges

- Startup is highly plugin-driven; small plugin-order changes can alter service availability at runtime.
- Many services are resolved dynamically from the application registry, so failures often appear late.
- The repo contains active and legacy paths side by side; confirm which launcher/plugin combination is actually used before editing.
- Cross-cutting globals and preferences in `pychron.globals` and `pychron.paths` make bootstrap bugs look like subsystem bugs.
