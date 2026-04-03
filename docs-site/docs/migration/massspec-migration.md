---
id: massspec-migration
title: MassSpec Migration Guide
sidebar_label: Migration Guide
sidebar_position: 2
---

# MassSpec Migration Guide

This guide covers the practical steps for migrating a lab from MassSpec to Pychron, including which data transfers automatically, which requires manual work, and what is permanently lost in the migration. See the [Migration Overview](./massspec-overview) for the architectural comparison.

## Migration tooling reference

| Tool | File | Status | What it does |
|---|---|---|---|
| `MassSpecReducedNode` | `pychron/pipeline/nodes/mass_spec_reduced.py` | ✅ Production-ready | Transfers intercepts, baselines, blanks, IC factors, flux, production from a live MassSpec DB into DVC JSON |
| `MassSpecFluxNode` | `pychron/pipeline/nodes/mass_spec_reduced.py` | ⚠️ Partial | Transfers J values and level structure; `IrradiationPositionTbl` SQL side incomplete (TODO at line 71) |
| `get_irradiation_import_spec()` | `pychron/mass_spec/database/massspec_database_adapter.py:106` | ✅ Production-ready | Extracts full irradiation structure (levels, positions, production ratios, chronology, samples, projects, PIs) |
| `MassSpecDBSource` | `pychron/data_mapper/sources/mass_spec_source.py` | 🚧 Stub | Both methods are `pass` — not usable |
| `MassSpecReverter` | `pychron/entry/mass_spec_reverter.py` | ⚠️ Partial | Reverse direction: writes Pychron data back to MassSpec; batch revert by labnumber is unimplemented |

## Step-by-step migration path

### Step 1: Set up Pychron DVC

Complete the [DVC First Run](../dvc/first-run) setup. You need a working MySQL database, MetaRepo, and GitHub/GitLab organization before importing anything.

### Step 2: Import irradiations

Use `MassSpecDatabaseAdapter.get_irradiation_import_spec(irrad_name)` to extract irradiation structure, then import via `DVCIrradiationImporterModel.do_import()`. This can be triggered from **Entry → Import → MassSpec Irradiation**.

**What transfers:**
- Irradiation levels and holder names (`SampleHolder`)
- All 18 production ratio keys: `Ca3637`, `Ca3937`, `K4039`, `P36Cl38Cl`, `Ca3837`, `K3839`, `K3739`, `ClOverKMultiplier`, `CaOverKMultiplier` (+ errors for each)
- Irradiation chronology (start time, end time — power hardcoded to `1.0`)
- Sample names, material, project, principal investigator
- Position numbers (`HoleNumber`), J values (`J`/`JEr`), notes, weights

**What does NOT transfer:**
- Irradiation level z-coordinates (not in MassSpec schema)
- Irradiation reactor power — hardcoded to `1.0` in `get_irradiation_import_spec()` (line 125)
- Level notes

### Step 3: Acquire new data in Pychron (or scaffold analysis records)

`MassSpecReducedNode` requires analyses to already exist in the Pychron DVC store (UUID assigned, JSON scaffolding committed). For **new data**, run acquisitions normally in pyExperiment. For **historical data**, there is no automated tool to scaffold analysis records from MassSpec — this is the primary gap in the migration path.

### Step 4: Run `MassSpecReducedNode`

In pyCrunch, build a pipeline that includes `MassSpecReducedNode`. Configure it with the MassSpec MySQL connection (set in **Preferences → MassSpec**). When run, for each analysis the node:

1. Calls `MassSpecRecaller.find_analysis(identifier, aliquot, step)` against the live MassSpec DB
2. Transfers isotope intercepts (`IsotopeResultsTable.Intercept`/`InterceptEr`)
3. Transfers baselines (decoded from `BaselinesChangeableItemsTable.InfoBlob` binary blob)
4. Transfers blank values (`IsotopeResultsTable.Bkgd`/`BkgdEr`) as frozen blanks — they will **not** be re-interpolated by Pychron's `FitBlanksNode`
5. Transfers IC factors (`DetectorTable.ICFactor`/`ICFactorEr`) as a frozen snapshot
6. Writes frozen flux files (`<IRRADNAME>.json`) and production files (`<IRRAD>.<LEVEL>.production.json`) to the data repo
7. Commits all changes under the `<MASS SPEC REDUCED>` tag and optionally pushes

---

## What transfers cleanly

| Data | MassSpec source | Transfer mechanism |
|---|---|---|
| Isotope intercepts | `IsotopeResultsTable.Intercept/InterceptEr` | `MassSpecReducedNode` → `iso.set_uvalue()` |
| Blank values | `IsotopeResultsTable.Bkgd/BkgdEr` | `set_temporary_blank(..., "mass_spec_reduced")` |
| Baselines | `BaselinesChangeableItemsTable.InfoBlob` (binary) | `_extract_average_baseline()` → `iso.baseline.set_uvalue()` |
| IC factors | `DetectorTable.ICFactor/ICFactorEr` | `set_temporary_uic_factor()` |
| J values | `IrradiationPositionTable.J/JEr` | Direct copy via `get_irradiation_import_spec()` |
| All production ratios | `IrradiationProductionTable` (18 fields) | Direct copy |
| Irradiation chronology | `IrradiationChronologyTable.StartTime/EndTime` | Direct copy |
| Samples, projects, PIs | `SampleTable`, `ProjectTable` | Via import spec |
| Comments | `AnalysesChangeableItemsTable.Comment` | Transferred as `comment` field in analysis JSON |
| Status tags | `AnalysesChangeableItemsTable.StatusLevel` (0/1/2) | Mapped: `0→ok`, `1→omit`, `2→invalid` |
| Fit types | `FittypeTable.Label` (lowercased) | Transferred to `iso.fit` |

## What is permanently lost

| Data | MassSpec source | Why it's lost |
|---|---|---|
| Sample salinity and temperature | `SampleTable.Salinity`, `SampleTable.Temperature` | No equivalent columns in Pychron's `SampleTbl` |
| Irradiation reactor power | Not stored in MassSpec schema | `get_irradiation_import_spec()` hardcodes `1.0` |
| DR session history | `DataReductionSessionTable`, `LoginSessionTable` | Pychron uses git history instead; original session timestamps are not transferred |
| Fit version history | `IsotopeResultsTable.Counter` (tracks each re-fit) | Only the most recent fit is transferred (`dbiso.results[-1]`) |
| Run scripts | `RunScriptTable.RunScriptText` | Not imported; must be recreated as PyScripts |
| Peak time series (raw signals) | `PeakTimeTable.PeakTimeBlob` | Binary blobs are not converted to Pychron acquisition JSON |
| Full peak detection parameters | `PDPTable.PDPBlob` | Only fit point count (`fn`) is extracted; full params discarded |
| Decay constants per analysis | `PreferencesTable.Lambda40Kepsilon/Beta/...` | Read into memory during `MassSpecAnalysis._sync()` but **not written to DVC JSON** |
| Analysis position x/y/z | `AnalysisPositionTable.X/Y/Z` | Not accessed in any migration path |

## Day-to-day workflow changes after migration

| Task | MassSpec | Pychron |
|---|---|---|
| Start a new experiment | Fill in Excel queue or GUI | Create experiment queue in pyExperiment; assign a `repository_identifier` (becomes a GitHub repo) |
| Blank assignment | Select one blank manually per analysis | `FitBlanksNode` interpolates temporally across blank runs |
| IC factor correction | Global value from `DetectorTable` applied automatically | `FitICFactorNode` in pipeline; per-analysis JSON, historically tracked |
| Re-fit isotopes | Edit in MassSpec GUI → new `Counter` row | `IsoEvolutionNode` in pipeline → new git commit |
| Flag/omit an analysis | Set `StatusLevel` | Set tag (`ok`/`omit`/`invalid`) via **Tag** action in pipeline |
| Export age table | Built-in export | `TableNode` in pipeline |
| Ideogram | Auto-generated | `IdeogramNode` in pipeline |
