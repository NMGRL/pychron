---
id: data-reduction
title: Data Reduction Walkthrough
sidebar_label: Data Reduction
sidebar_position: 1
---

# Data Reduction Walkthrough

This walkthrough covers reducing a set of Ar-Ar analyses in pyCrunch — from loading a data repository through blank correction, IC factor fitting, age calculation, and exporting a publication-ready age table and ideogram figure. It assumes DVC is configured and at least one experiment has been run and saved.

## What the Pipeline Is

The pyCrunch pipeline is a **directed acyclic graph (DAG)** of processing nodes. Each node reads from a shared `EngineState` object, does its work, and writes results back to state. Nodes run sequentially in the order they appear in the pipeline. Any node can set `state.veto` to pause execution and present a review UI before continuing.

```
EngineState
  .unknowns   ─── list of Analysis objects
  .references ─── list of reference (blank/air) Analysis objects
  .editors    ─── list of figure/table editors opened by nodes
  .modified   ─── True if any analyses were changed
```

Standard pipelines are defined in `pychron/pipeline/pipeline_defaults.py` as YAML templates. You select a template from the pipeline menu and it instantiates the node chain. You can also build a custom pipeline by adding and reordering nodes manually.

---

## Loading pyCrunch

Launch pyCrunch:

```bash
uv run pychron --app pipeline
```

On first launch confirm:
- `test_database` startup test is green
- `test_dvc_fetch_meta` startup test is green

The main window shows the **Pipeline** panel on the left (the node chain) and the **Browser** panel for selecting analyses.

---

## The Standard Reduction Sequence

For a typical Ar-Ar dataset, the complete reduction sequence is:

```
UnknownNode
  → FindBlanksNode
  → ReferenceNode (blanks)
  → FitIsotopeEvolutionNode
  → IsotopeEvolutionPersistNode
  → FindReferencesNode (air)
  → ReferenceNode (air)
  → FitICFactorNode
  → ICFactorPersistNode
  → FitBlanksNode
  → BlanksPersistNode
  → GroupingNode
  → SubGroupingNode
  → IdeogramNode
  → InverseIsochronNode
  → SubGroupAnalysisTableNode
  → XLSXAnalysisTablePersistNode
```

In practice you run these as **separate pipeline templates** (ISOEVO, BLANKS, ICFACTOR, then ARAR_IDEO / ANALYSIS_TABLE), not as one giant chain. The pipeline saves results to DVC after each stage, so each template picks up where the last left off.

---

## Node Reference

### `UnknownNode` — Load Analyses

**Template name:** `Unknowns`

Opens the analysis browser so you can select which analyses to reduce. You can filter by:
- Project, sample, material
- Irradiation, level
- Run date range
- Analysis type (unknown, blank, air, etc.)

Selected analyses become `state.unknowns`. All subsequent nodes operate on this list.

**Shortcuts available:**
- **Last N Analyses** — loads the N most recently acquired analyses
- **Last N Hours** — loads everything from the past N hours

:::tip Load blanks and airs alongside unknowns
Some pipelines (BLANKS, ICFACTOR) need reference analyses in `state.references`. The `FindBlanksNode` and `FindReferencesNode` locate these automatically from the database based on run sequence proximity — you don't need to add them manually to `state.unknowns`.
:::

---

### `FitIsotopeEvolutionNode` — Fit Signal Regressions

**Pipeline template:** `ISOEVO`

```
UnknownNode → FitIsotopeEvolutionNode → ReviewNode → IsotopeEvolutionPersistNode → PushNode
```

Fits the regression curve for each isotope's time-series data (the decay/growth curve collected during `multicollect`). The intercept at t=0 is the raw signal value used in all downstream calculations.

**Configuration (right-click node → Configure):**
- Select which isotopes to fit (Ar40, Ar39, Ar38, Ar37, Ar36, and baselines)
- Analysis types to include (`unknown`, `blank`, `air`, etc.)
- Goodness thresholds that flag low-quality fits:

| Threshold parameter | What it checks |
|---|---|
| `goodness_threshold` | Intercept error % — flag if uncertainty is too large |
| `signal_to_baseline_goodness` | Signal-to-baseline ratio — flag if signal is too small |
| `signal_to_blank_goodness` | Signal-to-blank ratio — flag if gas release is negligible |
| `slope_goodness` | Flag if signal shows unexpected slope behavior |
| `rsquared_goodness` | Fit R² — flag poor regression quality |
| `smart_filter` | Advanced filter based on fit coefficients |

After this node runs, an **IsoEvolutionResultsEditor** opens showing each analysis with color-coded fit quality. Red = failed goodness check. Double-click any analysis to see its raw time-series data and regression curve.

The `ReviewNode` that follows pauses the pipeline — you inspect the fits, fix any poor fits by right-clicking and changing the fit type (Linear, Parabolic, Cubic, Exponential, Average), then click **Accept** to continue.

`IsotopeEvolutionPersistNode` commits the fit results to the DVC repository with tag `<ISOEVO>`.

---

### `FindBlanksNode` + `FitBlanksNode` — Blank Correction

**Pipeline template:** `BLANKS`

```
UnknownNode → FindBlanksNode(threshold=10) → ReferenceNode → FitBlanksNode → ReviewNode → BlanksPersistNode → PushNode
```

**`FindBlanksNode`** searches the run sequence for blank analyses that bracket each unknown. The `threshold` parameter (default 10) controls how many runs away from the unknown Pychron will search. It populates `state.references` with the found blanks.

**`FitBlanksNode`** fits a correction curve through the blank analyses for each isotope. The fit is an interpolating regression — blanks between two unknowns are interpolated; blanks at the edges are extrapolated with a flat (average) fit.

**Configuration:**
- Select which isotopes to correct
- Choose which blank types to use (`blank_air`, `blank_cocktail`, `blank_unknown`)
- Set fit type per isotope (Linear is typical; use Average if few blanks)

The **BlanksEditor** that opens shows the blank fit curve with all blank analyses plotted. The x-axis is run sequence number (not time). Drag individual blank points to mark them as excluded if they are outliers.

After **Review** and **Accept**, `BlanksPersistNode` commits the blank fits to DVC with tag `<BLANKS>`.

:::warning Blank fitting requires brackets
If an unknown has no blanks within the threshold distance, it receives no blank correction and its ages will be systematically too old. Always check that the BlanksEditor shows corrections applied to all unknowns (shown as interpolated points on the fit curve).
:::

---

### `FindReferencesNode` + `FitICFactorNode` — IC Factor

**Pipeline template:** `ICFACTOR`

```
UnknownNode → FindReferencesNode(threshold=10, analysis_types=[air]) → ReferenceNode → FitICFactorNode → ReviewNode → ICFactorPersistNode → PushNode
```

**`FindReferencesNode`** locates air analyses near the unknowns (within `threshold` runs). Air analyses are used to determine the detector intercalibration factor (IC factor) — the relative efficiency of each detector pair.

**`FitICFactorNode`** computes the IC factor from the Ar40/Ar36 ratio in air analyses (expected atmospheric ratio = 298.56).

**Key configuration options:**
- `numerator` / `denominator` — isotope pair (default `Ar40` / `Ar36`)
- `standard_ratio` — expected ratio value (default 298.56 for atmospheric)
- `analysis_type` — which reference type to use (`air` or `cocktail`)
- `use_discrimination` — apply detector discrimination values

The **IntercalibrationFactorEditor** shows the IC factor vs run sequence. Drift in IC factor over time is common and expected — a linear or parabolic fit is usually appropriate.

`ICFactorPersistNode` commits the IC factors to DVC with tag `<ICFactor>`.

---

### `GroupingNode` — Organize for Plotting

**Template name:** `Grouping`

Assigns `group_id`, `graph_id`, or `tab_id` to each analysis so that figure nodes know how to arrange them. Common grouping keys:

| `by_key` | Groups by |
|---|---|
| `Identifier` | One group per irradiation position (most common for step-heat) |
| `Sample` | One group per sample name |
| `Aliquot` | One group per aliquot number |
| `No Grouping` | All analyses in a single group |

For a simple fusion dataset, `Sample` grouping is typical. For step-heat spectra, `Identifier` is required so each step-heat sequence plots as one spectrum.

---

### `SubGroupingNode` — Define Weighted Means

Sets up subgroups within main groups for weighted mean age calculation. Default key is `Aliquot`. The node stores preferred value types (weighted mean, MSEM, SD) for age, K/Ca, and other quantities that the table nodes use to compute group ages.

---

### `IdeogramNode` — Age Probability Distribution

**Template:** `ARAR_IDEO`

```
UnknownNode → ArArCalculationsNode → GroupingNode → IdeogramNode
```

Produces a relative probability (ideogram) plot. Each analysis contributes a Gaussian to the summed probability curve. Groups defined by `GroupingNode` appear as separate series or separate panels depending on the `graph_id`.

**`ArArCalculationsNode`** (insert before `IdeogramNode` for Ar-Ar data) sets calculation options:
- Decay constants (Steiger & Jäger, Min et al., Renne et al.)
- Atmospheric Ar40/Ar36 ratio
- Interference correction factors (if not loaded from DVC)

The `IdeogramNode` opens an interactive figure editor. You can:
- Zoom, pan, and export the figure
- Click individual analyses to highlight them
- Right-click analyses to tag/omit (see [Tagging and Omitting](#tagging-and-omitting-analyses))
- Export to PDF via **File → Save PDF**

---

### `InverseIsochronNode` — Isochron

**Template:** `INVERSE_ISOCHRON`

```
UnknownNode → GroupingNode → InverseIsochronNode
```

Plots Ar39/Ar40 vs Ar36/Ar40 (inverse isochron). The x-intercept gives the trapped Ar40/Ar36 component; the y-intercept gives the age. Use this to test whether initial Ar40 is atmospheric.

The isochron age and MSWD are reported in the figure legend. The `InverseIsochronEditor` supports point selection, exclusion, and regression type selection (York, OLS, etc.).

---

### `SubGroupAnalysisTableNode` — Age Table

**Template:** `ANALYSIS_TABLE`

```
UnknownNode → GroupingNode → SubGroupingNode → SubGroupAnalysisTableNode → ReviewNode → XLSXAnalysisTablePersistNode
```

Produces a table of analyses with one row per analysis and summary rows per subgroup (weighted mean age, MSWD, K/Ca, etc.).

Default columns:

| Column | Description |
|---|---|
| Status | OK / skip / omit flag |
| Name | Run identifier |
| Sample | Sample name |
| Identifier | Irradiation position |
| Material | Sample material |
| Irradiation | Irradiation name and level |
| Age Kind | Weighted mean / plateau / etc. |
| Age | Age value |
| Age Error | Age uncertainty |
| MSWD | Mean square weighted deviation |
| K/Ca | Potassium to calcium ratio |
| N | Number of analyses in subgroup |

**`XLSXAnalysisTablePersistNode`** exports the table to an Excel file in `~/.pychron.<appname>/tables/`.

---

## Tagging and Omitting Analyses

Any analysis can be tagged to control whether it is included in calculations and figures.

**To tag an analysis:**
- In any figure editor, right-click an analysis point → **Tag**
- In the Analysis Browser, select analyses → right-click → **Tag**

**Available tags:**
- `ok` — include (default)
- `skip` — exclude from plots and calculations
- `omit` — exclude from calculations but show in figure as a different symbol

The `FilterNode` can automate tagging based on criteria (age range, MSWD, extract value, etc.):

```
UnknownNode → FilterNode(attribute=age, comparator=>, criterion=10000) → IdeogramNode
```

This passes only analyses older than 10,000 years to the ideogram.

Tags are saved to DVC via `DVCPersistNode` and persist across sessions. The `skip_meaning` preference (at `pychron.pipeline.skip_meaning`) controls which nodes respect the skip tag.

---

## Exporting Results

### Export an Age Table (Excel)

Run the `ANALYSIS_TABLE` template:

1. Load unknowns with `UnknownNode`
2. Run through `GroupingNode` → `SubGroupingNode` → `SubGroupAnalysisTableNode`
3. Review the table in the `SubGroupAgeEditor`
4. Click **Accept** — `XLSXAnalysisTablePersistNode` writes `<tablename>.xlsx` to `~/.pychron.<appname>/tables/`

### Export a Figure (PDF)

Any figure editor supports direct PDF export:
- **File → Save PDF** in the figure editor toolbar
- Or add a `PDFFigureNode` at the end of the pipeline — it saves all open figure editors to PDF automatically on run

```
UnknownNode → GroupingNode → IdeogramNode → PDFFigureNode
```

`PDFFigureNode` saves to the directory set in its `root` parameter (default: `~/.pychron.<appname>/figures/`).

### Export Raw Data (CSV)

Use the `CSV_ANALYSES_EXPORT` template:

```
UnknownNode → CSVAnalysesExportNode
```

Configure `delimiter` (comma, tab, colon, semicolon) and `pathname` in the node dialog. The file is written to `~/.pychron.<appname>/csv/`.

For raw time-series signal data:

```
UnknownNode → CSVRawDataExportNode
```

This exports equilibration, signal, and baseline segments as separate sections in the CSV, with counter, time, and intensity columns for each selected isotope.

---

## Custom Pipelines

You can assemble a custom pipeline by adding nodes one at a time:

1. In the Pipeline panel, click **+** (Add Node)
2. Choose a node from the list
3. Drag to reorder
4. Right-click any node to configure it or remove it

Save a custom pipeline as a template via **Pipeline → Save Template**. Templates are stored as YAML files in `~/.pychron.<appname>/templates/pipeline/` and appear in the pipeline menu on next launch.

---

## Troubleshooting

### Analyses load but ages are all wrong

Check the reduction stages in order:
1. `FitIsotopeEvolutionNode` — open an analysis and confirm the isotope evolution fits look reasonable (not flat, not noisy)
2. `FitBlanksNode` — confirm blanks are applied (blank-corrected intercepts should differ from raw)
3. `FitICFactorNode` — confirm IC factors are applied and close to 1.0 for the primary detector pair

### "No analyses found" in `FindBlanksNode`

- The `threshold` is too small — increase it (default 10 means search up to 10 runs before/after each unknown)
- No blank analyses exist in the database for this run period — check in Analysis Browser that blanks were acquired
- The blank analysis type doesn't match — check `analysis_type` filter in `FindBlanksNode` configuration

### Figures open empty

- `GroupingNode` is missing or placed after the figure node — it must come before
- All analyses are tagged `skip` — check Analysis Browser
- The `use_plotting` option on the figure node is `False` — right-click and configure

### MSWD is very large

Large MSWD (> 2.5 for N > 10) indicates excess scatter beyond analytical uncertainty. This is a geological result, not a software error. Use an isochron or spectrum to investigate heterogeneous components.
