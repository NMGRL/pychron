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

Working Rules
=============

- Start from the current target branch and keep changes scoped.
- Prefer short-lived branches named `codex/<topic>`.
- Do not rewrite or discard user changes without explicit approval.
- Expect the repo to contain legacy modules, experimental files, and partial
  migrations; patch the active path you are changing instead of trying to
  normalize the whole tree in one pass.

Code Changes
============

- Prefer focused edits over opportunistic refactors.
- When replacing debug `print()` calls in runtime code, use the repo's existing
  logging style:
  - `Loggable` subclasses use `self.debug(...)`, `self.warning(...)`, etc.
  - other modules typically use `new_logger(...)` or a local logger
- Preserve `if __name__ == "__main__":` demo blocks unless the task is to remove
  them. Do not treat demo code as runtime code.
- Keep imports modern in active Qt code. Avoid reintroducing `PySide`,
  `traitsui.qt4`, or `pyface.ui.qt4` in touched files.
- Use ASCII unless the file already requires other characters.

Testing
=======

- Run the narrowest useful verification for the files you touched.
- Good default checks:
  - `python -m py_compile <files>`
  - `python -m unittest <module>`
- If a subsystem depends on Qt, Traits, or hardware services that are unavailable,
  say so explicitly and fall back to source-level verification.

Docs And Workflow
=================

- Keep `README.md` high signal. It should explain what the repo is, where docs
  live, and how development works now.
- Prefer documenting branch/release policy in `docs/dev_guide/`.
- When release workflow changes, keep these files aligned:
  - `docs/dev_guide/git_workflow.rst`
  - `docs/dev_guide/repository_settings.rst`
  - `.github/workflows/ci.yml`

Avoid
=====

- Do not mass-format unrelated files.
- Do not convert large legacy areas just because they match a pattern.
- Do not add broad policy text that conflicts with existing repo workflow.
