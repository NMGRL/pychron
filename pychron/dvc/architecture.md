# DVC Architecture

## Purpose

This package owns Pychron's repository-backed persistence layer. It bridges the
application domain with DVC metadata, Git-backed repositories, and related
save/import/export workflows.

## Main Responsibilities

- connect to DVC-related services and metadata stores
- persist analyses and associated artifacts
- pull, push, or sync repository-backed data
- support DVC-aware entry, loading, and import workflows
- expose helper types used by other packages that need DVC access

## Important Areas

- `dvc.py`
  - central DVC-facing service object used by multiple subsystems
- `dvc_persister.py`
  - analysis persistence workflow and save/upload coordination
- `tasks/`
  - DVC-related UI and preferences
- `reports/`
  - DVC-backed reporting helpers

Other packages often depend on DVC through mixins or helper base classes rather
than direct ownership. Common consumers include `entry`, `loading`, and
`data_mapper`.

## Integration Shape

Typical call patterns are:

- task or manager requests a DVC service from the application
- workflow gathers domain state
- DVC or `DVCPersister` translates that state into metadata, files, and
  repository operations

This package is a high-risk integration seam because failures may involve local
state, Git/DVC repositories, metadata databases, and operator configuration at
the same time.

## Change Guidance

- Instrument early around save, pull, push, and repository-selection boundaries.
- Prefer fixing the DVC service or persister layer over duplicating persistence
  behavior in consumers.
- Avoid broad repository-behavior changes unless the bug clearly spans multiple
  DVC consumers.
