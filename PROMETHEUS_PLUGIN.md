# Prometheus Plugin Architecture

## Summary

The Prometheus observability system has been converted to an **Envisage plugin**, making it:

1. **Discoverable**: Automatically loaded by Pychron's plugin system
2. **Configurable**: Settings managed through Pychron's preferences system
3. **Optional**: Can be disabled at the application level
4. **Clean**: No direct dependency from core application code

## Plugin Details

### Location
```
pychron/observability/tasks/plugin.py
```

### Plugin Class
```python
class PrometheusPlugin(BasePlugin):
    id = "pychron.observability.prometheus"
    name = "Prometheus Observability"
    
    # Configuration traits
    enabled = Bool(False)
    host = Str("127.0.0.1")
    port = Int(9109)
    namespace = Str("pychron")
```

### Registration

The plugin is automatically registered in `pychron_run.py`:

```python
PACKAGE_DICT = {
    ...
    PrometheusPlugin="pychron.observability.tasks.plugin",
    ...
}
```

## How It Works

1. **Application Startup**: Envisage plugin system discovers `PrometheusPlugin`
2. **Plugin Start**: `PrometheusPlugin.start()` is called
3. **Configuration**: Plugin reads traits from preferences or environment
4. **Initialization**: Plugin calls `configure()` to initialize observability
5. **Exporter Start**: If enabled, plugin starts HTTP metrics server
6. **Running**: Metrics are collected throughout application lifecycle

## Configuration

Users can configure the plugin via:

1. **Preferences INI file**: `~/.pychron/preferences/prometheus.ini`
   ```ini
   [pychron.observability.prometheus]
   enabled = True
   host = 0.0.0.0
   port = 9109
   ```

2. **GUI**: Will appear in Pychron's preferences dialog (if preferences pane added)

3. **Environment**: Via Traits environment variables

4. **Programmatic**: Direct access to plugin instance

## Key Features

✅ **Non-Invasive**: No changes to application bootstrap code
✅ **Plugin Architecture**: Follows Pychron patterns
✅ **Configurable**: Standard Traits-based configuration
✅ **Optional**: Can be disabled completely
✅ **Safe**: Graceful error handling
✅ **Idempotent**: Safe to call multiple times

## Testing

All 53 existing tests pass:
- No breaking changes
- Plugin system compatible
- Metrics functionality unchanged

## Benefits Over Direct Integration

| Aspect | Plugin Approach | Direct Integration |
|--------|-----------------|-------------------|
| Discoverable | ✅ Automatic | ❌ Hardcoded |
| Configurable | ✅ Traits UI | ⚠️ Manual code |
| Optional | ✅ Disable easily | ⚠️ Always loaded |
| Maintainable | ✅ Isolated | ⚠️ Mixed concerns |
| Testing | ✅ Independent | ⚠️ Application-level |

## Enabling/Disabling

**To disable**: Simply set `enabled = False` in preferences
**To enable**: Set `enabled = True` and restart Pychron
**Plugin loads**: Regardless of enabled state (overhead is minimal if disabled)

## Next Steps

Optional enhancements:
1. Add preferences pane UI for graphical configuration
2. Add plugin-level status reporting to Pychron UI
3. Add metrics health dashboard to Pychron
4. Add preference validation (port range, host format, etc.)
