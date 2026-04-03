---
id: intro
title: What is Pychron?
sidebar_label: Introduction
sidebar_position: 1
---

# What is Pychron?

Pychron is an open-source platform for automated noble gas mass spectrometry, developed at the New Mexico Geochronology Research Laboratory (NMGRL) and used by approximately 15 labs worldwide. It manages the complete Ar-Ar geochronology workflow — from automated extraction line and laser control, through multi-collector spectrometer acquisition, to git-backed data persistence, pipeline-based data reduction, and age calculation. Rather than a single monolithic application, Pychron is a suite of specialized apps (pyExperiment, pyCrunch, pyValve, pyLaser, furPi) built on the Enthought plugin framework, each handling a distinct part of the laboratory workflow and communicating over ZMQ/RPC when deployed across multiple computers.

## Who is Pychron for?

Pychron is aimed at geochronology labs running noble gas mass spectrometers (Thermo Argus VI / Helix, Isotopx NGX, Pfeiffer Quadera) with automated extraction lines, CO₂ or diode lasers, and resistance furnaces. It suits labs that want full version-controlled data provenance, programmatic scripting of acquisition sequences, and an open, auditable data format — or labs migrating away from proprietary platforms such as MassSpec.

## Where to start

- **New installation:** [Installation Guide](./getting-started/installation)
- **Already installed:** [Quick Start](./getting-started/quick-start)
- **Setting up data storage:** [DVC Setup Guide](./dvc/setup-guide)
- **Checking hardware compatibility:** [Hardware Overview](./hardware/overview)
- **Coming from MassSpec:** [MassSpec Migration Overview](./migration/massspec-overview)
