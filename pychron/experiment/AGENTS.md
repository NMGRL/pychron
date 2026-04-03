# AGENTS.md

Scope
=====

These instructions apply to `pychron/experiment/` and all subdirectories unless
a deeper `AGENTS.md` overrides them.

Local Architecture
==================

Experiment execution is in transition from a procedural executor to an explicit
state-machine-driven architecture.

Current split of responsibilities:

- `experiment_executor.py`
  - Traits/UI compatibility
  - service lookup and manager wiring
  - worker-thread creation
  - concrete side effects such as waits, dialogs, save calls, teardown calls,
    and queue/run display refresh
- `state_machines/controller.py`
  - executor/queue/run lifecycle policy
  - legal transition sequencing
  - overlap eligibility and settle policy
  - run-step progression policy
  - queue and run terminal result selection
- `state_machines/*.py`
  - explicit executor, queue, and run state definitions and transitions

When editing this package, preserve that direction. Do not push new lifecycle
policy back into ad hoc booleans or procedural branches if the controller or
machine layer is the natural home.

Working Rules
=============

- Prefer changing `state_machines/controller.py` for lifecycle policy and
  transition sequencing.
- Prefer controller-owned action-plan helpers for queue/run lifecycle
  sequencing when the executor only needs to perform concrete side effects.
- Prefer changing `experiment_executor.py` only for concrete effects, Traits
  compatibility, and UI/service integration.
- Keep public executor-facing Traits/events stable unless the task explicitly
  allows breaking editor/task compatibility.
- If you touch queue/run execution flow, update the nearest docs:
  - `docs/dev_guide/automated_analysis.rst`
  - `pychron/experiment/README.md`
  - `docs/architecture/experiment-execution.md` when architecture guidance changes
- If you add a new controller-owned policy helper, add or extend focused tests
  in `pychron/experiment/tests/executor_state_machine_test.py`.

Testing
=======

Good default verification for this subtree:

- `python -m py_compile pychron/experiment/experiment_executor.py pychron/experiment/state_machines/controller.py`
- `python -m unittest pychron.experiment.tests.executor_state_machine_test`
- add `pychron.experiment.tests.editor_executor_sync` when executor-facing Traits
  behavior changes
- add `pychron.experiment.tests.state_machine` when run-state compatibility changes

Avoid
=====

- Do not introduce new executor control flow keyed primarily on `alive`,
  `_canceled`, `_aborted`, `extracting`, or `measuring` when the controller can
  own the policy.
- Do not rewrite unrelated experiment UI/editor code while touching executor
  lifecycle behavior.
