---
id: overview
title: Hardware Overview
sidebar_label: Overview
sidebar_position: 1
---

# Hardware Overview

Pychron supports a wide range of mass spectrometry laboratory hardware — spectrometers, lasers, furnaces, vacuum gauges, temperature controllers, motion stages, and more — through a unified plugin and communicator architecture. Every physical device is represented by a Python driver class, and the communication transport (Serial, Ethernet, GPIB, Modbus, USB) is handled by a separate, swappable `Communicator` layer. This separation means adding support for a new device rarely requires changes outside its own driver file.

## How Hardware Support Works

Hardware loads through Pychron's Envisage plugin system. Each application (`pyExperiment`, `pyValve`, `furPi`, etc.) has an `initialization.xml` file that lists which plugins to load at startup. A hardware plugin entry looks like this:

```xml
<plugin name="ExtractionLine">
  <device name="mks_controller"
          klass="MKSController"
          manager="gauge_manager"/>
</plugin>
```

The `klass` attribute maps directly to a Python driver class — Pychron resolves the name by searching registered hardware modules. The `name` attribute becomes the device identifier used elsewhere in the system (scripts, dashboard config, valve descriptions). If a device listed in `initialization.xml` fails to load, Pychron logs a warning and continues; hardware failures at startup are non-fatal by design, but the device will be unavailable for the session.

Each driver class subclasses `CoreDevice` (or a category-specific base such as `BaseGauge`, `BaseLaser`, or `BaseMotionController`). The driver declares its communicator type — `SerialCommunicator`, `EthernetCommunicator`, or another transport class — and all raw I/O goes through that communicator. This means the same driver can switch between Serial and Ethernet by changing one line in its YAML config file, without touching driver code.

Device-specific settings (host, port, baud rate, addresses, calibration coefficients) live in a YAML file at:

```
~/.pychron.<appname>/setupfiles/devices/<device_name>.yaml
```

The filename (without `.yaml`) must match the `name` attribute in `initialization.xml`.

## Supported Protocols

Pychron communicates over Serial RS-232/RS-485, Ethernet TCP, GPIB (IEEE-488 via PyVISA), Modbus RTU and TCP, ZMQ publish/subscribe, internal RPC, USB (LabJack, MCC, Thorlabs Kinesis), I2C, and GPIO. Most labs use Serial and Ethernet for the majority of their hardware; GPIB remains common for Agilent instruments; Modbus is standard for Watlow and Eurotherm temperature controllers. Full per-device protocol details are in the [Compatibility Matrix](./compatibility-matrix).

## How to Read the Matrix

Each row in the matrix represents one device or device family. The **Status** column uses four badges:

| Badge | Meaning for your lab |
|---|---|
| **✓ Production** | Fully implemented and in active use. Safe to deploy. |
| **⚠ Partial** | Basic communication works but specific features are missing or have workarounds. Review the Notes column before committing to this device. |
| **✗ Stub** | Class exists in the codebase but the body is `pass`. The device is not functional — do not plan around it without contributing an implementation first. |
| **★ Lab-specific** | Implemented for one institution. May work elsewhere but has not been tested outside its origin lab. |

If you are evaluating Pychron for a new lab, focus on ✓ rows. ⚠ rows are usable with awareness of the noted limitations. ✗ rows require code contributions before deployment.

## Adding New Hardware

New drivers subclass the appropriate base class (`CoreDevice`, `BaseGauge`, `BaseLaser`, etc.), implement `load()`, `initialize()`, and the device-specific command methods, then register the class in the relevant hardware plugin. A minimal working driver requires fewer than 50 lines; see any existing simple driver such as `pychron/hardware/ionpump/spc_ion_pump_controller.py` as a starting template.

:::tip
See the [Hardware Compatibility Matrix](./compatibility-matrix) for the complete list of supported devices, their Python classes, protocols, configuration parameters, and known issues.
:::
