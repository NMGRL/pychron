# Complete executor.executable Trait Listener Map

## Search Results Summary

### Direct Listeners on executor.executable
**NONE FOUND**

No `@on_trait_change("executor:executable")` or `_executable_changed` handlers in:
- experimentor.py
- experiment_executor.py  
- base_queue.py
- experiment_queue.py
- Any queue implementations

### What CAN Respond to Trait Changes

#### 1. **Property Dependencies**
File: `pychron/experiment/experiment_executor.py:194`
```python
can_start = Property(depends_on="executable, _alive")
```
- This is a **computed property**, NOT a listener
- Only re-evaluates when accessed
- Does NOT trigger any cascade

---

## trait_setq(executable=value) Flow Analysis

Location: `pychron/experiment/experimentor.py:98`
```python
def refresh_executable(self, qs=None) -> None:
    executable = all([ei.is_executable() for ei in qs])
    self.executor.trait_setq(executable=executable)  # <-- HERE
    self.debug("setting executable {}".format(executable))
```

### What is_executable() Does
File: `pychron/experiment/queue/experiment_queue.py:494` 
```python
def is_executable(self):
    if self.check_runs():
        # test scripts
        return all([ai.executable for ai in self.cleaned_automated_runs])

def check_runs(self):
    hec = self.human_error_checker
    err = hec.check_runs(self.cleaned_automated_runs, test_all=True)
    # ...returns True/False
```

**Point**: `is_executable()` just reads current state, doesn't modify runs

### Trait-Setting Mechanics
- `trait_setq()` = "trait_set quietly" (doesn't batch events)
- Setting executor.executable should NOT trigger listeners on:
  - experiment_queue (no listener on executor changes)
  - Queues (no listener on executor changes)
  - Stats (no listener on executor changes)

---

## All refresh_info_needed Triggers (Revisited)

### Trigger 1: Timer-Based via invalidate_stats()
**File**: `pychron/experiment/queue/base_queue.py:197`
```python
def _flush_info_refresh(self) -> None:
    # Called via 75ms timer set by request_info_refresh()
    invoke_in_main_thread(setattr, self, "refresh_info_needed", True)
```

**Chain**: 
- Something calls `invalidate_stats()` 
- Sets 250ms timer -> `_flush_stats()` 
- Which calls `request_info_refresh()`
- Which sets 75ms timer -> `_flush_info_refresh()`
- Which sets `refresh_info_needed = True`

### Trigger 2: Direct via executor.set_queue_modified()
**File**: `pychron/experiment/experiment_executor.py:628`
```python
def set_queue_modified(self, queue=None):
    self.queue_modified = True
    # ...eventually...
    queue.refresh_info_needed = True  # direct, no timer
```
Called by: conditional actions, repeat runs (during execution only)

### Trigger 3: Direct via factory._mark_queue_changed()  
**File**: `pychron/experiment/factory.py:261`
```python
def _mark_queue_changed(self, queue, auto_save=True):
    queue.changed = True
    # ...eventually...
    queue.refresh_info_needed = True  # direct, no timer
```
Called by: queue factory operations (UI layer)

---

## Listener That Processes refresh_info_needed

**File**: `pychron/experiment/experimentor.py:316`
```python
@on_trait_change("experiment_queue:refresh_info_needed")
def _handle_refresh(self) -> None:
    if self.executor and self.executor.is_alive():
        self.debug("refresh_info_needed ignored while executor is running")
        return

    now = time.monotonic()
    if now - self._last_refresh_info_update_ts < 0.25:
        self.debug("refresh_info_needed throttled to avoid update loop")
        return

    self._last_refresh_info_update_ts = now
    self.update_info()  # <-- RE-TRIGGERS UPDATE!
```

**Throttle Window**: 0.25 seconds (250ms)

**Critical Issue**: If total timer cascade (250ms + 75ms = 325ms) exceeds throttle window,
and update_info() itself triggers invalidate_stats(), then refresh_info_needed fires AGAIN

---

## What Actually Invalidates Stats During _update()

Looking at experimentor.py `_update()` method (lines 147-170):

```python
def _update(self, queues=None) -> None:
    self.debug("update runs")
    if queues is None:
        queues = self.experiment_queues

    queues = [qi for qi in queues if qi.is_updateable()]
    if not queues:
        return

    self.debug("executor executable {}".format(self.executor.executable))
    self.debug("updating stats, ")
    self.executor.stats.experiment_queues = queues  # <-- Possible trigger?
    self.executor.stats.calculate()
    self.debug("stats calculated")

    self.refresh_executable(queues)
    self.debug("executable refreshed")

    self._set_analysis_metadata()
    self.debug("analysis metadata step finished")

    self.debug("info updated")
```

### Step 1: `self.executor.stats.experiment_queues = queues`
- This assigns a new list to stats.experiment_queues
- Don't know if this triggers any listeners on stats...

### Step 2: `self.executor.stats.calculate()`  
- File: `pychron/experiment/stats.py:234`
- Calls `trait_set(nruns=nruns, _total_time=tt, etf=etf, _queue_sig=queue_sig)`
- Do any queues listen to stats?

### Step 3: `self.refresh_executable(queues)` 
- File: `pychron/experiment/experimentor.py:90`
- Calls `self.executor.trait_setq(executable=executable)`
- NO listeners on executor.executable confirmed

### Step 4: `self._set_analysis_metadata()`
- File: `pychron/experiment/experimentor.py:165-184`
- Uses `db.session_ctx()` for database access
- Closes session on exit - no listeners detected

---

## All Listeners That Call invalidate_stats()

### Location 1: automated_runs[] changes
**File**: `pychron/experiment/queue/base_queue.py:601-603`
```python
@on_trait_change("automated_runs[]")
def _handle_automated_runs(self):
    # ...setup spectrometer manager...
    self.invalidate_stats()
```

### Location 2: Run property changes (19 properties)
**File**: `pychron/experiment/queue/base_queue.py:604-621`
```python
@on_trait_change(
    "automated_runs:[measurement_script,post_measurement_script,"
    "post_equilibration_script,extraction_script,syn_extraction_script,"
    "script_options,position,duration,cleanup,pre_cleanup,post_cleanup,"
    "extract_value,extract_units,light_value,beam_diameter,"
    "ramp_duration,ramp_rate,pattern,delay_after,skip,end_after,state]"
)
def _handle_automated_run_updates(self, obj, name, old, new):
    self.invalidate_stats()
```

### Location 3-7: Queue property changes
**File**: `pychron/experiment/queue/base_queue.py:576-598`
- `_delay_between_analyses_changed`
- `_delay_before_analyses_changed`  
- `_delay_after_blank_changed`
- `_delay_after_air_changed`
- `_repository_identifier_changed`
- `_mass_spectrometer_changed`

All call `self.invalidate_stats()`

---

## Critical Question: Why Does Cycle Continue?

Based on evidence:

1. **update_info()** called at t=0
2. **During _update()**, something invalidates stats
   - NOT from refresh_executable() trigger
   - Possibly from: 
     - Setting experiment_queues on stats?
     - Setting _total_time/etf/nruns on stats?
     - Some listener responding to stats changes?
3. **invalidate_stats()** sets 250ms timer
4. **At t=250ms**, timer fires, sets second 75ms timer
5. **At t=325ms**, second timer fires, sets `refresh_info_needed = True`
6. **At t=325ms**, _handle_refresh() checks throttle:
   - 325ms - 0ms > 250ms ✓ (EXCEEDS THROTTLE)
   - Calls `update_info()` again
7. **Loop repeats**

---

## Root Cause Hypothesis

**Most Likely**: During `_update()`, something modifies the queue state that triggers `invalidate_stats()`:
- Possible: Setting `executor.stats.experiment_queues = queues`
- Possible: Stats properties trigger listener on queues
- Possible: Database operation in `_set_analysis_metadata()` modifies something

**Need to Add Logging**: 
- In `invalidate_stats()`: Log stack trace to see which caller triggered it
- In `experiment_queues` assignment: Check if trait listener fires
- In `stats.calculate()` trait_set: Check if it cascades to queues
