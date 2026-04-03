---
id: massspec-overview
title: MassSpec Migration Overview
sidebar_label: Overview
sidebar_position: 1
---

# MassSpec Migration Overview

MassSpec and Pychron solve the same problem — automating Ar-Ar geochronology workflows — but with fundamentally different architectural assumptions. Understanding these differences is essential before planning a migration, because several of them affect what data can be transferred automatically, what requires manual re-entry, and how day-to-day lab operation will change after the switch.

## The core architectural difference

**MassSpec** stores everything in a single centralized MySQL database. Every analysis, reduction result, blank value, baseline, irradiation record, sample, and instrument configuration lives in that one database as rows in tables. There is no concept of per-analysis files, version history, or distributed storage.

**Pychron** uses three storage layers: a SQL database (the index), a MetaRepo (git-backed irradiation and instrument metadata), and one git repository per experiment batch (individual JSON files per analysis). This means every analysis has a full git history of every change to its reduction — but it also means migration is not as simple as pointing Pychron at the MassSpec database.

## Key differences at a glance

| Aspect | MassSpec | Pychron |
|---|---|---|
| Analysis data storage | Rows in `IsotopeResultsTable`, `ArArAnalysisTable` | Per-analysis JSON files in git |
| Versioning | `Counter` columns track re-fits; no true history | Full git commit history |
| Blanks | Single `Bkgd`/`BkgdEr` value per isotope per analysis | Full blank runs stored as analyses; temporal interpolation |
| IC factors | One global value per detector in `DetectorTable` | Per-analysis JSON, tracked historically |
| Irradiation IDs | Integer `IrradPosition` PK + `IrradiationLevel` string (e.g. `NM-315A`) | Name + level stored separately in MetaRepo |
| Scripts | Script text stored in `RunScriptTable` | PyScript `.py` files in MetaRepo |
| Decay constants | Per-DR-session in `PreferencesTable` | Global preferences (not stored per analysis) |

## What the migration tooling covers

Pychron includes `MassSpecReducedNode` — a pipeline node that reads directly from a live MassSpec MySQL database and transfers reduced data (intercepts, baselines, blank values, IC factors, flux, production ratios, comments, tags) into Pychron's DVC JSON format. This is the primary automated migration path.

Irradiation structure (levels, positions, J values, production ratios, chronology, samples, projects, PIs) can be imported via `MassSpecDatabaseAdapter.get_irradiation_import_spec()`.

## What the migration tooling does NOT cover

There is no tool that converts MassSpec raw time-series data (peak time blobs) into Pychron acquisition JSON files. Historical analyses can be imported with their MassSpec reduction results frozen as fixed values, but they cannot be re-reduced from first principles in Pychron without the original raw data being re-acquired or re-ingested separately.

See the [full migration guide](./massspec-migration) for field-by-field mappings, data loss inventory, and step-by-step instructions.
