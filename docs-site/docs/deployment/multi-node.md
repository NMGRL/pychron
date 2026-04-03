---
id: multi-node
title: Multi-Node Deployment
sidebar_label: Multi-Node Deployment
sidebar_position: 1
---

# Multi-Node Deployment

A typical Pychron installation spans multiple computers. The acquisition computer runs pyExperiment and connects directly to the spectrometer and extraction line hardware. A valve controller — often a Raspberry Pi running furPi or a small PC running pyValve — manages the extraction line solenoid valves. A separate pyCrunch workstation handles data reduction. Each node is its own Pychron application instance; they communicate over TCP RPC and ZMQ publish/subscribe.

## Node Roles

| Node | App | Key plugins | Typical hardware |
|---|---|---|---|
| Acquisition computer | pyExperiment | DVC, Spectrometer, ExtractionLine, Laser or Furnace | Spectrometer, laser, extraction line valves |
| Valve controller | pyValve or furPi | ExtractionLine, RemoteCommandServer | Valve actuators (Agilent, Arduino, LabJack) |
| Data reduction workstation | pyCrunch | DVC, Pipeline | None |
| Furnace controller | furPi | Furnace, RemoteCommandServer | Resistance furnace, temperature controller |

## Communication Architecture

```
pyExperiment (acquisition PC)
│
├── TCP port 1061 ──────────────────► RemoteCommandServer (pyValve / furPi)
│      RPC: "Open A\r\n"                 │
│      4-byte hex length prefix           └── drives physical valves
│
└── ZMQ PUB port 5555 ──────────────► Notifier / Subscriber (pyCrunch, Dashboard)
       topic: "pychron"                      status updates, spectrometer data
```

### Two Protocols

**TCP RPC (command channel)** — pyExperiment sends valve open/close commands and hardware commands to pyValve and furPi. The message format uses a 4-byte hex length prefix followed by the command and a CRLF terminator:

```
{000F}Open A\r\n
```

The 4 hex digits encode the total message length including the `{}` delimiters and the `\r\n`.

**ZMQ PUB/SUB (broadcast channel)** — pyExperiment publishes status updates, spectrometer data, and dashboard measurements on a ZMQ PUB socket. pyCrunch and any dashboard client connect as ZMQ SUB subscribers. Published messages use topic prefixes to allow subscriber filtering.

## Port Reference

| Port | Protocol | Direction | Purpose |
|---|---|---|---|
| 1061 | TCP | pyExperiment → pyValve / furPi | `RemoteCommandServer` — valve and hardware RPC |
| 5555 | ZMQ PUB | pyExperiment → all | Notifier broadcast (spectrometer, status) |
| 5556 | ZMQ REP | pyExperiment | Notifier reply socket (request/response) |
| 8100 | ZMQ PUB | DashboardServer → clients | Dashboard value stream |
| 8101 | ZMQ REP | DashboardServer | Dashboard config request socket |

All ports are configurable. The defaults above are the Pychron code defaults; override them in device YAML files and preferences as needed.

## The "Open Valve A" Call Chain

Tracing a `open('A')` call in an extraction script from source to hardware:

1. `ExtractionLinePyScript.open('A')` is called
2. `ValvePyScript._m_open('A')` dispatches to the extraction line manager
3. `ExtractionLineManager.open_valve('A')` looks up valve `'A'` in the canvas
4. If the valve is configured as a remote valve (`RemoteValve`), `RemoteExtractionLineManager` is used
5. `RemoteExtractionLineManager` sends `"Open A\r\n"` over TCP to port 1061 on the valve controller
6. `RemoteCommandServer` on pyValve receives the message, strips the length prefix
7. `RemoteCommandServer` dispatches to `ExtractionLineManager.open_valve('A')` on pyValve
8. pyValve's `ExtractionLineManager` looks up the physical valve actuator (e.g. `AgilentMultiplexer`)
9. The actuator driver sends the hardware command (e.g. RS-232 relay toggle)
10. The valve state change is published on ZMQ back to pyExperiment; `StatusMonitor` picks it up

## Status Monitor

`StatusMonitor` runs on pyExperiment and periodically polls valve states from the remote valve controller:

| Parameter | Default | Description |
|---|---|---|
| `state_freq` | 3 | How often (in `update_period` ticks) to poll valve open/closed state |
| `lock_freq` | 5 | How often to poll valve lock state |
| `update_period` | 1 | Seconds between ticks |

Effective polling rates: valve states every ~3 seconds, lock states every ~5 seconds.

## `initialization.xml` Per Node

Each node loads only the plugins it needs. Below are representative configurations.

### pyExperiment (acquisition computer)

```xml
<root>
  <globals>
    <plugin enabled="true">DVC</plugin>
    <plugin enabled="true">GitHub</plugin>
  </globals>
  <plugins>
    <general>
      <plugin enabled="true">Database</plugin>
      <plugin enabled="true">Spectrometer</plugin>
      <plugin enabled="true">ExtractionLine</plugin>
      <plugin enabled="true">Experiment</plugin>
      <plugin enabled="true">Laser</plugin>
      <plugin enabled="true">DashboardServer</plugin>
    </general>
  </plugins>
</root>
```

### pyValve (valve controller)

```xml
<root>
  <plugins>
    <general>
      <plugin enabled="true">ExtractionLine</plugin>
      <plugin enabled="true">RemoteCommandServer</plugin>
    </general>
  </plugins>
</root>
```

### furPi (furnace controller)

```xml
<root>
  <plugins>
    <general>
      <plugin enabled="true">Furnace</plugin>
      <plugin enabled="true">RemoteCommandServer</plugin>
    </general>
  </plugins>
</root>
```

### pyCrunch (data reduction workstation)

```xml
<root>
  <globals>
    <plugin enabled="true">DVC</plugin>
    <plugin enabled="true">GitHub</plugin>
  </globals>
  <plugins>
    <general>
      <plugin enabled="true">Database</plugin>
      <plugin enabled="true">Pipeline</plugin>
      <plugin enabled="true">DashboardClient</plugin>
    </general>
  </plugins>
</root>
```

## Device YAML Configuration

Each remote node is described by a device YAML file on the acquisition computer. pyExperiment reads these to know how to reach each remote controller.

Example — remote extraction line on pyValve:

```yaml
# ~/.pychron.experiment/setupfiles/devices/extraction_line.yaml
name: ExtractionLine
klass: RemoteExtractionLineManager
host: 192.168.1.50   # IP of the pyValve machine
port: 1061
timeout: 2
```

Example — furnace controller on furPi:

```yaml
# ~/.pychron.experiment/setupfiles/devices/furnace.yaml
name: Furnace
klass: RemoteFurnaceManager
host: 192.168.1.51
port: 1061
timeout: 5
```

:::warning
The `host` values above are examples. Replace with the actual IP addresses of your lab network. Static IPs or DHCP reservations are strongly recommended for all Pychron nodes — a changing IP breaks the device YAML without any visible error on startup.
:::

## RemoteCommandServer Configuration

On each remote node (pyValve, furPi), the `RemoteCommandServer` plugin binds to a TCP port. Configure it in preferences or in the device YAML on the remote machine:

```yaml
# On pyValve: setupfiles/servers/remote_command_server.yaml
port: 1061
host: 0.0.0.0   # listen on all interfaces
```

The server spawns a thread per connection. There is no authentication — restrict access at the network level (VLAN or firewall) if the lab network is untrusted.

## Network Requirements

| Requirement | Detail |
|---|---|
| Topology | All nodes must be on the same LAN or routed subnet |
| Firewall | TCP 1061 open from acquisition PC to each valve/furnace controller |
| ZMQ | UDP/TCP 5555–5556 open from acquisition PC to reduction workstations |
| Dashboard | TCP 8100–8101 open from dashboard server to clients |
| Latency | < 5 ms round-trip recommended; `StatusMonitor` has a 2-second default timeout |
| DNS | Not required — use IP addresses in device YAML files |

## Legacy: `RemoteHardwareServer`

Earlier Pychron versions used `RemoteHardwareServer` (in `pychron/hardware/remote/`) which accepted HTTP-style GET requests. This is superseded by `RemoteCommandServer` + ZMQ. If you are migrating an older installation, replace the `RemoteHardwareServer` plugin with `RemoteCommandServer` in `initialization.xml` and update device YAML host/port entries accordingly.
