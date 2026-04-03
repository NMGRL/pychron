# AGENTS.md

Scope
=====

These instructions apply to the repository root and all subdirectories unless a
more specific `AGENTS.md` overrides them.

Project Context
===============

Pychron is a long-lived scientific application with mixed concerns:

- desktop Qt UI
- hardware control and communication
- automated experiment execution
- DVC/repository-backed persistence
- data reduction and plotting

Favor conservative, low-regression changes over broad rewrites.

Repo Map
========

Start with the user-facing subsystem and only expand outward as needed.

- application/bootstrap and plugin wiring:
  - `launchers/`
  - `pychron/applications`
  - `pychron/envisage`
- experiment execution and scripting:
  - `pychron/experiment`
  - `pychron/pyscripts`
- data reduction, processing, and pipeline work:
  - `pychron/pipeline`
  - `pychron/processing`
- DVC and repository-backed persistence:
  - `pychron/dvc`
- hardware, instruments, and control surfaces:
  - `pychron/hardware`
  - `pychron/lasers`
  - `pychron/extraction_line`
  - `pychron/spectrometer`
  - `pychron/furnace`
- shared foundations used across many subsystems:
  - `pychron/core`
  - `pychron/database`
  - `pychron/paths.py`
  - `pychron/globals.py`

Working Rules
=============

- Start from the current target branch and keep changes scoped.
- Prefer short-lived branches named `codex/<topic>`.
- Do not rewrite or discard user changes without explicit approval.
- Expect the repo to contain legacy modules, experimental files, and partial
  migrations; patch the active path you are changing instead of trying to
  normalize the whole tree in one pass.
- If a subsystem repeatedly needs specialized guidance, add a nested
  `AGENTS.md` in that directory instead of overloading the root file. Only do
  this when the local conventions are stable and materially different from the
  repo-wide defaults.

Code Changes
============

- Prefer focused edits over opportunistic refactors.
- Add type annotations to any function you touch. If a full signature annotation
  would force broader churn, annotate the parameters and return value needed for
  the current edit and keep the rest of the change scoped.
- When debugging a bug or regression, add targeted instrumentation early to
  confirm control flow, state transitions, inputs, and external responses before
  attempting speculative fixes.
- When replacing debug `print()` calls in runtime code, use the repo's existing
  logging style:
  - `Loggable` subclasses use `self.debug(...)`, `self.warning(...)`, etc.
  - other modules typically use `new_logger(...)` or a local logger
- Prefer narrow, hypothesis-driven instrumentation near the suspected failure
  boundary first: UI actions, task/plugin entrypoints, hardware I/O, experiment
  state changes, and DVC/database calls.
- Remove temporary instrumentation before finishing unless it provides ongoing
  operational value. Do not broaden a debugging task into repo-wide logging
  cleanup or leave noisy logs in hot paths without justification.
- Preserve `if __name__ == "__main__":` demo blocks unless the task is to remove
  them. Do not treat demo code as runtime code.
- Keep imports modern in active Qt code. Avoid reintroducing `PySide`,
  `traitsui.qt4`, or `pyface.ui.qt4` in touched files.
- Use ASCII unless the file already requires other characters.

Triage Workflow
===============

- Identify the user-facing subsystem first, then trace inward to the smallest
  active module that implements the behavior.
- Check for nearby tests before editing. Prefer colocated tests under
  `pychron/*/tests`, `test/`, or a subsystem-specific test package before
  reaching for broad suites.
- Favor the path already exercised by launchers, plugins, tasks, or currently
  referenced docs. Do not normalize parallel legacy code paths unless the task
  explicitly requires it.
- Use documentation to disambiguate architecture, startup flow, or workflow
  expectations, but do not widen the implementation scope just because related
  docs exist.
- When adding a nested `AGENTS.md`, keep it limited to local setup, testing,
  or architectural traps. Do not duplicate root policies unless the local file
  is intentionally narrowing them for that subtree.

Testing
=======

- Run the narrowest useful verification for the files you touched.
- Good default checks:
  - `python -m py_compile <files>`
  - `python -m unittest <module>`
- Testing heuristics for this repo:
  - prefer module-level or package-level checks before full-suite runs
  - search for colocated tests under `pychron/*/tests` before using aggregate
    runners such as `pychron/test_suite.py`
  - if a change touches Qt, Traits, hardware, or external services, say what is
    unavailable and fall back to source-level verification when runtime checks
    are not feasible
- If a subsystem depends on Qt, Traits, or hardware services that are unavailable,
  say so explicitly and fall back to source-level verification.

Docs And Workflow
=================

- Keep `README.md` high signal. It should explain what the repo is, where docs
  live, and how development works now.
- Prefer documenting branch/release policy in `docs/dev_guide/`.
- Useful orientation documents:
  - `README.md`
  - `docs/dev_guide/index.rst`
  - `docs/dev_guide/running_pychron.rst`
  - `docs/dev_guide/git_workflow.rst`
- When release workflow changes, keep these files aligned:
  - `docs/dev_guide/git_workflow.rst`
  - `docs/dev_guide/repository_settings.rst`
  - `.github/workflows/ci.yml`

Avoid
=====

- Do not mass-format unrelated files.
- Do not convert large legacy areas just because they match a pattern.
- Do not add broad policy text that conflicts with existing repo workflow.
