# Experiment Execution

## Purpose

Describe how Pychron builds experiment queues, validates them, and executes automated runs by coordinating extraction-line, spectrometer, persistence, and conditional logic.

## Main modules

- `pychron/experiment/tasks/`: Experiment task and UI wiring
- `pychron/experiment/experimentor.py`: task-facing coordinator
- `pychron/experiment/factory.py`: queue and run construction
- `pychron/experiment/queue/`: queue models and queue editing helpers
- `pychron/experiment/experiment_executor.py`: runtime queue execution engine
- `pychron/experiment/automated_run/`: automated run specs, runtime execution, persistence, and state machine
- `pychron/experiment/conditional/`: queue/run/system conditional logic

## Key classes

- `ExperimentPlugin`
- `ExperimentEditorTask`
- `Experimentor`
- `ExperimentFactory`
- `ExperimentQueueFactory`
- `AutomatedRunFactory`
- `ExperimentQueue`
- `ExperimentExecutor`
- `AutomatedRun`
- `AutomatedRunSpec`

## Dependency boundaries

- Task/editor code should operate through `Experimentor`, factories, and queue models, not execute runs directly.
- `ExperimentExecutor` is the runtime boundary between queue models and instrument services.
- Instrument-specific actions should stay behind injected services such as extraction-line, spectrometer, ion optics, DVC, and dashboard clients.
- Conditional logic should remain in the `conditional` package rather than leaking into UI handlers.

## Common extension points

- Add new task actions, panes, and menu contributions in `pychron/experiment/tasks/experiment_plugin.py`.
- Contribute dock panes, activation hooks, deactivation hooks, and custom events through the Experiment plugin extension points.
- Extend queue creation by adding fields or defaults in the queue and run factories.
- Add runtime checks and policy through system, queue, or run conditionals.

## Known sharp edges

- `ExperimentExecutor` is a large coordinator with many service dependencies; regressions often surface only at runtime.
- Queue editing and queue execution share state; changes during execution require careful handling of `queue_modified` and generator reset paths.
- Persistence can target multiple backends and formats, so partial-save and recovery paths are easy to break.
- Much of the control flow is asynchronous and event-driven, which makes ordering bugs around cancellation, truncation, and recovery difficult to diagnose.
