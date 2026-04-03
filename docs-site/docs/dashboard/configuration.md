---
id: configuration
title: Dashboard Configuration
sidebar_label: Configuration
sidebar_position: 1
---

# Dashboard Configuration

The Pychron dashboard system provides real-time monitoring of laboratory instruments — vacuum levels, temperatures, laser power, and any other hardware value that a device driver can expose. It consists of a server process (running on the acquisition computer, reading from hardware) and one or more client processes (running on any networked machine) that subscribe to the published data stream over ZMQ. Both server and client are configured through a YAML file whose path is set in **Preferences → Dashboard**.

:::note
This page is a placeholder. Content will be populated from the documentation audit of `pychron/dashboard/`. The dashboard module was substantially refactored in the `develop` branch — `config.py` and `messages.py` were deleted and their logic consolidated into `server.py` and `client.py`. This page will cover the current `main` branch configuration format.
:::

## Server configuration

The dashboard server (`DashboardServer`) reads a YAML configuration file that lists which devices to monitor and at what polling interval. The configuration file is located at:

```
~/.pychron.<app>/setupfiles/dashboard.yaml
```

A minimal configuration looks like:

```yaml
server:
  host: 0.0.0.0
  port: 8100

devices:
  - name: MKSController
    attribute: pressure
    period: 5        # seconds between readings
    units: Torr

  - name: WatlowEZZone
    attribute: process_value
    period: 10
    units: C
```

## Client configuration

The dashboard client (`DashboardClient`) connects to the server over ZMQ and displays live values. Configure the server address in **Preferences → Dashboard Client**:

- **Host:** IP address of the acquisition computer running the server
- **Port:** Must match `server.port` in the server config (default `8100`)

## Available device attributes

Any device attribute that has a Traits notification (i.e. is defined as a `Float`, `Int`, or similar Traits type with `observe`) can be published to the dashboard. The attribute name in the YAML must match the Python attribute name on the device class exactly.
