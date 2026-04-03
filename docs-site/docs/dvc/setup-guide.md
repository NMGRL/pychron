---
id: setup-guide
title: DVC Setup Guide
sidebar_label: Setup Guide
sidebar_position: 1
---

# DVC Setup Guide

Pychron DVC (Data Version Control) is a custom git-backed data persistence and provenance system built into Pychron. It is **not** the open-source `dvc.org` tool and shares no code or concepts with it. DVC solves the dual challenge of noble gas mass spectrometry data: the catalog of what analyses exist needs fast SQL queries, while the actual measurement data needs full version history, provenance tracking, and reproducible sharing between labs. It accomplishes this by maintaining three storage layers simultaneously.

## The Three Storage Layers

| Layer | Type | Contents | Default location |
|---|---|---|---|
| **DVCDatabase** | MySQL or SQLite | Analysis index; irradiation, sample, project, and PI records; run tables | `localhost/pychronmeta` (MySQL) or a local `.sqlite3` file |
| **MetaRepo** | Single git repository | Irradiation geometry, chronology, flux values, production ratios, spectrometer gains, load holders, scripts | `~/.pychron.<app>/data/.dvc/<MetaRepoName>/` |
| **Data repos** | One git repository per experiment batch | Per-analysis JSON: signals, baselines, blanks, IC factors, intercepts, tags, peak center, extraction | `~/.pychron.<app>/data/.dvc/repositories/<repo_name>/` |

The SQL database is the **index** — it answers "what analyses exist matching these criteria?" quickly. The git repositories are the **truth** — every measurement value, fit, and reduction result is in a version-controlled JSON file that can be audited, diffed, and re-reduced at any time.

## Directory Layout on Disk

```
~/.pychron.<app>/
├── data/
│   ├── .dvc/
│   │   ├── <MetaRepoName>/              ← MetaRepo (single git repo)
│   │   │   ├── irradiation_holders/
│   │   │   │   └── 24Spokes.txt
│   │   │   ├── productions/
│   │   │   │   └── TRIGA.txt
│   │   │   ├── load_holders/
│   │   │   │   ├── 221.txt
│   │   │   │   └── 65.txt
│   │   │   └── <IrradiationName>/
│   │   │       ├── chronology.txt
│   │   │       ├── flux.json
│   │   │       └── geometry.txt
│   │   └── repositories/
│   │       └── <ExperimentRepo>/        ← one data repo per batch
│   │           ├── .data/               ← raw integration signals
│   │           ├── baselines/
│   │           ├── blanks/
│   │           ├── icfactors/
│   │           ├── intercepts/
│   │           ├── tags/
│   │           ├── peakcenter/
│   │           └── extraction/
│   └── offline_db/
│       └── index.sqlite3                ← offline SQLite copy
├── logs/
│   └── pychron.log
└── appdata/
    └── oauth.json                       ← GitHub OAuth token cache
```

## Data Flow: What Happens Per Analysis

During a single automated run, `DVCPersister` coordinates these writes in sequence:

1. **Extraction** — Writes `extraction/<runid>.json` recording laser power, duration, and valve sequence as the gas is being released.
2. **Measurement** — Each isotope's integration signals are written to `.data/<runid>.json` as they arrive from the spectrometer.
3. **Post-measurement** — Baseline signals, blank values, and IC factors are written to their respective subdirectories.
4. **Commit and push** — All new files are staged (`git add`) and committed to the `data_collection` branch with a `<COLLECTION>` tag. The commit is pushed to GitHub/GitLab asynchronously.

During data reduction via the pipeline, further commits are written:

5. **Intercepts** — Isochron fit results written to `intercepts/<runid>.json` and tagged `<ISOEVO>`.
6. **Blanks and IC factors** — Updated correction values committed with `<BLANKS>` and `<ICFactor>` tags.
7. **Ages** — Computed ages stored in the SQL database; reduction metadata committed back to the data repo.

At every step the data repo accumulates a permanent, auditable record. The SQL database stores only final reduced values and is always reconstructable from the git history.

## In This Section

- [First-Run Setup](./first-run) — Choose your git host and database, then walk through initialization step by step
- [Configuration Reference](./configuration) — Every preference field, environment variable, and file path
- [Failure Modes](./failure-modes) — What fails silently vs loudly, how to detect it, and how to recover
- [Offline Mode](./offline-mode) — Running data reduction without network access
