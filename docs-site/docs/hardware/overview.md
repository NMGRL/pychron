---
id: overview
title: Hardware Overview
sidebar_label: Overview
sidebar_position: 1
---

# Hardware Overview

Pychron communicates with laboratory hardware through a layered driver architecture: each physical device is represented by a Python class that inherits from `CoreDevice` (or a hardware-category-specific base), and communication is handled by a pluggable `Communicator` layer that abstracts the underlying transport protocol. This means the same high-level spectrometer API works whether the instrument talks over Ethernet to a Qtegra server or over a direct serial connection. The [Hardware Compatibility Matrix](./compatibility-matrix) lists every supported device, its implementing class and file location, and the protocol and configuration details needed to connect it.

## How to read the matrix

Each row in the compatibility matrix represents one device or device family. The columns are:

| Column | Meaning |
|---|---|
| **Device / Model** | The commercial product name or family |
| **Class** | The Python class that implements the device |
| **Module** | The dotted import path (e.g. `pychron.hardware.gauges.mks.controller`) |
| **Protocol** | The communication layer used (see below) |
| **Config** | Key configuration fields required in the device YAML file |
| **Status** | `✅ Complete`, `⚠️ Partial`, or `🚧 Stub` |

A **Partial** status means the class exists and basic communication works but one or more documented features (e.g. setpoint writing, full fault reporting) are commented out or flagged with TODO. A **Stub** status means the class is present but the method bodies are `pass` — the device is not functional.

## Supported protocols

| Protocol | Transport | Pychron communicator | Typical use |
|---|---|---|---|
| Serial RS-232/RS-485 | USB-serial or COM port | `SerialCommunicator` | Older gauges, temperature controllers |
| Ethernet TCP | LAN | `EthernetCommunicator` | Spectrometers (Qtegra, NGX), modern controllers |
| GPIB (IEEE-488) | GPIB bus or USB-GPIB adapter | PyVISA / `GPIBCommunicator` | Agilent instruments |
| Modbus RTU | RS-485 | `pymodbus` | Eurotherm, WatlowEZZone temperature controllers |
| Modbus TCP | LAN | `pymodbus` | Network-connected temperature controllers |
| ZMQ | LAN | `zmq` | Inter-process communication between Pychron nodes |
| RPC | LAN | `pychron.messaging` | Remote command server (pyValve ↔ pyExperiment) |
| Watlow Standard Bus | RS-485 | Built into `WatlowEZZone` driver | WatlowEZZone PM controllers |
| MDrive M-code | Serial | `MicroMotionController` | MDrive stepper motor stages |
| MCC USB | USB | `mcculw` / `mccdaq` | MCC USB-based DAQ and ADC modules |
| OPC | LAN | `opcua` | OPC-UA compatible instruments |

## Device configuration files

Each hardware device is configured through a YAML file placed in `~/.pychron.<appname>/setupfiles/devices/`. The filename (without `.yaml`) becomes the device name referenced in `initialization.xml`. The minimum required fields are `klass` (the Python class name) and `port` or `host`/`port` depending on the transport. See each device's entry in the compatibility matrix for its specific required fields.
