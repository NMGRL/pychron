---
id: multi-node
title: Multi-Node Deployment
sidebar_label: Multi-Node Deployment
sidebar_position: 1
---

# Multi-Node Deployment

A typical Pychron installation spans multiple computers: one running pyExperiment (the acquisition computer connected to the spectrometer and extraction line hardware), one running pyValve (the extraction line valve controller, often on a dedicated Raspberry Pi or small PC), and optionally a separate pyCrunch workstation for data reduction. Each node is a separate Pychron application instance, and they communicate over ZMQ publish/subscribe and RPC channels across the lab network. This page covers the network configuration, inter-process communication setup, and `initialization.xml` structure required for a multi-node deployment.

:::note
This page is a placeholder. Content will be populated from the documentation audit of `pychron/extraction_line/`, `pychron/messaging/`, and the inter-process communication architecture described in `docs/dev_guide/communications.rst`.
:::

## Node roles

| Node | App | Key plugins | Typical hardware |
|---|---|---|---|
| Acquisition computer | pyExperiment | DVC, Spectrometer, ExtractionLine, Laser/Furnace | Spectrometer, laser, extraction line valves |
| Valve controller | pyValve | ExtractionLine, RemoteCommandServer | Valve actuators (Agilent, Arduino, LabJack) |
| Data reduction workstation | pyCrunch | DVC, Pipeline | No hardware |
| Furnace controller | furPi | Furnace, RemoteCommandServer | Resistance furnace, temperature controller |

## Communication channels

Pychron nodes communicate using:

- **ZMQ PUB/SUB** — broadcast channels for valve state updates, spectrometer readbacks, and dashboard data
- **RPC (Remote Command Server)** — request/reply for direct hardware commands sent from pyExperiment to pyValve or furPi
- **`RemoteCommandServer`** — the server-side plugin that listens for RPC calls (`pychron.messaging.remote_command_server`)

Each node that receives remote commands must load the `RemoteCommandServer` plugin in its `initialization.xml` and configure the host/port it listens on.
