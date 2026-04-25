# Prometheus Preferences Pane - Issues Found & Fixed

**Date:** 2026-04-05  
**Status:** ✅ Fixed and Tested  
**Tests:** 90/90 Passing

---

## Issues Discovered

### Issue 1: Preferences Pane Factory Pattern Error

**Error:**
```
TraitError: Each element of the 'preferences_panes' trait of a myTasksPlugin instance 
must be a callable value, but a value of <pychron.observability.tasks.preferences_pane.PrometheusPreferencesPane object at 0x...> 
<class 'pychron.observability.tasks.preferences_pane.PrometheusPreferencesPane'> was specified.
```

**Root Cause:**
- Envisage `preferences_panes` extension point expects a list of **callable factories** (classes), not instances
- Our plugin was returning `[PrometheusPreferencesPane()]` (an instance)
- Envisage instantiates the classes itself when building the preferences dialog

**Fix Applied:**
```python
# BEFORE: ❌
def _preferences_panes_default(self):
    return [PrometheusPreferencesPane()]

# AFTER: ✅
def _preferences_panes_default(self):
    return [PrometheusPreferencesPane]
```

**File:** `pychron/observability/tasks/plugin.py:50-57`  
**Commit:** `987b39d68`

---

### Issue 2: Preferences Model Error

**Error:**
```
ValueError: A preferences pane must have a model!
```

**Root Cause:**
- Envisage `PreferencesPane.trait_context()` requires:
  - Either a `model` instance passed in, OR
  - A `model_factory` callable that can create a PreferencesHelper
- We were using:
  - Wrong inheritance: `PrometheusPreferences(HasTraits)` instead of `PreferencesHelper`
  - Wrong pattern: `model_class` instead of `model_factory`
- `PreferencesHelper` is required because it:
  - Knows how to work with the preferences system
  - Can be instantiated with `preferences=preferences` parameter
  - Handles trait synchronization with INI files

**Fix Applied:**
```python
# BEFORE: ❌
class PrometheusPreferences(HasTraits):  # Wrong!
    pass

class PrometheusPreferencesPane(PreferencesPane):
    model_class = PrometheusPreferences  # Wrong pattern!

# AFTER: ✅
class PrometheusPreferences(BasePreferencesHelper):  # Correct inheritance
    preferences_path = "pychron.observability"
    # ... traits ...

class PrometheusPreferencesPane(PreferencesPane):
    model_factory = PrometheusPreferences  # Correct pattern
```

**File:** `pychron/observability/tasks/preferences_pane.py`  
**Commit:** `a698b9945`

---

## Technical Details

### Envisage Preferences System Architecture

```
Application Start
├── Get PreferencesPane factories from extension point
├── For each factory (class):
│   ├── Call factory(dialog=dialog)
│   ├── This creates a PreferencesPane instance
│   ├── On model initialization:
│   │   ├── If model is None and model_factory exists:
│   │   │   ├── Call model_factory(preferences=preferences)
│   │   │   └── Creates a PreferencesHelper subclass instance
│   │   └── Envisage now has a working model with preferences connected
│   └── Display UI with model traits
└── When user applies changes:
    └── PreferencesHelper syncs traits back to preferences system
```

### Key Differences: model_class vs model_factory

| Aspect | model_class | model_factory |
|--------|-------------|---------------|
| Pattern | Not standard Envisage | Official pattern |
| Type | Reference to class | Callable factory |
| Instantiation | Manual (user responsibility) | Automatic by Envisage |
| Arguments | None | `preferences=preferences` passed automatically |
| PreferencesHelper | Not required | **Required** |

### Why PrometheusPreferences Must Extend BasePreferencesHelper

```python
# BasePreferencesHelper = PreferencesHelper

class PreferencesHelper(HasTraits):
    """Base class for preference models.
    
    Provides:
    - preferences_path trait (location in preferences system)
    - Automatic trait persistence to preferences
    - Support for preferences.save()
    - Integration with Envisage preferences dialog
    """
    preferences = Instance(Preferences)  # Connected by Envisage
    preferences_path = Str()              # Path in preferences INI
    
    def _is_preference_trait(self, name):
        """Trait persistence logic"""
        ...
```

---

## Test Coverage

All existing tests updated to reflect the correct patterns:

```python
# BEFORE: ❌
def test_plugin_preferences_panes_default(self):
    panes = plugin._preferences_panes_default()
    self.assertIsInstance(panes[0], PrometheusPreferencesPane)  # Wrong!

# AFTER: ✅  
def test_plugin_preferences_panes_default(self):
    panes = plugin._preferences_panes_default()
    self.assertEqual(panes[0], PrometheusPreferencesPane)  # Correct: returns class
    pane_instance = panes[0](dialog=None)  # Verify it can be instantiated
    self.assertIsInstance(pane_instance, PrometheusPreferencesPane)
```

**Test File:** `test/observability/test_prometheus_initialization.py`  
**Test Results:** 90/90 passing ✅

---

## Files Modified

| File | Changes | Impact |
|------|---------|--------|
| `pychron/observability/tasks/plugin.py` | Fixed factory pattern in `_preferences_panes_default()` | CRITICAL |
| `pychron/observability/tasks/preferences_pane.py` | Fixed inheritance and model pattern | CRITICAL |
| `test/observability/test_prometheus_initialization.py` | Updated test assertions | MEDIUM |

---

## How to Verify the Fix

### 1. Code Verification
```bash
python -c "
from pychron.observability.tasks.preferences_pane import PrometheusPreferences, PrometheusPreferencesPane
from pychron.envisage.tasks.base_preferences_helper import BasePreferencesHelper

# Check inheritance
print('Inheritance check:', issubclass(PrometheusPreferences, BasePreferencesHelper))

# Check model_factory pattern
pane = PrometheusPreferencesPane()
print('Model factory:', pane.model_factory)
print('Is callable:', callable(pane.model_factory))

# Check instantiation works
instance = pane.model_factory()
print('Instance created:', instance)
print('Has preferences_path:', hasattr(instance, 'preferences_path'))
"
```

### 2. Test Verification
```bash
pytest test/observability/test_prometheus_initialization.py -v
pytest test/observability/ pychron/experiment/tests/test_device_io_metrics.py pychron/experiment/tests/test_executor_metrics.py --tb=short
```

### 3. Runtime Verification
```bash
# Start Pychron
pychron

# Open Edit → Preferences
# Verify "Prometheus" category appears
# Verify settings can be changed and saved
# Verify no errors in logs
```

---

## Related Documentation

- **Envisage Architecture:** https://docs.enthought.com/envisage/
- **PreferencesPane Pattern:** Envisage UI Tasks system
- **Pychron Preferences:** `pychron/envisage/tasks/preferences.py` (GeneralPreferencesPane example)

---

## Summary

**Two critical pattern issues in preferences pane integration were identified and fixed:**

1. ✅ Factory pattern: Now returns class, not instance
2. ✅ Preferences model: Now extends BasePreferencesHelper with model_factory pattern

**Result:** Preferences pane can now be opened without errors, preferences can be configured and persisted.

**Test Status:** 90/90 observability tests passing ✅

---

**Commits:**
- `987b39d68` - Fix preferences pane factory pattern
- `a698b9945` - Fix preferences model inheritance and pattern
