---
id: experiment-workflow
title: Running Your First Experiment
sidebar_label: First Experiment
sidebar_position: 3
---

# Running Your First Experiment

This walkthrough takes you from a fully configured Pychron installation through a complete automated acquisition run and verifies that data was written to DVC. It assumes you have completed the [Installation Guide](./installation) and [Quick Start](./quick-start) verification steps.

## Prerequisites

Confirm all of the following before proceeding:

- [ ] `test_database` startup test is **green**
- [ ] `test_dvc_fetch_meta` startup test is **green**
- [ ] At least one irradiation is loaded in the database — check via **Entry → Irradiation**
- [ ] Hardware is responding (spectrometer connection test passes, extraction line canvas shows live gauge readings)
- [ ] A data repository exists on your git host (GitHub, GitLab, or LocalGit) for your experiment data
- [ ] `use_dvc_persistence = true` in **Preferences → Experiment → DVC**

:::warning Without a loaded irradiation, no unknown runs can be saved
Pychron requires an irradiation record in the database to associate analyses with samples and positions. An empty `pychronmeta` database with no irradiation data is a valid first-launch state, but you must add at least one irradiation before running unknowns. Go to **Entry → Irradiation** to add one, or follow the [DVC First-Run Setup](../dvc/first-run) guide.
:::

---

## Step 1 — Set Up the Experiment Queue

### Open the Experiment Editor

In pyExperiment, go to **Experiment → New Experiment Queue** (or open an existing `.xls` or `.yaml` queue file via **Experiment → Open**).

### Queue-Level Fields

These fields apply to every run in the queue. Set them first in the queue header:

| Field | What it does | Required |
|---|---|---|
| `mass_spectrometer` | Selects which spectrometer drives this queue | Yes |
| `extract_device` | Laser, furnace, or `None` | Yes |
| `username` | Who is running the experiment | Yes |
| `load_name` | Tray/load identifier (matches the loaded tray in the database) | Yes |
| `repository_identifier` | Git repository where data is saved (see below) | Yes |
| `queue_conditionals_name` | Name of a `.yaml` file in `conditionals/` to apply to all runs | No |
| `delay_before_analyses` | Seconds to wait before the first run | No |
| `delay_between_analyses` | Seconds to wait between runs | No |

### Understanding `repository_identifier`

`repository_identifier` is the name of the git repository (inside your DVC git host) where analysis JSON files will be committed after each run. It must already exist on your git host — Pychron will not create it automatically.

The convention for naming repositories is `<Organization>_<Project>`, for example `NMGRL_Jan2025`. You can set a single identifier for the entire queue, or override it per-run. If left blank, Pychron generates a default based on analysis type, mass spectrometer, and the current month/year (e.g., `Blank_Air_Jan_2025`).

:::tip For a first run, use a dedicated test repository
Create a repository named `<YourOrg>_Test` on your git host before your first experiment run. Set `repository_identifier` to that name. This keeps test data isolated from production data.
:::

### Adding Runs to the Queue

Each row in the queue is one `AutomatedRunSpec`. The columns you will fill in are:

| Field | What it does |
|---|---|
| `labnumber` | The irradiation position identifier (e.g., `J001-01A`). Must exist in the database. |
| `aliquot` | Run number for this sample (auto-incremented by Pychron if left blank) |
| `position` | Tray hole number for the laser stage |
| `extract_value` | Laser power or furnace temperature |
| `extract_units` | `watts`, `temp`, or `percent` |
| `duration` | Extraction time in seconds |
| `cleanup` | Post-extraction cleanup time in seconds |
| `pre_cleanup` | Pre-extraction pump-down time in seconds |
| `extraction_script` | Name of the extraction script (no path, no extension) |
| `measurement_script` | Name of the measurement script |
| `post_equilibration_script` | Post-equilibration script (usually `none` or `default`) |
| `post_measurement_script` | Post-measurement cleanup script |
| `repository_identifier` | Per-run override (inherits queue-level value if blank) |
| `skip` | Check to skip this run without deleting it |
| `end_after` | Check to stop the queue after this run completes |

**Special run types** are identified by `labnumber` prefix:

| Prefix | Type | Purpose |
|---|---|---|
| `b-` | Blank | Air or gas blank (no sample extraction) |
| `a-` | Air | Atmospheric air for IC factor determination |
| `c-` | Cocktail | Gas cocktail for IC factor determination |
| `dg-` | Detector IC | Detector intercalibration |

A typical queue for a single unknown analysis looks like:

```
b-01  (blank)    — no position — extraction: blank_air — measurement: measurementdefaults
J001-01A         — position 1  — extraction: jan_unknown — measurement: measurementdefaults
b-02  (blank)    — no position — extraction: blank_air — measurement: measurementdefaults
```

Bracketing unknowns with blanks is standard practice for blank interpolation during data reduction.

---

## Step 2 — Write or Select Scripts

### Where Scripts Live

All scripts reside in the MetaRepo under `scripts/`:

```
<MetaRepoName>/
  scripts/
    extraction/
      blank_air.py          ← no sample heating, just opens inlet
      jan_unknown.py        ← laser extraction for unknown
    measurement/
      measurementdefaults.py
      jan_unknown.py
    post_equilibration/
      default.py
    post_measurement/
      default.py
```

### Referencing Scripts in the Queue

In the queue editor, script name fields contain just the filename without path or `.py` extension. Pychron resolves them relative to `<MetaRepo>/scripts/<type>/`. If the script file does not exist, the run will fail the pre-run check and be skipped.

### A Minimal Extraction Script

```python
# scripts/extraction/blank_air.py
info('running blank air extraction')
sleep(5)
open('C')
sleep(20)
close('C')
```

```python
# scripts/extraction/jan_unknown.py
info('extracting position: {}'.format(position))
move_to_position(position)
extract(extract_value, units=extract_units)
sleep(duration)
end_extract()
sleep(cleanup)
```

Context variables (`position`, `extract_value`, `extract_units`, `duration`, `cleanup`) are injected automatically from the run spec — you do not pass them explicitly.

### A Minimal Measurement Script

```python
# scripts/measurement/measurementdefaults.py
peak_center(detector='H1', isotope='Ar40')
position_magnet(39.948, 'H1')
activate_detectors('H2', 'H1', 'AX', 'L1', 'L2', 'CDD')
equilibrate(eqtime=20, inlet='C', outlet='S', close_inlet=True)
multicollect(ncounts=200, integration_time=1.04)
baselines(ncounts=5, mass=39.5, detector='H1', settling_time=4)
```

### Script Syntax Check

Before running, verify scripts pass syntax checking: right-click any run in the queue and choose **Test Scripts**. This executes each script in `test_syntax=True` mode — all hardware commands are no-ops and the estimated duration is reported. Fix any syntax errors before launching.

---

## Step 3 — Run the Experiment

### Pre-Execute Checks

When you click **Run** (the green arrow in the experiment toolbar), `ExperimentExecutor` runs `_pre_execute_check()` before touching any hardware:

1. Spectrometer manager is available and connected
2. Extraction line manager is available and connected
3. Database is accessible
4. (Optional) Spectrometer configuration matches the expected configuration

If any check fails, a dialog appears and the queue does not start. Fix the reported issue before retrying.

### What Happens During a Run

Each run (`AutomatedRun`) progresses through four phases:

**1. Extraction**
- The extraction script runs
- The extraction line is driven by the script commands (valve opens/closes, laser fires, furnace ramps)
- On completion, extraction data is written to DVC (`extraction/<repo>/<uuid>/extraction.json`)

**2. Equilibration + Measurement** (concurrent)
- The measurement script starts
- `equilibrate()` in the script opens the inlet valve and waits
- The post-equilibration script runs (if configured) while measurement runs concurrently
- `multicollect()` acquires signal data from the spectrometer

**3. Post-Measurement**
- The post-measurement script runs (typically pumps out gas, closes valves)

**4. Save**
- All isotope data, script blobs, spectrometer config, and metadata are committed to the DVC repository
- The database record is updated

### What to Watch During a Run

The experiment pane shows the active run in the **Run Status** section. Key indicators:

| Indicator | Meaning |
|---|---|
| Run state = EXTRACTION | Extraction script is executing |
| Run state = MEASUREMENT | Mass spec is acquiring |
| Run state = SUCCESS | Run completed and data was saved |
| Run state = FAILED | Script error — check log |
| Run state = TRUNCATED | A truncation conditional fired; run was abbreviated |

The **Spectrometer** panel updates in real time during measurement. Ion beam signals should rise from baseline during equilibration and stabilize at peak intensity during `multicollect`.

### Conditionals

Conditionals evaluate live acquisition data against threshold expressions. They are checked on each data point during `multicollect`. Four types:

| Type | What it does |
|---|---|
| **Termination** | Stops the current run immediately; moves to next run |
| **Truncation** | Stops the current measurement phase early; run is abbreviated |
| **Cancelation** | Stops the entire experiment queue |
| **Action** | Executes a PyScript snippet when the condition fires; can resume |

Conditionals are defined in `.yaml` files in `<MetaRepo>/conditionals/` and referenced by name in the queue's `queue_conditionals_name` field or per-run. Example conditional:

```yaml
- type: termination
  attr: Ar40.signal
  teststr: x < 1e-14
  start_count: 20
  frequency: 5
  ntrips: 3
```

This terminates any run where the Ar40 signal drops below 1e-14 amps, checked after 20 counts, every 5 counts, requiring 3 consecutive trips before firing.

:::warning A tripped termination conditional does not save the analysis
If a run is terminated by a conditional, it is marked `FAILED` and no data is written to DVC. This is by design — a failed run does not clutter your data repository.
:::

---

## Step 4 — Verify Data Was Saved

### Check the Run Status

After the queue completes (or after each run), the run list shows final states. A green `SUCCESS` state means data was saved. A red `FAILED` state means the run did not produce a saved analysis.

### Check the DVC Repository

Data is committed to your `repository_identifier` repository after each successful run. To verify:

```bash
cd ~/.pychron.<appname>/data/.dvc/<RepositoryName>/
git log --oneline -5
```

A healthy post-run git log looks like:

```
a1b2c3d <COLLECTION> J001-01A-01 (Ar40=3.45e-13)
e4f5g6h <COLLECTION> b-blank_air-01
```

Each commit is tagged with `<COLLECTION>` and includes the run identifier in the message.

The data files written for each analysis are:

```
analysis/<uuid>/
  analysis.json         ← run metadata, scripts, spectrometer config
  intercepts.json       ← isotope intercepts (fitted values at t=0)
  blanks.json           ← blank corrections applied
  baselines.json        ← baseline values
  icfactors.json        ← detector IC factors
  <uuid>.data.json      ← raw signal/baseline/sniff time-series blobs
extraction/<uuid>/
  extraction.json       ← extraction parameters and response data
```

### Check via the Analysis Browser

In pyExperiment or pyCrunch, open **Analysis → Analysis Browser**. Your newly run analyses should appear under the correct project, sample, and irradiation. If they do not appear, the database save failed — check the log at `~/.pychron.<appname>/logs/pychron.log`.

### Confirm Isotope Data

Select an analysis in the browser and open it. In the **Isotope Evolution** tab, you should see fitted signal curves for each active detector (Ar40, Ar39, Ar38, Ar37, Ar36). Flat baselines and decaying or stable signals are expected. An entirely flat signal means the run collected no gas — check the extraction script and the inlet valve configuration.

---

## Step 5 — What to Do If Something Goes Wrong

### Startup Tests Red

| Red test | First check | Guide |
|---|---|---|
| `test_database` | `pychron.log` for `OperationalError` | [DVC Failure Modes — Database Failures](../dvc/failure-modes#database-failures) |
| `test_dvc_fetch_meta` | `pychron.log` for `"Error opening meta repo"` | [DVC Failure Modes — GitHub/GitLab Unreachable](../dvc/failure-modes#github--gitlab-unreachable) |

Do not proceed until both are green.

### Hardware Not Responding

**Spectrometer connection fails:**
- Confirm Qtegra (Argus/Helix) or the NGX controller is powered and network-accessible
- Check host/port in **Preferences → Spectrometer**
- Check `~/.pychron.<appname>/setupfiles/devices/<spectrometer>.yaml` for correct IP

**Extraction line gauges show `???`:**
- The gauge controller device is not responding
- Check serial port or Ethernet settings in the device YAML file
- Try **Extraction Line → Test Connection** for each device

**Laser does not fire:**
- Check **Laser → Test Connection**
- Confirm interlock status (enable must be called in the extraction script before extract)
- Check beam diameter is non-zero

### DVC Not Writing

**Run completes as SUCCESS but no commit appears in the repository:**
1. Check `use_dvc_persistence` is `True` in **Preferences → Experiment → DVC**
2. Check `pychron.log` for `DVCPersister` errors
3. Confirm the repository exists on the git host — Pychron will not create a missing repository
4. Confirm SSH keys or PAT credentials are valid for the git host

**Push fails with a permission error:**
- The git credential stored in the macOS Keychain or SSH agent may have expired
- Run `git push` manually from the repository directory to diagnose

### Run Fails Pre-Run Check

If a run shows `INVALID` before it even starts:
- Right-click the run and choose **Test Scripts** to see the syntax error
- Confirm the script name exists in `<MetaRepo>/scripts/<type>/`
- Confirm `labnumber` exists in the database — check **Entry → Irradiation**

### Experiment Stops Mid-Queue

Check the **Experiment Log** panel for the reason. Common causes:
- A `CancelationConditional` fired (check `queue_conditionals_name` file)
- A fatal DVC save error (check `pychron.log`)
- User pressed the **Stop** button
- `end_after` was checked on a run that completed
