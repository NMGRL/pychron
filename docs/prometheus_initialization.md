# Prometheus Integration in Pychron Initialization

## Overview

Prometheus metrics collection has been integrated into Pychron's initialization and configuration system. Users can enable and configure Prometheus metrics export through:

1. **Initialization UI** - Enable/disable during Pychron setup
2. **Preferences Pane** - Configure settings in the Pychron preferences dialog
3. **Configuration Files** - Manual configuration via INI files
4. **Environment Variables** - Programmatic configuration

---

## Initialization UI Integration

### Plugin Registration

The Prometheus plugin is registered in the Pychron initialization system and appears in the "General" plugin group:

- **Plugin Name:** Prometheus
- **Category:** General
- **Description:** Prometheus metrics export for monitoring and observability

### Plugin Tree

```
Plugins (Root)
├── General
│   ├── Experiment
│   ├── MassSpec
│   ├── ...
│   ├── Usage
│   └── Prometheus ← NEW
├── Data
└── Hardware
```

### Default Behavior

- **Disabled by default** - Prometheus metrics are not collected unless explicitly enabled
- **Zero overhead when disabled** - No performance impact on experiment execution
- **Optional startup tests** - Can be configured to run metrics validation tests

---

## Configuration Methods

### 1. Initialization Editor UI (Recommended)

When launching Pychron with `--init`, users can enable Prometheus from the GUI:

```
Pychron Initialization Editor
├── Plugins (Tree view)
│   ├── General
│   │   ├── ✓ Experiment
│   │   ├── ✓ MassSpec
│   │   ...
│   │   └── ☐ Prometheus  ← Click to enable
```

**Steps:**
1. Launch: `pychron --init`
2. Navigate to: Plugins → General
3. Check "Prometheus" checkbox
4. Save configuration
5. (Optional) Click "Configure" to set custom host/port

### 2. Preferences Pane

After Pychron starts, configure Prometheus via Preferences dialog:

**Path:** Edit → Preferences → Prometheus

**Options:**
- **Enabled**: Toggle metrics collection
- **Host**: Hostname/IP for metrics HTTP server (default: 127.0.0.1)
- **Port**: Port number (default: 9109, range: 1-65535)
- **Namespace**: Metric prefix (default: pychron)

**Changes take effect on next Pychron restart.**

### 3. Preferences Configuration File

Edit: `~/.pychron/preferences/prometheus.ini`

```ini
[pychron.observability]
# Enable Prometheus metrics collection and HTTP export
enabled = true

# Host address to bind metrics HTTP server to
host = 0.0.0.0

# Port to bind metrics HTTP server to
port = 9109

# Prometheus metric namespace prefix
namespace = pychron
```

### 4. Environment Variables (Advanced)

Set via shell before launching Pychron:

```bash
export PYCHRON_PROMETHEUS_ENABLED=true
export PYCHRON_PROMETHEUS_HOST=0.0.0.0
export PYCHRON_PROMETHEUS_PORT=9109
export PYCHRON_PROMETHEUS_NAMESPACE=pychron

pychron
```

---

## Plugin Lifecycle

### Plugin Initialization

```
Pychron Application Start
├── Load PACKAGE_DICT plugins
│   └── PrometheusPlugin discovered
├── Create PrometheusPlugin instance
├── Read preferences from INI file
├── Apply traits-based configuration
└── Call plugin.start()
```

### Plugin Start Sequence

```python
def start(self):
    # 1. Read configuration (traits)
    # 2. Call _configure_observability()
    #    └── Create MetricsConfig
    #    └── Call observability.configure()
    # 3. If enabled:
    #    └── Call _start_exporter()
    #        └── Start HTTP server on host:port
```

### Validation

Plugin includes `check()` method for startup validation:

- ✓ Port range validation (1-65535)
- ✓ Configuration consistency checks
- ✓ No-op when disabled (always valid)

---

## Integration Points

### 1. Initialization Parser

File: `pychron/envisage/initialization/initialization_parser.py`

- Reads plugin configurations from YAML
- Persists user preferences
- Loaded on each startup

### 2. Initialization Edit View

File: `pychron/envisage/initialization/initialization_edit_view.py`

- Provides GUI for plugin management
- Enable/disable plugins
- Set default configurations

### 3. Plugin Registry

File: `pychron/envisage/pychron_run.py` - PACKAGE_DICT

```python
PACKAGE_DICT = dict(
    ...
    PrometheusPlugin="pychron.observability.tasks.plugin",
    ...
)
```

### 4. Preferences System

File: `pychron/observability/tasks/preferences_pane.py`

- `PrometheusPreferences` - Traits model for configuration
- `PrometheusPreferencesPane` - Envisage preferences pane

---

## Configuration Hierarchy

Pychron applies settings in this priority order:

1. **Environment variables** (highest priority)
2. **Preferences INI file** (~/.pychron/preferences/prometheus.ini)
3. **Plugin defaults** (lowest priority)

Example:
```
defaults: host=127.0.0.1, port=9109
+ INI file: host=0.0.0.0
+ Env var: not set
= Result: host=0.0.0.0, port=9109
```

---

## Metrics Endpoints

### Default

When enabled with default configuration:

```
Metrics URL: http://127.0.0.1:9109/metrics
Health URL: http://127.0.0.1:9109/health (optional)
```

### Custom Host/Port

If configured with custom host/port:

```
host = 192.168.1.100
port = 8888
→ http://192.168.1.100:8888/metrics
```

### Accessing from Other Machines

To access Prometheus metrics from other machines, set `host = 0.0.0.0`:

```ini
[pychron.observability]
enabled = true
host = 0.0.0.0
port = 9109
```

⚠️ **Security:** This exposes metrics on all network interfaces. Use with care in untrusted networks.

---

## Startup Behavior

### When Enabled

1. ✓ Plugin starts
2. ✓ Configuration applied
3. ✓ HTTP server starts on host:port
4. ✓ Metrics exporter ready to receive scrapes
5. ✓ Log message: "Prometheus metrics exporter started on <host>:<port>/metrics"

### When Disabled

1. ✓ Plugin starts (no-op)
2. ✓ Configuration applied (no-op)
3. → HTTP server not started
4. → No metrics collection
5. → No performance impact

### On Error

If startup fails:

1. ✗ HTTP server fails to bind
2. ✗ Log warning: "Failed to start Prometheus metrics exporter"
3. ✓ Application continues normally
4. → Metrics collection disabled
5. → No experiment impact

---

## Best Practices

### Development

```ini
[pychron.observability]
enabled = true
host = 127.0.0.1
port = 9109
namespace = pychron_dev
```

### Production

```ini
[pychron.observability]
enabled = true
host = 0.0.0.0
port = 9109
namespace = pychron_prod
```

Then configure Prometheus to scrape:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'pychron'
    static_configs:
      - targets: ['<pychron-host>:9109']
```

### Testing

```ini
[pychron.observability]
enabled = false
```

---

## Troubleshooting

### Metrics not appearing

1. Check plugin is enabled:
   - Preferences → Prometheus → "Enabled" is checked
   - Or check INI file: `enabled = true`

2. Check server is running:
   ```bash
   curl http://127.0.0.1:9109/metrics
   ```

3. Check logs for errors:
   - Look for "Failed to start Prometheus metrics exporter"
   - Check port isn't already in use: `lsof -i :9109`

### Port already in use

```
Error: [Errno 48] Address already in use
```

**Solution:** 
- Use different port: `port = 9110`
- Or kill process using port: `kill -9 $(lsof -t -i :9109)`

### Connection refused

```
Error: [Errno 111] Connection refused
```

**Causes:**
- Prometheus plugin not enabled
- Server crashed silently (check logs)
- Firewall blocking connection

**Solution:**
- Enable plugin: `enabled = true`
- Check firewall: `sudo ufw status`
- Verify host binding: Check preferences

---

## Files Modified/Created

### Created

- `pychron/observability/tasks/preferences_pane.py` - Preferences UI
- `ops/preferences/prometheus.ini` - Configuration template

### Modified

- `pychron/envisage/initialization/utilities.py` - Added Prometheus to plugin lists
- `pychron/observability/tasks/plugin.py` - Added preferences pane integration

---

## Testing

To verify integration:

```bash
# 1. Start Pychron with initialization editor
pychron --init

# 2. Enable Prometheus in GUI
# Plugins → General → Check Prometheus

# 3. Launch application
pychron

# 4. Verify metrics endpoint
curl http://127.0.0.1:9109/metrics

# 5. Check log message
# Should see: "Prometheus metrics exporter started on 127.0.0.1:9109/metrics"
```

---

## Summary

Prometheus integration is now available in Pychron's initialization and configuration system:

✅ **Initialization UI** - Enable/disable during setup  
✅ **Preferences Pane** - Configure in GUI  
✅ **Config Files** - Manual configuration  
✅ **Default Settings** - Disabled by default (zero overhead)  
✅ **Error Handling** - Graceful failures don't affect experiments  

**Ready for production use!**
