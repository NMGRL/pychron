# Comprehensive Search Results: executor.executable and refresh_info_needed Loop

## Search Queries Performed

1. ✓ All listeners or observers on `executor.executable` trait changes
2. ✓ What happens after `refresh_executable` calls `self.executor.trait_setq(executable=...)`
3. ✓ Any trait listeners in experimentor, executor, or queues that fire when executable changes
4. ✓ Whether setting executable trait causes invalidate_stats() or refresh_info_needed=True

---

## Key Findings

### 1. NO Direct Listeners on executor.executable
**Result**: Searched entire workspace, found ZERO listeners:
- No `@on_trait_change("executor:executable")` handlers
- No `_executable_changed()` methods
- No listeners that respond to executor.executable being set

**Implication**: Setting `executor.trait_setq(executable=value)` does NOT directly trigger any invalidation or refresh

---

### 2. What refresh_executable() Does

**File**: `pychron/experiment/experimentor.py:90-100`
```python
def refresh_executable(self, qs=None) -> None:
    if qs is None:
        qs = self.experiment_queues

    if self.executor.is_alive():
        qs = (self.executor.experiment_queue,)

    executable = all([ei.is_executable() for ei in qs])
    self.executor.trait_setq(executable=executable)  # <-- QUIET SET
    self.debug("setting executable {}".format(executable))
```

**Key**: Uses `trait_setq()` (quiet trait set) which doesn't fire listeners

**Calls**: `queue.is_executable()` which checks if all runs are executable (read-only operation)

---

### 3. What ACTUALLY Sets refresh_info_needed = True

#### Source 1: Timer-Based Cascade (via invalidate_stats)
**File**: `pychron/experiment/queue/base_queue.py:197-203`
```python
def _flush_info_refresh(self) -> None:
    if self._info_refresh_timer:
        self._info_refresh_timer.stop()
        self._info_refresh_timer = None
    # ... set scroll row ...
    invoke_in_main_thread(setattr, self, "refresh_info_needed", True)
```

**Trigger Chain**:
1. Something calls `queue.invalidate_stats()`
2. Sets 250ms timer for `_flush_stats()`
3. When timer fires: calls `request_info_refresh()`
4. Sets 75ms timer for `_flush_info_refresh()`
5. When timer fires: sets `refresh_info_needed = True`

**Total Cascade Time**: 250ms + 75ms = 325ms (exceeds 250ms throttle!)

#### Source 2: Executor.set_queue_modified()
**File**: `pychron/experiment/experiment_executor.py:615-628`
```python
def set_queue_modified(self, queue=None):
    self.queue_modified = True
    self.stats.refresh_on_queue_change()
    queue = queue or self.experiment_queue
    if queue is not None:
        if hasattr(queue, "request_table_refresh"):
            queue.request_table_refresh()
        if hasattr(queue, "request_info_refresh"):
            queue.request_info_refresh()
        else:
            queue.refresh_info_needed = True  # Direct assignment
```

**Called During**: Conditional actions, repeat runs (execution time only)

#### Source 3: ExperimentFactory._mark_queue_changed()
**File**: `pychron/experiment/factory.py:255-265`
```python
def _mark_queue_changed(self, queue, auto_save=True):
    queue.changed = True
    # ...
    if hasattr(queue, "request_info_refresh"):
        queue.request_info_refresh()
    else:
        queue.refresh_info_needed = True  # Direct assignment
    if auto_save:
        self._auto_save()  # <-- May trigger persistence
```

**Called During**: Queue factory operations (UI modifications)

---

### 4. Listeners That Respond to refresh_info_needed

**File**: `pychron/experiment/experimentor.py:316-326`
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
    self.update_info()  # <-- RE-TRIGGERS CYCLE
```

**Throttle**: 250ms minimum between calls

**Critical**: If refresh_info_needed fires > 250ms after last update_info(), it will trigger again!

---

### 5. What Calls invalidate_stats() During _update()

All listeners that trigger `invalidate_stats()`:

**Location 1**: `pychron/experiment/queue/base_queue.py:601-603`
```python
@on_trait_change("automated_runs[]")
def _handle_automated_runs(self):
    self.invalidate_stats()
```

**Location 2**: `pychron/experiment/queue/base_queue.py:611-621`
```python
@on_trait_change("automated_runs:[measurement_script,post_measurement_script,post_equilibration_script,"
                                  "extraction_script,syn_extraction_script,script_options,position,duration,"
                                  "cleanup,pre_cleanup,post_cleanup,extract_value,extract_units,light_value,"
                                  "beam_diameter,ramp_duration,ramp_rate,pattern,delay_after,skip,end_after,state]")
def _handle_automated_run_updates(self, obj, name, old, new):
    self.invalidate_stats()
```

**Location 3-7**: `pychron/experiment/queue/base_queue.py:576-598`
```python
def _delay_between_analyses_changed(self, new):
    self.stats.delay_between_analyses = new
    self.invalidate_stats()

def _delay_before_analyses_changed(self, new):
    self.stats.delay_before_analyses = new
    self.invalidate_stats()

def _delay_after_blank_changed(self, new): ... invalidate_stats()
def _delay_after_air_changed(self, new): ... invalidate_stats()
def _repository_identifier_changed(self, new): ... invalidate_stats()
def _mass_spectrometer_changed(self): ... invalidate_stats()
```

---

### 6. All Other Listeners in experimentor.py

**Executed During update_info()** (from _update):

```python
@on_trait_change("executor:experiment_queue")
def _activate_editor(self, eq):
    self.activate_editor_event = id(eq)  # <-- Just sets an event ID

@on_trait_change("experiment_queues[]")
def _update_queues(self):
    qs = self.experiment_queues
    self.executor.stats.experiment_queues = qs  # <-- Doesn't trigger cascade

@on_trait_change("experiment_factory:run_factory:changed")
def _queue_dirty(self):
    self.experiment_queue.changed = True  # <-- Just marks queue dirty

@on_trait_change("executor:queue_modified")
def _refresh5(self, new):
    if new:
        self.debug("queue modified fired")
        self.update_info()  # <-- ONLY if queue_modified=True (not during normal update)
```

**Not Triggered During Normal _update()**

---

## The Loop Mechanism

```
Time: t=0ms
  update_info() called
  Lock acquired
  _update() starts
    ├─ stats.calculate() called
    ├─ stats.trait_set(nruns, _total_time, etf, _queue_sig)
    ├─ refresh_executable() called
    │  └─ trait_setq(executable=value)  [NO listeners]
    └─ _set_analysis_metadata() called
    
Time: t=0ms to t=150ms
  _update() completes
  Lock released
  
Time: t=50ms DURING _update()
  (Unknown listener fires)
  invalidate_stats() called
  Timer set for 250ms

Time: t=250ms  
  Timer fires: _flush_stats()
  Calls: request_info_refresh()
  Timer set for 75ms

Time: t=325ms
  Timer fires: _flush_info_refresh()
  Sets: refresh_info_needed = True
  
Time: t=325ms
  Listener @on_trait_change("experiment_queue:refresh_info_needed")
  Calls: _handle_refresh()
  Checks throttle:
    now (325ms) - last (0ms) = 325ms
    325ms > 250ms (THROTTLE EXCEEDED!)
    Calls: update_info()  <-- CYCLE RESTARTS
    
Time: t=325ms+
  Loop begins again...
```

---

## Root Cause Not Yet Found

**Still Unknown**:
- What listener triggers `invalidate_stats()` during _update()?
- Is it called during stats.calculate()?
- Is it called during _set_analysis_metadata()?
- Is it a run property change that happens during metadata setting?

**Hypothesis**:
- Some operation in _update() is modifying run state/properties
- This fires a listener that calls invalidate_stats()
- Timer cascade then exceeds throttle window
- Loop continues indefinitely

**Next Step**: Add logging to identify which invalidate_stats() caller is firing during _update()
