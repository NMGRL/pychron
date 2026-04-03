---
id: api-reference
title: PyScript API Reference
sidebar_label: API Reference
sidebar_position: 2
---

# PyScript API Reference

This page will contain the full command reference for Pychron's PyScript DSL, generated from the source docstrings in `pychron/pyscripts/`. It is currently a placeholder — content will be populated from the documentation audit of `pychron/pyscripts/measurement_pyscript.py`, `pychron/pyscripts/extraction_line_pyscript.py`, and related files.

## Extraction Line Commands (partial)

Commands available in extraction scripts (`ExtractionLinePyScript`):

| Command | Signature | Description |
|---|---|---|
| `open` | `open(name)` | Open the named valve |
| `close` | `close(name)` | Close the named valve |
| `get_valve_state` | `get_valve_state(name) -> bool` | Return current state of the named valve |
| `cycle_valve` | `cycle_valve(name, niterations=1)` | Open and close a valve N times |
| `extract` | `extract(power, units='watts')` | Fire the laser at the given power |
| `end_extract` | `end_extract()` | Stop the laser |
| `sleep` | `sleep(duration)` | Wait for `duration` seconds |
| `info` | `info(msg)` | Log an info message |
| `gosub` | `gosub(name, **kw)` | Call another script by name |

## Measurement Commands (partial)

Commands available in measurement scripts (`MeasurementPyScript`):

| Command | Signature | Description |
|---|---|---|
| `multicollect` | `multicollect(ncounts, integration_time=1.0)` | Collect ion beam signals for `ncounts` integrations |
| `baselines` | `baselines(ncounts, mass, detector)` | Collect baseline at `mass` on `detector` |
| `peak_center` | `peak_center(detector, isotope)` | Run a peak center scan |
| `position_magnet` | `position_magnet(mass, detector)` | Position magnet at `mass` on `detector` |
| `set_deflection` | `set_deflection(detector, value)` | Set deflection voltage on `detector` |
| `add_termination` | `add_termination(condition, **kw)` | Add a run-termination conditional |
| `add_truncation` | `add_truncation(condition, **kw)` | Add a run-truncation conditional |
| `add_action` | `add_action(condition, action, **kw)` | Add a conditional action |

:::note
This page will be expanded with the full command signatures, parameter descriptions, and usage examples from the source code. See `docs/user_guide/operation/scripts/measurement_script.rst` in the legacy RST docs for the most complete existing reference.
:::
