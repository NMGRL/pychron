# Extraction Line

## Purpose

Document the subsystem that controls and visualizes the extraction-line valve network, related gauges and pumps, and the procedure hooks that experiments and scripts use during gas handling.

## Main modules

- `pychron/extraction_line/extraction_line_manager.py`: top-level extraction-line service
- `pychron/extraction_line/switch_manager.py`: valve and switch state management
- `pychron/extraction_line/tasks/`: task/plugin wiring and panes
- `pychron/extraction_line/canvas/` and `pychron/extraction_line/extraction_line_canvas.py`: 2D canvas state and rendering
- `pychron/extraction_line/graph/`: valve network topology
- `pychron/pyscripts/` and `pychron/extraction_line/*script_runner*.py`: script integration points

## Key classes

- `ExtractionLineManager`
- `SwitchManager`
- `ExtractionLineTask`
- `ExtractionLineCanvas`
- `ExtractionLineCanvasViewModel`
- `ExtractionLineGraph`
- `IPyScriptRunner` and `PyScriptRunner`

## Dependency boundaries

- `ExtractionLineManager` is the service boundary exposed to tasks and higher-level workflows.
- `SwitchManager` owns valve/switch state and actuator coordination; UI code should not talk to actuators directly.
- Hardware devices are resolved through `ICoreDevice` and shared hardware abstractions rather than extraction-line UI classes.
- Canvas/view-model code should reflect manager state, not become a second source of truth.

## Common extension points

- Add task actions, menu items, and panes in `pychron/extraction_line/tasks/extraction_line_plugin.py`.
- Add plugin canvases through the `pychron.extraction_line.plugin_canvases` extension point.
- Add new managers such as gauges, pumps, or cryo support through `ExtractionLineManager` service wiring.
- Add new valve definitions, interlocks, and switch metadata through the extraction-line configuration files parsed by `SwitchManager`.

## Known sharp edges

- Valve state is a mix of live hardware, cached state files, and canvas refresh events; stale state bugs are common.
- Interlocks, ownership, and child-actuation rules are spread across config and runtime code, so behavior can be surprising.
- There are polling, monitoring, and file-listener paths running concurrently; race conditions are easy to introduce.
- `.orig` and older alternative code paths exist in this area; edit the active files, not the backups.
