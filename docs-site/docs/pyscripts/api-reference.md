---
id: api-reference
title: PyScript API Reference
sidebar_label: API Reference
sidebar_position: 2
---

# PyScript API Reference

This page is the complete command reference for Pychron's PyScript DSL, compiled from source code in `pychron/pyscripts/`. Commands are grouped by script type. All commands are Python function calls in plain `.py` files.

## File Location and Naming

Scripts live under the MetaRepo inside `scripts/`:

```
<MetaRepoName>/
  scripts/
    measurement/
      measurementdefaults.py        # loaded for every run unless overridden
      jan_blank.py
      jan_unknown.py
    extraction/
      jan_blank.py
      jan_unknown.py
    post_measurement/
      default.py
    post_equilibration/
      default.py
    procedures/
      my_procedure.py               # called via gosub
```

The `<MetaRepoName>/scripts/` path is the root. To reference a sub-directory script in `gosub`, pass the relative path without extension.

---

## The `gosub` Mechanism

`gosub` calls another script in the same MetaRepo. The child script shares the same `_ctx` dictionary as the parent — variables set in a gosub are visible in the caller after it returns.

```python
# Parent script
gosub('procedures/pump_line', valve='A', timeout=60)
info('pump complete, v was: {}'.format(get_context()['v']))
```

```python
# procedures/pump_line.py
open(valve)
sleep(timeout)
close(valve)
v = get_valve_state(valve)
```

Parameters passed as keyword arguments become local variables inside the child script.

---

## Common Base Commands (`PyScript`)

Available in every script type.

| Command | Signature | Description |
|---|---|---|
| `sleep` | `sleep(duration)` | Pause execution for `duration` seconds. Alias: `delay`. |
| `delay` | `delay(duration)` | Alias for `sleep`. |
| `gosub` | `gosub(name, **kw)` | Execute another script by name (relative path, no extension). Keyword args become context variables. |
| `interval` | `interval(duration)` | Set the interval for `begin_interval` / `complete_interval`. |
| `begin_interval` | `begin_interval(duration)` | Start a timed interval; use `complete_interval` to wait for it to finish. |
| `complete_interval` | `complete_interval()` | Block until the interval started by `begin_interval` elapses. |
| `safe_while` | `safe_while(func, timeout)` | Loop while `func()` returns True, up to `timeout` seconds. |
| `abort` | `abort()` | Abort the current script run immediately. |
| `cancel` | `cancel()` | Cancel the run gracefully. |
| `exit` | `exit()` | Exit the script (same as `cancel`). |
| `info` | `info(msg)` | Log an info-level message. |
| `get_context` | `get_context() -> dict` | Return the shared context dictionary. |

---

## Valve Commands (`ValvePyScript`)

Available in extraction scripts and everything that inherits from it.

| Command | Signature | Description |
|---|---|---|
| `open` | `open(name, mode='normal')` | Open the named valve. `mode='normal'` or `'force'`. Retries up to 100 times at 1-second intervals on failure. |
| `close` | `close(name, mode='normal')` | Close the named valve. Same retry behavior. |
| `is_open` | `is_open(name) -> bool` | Return `True` if the valve is open. |
| `is_closed` | `is_closed(name) -> bool` | Return `True` if the valve is closed. |
| `get_valve_state` | `get_valve_state(name) -> bool \| None` | Return current state (`True`=open, `False`=closed, `None`=unknown). |
| `lock` | `lock(name)` | Lock the valve so it cannot be changed from the UI. |
| `unlock` | `unlock(name)` | Unlock the valve. |
| `cycle_valve` | `cycle_valve(name, niterations=1, delay=0)` | Open and close the valve `niterations` times with optional `delay` between cycles. |

:::note Lock behavior
`allow_lock` is `False` by default on `ValvePyScript`. Valve lock/unlock commands are no-ops unless the subclass sets `allow_lock = True`. `ExtractionLinePyScript` does set this to `True`.
:::

---

## Extraction Line Commands (`ExtractionLinePyScript`)

All valve commands above are also available.

### Laser / Furnace Control

| Command | Signature | Description |
|---|---|---|
| `extract` | `extract(power, units='watts', x=None, y=None, z=None)` | Start extraction at `power`. `units` can be `'watts'`, `'temp'`, or `'percent'`. Optional position. |
| `end_extract` | `end_extract()` | Stop the laser / furnace. |
| `fire_laser` | `fire_laser()` | Fire the laser without power control (used for diode pre-fire). |
| `enable` | `enable()` | Enable the laser (interlock clearance). |
| `disable` | `disable()` | Disable the laser. |
| `prepare` | `prepare()` | Run laser preparation sequence (warm-up, interlock checks). |
| `ramp` | `ramp(start, stop, duration, dt=0.1, mode='watts')` | Ramp laser power from `start` to `stop` over `duration` seconds, updating every `dt` seconds. |
| `set_motor` | `set_motor(name, value, block=False)` | Set a motor position. `block=True` waits for completion. |

### Position Control

| Command | Signature | Description |
|---|---|---|
| `move_to_position` | `move_to_position(position, autocenter=False)` | Move stage to named position or hole number. |
| `set_x` | `set_x(value)` | Set stage X position (mm). |
| `set_y` | `set_y(value)` | Set stage Y position (mm). |
| `set_z` | `set_z(value)` | Set stage Z position (mm). |
| `set_xy` | `set_xy(x, y)` | Set stage X and Y simultaneously. |

### Pattern / Imaging

| Command | Signature | Description |
|---|---|---|
| `execute_pattern` | `execute_pattern(name)` | Run a named laser pattern file (from `patterns/` in the MetaRepo). |
| `autofocus` | `autofocus(new_value=None)` | Run autofocus routine. Optionally force focus to `new_value`. |
| `snapshot` | `snapshot(name=None, prefix=None)` | Save a camera snapshot. Optional file name or prefix. |
| `video_recording` | `video_recording(start=True)` | Start or stop video recording (pass `start=False` to stop). |
| `lighting` | `lighting(value)` | Set illumination level (0–100). |

### Sample Handling

| Command | Signature | Description |
|---|---|---|
| `dump_sample` | `dump_sample()` | Trigger sample dump mechanism. |
| `drop_sample` | `drop_sample()` | Drop the current sample. |
| `set_tray` | `set_tray(tray)` | Set the active tray by name. |
| `load_pipette` | `load_pipette(identifier)` | Load a pipette by identifier. |
| `extract_pipette` | `extract_pipette(identifier)` | Extract gas from a pipette. |

### Pressure / Gas Handling

| Command | Signature | Description |
|---|---|---|
| `get_pressure` | `get_pressure(controller, gauge) -> float` | Return pressure from the named gauge on the named controller. |
| `store_manometer_pressure` | `store_manometer_pressure(name)` | Store current manometer reading under `name` for later retrieval. |

### Cryo Control

| Command | Signature | Description |
|---|---|---|
| `set_cryo` | `set_cryo(value)` | Set cryo target setpoint. |
| `get_cryo_temp` | `get_cryo_temp() -> float` | Return current cryo temperature. |

### Flow Control

| Command | Signature | Description |
|---|---|---|
| `waitfor` | `waitfor(func_or_attr, comparator='>', threshold=0, timeout=60, period=0.25)` | Block until condition is met. `func_or_attr` is a callable or an attribute path string on a named device. |
| `pause` | `pause(duration=None)` | Pause execution. If `duration` is given, pauses for that many seconds. Otherwise waits for user resume. |
| `wake` | `wake()` | Resume a paused script. |
| `acquire` | `acquire(name)` | Acquire a named lock/resource (blocks until available). |
| `release` | `release(name)` | Release a previously acquired lock/resource. |
| `wait` | `wait(duration, msg='')` | Display `msg` while waiting `duration` seconds. |

### Device / Resource Access

| Command | Signature | Description |
|---|---|---|
| `get_device` | `get_device(name) -> object` | Return the device manager object for `name`. |
| `get_value` | `get_value(device, attr) -> float` | Return `attr` from the named device. |
| `set_resource` | `set_resource(device, attr, value)` | Set `attr` on the named device to `value`. |
| `get_resource_value` | `get_resource_value(device, attr) -> any` | Get a resource attribute value. |

---

## Measurement Commands (`MeasurementPyScript`)

Measurement scripts run during spectrometer data acquisition. All base `PyScript` commands are available.

### Acquisition

| Command | Signature | Description |
|---|---|---|
| `multicollect` | `multicollect(ncounts=200, integration_time=1.04)` | Collect ion beam signals for `ncounts` integrations at `integration_time` seconds each. |
| `sniff` | `sniff(ncounts=55, integration_time=1.04)` | Collect data without storing to the analysis record (used to confirm gas is present). |
| `baselines` | `baselines(ncounts=1, mass=None, detector='', use_dac=False, integration_time=1.04, settling_time=4)` | Collect baselines. `mass` sets the magnet position; `detector` selects the detector to peak at. `use_dac=True` positions by DAC voltage instead of mass. `settling_time` is the seconds to wait after moving before collecting. |
| `peak_hop` | `peak_hop(ncycles=5, hops=None, config_name='default', use_dac=False)` | Run a peak-hopping sequence. `hops` is a list of `(detector, isotope, count)` tuples or loaded via `load_hops`. |
| `whiff` | `whiff(ncounts=5, integration_time=1.04)` | Short multicollect used to check for a gas peak before proceeding. |
| `coincidence` | `coincidence()` | Run coincidence scan to correct for cross-detector contamination. |
| `reset_measurement` | `reset_measurement()` | Reset the measurement state (clears counts). |
| `reset_data` | `reset_data()` | Clear all accumulated data for this analysis. |
| `reset_series` | `reset_series()` | Reset the data series index. |
| `measurement_delay` | `measurement_delay(duration)` | Pause acquisition for `duration` seconds. |

### Equilibration / Post-Equilibration

| Command | Signature | Description |
|---|---|---|
| `equilibrate` | `equilibrate(eqtime=20, inlet=None, outlet=None, do_post_equilibration=True, close_inlet=True, delay=3)` | Open `inlet` valve and wait `eqtime` seconds. If `do_post_equilibration=True`, runs post-equilibration script when done. |
| `post_equilibration` | `post_equilibration()` | Explicitly invoke the post-equilibration script. |

### Magnet / Detector Setup

| Command | Signature | Description |
|---|---|---|
| `position_magnet` | `position_magnet(mass, detector='H1', dac=None)` | Position the magnet so `mass` falls on `detector`. Pass `dac` to position by raw DAC voltage. |
| `position_hv` | `position_hv(dac)` | Set the high-voltage DAC value directly. |
| `activate_detectors` | `activate_detectors(*detectors)` | Enable the listed detectors for acquisition. |
| `define_detectors` | `define_detectors(*detectors)` | Define which detectors are used in this measurement. |
| `define_hops` | `define_hops(hops)` | Define the hop table as a list of `(detector, isotope, count)` tuples. |
| `load_hops` | `load_hops(name)` | Load a hop table by name from the `hops/` directory in the MetaRepo. |
| `set_integration_time` | `set_integration_time(t)` | Set the spectrometer integration period in seconds. |
| `set_spectrometer_configuration` | `set_spectrometer_configuration(name)` | Load a named spectrometer configuration file. |
| `raw_spectrometer_command` | `raw_spectrometer_command(cmd)` | Send a raw command string to the spectrometer (use sparingly). |

### Fits and Data

| Command | Signature | Description |
|---|---|---|
| `set_fits` | `set_fits(fits)` | Set regression fit types for all isotopes. `fits` is a list of fit-name strings (`'linear'`, `'parabolic'`, `'cubic'`, `'average'`). |
| `set_baseline_fits` | `set_baseline_fits(fits)` | Set regression fit types for baselines. |
| `set_isotope_group` | `set_isotope_group(name)` | Set the active isotope group by name. |
| `set_ncounts` | `set_ncounts(n)` | Dynamically change the number of counts for the current acquisition. |
| `set_time_zero` | `set_time_zero()` | Mark the current time as t=0 for signal extrapolation. |
| `get_intensity` | `get_intensity(detector) -> float` | Return the current signal intensity on `detector`. |

### Conditionals

All conditional commands evaluate an expression against a running measurement value. `attr` is a Pychron attribute string (e.g. `'age'`, `'Ar40.signal'`). `teststr` is a Python expression string.

| Command | Signature | Description |
|---|---|---|
| `add_termination` | `add_termination(attr, teststr, start_count=0, frequency=10, window=0, mapper='', ntrips=1)` | Terminate the run if the condition evaluates True. `start_count`: skip first N integrations. `frequency`: check every N integrations. `window`: rolling window size for average. `ntrips`: number of consecutive True evaluations before triggering. |
| `add_cancelation` | `add_cancelation(attr, teststr, start_count=0, frequency=10, window=0, mapper='', ntrips=1)` | Cancel the run (not just truncate). Same parameters as `add_termination`. |
| `add_truncation` | `add_truncation(attr, teststr, start_count=0, frequency=10, ntrips=1, abbreviated_count_ratio=1.0)` | Truncate the run (jump to baselines). `abbreviated_count_ratio`: fraction of remaining counts to collect after truncation (1.0 = skip to end immediately). |
| `add_action` | `add_action(attr, teststr, start_count=0, frequency=10, ntrips=1, action=None, resume=False)` | Execute `action` (a callable or script name) when condition is True. `resume=True` continues after the action. |
| `clear_terminations` | `clear_terminations()` | Remove all termination conditionals. |
| `clear_cancelations` | `clear_cancelations()` | Remove all cancelation conditionals. |
| `clear_truncations` | `clear_truncations()` | Remove all truncation conditionals. |
| `clear_actions` | `clear_actions()` | Remove all action conditionals. |

### Context Variables

These variables are injected into the measurement script's execution context:

| Variable | Type | Description |
|---|---|---|
| `analysis_type` | `str` | `'blank'`, `'unknown'`, `'air'`, `'cocktail'`, etc. |
| `run_identifier` | `str` | The run identifier string. |
| `position` | `str \| int` | Tray position for this run. |
| `duration` | `float` | Extraction duration in seconds. |
| `cleanup` | `float` | Post-extraction cleanup time in seconds. |
| `extract_value` | `float` | Laser/furnace power setpoint. |
| `extract_units` | `str` | Units for `extract_value`. |
| `pattern` | `str` | Laser pattern name (if any). |
| `beam_diameter` | `float` | Laser beam diameter (mm). |
| `truncated` | `bool` | `True` if this run has been truncated. |
| `measuring` | `bool` | `True` while multicollect is active. |

---

## The `@verbose_skip` Decorator

Every command decorated with `@verbose_skip` is a no-op when:

- The script is running in **syntax-check mode** (`test_syntax()`)
- The run has been **cancelled** or **aborted**
- The run has been **truncated** (for extraction commands)

This is why `syntax_only=True` passes even with hardware commands — they are all skipped.

---

## Script Examples

### Minimal extraction script

```python
# extraction/blank.py
sleep(2)
open('C')
sleep(10)
close('C')
```

### Multicollect with conditional termination

```python
# measurement/unknown.py
peak_center(detector='H1', isotope='Ar40')
position_magnet(39.948, 'H1')

add_termination('Ar40.signal', 'x < 1e-14', start_count=20, frequency=5)

equilibrate(eqtime=20, inlet='C', outlet='S', close_inlet=True)
multicollect(ncounts=200, integration_time=1.04)
baselines(ncounts=5, mass=39.5, detector='H1', settling_time=4)
```

### Power ramp with gosub

```python
# extraction/ramp_extract.py
gosub('procedures/pump_line')
ramp(start=0, stop=5, duration=30, mode='watts')
extract(5, units='watts')
sleep(duration)
end_extract()
gosub('procedures/cleanup')
```
