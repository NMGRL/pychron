---
id: quick-start
title: Quick Start
sidebar_label: Quick Start
sidebar_position: 2
---

# Quick Start

This guide walks through the five things to verify on first launch and what to do when something is not green. It assumes Pychron is already installed (`uv sync` complete, `pychron-bootstrap` run) and you are ready to launch for the first time.

## Before You Start

Confirm each of these before launching:

- [ ] `pychron-doctor` reports all checks green (see [Installation Guide](./installation))
- [ ] `initialization.xml` exists at `~/.pychron.<appname>/setupfiles/initialization.xml`
- [ ] Your DVC git host choice (GitHub, GitLab, or LocalGit) plugin is listed in `initialization.xml`
- [ ] The `DVC` plugin is listed in `initialization.xml`
- [ ] `meta_repo_name` is set in **Preferences → DVC → Connection**
- [ ] MySQL is running (or SQLite path exists) and `PYCHRON_ALEMBIC_URL` is set
- [ ] Hardware is powered on and network/serial cables are connected

:::tip For data-reduction-only setups (pyCrunch)
If you are setting up a reduction workstation with no hardware attached, you only need DVC + a git host plugin. Skip the hardware verification steps and go straight to [Verify 3 — Database Connected](#verify-3--database-connected).
:::

## Choose and Launch Your Application

Pychron has separate apps for different roles. Start with the one that matches your first task:

| App | Launch command | Use for |
|---|---|---|
| pyExperiment | `uv run pychron --app experiment` | Automated acquisition + full lab control |
| pyCrunch | `uv run pychron --app pipeline` | Data reduction only |
| pyValve | `uv run pychron --app valve` | Extraction line control only |

```bash
uv run pychron --app experiment
```

## Verify 1 — Startup Tests Green

On every launch, Pychron runs a set of startup tests defined in `startup_tests.yaml`. After the splash screen, a results panel appears briefly (or stays open if anything is red). The two critical tests are:

| Test | What it checks | Expected result |
|---|---|---|
| `test_database` | MySQL (or SQLite) connection and schema version | Green |
| `test_dvc_fetch_meta` | MetaRepo clone exists locally and `git pull` succeeds | Green |

**If `test_database` is red:** MySQL is not running, the database doesn't exist, or the credentials are wrong. See [Database Failures](../dvc/failure-modes#database-failures).

**If `test_dvc_fetch_meta` is red:** The MetaRepo could not be opened or cloned. The failure is almost always silent — Pychron logs the reason but shows no popup. Check `~/.pychron.<appname>/logs/pychron.log` and search for `"Error opening meta repo"`. See [GitHub / GitLab Unreachable](../dvc/failure-modes#github--gitlab-unreachable).

:::warning Red startup tests block most functionality
With `test_database` red, the analysis browser, pipeline, and experiment queue are all non-functional. With `test_dvc_fetch_meta` red, DVC data cannot be read or written. Fix both before proceeding.
:::

## Verify 2 — MetaRepo Cloned

Confirm the MetaRepo directory was created on disk:

```bash
ls ~/.pychron.<appname>/data/.dvc/<MetaRepoName>/
```

You should see at least `irradiation_holders/`, `productions/`, and `load_holders/` — the defaults created by `DVC._defaults()` on first run. If the directory is empty or missing, DVC either failed to clone (check the log) or `_defaults()` did not run (re-check `meta_repo_name` in preferences).

```bash
# Check what was committed on first run
cd ~/.pychron.<appname>/data/.dvc/<MetaRepoName>/
git log --oneline
```

A healthy first run shows one commit: `"adding default files"` or similar.

## Verify 3 — Database Connected

Confirm the Pychron database has its schema in place. In pyCrunch or pyExperiment, open **Help → Startup Tests** (or look at the startup panel result) and confirm `test_database` is green with no error message.

You can also verify directly:

```bash
mysql -u root pychronmeta -e "SHOW TABLES;" | head -20
```

A migrated database shows tables like `AnalysisTbl`, `IrradiationTbl`, `SampleTbl`, `ProjectTbl`. An empty list means `alembic upgrade head` has not been run.

:::info First launch with an empty database is normal
An empty `pychronmeta` database is expected on a brand-new install — no analyses, no irradiations, nothing. That is not an error. Add irradiation data via **Entry → Irradiation** or by following the [DVC First-Run Setup](../dvc/first-run) guide.
:::

## Verify 4 — Hardware Responding

**Spectrometer (pyExperiment only):**

Go to **Spectrometer → Test Connection**. A successful response returns the instrument's current magnet position or detector readings. If this fails:

- **Argus / Helix:** Confirm Qtegra is running on the spectrometer PC and `RemoteControlServer` is active. Check the host/port in **Preferences → Spectrometer**.
- **NGX:** Confirm the NGX controller is powered and on the network. Check credentials (username/password) in the NGX device YAML file.
- **Other:** See the [Hardware Compatibility Matrix](../hardware/compatibility-matrix) for protocol and configuration details for your specific instrument.

**Laser (pyExperiment / pyLaser):**

Go to **Laser → Test Connection** or attempt to enable the laser in the control panel. A partial power command should return a value near zero.

**Extraction line gauges:**

In pyExperiment or pyValve, open the extraction line canvas. Gauge readings should update in real time. Static `???` values mean the gauge controller is not responding — check serial port or Ethernet connection in the device YAML.

:::warning Hardware errors on first launch are common
Device YAML files (in `~/.pychron.<appname>/setupfiles/devices/`) contain defaults that almost certainly need to be edited for your lab's specific hardware addresses, serial ports, and IP addresses. A device that fails to connect on first launch is not a bug — it means the configuration file needs the correct values for your lab.
:::

## Verify 5 — Extraction Line Canvas Loading

In pyExperiment or pyValve, open the extraction line view. The canvas should render the valve network diagram defined in `~/.pychron.<appname>/setupfiles/canvas2D/canvas.xml`. If the canvas is blank or shows an error:

- Confirm `canvas.xml` exists in the setupfiles directory
- Check the log for canvas parsing errors (`~/.pychron.<appname>/logs/pychron.log`)
- The default canvas file installed by `pychron-bootstrap` is a placeholder — your lab's actual valve network must be defined. Contact NMGRL or your Pychron Labs LLC support contact for a starting template.

## What a Successful First Launch Looks Like

A clean first launch of pyExperiment on a fully configured acquisition computer:

1. Splash screen appears briefly
2. Startup tests panel shows — both `test_database` and `test_dvc_fetch_meta` are **green**
3. Main window opens with the experiment queue tab, extraction line canvas, and spectrometer panel visible
4. Gauge readouts in the extraction line canvas show live values (numbers updating, not `???`)
5. Spectrometer panel shows mass position and detector voltages

At this point Pychron is ready to run an experiment. Before doing so, confirm:

- At least one irradiation is loaded in the database (**Entry → Irradiation** to check)
- A test data repository exists on GitHub/GitLab (or is initialized locally) with `repository_identifier` matching what you plan to use in your experiment queue
- `use_dvc_persistence = true` in **Preferences → Experiment → DVC**

## Startup Tests Are Red — Where to Look

| Red test | First place to check | Guide |
|---|---|---|
| `test_database` | `~/.pychron.<appname>/logs/pychron.log` for `OperationalError` | [Database Failures](../dvc/failure-modes#database-failures) |
| `test_dvc_fetch_meta` | Same log, search for `"Error opening meta repo"` | [GitHub / GitLab Unreachable](../dvc/failure-modes#github--gitlab-unreachable) |
| Hardware test | Device YAML in `setupfiles/devices/<device>.yaml` — check host/port/serial port | [Hardware Compatibility Matrix](../hardware/compatibility-matrix) |

If both DVC tests pass but hardware is not responding, the problem is isolated to a device configuration file. If both DVC tests are red, fix DVC first — hardware debugging without a working data store is not productive.
