# Pychron Observability & Prometheus Metrics

This document describes the Prometheus metrics export system integrated into Pychron.

## Overview

Pychron exports operational metrics to Prometheus, enabling:

- **Run and Queue Lifecycle Tracking**: Monitor experiment execution progress
- **Device I/O Instrumentation**: Track device operation success/failure rates and latency
- **Phase Duration Analysis**: Measure extraction, measurement, and other phase timing
- **Service & Watchdog Health**: Monitor DVC, database, and dashboard service health

## Architecture

The observability system is implemented as an **Envisage plugin** (`PrometheusPlugin`):

- **Plugin ID**: `pychron.observability.prometheus`
- **Location**: `pychron/observability/tasks/plugin.py`
- **Automatically Discovered**: Registered in plugin system via `pychron_run.py`

The plugin:
1. Reads configuration on startup
2. Initializes observability system
3. Starts HTTP metrics exporter if enabled
4. Provides no-op behavior when disabled (zero overhead)

## Configuration

### Enable via Preferences

Create or edit `~/.pychron/preferences/prometheus.ini`:

```ini
[pychron.observability.prometheus]
enabled = True
host = 127.0.0.1
port = 9109
namespace = pychron
```

### Enable via Environment Variables

```bash
export PYCHRON_PROMETHEUS_ENABLED=true
export PYCHRON_PROMETHEUS_HOST=127.0.0.1
export PYCHRON_PROMETHEUS_PORT=9109
export PYCHRON_PROMETHEUS_NAMESPACE=pychron
```

### Programmatic Configuration

```python
from pychron.observability import configure, MetricsConfig

config = MetricsConfig(
    enabled=True,
    host="0.0.0.0",
    port=9109,
    namespace="pychron"
)
configure(config)
```

## Metrics Reference

### Queue Lifecycle

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `pychron_queue_starts_total` | Counter | - | Total number of queues started |
| `pychron_queue_completions_total` | Counter | - | Total number of queues completed |
| `pychron_active_queues` | Gauge | - | Number of active/running queues |

### Run Lifecycle

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `pychron_runs_started_total` | Counter | - | Total runs started |
| `pychron_runs_completed_total` | Counter | - | Total runs completed successfully |
| `pychron_runs_failed_total` | Counter | - | Total runs that failed |
| `pychron_runs_canceled_total` | Counter | - | Total runs canceled |
| `pychron_active_runs` | Gauge | - | Number of active/running runs |
| `pychron_run_duration_seconds` | Histogram | - | Duration of completed runs (seconds) |

### Phase Lifecycle

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `pychron_phase_duration_seconds` | Histogram | `phase` | Duration of run phases (extraction, measurement, etc.) |
| `pychron_current_phase_duration_seconds` | Gauge | `phase` | Current/in-progress phase duration |

### Device I/O

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `pychron_device_io_operations_total` | Counter | `device`, `operation`, `result` | Total device I/O operations (result=success\|failure) |
| `pychron_device_io_duration_seconds` | Histogram | `device`, `operation` | Device I/O operation latency |
| `pychron_device_last_success_timestamp_seconds` | Gauge | `device` | Unix timestamp of last successful device operation |

### Service & Watchdog Health

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `pychron_phase_healthcheck_failures_total` | Counter | `phase`, `kind` | Health check failures (kind=device\|service) |
| `pychron_service_health_state` | Gauge | `service` | Service health state (0=unknown, 1=healthy, 2=degraded, 3=unavailable) |
| `pychron_service_last_success_timestamp_seconds` | Gauge | `service` | Unix timestamp of last successful service operation |

## Label Cardinality Policy

To prevent high-cardinality metrics issues:

- All label values are **normalized**: lowercase, spaces→underscores, truncated to 50 chars
- **Allowed labels**: `device`, `operation`, `result`, `phase`, `kind`, `service`
- **Forbidden labels**: sample name, labnumber, queue name (if dynamic), username, exception text, script text, free-form comments

## Running Prometheus

### Docker (Recommended)

```bash
docker run -p 9090:9090 -v $(pwd)/ops/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

Then access Prometheus at: `http://localhost:9090`

### Local Install

```bash
# Download from https://prometheus.io/download/
prometheus --config.file=ops/prometheus/prometheus.yml
```

## Running Grafana

### Docker

```bash
docker run -p 3000:3000 grafana/grafana
```

Access Grafana at: `http://localhost:3000` (admin/admin)

### Import Dashboards

1. Add Prometheus as a data source:
   - URL: `http://localhost:9090`
   - Save

2. Import dashboards from `ops/grafana/dashboards/`:
   - **pychron-overview.json**: High-level experiment status
   - **pychron-device-health.json**: Device I/O and service health

## Docker Compose

A sample docker-compose file is provided in `ops/` (if available):

```bash
cd ops
docker-compose -f docker-compose.observability.yml up
```

This starts Prometheus and Grafana together.

## Instrumentation Details

### Device I/O Metrics

Added to `pychron/experiment/telemetry/device_io.py`:
- Decorator and context manager auto-record operation success/failure
- Duration measured in seconds
- Last success timestamp tracks device availability

### Executor Lifecycle

Helper functions in `pychron/experiment/instrumentation.py` record:
- Queue start/completion events
- Run terminal state (completed/failed/canceled)
- Phase duration

### Watchdog Integration

Extended `pychron/experiment/executor_watchdog_integration.py`:
- Records device health check failures
- Records service health check failures
- Non-intrusive: failures don't block execution

## Best Practices

### Querying Metrics

**Success rate over 5 minutes:**
```promql
rate(pychron_device_io_operations_total{result="success"}[5m]) 
/ 
rate(pychron_device_io_operations_total[5m])
```

**Average device I/O latency:**
```promql
avg(rate(pychron_device_io_duration_seconds_sum[5m])) 
/ 
avg(rate(pychron_device_io_duration_seconds_count[5m]))
```

**Runs in progress:**
```promql
pychron_active_runs
```

### Alerting

Example alert rule:

```yaml
- alert: HighDeviceIOFailureRate
  expr: rate(pychron_device_io_operations_total{result="failure"}[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High device I/O failure rate ({{ $value | humanizePercentage }})"
```

## Disabling Metrics

Metrics export is designed to be safe to disable:

- Set `PYCHRON_METRICS_ENABLED=false` or configure metrics `enabled=False`
- All metric operations become no-ops
- Zero performance impact when disabled

## Performance Considerations

- Metrics recording uses best-effort approach: failures are silently ignored
- Metric failures never affect instrument control flow
- Minimal overhead: timing uses `time.monotonic()`, label normalization is fast
- Batching handled by Prometheus client library

## Troubleshooting

### Metrics endpoint not responding

1. Check Pychron logs for startup messages:
   ```
   Prometheus metrics exporter started on 127.0.0.1:9109/metrics
   ```

2. Verify metrics are enabled in config

3. Check firewall rules (port 9109)

### Missing metrics in Prometheus

1. Verify Prometheus can reach Pychron: `http://localhost:9109/metrics`
2. Check Prometheus targets: `http://localhost:9090/targets`
3. Verify scrape is happening: look for `pychron_device_io_operations_total` in `/metrics`

### High cardinality warnings

If you see warnings about label cardinality:
1. Check for dynamic/unbounded label values
2. Report as a bug if using only approved label names
3. Labels are automatically normalized but can still be problematic with many device/operation combos

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
