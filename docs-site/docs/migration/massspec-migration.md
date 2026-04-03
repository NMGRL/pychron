---
id: massspec-migration
title: MassSpec Migration Guide
sidebar_label: Migration Guide
sidebar_position: 2
---

# MassSpec Migration Guide

Step-by-step instructions for migrating a lab from MassSpec to Pychron. See the [Migration Overview](./massspec-overview) for architectural differences and strategy options before starting.

## Migration Tooling Status

| Tool | File | Status | Purpose |
|---|---|---|---|
| `MassSpecDatabaseAdapter` | `pychron/mass_spec/database/massspec_database_adapter.py` | ✓ Production | SQLAlchemy ORM adapter to the live MassSpec MySQL DB. Implements `IImportSource`. Requires MassSpec schema version ≥ 16.3. |
| `MassSpecReducedNode` | `pychron/pipeline/nodes/mass_spec_reduced.py` | ✓ Production | Transfers intercepts, baselines, blanks, IC factors, flux, and production ratios from the live MassSpec DB into DVC JSON. Primary automated migration path. |
| `get_irradiation_import_spec()` | `pychron/mass_spec/database/massspec_database_adapter.py:106` | ✓ Production | Extracts complete irradiation structure (levels, positions, J values, production ratios, chronology, samples, projects, PIs) for import via `DVCIrradiationImporterModel`. |
| `MassSpecFluxNode` | `pychron/pipeline/nodes/mass_spec_reduced.py` | ⚠ Partial | Transfers J values and level structure. The `IrradiationPositionTbl` SQL side is incomplete — TODO at line 71 may cause missing positions for some irradiation configurations. |
| `MassSpecReverter` | `pychron/entry/mass_spec_reverter.py` | ⚠ Partial | Reverse direction: writes Pychron data back into a MassSpec database for labs running both systems in parallel. Batch revert by labnumber range is not implemented. |
| `MassSpecDBSource` | `pychron/data_mapper/sources/mass_spec_source.py` | ✗ Stub | Intended as a DataMapper bridge between MassSpec and Pychron acquisition formats. Both `load_analyses()` and `load_analysis()` are `pass`. Not usable. |

:::warning `MassSpecDBSource` is a stub
`MassSpecDBSource` looks like a complete migration tool from the class name and interface, but both of its public methods are empty (`pass`). Do not include it in any migration pipeline — it will silently do nothing. Use `MassSpecReducedNode` for analysis data transfer and `get_irradiation_import_spec()` for irradiation structure.
:::

## What `MassSpecReducedNode` Does

When the node runs for each analysis in the pipeline, it performs these steps in order:

1. **Locate the analysis in MassSpec** — calls `MassSpecRecaller.find_analysis(identifier, aliquot, step)` using the Pychron labnumber (= MassSpec labnumber), aliquot integer, and step letter. Fails silently if not found.
2. **Transfer isotope intercepts** — reads `IsotopeResultsTable.Intercept` and `InterceptEr`; writes to each isotope via `iso.set_uvalue(nominal, error)`.
3. **Transfer baselines** — decodes `BaselinesChangeableItemsTable.InfoBlob` binary blob using `_extract_average_baseline()`; writes to `iso.baseline.set_uvalue()`.
4. **Transfer blanks as frozen values** — reads `IsotopeResultsTable.Bkgd` and `BkgdEr`; calls `set_temporary_blank(iso, ufloat, "mass_spec_reduced")`. These values are flagged as `"mass_spec_reduced"` and will **not** be overwritten by `FitBlanksNode` in subsequent pipeline runs unless the analyst explicitly removes the flag.
5. **Transfer IC factors** — reads `DetectorTable.ICFactor` and `ICFactorEr`; calls `set_temporary_uic_factor()`. Stored as a frozen snapshot, not linked to any live IC factor run.
6. **Write flux and production files** — writes `<IRRADNAME>.json` flux files and `<IRRAD>.<LEVEL>.production.json` production files to the data repository.
7. **Commit** — stages all modified files, commits under the `<MASS SPEC REDUCED>` tag, and optionally pushes to the remote.

:::warning Blank handling: frozen, not interpolated
Blanks imported from MassSpec are written as fixed values with the `"mass_spec_reduced"` source flag. They are not blank analyses stored in the system and will not participate in Pychron's temporal blank interpolation. If you later run `FitBlanksNode` on imported analyses without first removing the frozen flag, the pipeline will skip those analyses and leave the MassSpec blank values in place. This is intentional — it preserves the original MassSpec reduction — but it means imported analyses cannot benefit from Pychron's improved blank interpolation without manual intervention.
:::

---

## Pre-Migration Checklist

Complete every item before starting the migration steps.

**Pychron setup:**
- [ ] Pychron DVC fully configured (see [DVC First Run](../dvc/first-run))
- [ ] Working MySQL database for Pychron (`pychronmeta`)
- [ ] MetaRepo created and cloned
- [ ] GitHub/GitLab organization and auth configured
- [ ] `use_dvc_persistence = true` in **Preferences → Experiment → DVC**

**MassSpec database:**
- [ ] MassSpec MySQL instance accessible from the Pychron workstation
- [ ] MassSpec schema version ≥ 16.3 (check `VersionTable` or ask your MassSpec admin)
- [ ] Read-only MySQL credentials for the MassSpec DB available
- [ ] MassSpec connection configured in **Preferences → MassSpec** (host, port, database, username, password)

**Data inventory:**
- [ ] List of irradiation names to import noted
- [ ] Known MassSpec labnumber ranges recorded
- [ ] Backup of MassSpec database taken before starting

---

## Migration Steps

### Step 1 — Verify MassSpec Database Compatibility

Confirm the MassSpec schema version is ≥ 16.3. `MassSpecDatabaseAdapter` checks this at connection time and will refuse to connect if the version is too old.

Connect to the MassSpec MySQL instance and check:

```sql
SELECT * FROM VersionTable ORDER BY ID DESC LIMIT 1;
```

If the version is below 16.3, the MassSpec database must be upgraded before migration can proceed. Contact your MassSpec administrator.

### Step 2 — Configure the MassSpec Connection in Pychron

In **Preferences → MassSpec**, enter the connection details for the live MassSpec MySQL database:

- **Host** — hostname or IP of the MassSpec MySQL server
- **Port** — default `3306`
- **Database** — typically `massspecdata` or the lab's database name
- **Username / Password** — read-only credentials recommended

Test the connection with the **Test** button. If the test fails, check that the Pychron workstation can reach the MassSpec host on port 3306, and that the credentials have `SELECT` privileges on the database.

### Step 3 — Import Irradiation Structure

Import all irradiation levels, positions, flux values, production ratios, and sample records from MassSpec into the Pychron MetaRepo and database.

In pyExperiment or pyCrunch, go to **Entry → Import → MassSpec Irradiation** and select the irradiation(s) to import. This calls `MassSpecDatabaseAdapter.get_irradiation_import_spec(irrad_name)` and passes the result to `DVCIrradiationImporterModel.do_import()`.

**What transfers in this step:**

| Data | MassSpec source table | Notes |
|---|---|---|
| Irradiation levels and holder geometry | `IrradiationLevelTable`, `SampleHolder` | Holder geometry (hole positions) must exist in MetaRepo already |
| All 18 production ratio keys + errors | `IrradiationProductionTable` | Full set: Ca/K/Cl ratios and multipliers |
| Irradiation chronology | `IrradiationChronologyTable.StartTime/EndTime` | Reactor power hardcoded to `1.0` |
| Samples, materials, projects, PIs | `SampleTable`, `ProjectTable`, `PrincipalInvestigatorTable` | |
| Position numbers and J values | `IrradiationPositionTable.HoleNumber`, `J/JEr` | |
| Position notes and weights | `IrradiationPositionTable.Note`, `Weight` | |

**What does NOT transfer:**

- Irradiation level z-coordinates (not in MassSpec schema)
- Reactor power — hardcoded to `1.0` in `get_irradiation_import_spec()` line 125; must be set manually afterward
- Level notes

### Step 4 — Scaffold Analysis Records (Historical Data)

`MassSpecReducedNode` requires analysis records to already exist in the Pychron DVC store — UUIDs assigned, JSON file structure committed — before it can write imported data into them.

**For new data (going forward):** Run acquisitions normally in pyExperiment. Analysis scaffolding happens automatically during acquisition.

**For historical data:** There is no automated tool to create Pychron analysis records from MassSpec run history. This is the primary gap in the migration path. Options:

- Import historical analyses by re-running a dummy experiment queue that references the correct labnumbers, repositories, and run identifiers. This creates the file scaffolding without acquiring new data.
- Work with the NMGRL community on a batch-scaffolding tool (not yet available in `main`).

### Step 5 — Run `MassSpecReducedNode` in pyCrunch

In pyCrunch, build a new pipeline and add `MassSpecReducedNode`. Configure the MassSpec connection (same credentials from Step 2). Select the analyses to process — typically all analyses from one irradiation or experiment batch.

Run the pipeline. For each matched analysis, the node writes frozen intercepts, blanks, baselines, and IC factors to the DVC JSON files and commits them under the `<MASS SPEC REDUCED>` tag.

Check the pipeline output for any analyses that failed to match (the node skips analyses it cannot find in MassSpec without raising an error — watch for a lower-than-expected analysis count in the output).

### Step 6 — Run `MassSpecFluxNode` (if J values need updating)

If J values were updated in MassSpec after the irradiation import in Step 3, run `MassSpecFluxNode` to sync the current values. Note the known partial implementation: the `IrradiationPositionTbl` SQL side has a TODO at line 71 that may cause some positions to be skipped. Verify J values manually for any positions flagged in the output log.

### Step 7 — Verify and Configure for Forward Acquisition

After import, verify a sample of imported analyses in pyCrunch:

- Load the data repository and confirm analyses appear in the browser
- Run an age computation pipeline node on a known sample and confirm the age matches the MassSpec result
- Check that status tags (`ok`/`omit`/`invalid`) transferred correctly from MassSpec `StatusLevel` values

Then configure pyExperiment for new acquisitions:
- Create experiment queues with `repository_identifier` pointing to the correct GitHub/GitLab repo
- Confirm `use_dvc_persistence = true`
- Run a test blank and unknown pair to verify the full DVC write/commit/push cycle works

---

## What Transfers Cleanly

| Data | MassSpec source | Transfer mechanism |
|---|---|---|
| Isotope intercepts | `IsotopeResultsTable.Intercept/InterceptEr` | `MassSpecReducedNode` → `iso.set_uvalue()` |
| Blank values (frozen) | `IsotopeResultsTable.Bkgd/BkgdEr` | `set_temporary_blank(..., "mass_spec_reduced")` |
| Baselines | `BaselinesChangeableItemsTable.InfoBlob` (binary blob) | `_extract_average_baseline()` → `iso.baseline.set_uvalue()` |
| IC factors (frozen) | `DetectorTable.ICFactor/ICFactorEr` | `set_temporary_uic_factor()` |
| J values | `IrradiationPositionTable.J/JEr` | `get_irradiation_import_spec()` direct copy |
| All 18 production ratio keys | `IrradiationProductionTable` | Direct copy |
| Irradiation chronology | `IrradiationChronologyTable.StartTime/EndTime` | Direct copy |
| Samples, projects, PIs | `SampleTable`, `ProjectTable` | Via import spec |
| Fit types | `FittypeTable.Label` (lowercased) | Transferred to `iso.fit` |
| Analysis comments | `AnalysesChangeableItemsTable.Comment` | Written as `comment` field in analysis JSON |
| Status/omit flags | `AnalysesChangeableItemsTable.StatusLevel` (0/1/2) | Mapped: `0→ok`, `1→omit`, `2→invalid` |
| Peak fit point count | `PDPTable.PDPBlob` (`fn` field only) | Extracted from blob; used in fit setup |

---

## What Is Permanently Lost

These data exist in MassSpec but have no equivalent in Pychron's data model and cannot be recovered after migration.

| Data | MassSpec source | Why it's lost |
|---|---|---|
| Peak time series (raw signals) | `PeakTimeTable.PeakTimeBlob` | Binary blobs are not converted to Pychron acquisition JSON; re-reduction from first principles is impossible |
| Full peak detection parameters | `PDPTable.PDPBlob` | Only `fn` (fit point count) is extracted; all other parameters are discarded |
| Decay constants per analysis | `PreferencesTable.Lambda40Kepsilon/Beta/...` | Read into memory during `MassSpecAnalysis._sync()` but **not written to DVC JSON** |
| DR session history | `DataReductionSessionTable`, `LoginSessionTable` | Pychron uses git history; original session timestamps are not transferred |
| Fit version history | `IsotopeResultsTable.Counter` (tracks each re-fit) | Only the most recent fit (`dbiso.results[-1]`) is transferred |
| Sample salinity and temperature | `SampleTable.Salinity/Temperature` | No equivalent columns in Pychron `SampleTbl` |
| Analysis position x/y/z | `AnalysisPositionTable.X/Y/Z` | Not accessed in any migration path |
| Reactor power per irradiation | Not stored in MassSpec schema | `get_irradiation_import_spec()` hardcodes `1.0` |
| Run script text | `RunScriptTable.RunScriptText` | Not imported; must be recreated as PyScript `.py` files |

---

## What Requires Manual Re-Entry

These data are not transferred automatically and must be entered by hand after migration.

| Data | Where to enter it in Pychron | Notes |
|---|---|---|
| Reactor power per irradiation | **Entry → Irradiation → Edit Chronology** | Set after import; `1.0` placeholder is the default |
| Irradiation level z-coordinates | **Entry → Irradiation → Edit Level** | Not in MassSpec schema; enter if known |
| Level notes | **Entry → Irradiation → Edit Level** | Not transferred |
| Run scripts | MetaRepo `scripts/` directory | Recreate MassSpec run scripts as PyScript `.py` files; see [PyScripts Overview](../pyscripts/overview) |
| Irradiation holder geometry | MetaRepo `irradiation_holders/` | Must exist before import; default 24-spoke geometry is created automatically |
| New-style IC factor runs | pyExperiment acquisition | IC factors imported as frozen snapshots; new ones must be acquired in Pychron |

---

## Workflow Differences After Migration

### Experiment Setup

| Task | MassSpec | Pychron |
|---|---|---|
| Create a run queue | Fill in an Excel spreadsheet or GUI form | Build an experiment queue in pyExperiment; assign a `repository_identifier` (becomes a GitHub/GitLab repo) |
| Assign samples to positions | Link `SampleID` in database | Assign loaded positions in **Entry → Loads** |
| Schedule blank runs | Manual placement in queue | Follow the standard blank-unknown-blank bracketing pattern; Pychron interpolates temporally |
| Run script assignment | Select from `RunScriptTable` dropdown | Select a PyScript filename from the MetaRepo `scripts/` directory |
| Air/cocktail assignments | Manual flag per run | Set `analysis_type` field in experiment queue row |

### Data Reduction

| Task | MassSpec | Pychron |
|---|---|---|
| Re-fit isotope evolution | Edit intercept in GUI → new `Counter` row in DB | `IsoEvolutionNode` in pipeline → new git commit; prior fit preserved in history |
| Blank correction | Single `Bkgd` value per isotope applied globally | `FitBlanksNode` — temporal interpolation across blank runs in the queue |
| IC factor correction | Global value from `DetectorTable` applied automatically | `FitICFactorNode` in pipeline; per-analysis JSON, historically tracked |
| Flag / omit an analysis | Set `StatusLevel = 1` or `2` | **Tag** action in the pipeline browser: `ok`, `omit`, `invalid` |
| Compute ages | Automatic after re-fit | `InverseIsochronNode` or `IsochronNode` in pipeline |
| Export age table | Built-in export dialog | `TableNode` in pipeline |
| Plot ideogram | Auto-generated on reduction | `IdeogramNode` in pipeline |
| Share results | Send DB dump or Excel export | Push data repo to GitHub; collaborators clone |
