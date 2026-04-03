---
id: intro
title: Welcome to Pychron
sidebar_label: Introduction
sidebar_position: 1
---

# Welcome to Pychron

Pychron is an open-source noble gas mass spectrometry platform for Ar-Ar geochronology and thermochronology, developed at the New Mexico Geochronology Research Laboratory (NMGRL) and actively used by more than 12 institutions worldwide. It manages the complete laboratory workflow in a single integrated system: automated extraction line control, CO₂ and diode laser operation, resistance furnace management, multi-collector spectrometer acquisition, programmatic scripting of run sequences, git-backed per-analysis data persistence, pipeline-based data reduction, age calculation, and publication-ready output. Pychron is not one application — it is a suite of specialized apps (pyExperiment, pyCrunch, pyValve, pyLaser, furPi) built on the Enthought plugin framework, each responsible for a distinct part of the workflow and communicating over ZMQ and RPC when deployed across multiple lab computers.

## Who Uses Pychron

Pychron is in active production at geochronology labs on four continents:

- **NMGRL** — New Mexico Geochronology Research Laboratory (New Mexico Tech), the primary developer
- **WiscAr** — University of Wisconsin–Madison Argon Geochronology Laboratory
- **GSC** — Geological Survey of Canada (Natural Resources Canada)
- **USGS** — U.S. Geological Survey, Menlo Park and Reston facilities
- **University of Melbourne** — Thermochronology Research Group
- And 7+ additional labs running supported or community installations

If your lab uses a Thermo Argus, Helix, or Helix SFT, an Isotopx NGX, or a Pfeiffer Quadera, and runs an automated extraction line with Photon Machines or Synrad lasers or a resistance furnace, Pychron is designed for your workflow.

:::tip Start with hardware compatibility
Before installing, confirm that your spectrometer, laser, and extraction line hardware are supported. Check the [Hardware Compatibility Matrix](./hardware/compatibility-matrix) — it lists every supported device, its implementation status, and known limitations.
:::

## Three Tiers

| Tier | What it is | Who it's for |
|---|---|---|
| **Open-Source Core** | The full Pychron codebase on [GitHub](https://github.com/NMGRL/pychron) — all acquisition, reduction, and DVC functionality | Labs with in-house Python expertise who want full control |
| **Supported Lab Edition** | Open-source core plus a support contract from Pychron Labs LLC — installation assistance, configuration review, priority issue response | Labs transitioning from MassSpec or standing up a new instrument |
| **Pychron Cloud** | Hosted DVC data management — MetaRepo and data repositories managed in the cloud, no self-hosted GitHub/GitLab required | Labs without institutional IT infrastructure for self-hosted git |

## Getting Started in Four Steps

1. **Check hardware compatibility** — [Hardware Compatibility Matrix](./hardware/compatibility-matrix). Confirm your spectrometer and extraction line hardware are supported (✓ rows) before committing to the migration.
2. **Install Pychron** — [Installation Guide](./getting-started/installation). Uses `uv` and Python 3.12. Takes ~15 minutes on a clean system.
3. **Configure DVC** — [DVC Setup Guide](./dvc/setup-guide). Choose a git host (GitHub, GitLab, or LocalGit) and a database backend (MySQL or SQLite), then initialize the MetaRepo.
4. **Run your first experiment** — [Quick Start](./getting-started/quick-start). Verify startup tests, confirm hardware responds, and run a test blank-unknown-blank sequence.

## Coming From MassSpec

If your lab currently runs MassSpec, see the [Migration Overview](./migration/massspec-overview) for an honest comparison of the two architectures and a clear picture of what the automated migration tooling covers — and what it does not.

## Get Help

**Community support** — Issues and questions: [github.com/NMGRL/pychron/issues](https://github.com/NMGRL/pychron/issues). Search existing issues before opening a new one; many installation and configuration questions have been answered there.

**Pychron Labs LLC** — Commercial support contracts cover installation, initial configuration, DVC setup, MassSpec migration, and ongoing troubleshooting. A support contract is the fastest path to a working system for labs without dedicated Python expertise. Contact Pychron Labs LLC through the NMGRL website or via the GitHub issues page for current pricing and scope.
