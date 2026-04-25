---
id: configuration
title: Dashboard Configuration
sidebar_label: Configuration
sidebar_position: 1
---

# Dashboard Configuration

The Pychron dashboard system provides real-time monitoring of laboratory instruments — vacuum levels, temperatures, laser power, and any other hardware value that a device driver exposes. It consists of:

- **`DashboardServer`** — runs on the acquisition computer; polls devices and publishes values over ZMQ
- **`DashboardClient`** — runs on any networked machine; subscribes to the ZMQ stream and displays live values

Both are Envisage plugins. The server is enabled in `initialization.xml` on the acquisition computer; the client is enabled on reduction workstations or secondary displays.

## Architecture

```
DashboardServer (acquisition PC)
│
├── polls device objects every N seconds (per-metric period)
├── evaluates thresholds / conditionals
├── sends email alerts on WARNING / CRITICAL
├── calls LabspyClient.add_measurement() for database logging
│
└── ZMQ PUB port 8100 ──────────────► DashboardClient (any networked machine)
     topic: "dashboard"                    │
     JSON payload                          └── displays live values in UI
     
ZMQ REP port 8101 ◄──────────────────── DashboardClient config request
```

## Enabling the Plugins

### `initialization.xml` on the acquisition computer

```xml
<plugin enabled="true">DashboardServer</plugin>
```

### `initialization.xml` on a client machine

```xml
<plugin enabled="true">DashboardClient</plugin>
```

:::warning Enable the notifier preference or nothing will be published
The `DashboardServer` plugin will start and poll devices, but **will not bind the ZMQ socket** unless `notifier_enabled` is explicitly set to `True` in preferences. Open **Preferences → Dashboard → Server** and check **Enable Notifier**. The preference path is `pychron.dashboard.server.notifier_enabled`. Without it, the server runs silently and no client will receive data.
:::

## Server Config File

The server reads a YAML (preferred) or XML (legacy) config file from:

```
~/.pychron.<appname>/setupfiles/dashboard.yaml
```

If both `dashboard.yaml` and `dashboard.xml` exist, YAML is used and XML is ignored.

### Full YAML Schema

```yaml
# dashboard.yaml

# Optional: ZMQ port override. Default: 8100.
# Clients must set the same port in Preferences → Dashboard Client → Port.
port: 8100

devices:
  - name: MKSController          # Required. Must match the Python device class name
                                 # as registered with the device manager.
    tag: mks_pressure            # Optional. Unique string identifier used in ZMQ messages
                                 # and LabspyClient records. Defaults to name if omitted.
                                 # Must be unique across all devices in the file.

    enabled: true                # Optional. Default: true. Set false to disable without
                                 # removing from the file.

    values:
      - name: pressure           # Required. Python attribute name on the device object.
        tag: ing_pressure        # Optional. Overrides device-level tag for this value.
        units: Torr              # Optional. String label shown in the UI and stored by Labspy.
        period: 5                # Optional. Seconds between polls. Default: 5.
                                 # Special value: "on_change" — publish only when the value
                                 # changes. Caution: uses Traits observe() which fires on every
                                 # assignment, not just on numeric change.
        enabled: true            # Optional. Default: true.
        record: true             # Optional. Default: true. If false, value is published to ZMQ
                                 # but not recorded in the Labspy database.
        bindname: ""             # Optional. Internal binding name used by Labspy client.

        timeout: 60              # Optional. Seconds with no update before a timeout event is
                                 # fired. Default: 0 (disabled). A timeout publishes a
                                 # {"kind": "timeout"} ZMQ message and triggers email alert.

        threshold:               # Optional. Conditional alert block.
          warning: 1e-5          # Publish a warning event when value exceeds this.
          critical: 1e-4         # Publish a critical event and run action_script.
          comparator: ">"        # Optional. Default: ">". Supports: ">", "<", ">=", "<=", "==".
          action_script: ""      # Optional. PyScript name to execute on critical threshold.

  - name: WatlowEZZone
    values:
      - name: process_value
        tag: furnace_temp
        units: C
        period: 10
        threshold:
          warning: 900
          critical: 1000
          comparator: ">"
```

### Legacy XML Schema

XML support exists for backward compatibility. Prefer YAML for new configurations.

```xml
<dashboard>
  <port>8100</port>
  <device name="MKSController">
    <value name="pressure" tag="ing_pressure" units="Torr" period="5">
      <threshold warning="1e-5" critical="1e-4" comparator="&gt;"/>
    </value>
  </device>
</dashboard>
```

## Client Configuration

Configure the client in **Preferences → Dashboard → Client**:

| Preference | Default | Description |
|---|---|---|
| `host` | `127.0.0.1` | IP address of the machine running `DashboardServer` |
| `port` | `8100` | Must match `port` in `dashboard.yaml` |
| `use_dashboard_client` | `False` | Must be `True` for the experiment manager to query dashboard values |

The client connects via ZMQ SUB to `tcp://<host>:<port>` and requests the server config via ZMQ REQ to `tcp://<host>:<port+1>`.

## ZMQ Message Format

All messages use the topic `"dashboard"`. The full wire format is:

```
"dashboard {<json_payload>}"
```

### Event Types

| `kind` | When published | Payload fields |
|---|---|---|
| `heartbeat` | Every ~5 seconds | `ts` |
| `value_update` | Each poll cycle for enabled values | `ts`, `device`, `tag`, `value`, `units` |
| `timeout` | When a value hasn't updated in `timeout` seconds | `ts`, `device`, `tag` |
| `warning` | When value crosses `threshold.warning` | `ts`, `device`, `tag`, `value`, `threshold` |
| `critical` | When value crosses `threshold.critical` | `ts`, `device`, `tag`, `value`, `threshold` |
| `error` | Device read exception | `ts`, `device`, `message` |

Example `value_update` message:

```json
{
  "kind": "value_update",
  "ts": 1712000000.123,
  "device": "MKSController",
  "tag": "ing_pressure",
  "value": 3.2e-7,
  "units": "Torr"
}
```

### Legacy Message Format

Older `DashboardClient` versions also accepted plain-text messages in the form `"<tag> <value>"` (e.g. `"ing_pressure 3.2e-7"`). This format is still supported for backward compatibility but is not emitted by the current server.

## Alert Actions

| Threshold level | Server behavior |
|---|---|
| `warning` | Publishes `{"kind": "warning", ...}` ZMQ event; sends email if `LabspyClient` has email configured |
| `critical` | Publishes `{"kind": "critical", ...}` ZMQ event; sends email; executes `action_script` (if set); calls `LabspyClient.update_status(error=message)` |
| `timeout` | Publishes `{"kind": "timeout", ...}` ZMQ event; sends email |

Email alerting is configured through **Preferences → Notifier** (the `Notifier` plugin, separate from the dashboard). The dashboard server calls `LabspyClient.notify()` when a threshold fires — Labspy handles email delivery.

## LabspyClient Integration

When `LabspyClient` is configured and connected, the `DashboardServer` calls it directly (not via ZMQ) for every polled value:

```python
labspy_client.add_measurement(device_name, tag, value, units)
```

This writes measurements to a Labspy-managed SQLite or PostgreSQL database for historical trending. The Labspy `NotificationTrigger` system is independent of the dashboard conditional system — it can trigger alerts based on database queries rather than live stream thresholds.

## Startup Timing

The `DashboardServer` activates **5 seconds after the application starts** (`do_after(5000, activate)`). This delay prevents the dashboard from polling devices before the device manager has finished initializing all hardware connections. If your devices take longer to initialize, there is no configuration knob for this delay — it requires a source code change in `pychron/dashboard/tasks/server/plugin.py`.

## Undocumented Behaviors

1. **`notifier_enabled` must be `True`** — If the preference is `False` (the default value for a new install), the ZMQ PUB socket is never bound. The server polls devices silently but no client receives data. There is no warning in the log or UI. Always confirm this preference is enabled after first setup.

2. **`period: "on_change"`** — When a value's period is set to `"on_change"`, the server uses Traits `observe()` to watch the attribute instead of polling on a timer. This fires on every Traits assignment, which may be more frequent than expected — some device drivers reassign the same value repeatedly even when it hasn't changed numerically.

3. **`dashboard_simulation` flag** — Setting `dashboard_simulation: true` in the YAML causes the server to generate random test values instead of reading from hardware. Useful for testing client connectivity and UI layout without real devices attached.

4. **Config loading fails fast** — If `dashboard.yaml` has a YAML parse error, the server logs the error and continues with no devices configured. No exception is raised to the UI. The dashboard appears to work (ZMQ socket binds, heartbeats publish) but no device values are ever sent.

5. **`tag` uniqueness** — Tags must be unique across all devices and values in the config file. Duplicate tags cause the later entry to silently overwrite the earlier one in the server's internal device map.

6. **`on_change` period and `timeout`** — `timeout` is measured from the last ZMQ publication, not from the last attribute assignment. For `period: "on_change"` values, if the Traits observer stops firing (e.g. device driver crash), the timeout will not trigger until `timeout` seconds have elapsed since the last publication.

7. **Client `load_configuration()`** — On startup, the `DashboardClient` sends a REQ to port+1 to fetch the server's device list. If the server is not yet running (within the 5-second startup window), this request times out silently and the client shows an empty device list. The client does not retry — restart the client or use the **Reconnect** button in the dashboard UI to re-fetch the config.
