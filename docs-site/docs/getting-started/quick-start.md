---
id: quick-start
title: Quick Start
sidebar_label: Quick Start
sidebar_position: 2
---

# Quick Start

After installing Pychron with `uv sync` and running `pychron-bootstrap`, the first launch requires two pieces of configuration before the application will fully start: selecting which plugins to load by editing `initialization.xml`, and setting up at least one DVC connection profile in Preferences. Without both, the startup tests (run automatically on every launch) will fail and block access to most functionality. This guide walks through the minimal configuration needed to reach a working state — hardware connected, DVC initialized, and startup tests passing green.

## 1. Choose an application

Pychron is not a single executable. Run the app that matches your role:

| App | Command | Purpose |
|---|---|---|
| pyExperiment | `uv run pychron --app experiment` | Automated acquisition |
| pyCrunch | `uv run pychron --app pipeline` | Data reduction |
| pyValve | `uv run pychron --app valve` | Extraction line only |

## 2. Edit `initialization.xml`

The file at `~/.pychron.<appname>/setupfiles/initialization.xml` controls which plugins are loaded. A minimal working configuration for data reduction looks like:

```xml
<root>
  <globals>
    <global name="use_login" value="0"/>
  </globals>
  <plugins>
    <general>
      <plugin name="DVC" enabled="true"/>
      <plugin name="GitHub" enabled="true"/>
      <plugin name="Pipeline" enabled="true"/>
    </general>
  </plugins>
</root>
```

The `GitHub` (or `GitLab`, or `LocalGit`) plugin **must** be enabled alongside `DVC` or DVC will refuse to initialize.

## 3. Configure DVC in Preferences

On first launch, go to **Preferences → DVC** and fill in:

- **Organization:** your GitHub org name (e.g. `NMGRL`)
- **MetaData Name:** the name of your MetaRepo (e.g. `NMGRLMetaData`)
- **Connection kind:** `mysql`, host `localhost`, database `pychronmeta`

Then go to **Preferences → GitHub** and enter your OAuth token.

## 4. What success looks like

On startup, Pychron runs a set of startup tests defined in `startup_tests.yaml`. A healthy launch shows:

- `test_database` — green (MySQL connection successful)
- `test_dvc_fetch_meta` — green (MetaRepo cloned or opened, `git pull` succeeded)

If either test is red, see the [DVC Failure Modes](../dvc/failure-modes) guide.

## 5. Verify the spectrometer connection

In pyExperiment, go to **Spectrometer → Test Connection**. A successful response returns the spectrometer's current mass position. If this fails, check that the spectrometer controller (Qtegra for Argus/Helix, NGX controller for Isotopx) is running and reachable on the configured host/port.
