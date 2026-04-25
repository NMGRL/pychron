---
id: massspec-overview
title: Migrating from MassSpec
sidebar_label: Overview
sidebar_position: 1
---

# Migrating from MassSpec

MassSpec and Pychron solve the same problem — automating Ar-Ar geochronology workflows — but with fundamentally different architectural assumptions. Understanding these differences before planning a migration determines what data can be transferred automatically, what requires manual re-entry, and how day-to-day lab operations will change after the switch.

## The Honest Summary

**MassSpec** is a single centralized MySQL database. Every analysis, reduction result, blank value, baseline, irradiation record, sample, and instrument configuration lives as rows in one database on one machine. Backups are a database dump. Sharing data with collaborators means giving them database access.

**Pychron** uses three distributed storage layers: a SQL index, a MetaRepo (git-backed irradiation and instrument metadata), and one git repository per experiment batch (individual JSON files per analysis). There is full git history for every reduction change. Sharing data means pushing to GitHub. Migration is not a simple database-to-database copy — Pychron's DVC system expects data in a specific file and directory structure that MassSpec never produced.

## Key Architectural Differences

| Aspect | MassSpec | Pychron |
|---|---|---|
| **Primary data store** | Single MySQL database | Per-analysis JSON files in git + SQL index |
| **Version history** | `Counter` column tracks re-fits; overwrites prior values | Full git commit history; every reduction is a commit |
| **Blanks** | Single `Bkgd`/`BkgdEr` value per isotope stored in `IsotopeResultsTable` | Full blank runs stored as analyses; temporal interpolation via `FitBlanksNode` |
| **IC factors** | One global value per detector in `DetectorTable` | Per-analysis JSON, historically tracked |
| **Irradiation IDs** | Integer `IrradPosition` PK + `IrradiationLevel` string (e.g. `NM-315A`) | Name + level stored separately in MetaRepo git repo |
| **Scripts** | Script text stored in `RunScriptTable` rows | PyScript `.py` files in MetaRepo, version-controlled |
| **Decay constants** | Per-DR-session in `PreferencesTable` per analysis | Global preferences; not stored per analysis |
| **Analysis status** | `StatusLevel` integer (0/1/2) | Named tags: `ok`, `omit`, `invalid` |
| **Data sharing** | Database access or export | GitHub/GitLab push; any lab can clone |
| **Backup** | MySQL dump | Git history is the backup |

## The Labnumber System

MassSpec identifies samples by a sequential integer **labnumber** (also called `SampleID` or `LabID`) assigned per irradiation position. A typical labnumber looks like `70847`. This integer is stored in `SampleTable.SampleID`, cross-referenced from `IrradiationPositionTable.SampleID`, and used in `RunTable` to link analyses to positions.

Pychron preserves this labnumber as the `labnumber` field in `IrradiationPositionTbl`. During irradiation import, the integer is carried across directly. When `MassSpecReducedNode` matches historical analyses, it uses the labnumber (formatted as an identifier string), aliquot, and step to locate the correct row in the MassSpec database.

The key implication: **your MassSpec labnumbers survive the migration intact**. Analysts can continue using them as identifiers. The difference is that in Pychron they are stored as the position identifier within a named irradiation level, rather than as a foreign key into a monolithic sample table.

## The Critical Gap: Raw Data Is Not Importable

MassSpec stores raw integration signals as binary blobs in `PeakTimeTable.PeakTimeBlob`. There is no tool in Pychron — and no planned tool — that converts these blobs into Pychron acquisition JSON files. This is the fundamental constraint that shapes every migration decision:

**Historical analyses can be imported with their MassSpec reduction results frozen as fixed values. They cannot be re-reduced from first principles in Pychron.**

`MassSpecReducedNode` imports the *outputs* of MassSpec's reduction (intercepts, blanks, baselines, IC factors) and writes them as frozen constants into the Pychron DVC JSON structure. The Pychron pipeline can then compute ages from those frozen values, produce ideograms, and export age tables — but it cannot refit the isochrons from raw signals, because the raw signals are not present.

:::info Choosing your migration strategy

**Option A — Frozen values (recommended for most labs)**

Use `MassSpecReducedNode` to import historical analyses with their MassSpec reduction results preserved as fixed values. Pychron treats them as pre-reduced data: ages are computed from the imported intercepts and blanks, but `IsoEvolutionNode` and `FitBlanksNode` will not alter them without explicit action.

- Best for: labs that are satisfied with their existing MassSpec reductions, or that have published results they do not want to re-derive
- Result: full historical dataset available in Pychron for age calculations, plotting, and export immediately after import
- Limitation: not re-reducible from raw signals

**Option B — Re-acquire from scratch (gold standard)**

Treat the MassSpec database as a historical archive and run all future work natively in Pychron. Import irradiation structure and sample records from MassSpec, but do not attempt to import analysis data. New analyses are acquired in pyExperiment and reduced through the full Pychron pipeline.

- Best for: labs starting a new irradiation, labs with concerns about MassSpec reduction quality, or labs that want full Pychron reduction capability from day one
- Result: complete, re-reducible dataset for all analyses done in Pychron going forward
- Limitation: historical MassSpec analyses remain in the legacy database, not in Pychron

**Most labs do both**: Option A to archive the historical record in Pychron, Option B going forward. New irradiations are run entirely in Pychron; old irradiations are imported as frozen values for reference and publication.
:::

See the [Migration Guide](./massspec-migration) for step-by-step instructions, tooling status, data transfer tables, and workflow differences.
