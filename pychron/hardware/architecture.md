# Hardware Architecture

## Purpose

This package is the shared hardware-control layer for Pychron. It provides the
manager, controller, and device abstractions used by extraction-line, laser,
spectrometer, furnace, and other instrument-facing workflows.

## Main Responsibilities

- bootstrap and manage hardware devices and controllers
- provide common device abstractions and communication helpers
- support task-level hardware UIs through managers and services
- integrate with remote hardware and hardware-specific plugins

## Important Related Packages

The full hardware story spans multiple packages:

- `pychron/hardware`
  - shared device, controller, and communication infrastructure
- `pychron/extraction_line`
  - extraction-line domain logic and UI
- `pychron/lasers`
  - laser-specific managers, stage managers, and tasks
- `pychron/spectrometer`
  - spectrometer integration and measurement workflows
- `pychron/furnace`
  - furnace-specific managers, firmware, and tasks

Use this package when the issue is in shared hardware abstractions. Use the
domain package when the issue is specific to one instrument family or task.

## Bootstrap Shape

Hardware setup is plugin-driven:

1. application startup includes hardware-related plugins
2. the hardware plugin initializes managers and devices
3. domain packages resolve those services and drive device actions

Remote hardware and embedded hardware-server paths also exist. Confirm which
path is active before changing communication code.

## Change Guidance

- Instrument device boundaries early: command writes, responses, connection
  state, bootstrap, and polling loops.
- Keep changes narrow; shared hardware code can affect multiple instruments.
- Preserve existing logging behavior and avoid replacing field-tested device
  flows unless the bug requires it.
