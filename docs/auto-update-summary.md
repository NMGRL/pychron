# Documentation Update Review

**Triggered by commit:** `4101592fb`  
**Generated:** 2026-04-27 18:56 UTC  
**Compare:** [`6b633738f18d04611ee04bb863f3bfc53aeeb7e6...4101592fb`](../../compare/6b633738f18d04611ee04bb863f3bfc53aeeb7e6...4101592fb)

## Affected Documents

| Document | Files Changed | Status |
|---|---|---|
| [DVC Setup Guide](#dvc-setup-guide) | 2 files | ✅ Reviewed |
| [Multi-Node Deployment Guide](#multi-node-deployment) | 3 files | ✅ Reviewed |

## All Changed Files in This Commit

<details>
<summary>Click to expand</summary>

```
pychron/core/ui/gui.py
pychron/core/ui/qt/camera_editor.py
pychron/core/ui/qt/video_component_editor.py
pychron/core/wait/wait_control.py
pychron/core/wait/wait_group.py
pychron/dvc/dvc.py
pychron/dvc/repository_sync.py
pychron/envisage/pychron_run.py
pychron/envisage/tasks/base_tasks_application.py
pychron/experiment/automated_run/automated_run.py
pychron/experiment/automated_run/data_collector.py
pychron/experiment/experiment_executor.py
pychron/experiment/experimentor.py
pychron/experiment/factory.py
pychron/experiment/plot_panel.py
pychron/experiment/queue/base_queue.py
pychron/extraction_line/tasks/extraction_line_pane.py
pychron/extraction_line/tasks/extraction_line_pane.py.bak
pychron/extraction_line/tasks/extraction_line_task.py
pychron/graph/guide_overlay.py
pychron/options/options.py
pychron/pipeline/plot/plotter/arar_figure.py
pychron/pipeline/tests/grid_axis_visibility_test.py
```

</details>

---

## DVC Setup Guide {#dvc-setup-guide}

**Doc file:** `docs/dvc_setup_guide.md`  
**Matched prefixes:** `pychron/dvc/`

### Changed Files

- `pychron/dvc/dvc.py`
- `pychron/dvc/repository_sync.py`

### AI Review

## Code Change Summary

The changes introduce a new `repository_root` configuration attribute to the DVC class, improve error handling by properly raising DVCException instead of printing errors, and add comprehensive repository recovery mechanisms with detailed logging for sync failures. These changes affect how DVC handles repository synchronization errors and may introduce new configuration options that users need to understand.

## Documentation Updates Required

- **Section/Topic:** Configuration fields and preferences
  **Issue:** The new `repository_root` attribute is not documented as a configurable field
  **Suggested update:** Add `repository_root` to the list of DVC configuration fields with a description of its purpose (likely specifies the root directory where repositories are stored)

- **Section/Topic:** Failure modes when GitHub/GitLab is unreachable
  **Issue:** The documentation doesn't cover the new automatic repository recovery behaviors and enhanced error handling
  **Suggested update:** Add a subsection describing the automatic recovery process that attempts to clean repository state when sync fails, including the sequence of recovery steps (fetch, pull, reset to remote) and that local commits may be discarded during recovery

- **Section/Topic:** Error handling and troubleshooting
  **Issue:** The change from printing errors to raising DVCException for missing attributes may affect user-visible error behavior
  **Suggested update:** Update any examples or descriptions of error messages to reflect that attribute access errors now raise DVCException instead of being silently printed, which may require users to handle these exceptions differently in their workflows

---

## Multi-Node Deployment Guide {#multi-node-deployment}

**Doc file:** `docs/multi_node_deployment_guide.md`  
**Matched prefixes:** `pychron/extraction_line/`

### Changed Files

- `pychron/extraction_line/tasks/extraction_line_pane.py`
- `pychron/extraction_line/tasks/extraction_line_pane.py.bak`
- `pychron/extraction_line/tasks/extraction_line_task.py`

### AI Review

## Code Change Summary
The extraction line pane implementation has been significantly refactored, replacing complex hardcoded UI layouts with manager-based views and removing detailed tabular adapters. The canvas pane now uses Qt-level size policies and minimum size enforcement, while several panes (ExplanationPane, InspectorPane, ReadbackPane, EditorPane) now delegate their UI rendering to manager classes rather than defining UI elements directly in the pane code.

## Documentation Updates Required

- **Section/Topic:** Canvas Configuration
  **Issue:** Documentation may reference the old hardcoded canvas sizing approach (height=700, width=900 in TraitsUI) which has been replaced with Qt-level size policies and setMinimumSize(1200, 900)
  **Suggested update:** Update canvas configuration examples to reflect that canvas sizing is now handled at the Qt level with a minimum size of 1200x900 pixels and expanding size policy, rather than through TraitsUI height/width parameters

- **Section/Topic:** Valve and Extraction Line XML/YAML Configuration  
  **Issue:** The PumpPane ID has changed from "pychron.extraction_line.pumps" to "pychron.extraction_line.pump" (singular), which may affect pane layout configurations
  **Suggested update:** Update any XML/YAML configuration examples that reference pump pane layouts to use the new singular ID "pychron.extraction_line.pump" instead of "pychron.extraction_line.pumps"

- **Section/Topic:** Multi-Node UI Components/Pane Configuration
  **Issue:** The ReadbackPane no longer uses a TabularEditor with ReadbackAdapter but delegates to a "readback_manager", and similarly ExplanationPane and InspectorPane now use "canvas_manager" instead of direct UI elements
  **Suggested update:** Update documentation to reflect that ReadbackPane, ExplanationPane, and InspectorPane now use manager-based UI delegation (readback_manager, canvas_manager) rather than direct UI element definitions, which may affect how these components are configured in multi-node setups

---

_This file was auto-generated by `scripts/doc_audit.py`. A human must review and apply any changes to the documentation._