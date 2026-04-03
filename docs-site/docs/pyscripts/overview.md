---
id: overview
title: PyScripts Overview
sidebar_label: Overview
sidebar_position: 1
---

# PyScripts Overview

PyScripts are Pychron's built-in domain-specific language for scripting automated laboratory sequences. Rather than writing general Python, operators write scripts in a constrained vocabulary of commands that map directly to physical laboratory actions — opening valves, firing lasers, collecting ion beam signals, running peak centers. Scripts are stored as `.py` files in the MetaRepo and are referenced by name in the experiment queue, ensuring that the exact script used for each analysis is version-controlled alongside the data it produced.

## Two script types

| Type | Base class | File location in MetaRepo | Purpose |
|---|---|---|---|
| Extraction | `ExtractionLinePyScript` | `scripts/extraction/` | Controls the extraction line: valve sequencing, laser firing, furnace ramping, gas cleanup |
| Measurement | `MeasurementPyScript` | `scripts/measurement/` | Controls the spectrometer: multicollect sequences, peak center, baseline collection, equilibration waits |

Scripts can call each other using `gosub`, allowing common sequences (e.g. a standard gas cleanup procedure) to be defined once and reused across many experiment types.

## Command categories

**Extraction scripts** have access to:
- Valve commands: `open`, `close`, `get_valve_state`, `cycle_valve`
- Laser commands: `extract`, `end_extract`, `set_laser_power`, `set_laser_temperature`
- Timing: `sleep`, `wait_for_condition`
- Logging: `info`, `warning`
- Control flow: `gosub`, `if/else` (standard Python)

**Measurement scripts** have access to:
- Acquisition commands: `multicollect`, `baselines`, `peak_center`, `coincidence`
- Spectrometer control: `set_deflection`, `set_integration_time`, `set_source_parameters`
- Position: `position_magnet`
- Context variables: `analysis_type`, `mass_spectrometer`, `extract_device`, `position`
- Conditionals: `add_termination`, `add_truncation`, `add_action`, `add_queue_condition`

## Where scripts live

Scripts are stored in the MetaRepo under a `scripts/` directory:

```
<MetaRepoName>/
└── scripts/
    ├── extraction/
    │   ├── air.py
    │   ├── unknown.py
    │   └── blank_unknown.py
    ├── measurement/
    │   ├── argus.py
    │   ├── ngx_multicollect.py
    │   └── peak_center.py
    └── post_measurement/
        └── default.py
```

Each script in the experiment queue is referenced by its filename without the `.py` extension (e.g. `argus` or `unknown`). Pychron resolves this to the corresponding file in the MetaRepo at run time.

## See also

- [PyScript API Reference](./api-reference) — full command reference
- Conditionals guide — `add_termination`, `add_truncation`, `add_action` (page coming soon)
