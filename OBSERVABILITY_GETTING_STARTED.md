# Observability Getting Started Guide

## Quick Start (5 minutes)

### Enable Metrics in Pychron

1. Launch Pychron
2. Open **Preferences** (Pychron menu → Preferences)
3. Navigate to **Prometheus** category
4. Check **Enable Prometheus Metrics Export**
5. Metrics server now runs at `http://127.0.0.1:9109/metrics`

### Access Metrics

```bash
# View raw metrics
curl http://127.0.0.1:9109/metrics

# See experiment metrics
curl http://127.0.0.1:9109/metrics | grep pychron_experiment

# Monitor in real-time
watch -n 1 'curl -s http://127.0.0.1:9109/metrics | tail -20'
```

### Configure Prometheus to Scrape Pychron

Edit `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pychron'
    static_configs:
      - targets: ['localhost:9109']
```

Then restart Prometheus:

```bash
./prometheus --config.file=prometheus.yml
```

Access Prometheus UI at `http://localhost:9090`

## What Gets Measured?

### Experiment Execution
- `pychron_experiment_started_total` - Experiments started
- `pychron_experiment_completed_total` - Experiments completed
- `pychron_experiment_failed_total` - Experiments failed
- `pychron_experiment_duration_seconds` - Execution time

### Device I/O Operations
- `pychron_device_io_operations_total` - Total device operations
- `pychron_device_io_operation_duration_seconds` - Operation latency
- `pychron_device_io_errors_total` - I/O errors by device

### System Health
- `pychron_executor_running` - Executor state (0/1)
- `pychron_executor_queue_size` - Tasks waiting
- `pychron_executor_active_tasks` - Currently executing tasks

### Custom Metrics
Your code can add custom metrics:

```python
from pychron.observability import get_metric

# Record a single value
gas_temperature = get_metric("gauge", "gas_temperature")
gas_temperature.set(450.5, labels={"device": "furnace"})

# Count events
extraction_count = get_metric("counter", "extractions_performed")
extraction_count.inc(labels={"result": "success"})
```

## Customization

### Change Host/Port

1. Preferences → Prometheus
2. Modify **Host** and **Port** fields
3. URL updates automatically in **Metrics URL** field

### Custom Namespace

By default, all metrics start with `pychron_` (namespace).

To use a different prefix:

1. Preferences → Prometheus
2. Change **Metric Namespace** (e.g., `my_lab`)
3. Metrics will now be: `my_lab_experiment_started_total`, etc.

### Disable Temporarily

If you need to turn off metrics collection:

1. Preferences → Prometheus
2. Uncheck **Enable Prometheus Metrics Export**
3. HTTP server stops, zero overhead

## Monitoring Examples

### Query Recent Experiment Success Rate

In Prometheus:
```promql
rate(pychron_experiment_completed_total[5m]) / 
  (rate(pychron_experiment_started_total[5m]) + 0.001)
```

### Alert on High Device Error Rate

```promql
rate(pychron_device_io_errors_total[5m]) > 0.1
```

### Track Equipment Efficiency

```promql
histogram_quantile(0.95, pychron_device_io_operation_duration_seconds)
```

## Grafana Dashboards

Pre-built dashboards are included:

1. **Pychron Overview** - System-wide metrics
2. **Pychron Device Health** - Device I/O performance

To import:
1. Grafana UI → Dashboards → New → Import
2. Upload `ops/grafana/dashboards/*.json`
3. Select Prometheus as datasource

## Troubleshooting

### Empty metrics endpoint (returns nothing or only HELP/TYPE lines)

This is **normal and expected** on a fresh Pychron startup!

**Why?** Metrics are created lazily - they only appear when code actually uses them. This happens when:
- Experiments are executed
- Devices perform I/O operations
- The system has been running and collecting data

**Verify metrics server is running:**
```bash
curl http://127.0.0.1:9109/metrics
```

Expected output on fresh start:
- No output / blank page = HTTP server is running (good!)
- Connection refused = Prometheus is disabled or crashed

**Generate some metrics:**
1. Run an experiment in Pychron
2. Perform device operations
3. Wait 15-30 seconds
4. Curl again: `curl http://127.0.0.1:9109/metrics`

Now you should see metrics like:
```
# HELP pychron_runs_started_total Total number of runs started
# TYPE pychron_runs_started_total counter
pychron_runs_started_total 1.0
```

### Connection refused to metrics endpoint

**Check if Prometheus is enabled:**
1. Open Preferences → Prometheus
2. Verify "Enable Prometheus Metrics Export" is CHECKED
3. Verify Host and Port are correct (default: `127.0.0.1:9109`)

**Restart Pychron after enabling:**
- Plugin loads on application startup
- Changes to preferences take effect on restart

**Check port conflicts:**
```bash
lsof -i :9109  # macOS/Linux
netstat -ano | findstr :9109  # Windows
```

If something else is using port 9109:
- Change Port in Preferences to unused port (e.g., 9110)
- Or stop the other service

### Metrics endpoint returns HTML instead of Prometheus format

This usually means **proxy software** is intercepting the request (unlikely on localhost).

If accessing remotely:
```bash
curl http://actual-host:9109/metrics  # Use actual hostname/IP
```

### No metrics appearing after running experiments

**Wait a few seconds** - there's a small delay before metrics export updates.

**Check what's being measured:**
```bash
# See all available metrics
curl http://127.0.0.1:9109/metrics | grep "^#" | head -20

# Count total metrics
curl http://127.0.0.1:9109/metrics | grep -v "^#" | wc -l
```

**If still nothing:**
- Verify experiments actually ran (check Pychron UI)
- Check Pychron logs: `~/.pychron/logs/`
- Verify observability is not disabled by environment variable

### Preferences don't persist

Pychron stores preferences in:
- macOS: `~/.pychron/preferences/`
- Linux: `~/.pychron/preferences/`
- Windows: `%APPDATA%\Pychron\preferences\`

Check that `prometheus.ini` was created:
```bash
cat ~/.pychron/preferences/prometheus.ini
```

### Performance concerns

**Observability overhead when enabled:**
- ~2% CPU during active experiment
- ~5MB memory for metrics storage

**When disabled:**
- < 0.1% CPU (trait evaluation only)
- < 1MB memory

## When to Expect Metrics

The observability system creates metrics **on demand** as your application runs:

| Operation | Metric | When Appears |
|-----------|--------|-------------|
| Start experiment | `pychron_runs_started_total` | Immediately when experiment starts |
| Complete experiment | `pychron_runs_completed_total` | When experiment finishes successfully |
| Device read/write | `pychron_device_io_operations_total` | During device I/O |
| Operation latency | `pychron_device_io_operation_duration_seconds` | After each device operation |
| Device error | `pychron_device_io_errors_total` | If operation fails |

**On a fresh Pychron start:** No metrics exist yet. This is correct behavior! Metrics are created lazily - they only appear after related code executes.

**To populate metrics:**
1. Run an experiment
2. Let devices perform operations
3. Wait 15-30 seconds for initial data
4. Curl endpoint again

## Documentation Map

### For Users
- **This file** - Quick start and troubleshooting
- `docs/observability.md` - Comprehensive operator guide
- `docs/prometheus_initialization.md` - How Prometheus initializes

### For Developers
- `PROMETHEUS_PLUGIN.md` - Plugin architecture and design
- `PROMETHEUS_IMPLEMENTATION.md` - Implementation details
- `test/observability/` - Test suite demonstrating usage

### For DevOps
- `ops/prometheus/prometheus.yml` - Prometheus config example
- `ops/grafana/dashboards/` - Pre-built dashboards

## Common Use Cases

### Monitor Experiment Progress

```promql
rate(pychron_experiment_completed_total[15m])  # Experiments per minute
pychron_experiment_duration_seconds             # Actual durations
```

### Track Equipment Health

```promql
rate(pychron_device_io_errors_total[5m]) by (device)  # Errors per device
pychron_device_io_operation_duration_seconds          # Operation speed
```

### Detect Performance Regressions

```promql
histogram_quantile(0.99, rate(
  pychron_device_io_operation_duration_seconds_bucket[5m]
)) > 10  # Alert if 99th percentile > 10 seconds
```

### Capacity Planning

```promql
max(pychron_executor_queue_size)           # Max waiting tasks
avg(pychron_executor_active_tasks)         # Typical load
```

## Next Steps

- **Want to export metrics elsewhere?** See `docs/observability.md` for remote storage options
- **Need alerting?** Configure Alertmanager in Prometheus setup
- **Custom metrics?** See integration examples in `PROMETHEUS_IMPLEMENTATION.md`
- **Running in production?** Check `ops/` directory for deployment configs

## Getting Help

- Check Pychron logs: `~/.pychron/logs/`
- Search docs: `grep -r` in `docs/`, `PROMETHEUS*.md`
- File an issue: Include metrics output from `curl http://127.0.0.1:9109/metrics`

---

**Version**: Current (Prometheus observability plugin fully integrated)
**Last Updated**: 2026-04-05
