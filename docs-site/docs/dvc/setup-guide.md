---
id: setup-guide
title: DVC Setup Guide
sidebar_label: Setup Guide
sidebar_position: 1
---

# DVC Setup Guide

Pychron DVC (Data Version Control) is a custom git-backed data persistence system — it is **not** the open-source `dvc` tool and shares no code or concepts with it. DVC solves the dual nature of mass spectrometry data: the catalog of what analyses exist needs fast SQL queries, while the data content itself needs full version history, provenance tracking, and reproducible sharing between labs. It accomplishes this by maintaining three storage layers simultaneously: a SQL database that indexes all analyses, irradiations, samples, and projects; a single MetaRepo git repository that stores irradiation geometry, flux values, production ratios, and spectrometer configurations; and one git data repository per experiment batch that stores the actual per-analysis JSON files for signals, baselines, blanks, IC factors, and reduction results.

## The three storage layers

| Layer | Type | Contents | Default location |
|---|---|---|---|
| **DVCDatabase** | MySQL or SQLite | Analysis index, irradiation catalog, sample/project/PI records | `localhost/pychronmeta` |
| **MetaRepo** | Git repository | Irradiation geometry, chronology, production ratios, flux values, spectrometer gains, load holders, scripts | `~/.pychron.<app>/data/.dvc/<MetaRepoName>/` |
| **Data repos** | Git repositories (one per experiment batch) | Per-analysis JSON: signals, baselines, blanks, IC factors, intercepts, tags, peak center, extraction | `~/.pychron.<app>/data/.dvc/repositories/<repo_name>/` |

## Data flow summary

During acquisition, `DVCPersister` writes JSON files for each analysis phase (extraction, measurement, peak center), stages them in the data repo, commits under the `<COLLECTION>` tag, and pushes to GitHub/GitLab. During data reduction, the pipeline reads those JSON files through `DVCAnalysis`, computes fits and ages, and writes results back as new commits tagged `<ISOEVO>`, `<BLANKS>`, `<ICFactor>`.

## In this section

- [First Run](./first-run) — Prerequisites checklist and initialization sequence
- [Configuration Reference](./configuration) — Every configuration field, preference, and environment variable
- [Failure Modes](./failure-modes) — What fails silently vs loudly, and how to recover
- [Offline Mode](./offline-mode) — Working without GitHub/GitLab connectivity
