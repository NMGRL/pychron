# Hardware Abstractions

## Purpose

Capture the shared device and communication layer used by extraction-line, laser, furnace, and spectrometer workflows so changes in `pychron/hardware` stay scoped and low-regression.

## Main modules

- `pychron/hardware/core/`: base device abstractions, interfaces, communicators, schedulers, alarms, and tests
- `pychron/hardware/actuators/`: switch and valve actuator implementations
- `pychron/hardware/*/`: concrete device families such as gauges, controllers, labjacks, Eurotherms, and motion hardware
- `pychron/hardware/tasks/hardware_plugin.py`: plugin wiring for shared hardware services

## Key classes

- `ICoreDevice`
- `BaseCoreDevice`
- `CoreDevice`
- `AbstractDevice`
- `Communicator`
- `SwitchController`
- `HasCommunicator`

## Dependency boundaries

- Domain packages should depend on `ICoreDevice`-style service boundaries instead of concrete communicators when possible.
- `BaseCoreDevice` owns communicator lifecycle, request/response flow, polling, and scheduler integration.
- `AbstractDevice` is for composition over another device; it should not grow direct transport logic that belongs in the wrapped core device.
- Transport/protocol code belongs under `hardware/core/communicators`, not in UI managers or task code.

## Common extension points

- Add new concrete hardware by subclassing `CoreDevice` or `BaseCoreDevice`.
- Add derived or proxy devices by subclassing `AbstractDevice`.
- Add new transports or protocol adapters under `pychron/hardware/core/communicators/`.
- Add shared hardware managers and task wiring through the hardware plugin and the consuming subsystem plugin.

## Known sharp edges

- Communication behavior depends on config files, scheduler selection, simulation mode, and runtime preferences; verify the full path before changing command logic.
- Shared hardware classes are reused across multiple instrument families, so small changes can have wide blast radius.
- `ask`, `tell`, polling, and post-initialize scanning interact with threads and schedulers; deadlocks and timing bugs are possible.
- Many device classes are configured dynamically by class name and package path, so import-time refactors can silently break setup.
