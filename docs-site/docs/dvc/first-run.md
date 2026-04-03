---
id: first-run
title: DVC First Run
sidebar_label: First Run
sidebar_position: 2
---

# DVC First Run

DVC initialization runs automatically every time Pychron starts, triggered by the `DVCPlugin` startup tests `test_database` and `test_dvc_fetch_meta`. Both must pass before any DVC-dependent functionality (experiment acquisition, pipeline data reduction) is accessible. The initialization sequence has hard prerequisites — if any are missing, DVC will silently abort or show a warning dialog and leave the system in a non-functional state without a clear error message. This page covers exactly what must be in place before the first launch and what Pychron does automatically on first run.

## Prerequisites checklist

Before launching Pychron with DVC enabled, verify every item on this list:

### Git host plugin
- [ ] One of `GitHub`, `GitLab`, or `LocalGit` plugin is enabled in `initialization.xml`
- [ ] `DVC` plugin is also enabled in `initialization.xml`

If no git host plugin is loaded, DVC displays: *"GitLab or GitHub or LocalGit plugin is required"* and stops. There is no fallback.

### MetaRepo name
- [ ] `meta_repo_name` is set in **Preferences → DVC → Connection** (e.g. `NMGRLMetaData`)

If this field is empty, `DVC.initialize()` shows a warning dialog and returns without initializing. All subsequent DVC operations will fail with `AttributeError`.

### Authentication (GitHub or GitLab only)
- [ ] **GitHub:** OAuth token entered in **Preferences → GitHub → Token**, or stored in `~/.pychron.<app>/appdata/oauth.json`
- [ ] **GitLab:** OAuth token + host URL entered in **Preferences → GitLab**
- [ ] Git credential helper configured so `git clone` and `git push` can authenticate non-interactively

### Database
- [ ] MySQL 8.x running on `localhost` (or configured host)
- [ ] Database `pychronmeta` created
- [ ] `PYCHRON_ALEMBIC_URL` environment variable set, e.g. `mysql+pymysql://root:Argon@localhost/pychronmeta`
- [ ] Schema migrated: `cd alembic_dvc && alembic upgrade head`

### MetaRepo on GitHub/GitLab (for new labs)
- [ ] A repository named `<meta_repo_name>` (e.g. `NMGRLMetaData`) exists in the configured organization on GitHub/GitLab
- [ ] The configured OAuth token has `repo` scope (full read/write) for that organization

## Initialization sequence

When `DVC.initialize()` runs (`pychron/dvc/dvc.py:165`):

```
1. Check meta_repo_name is set
   └─ if empty: show warning dialog, return (SILENT FAILURE)

2. open_meta_repo()
   ├─ if <dvc_dir>/<meta_repo_name>/.git exists: open existing repo
   ├─ elif git host returns a clone URL: git clone to <dvc_dir>/<meta_repo_name>/
   └─ else: git init locally, warn user to clone manually
              └─ returns False (PARTIAL FAILURE — no remote data)

3. meta_pull()
   └─ git pull on MetaRepo (fast-forward only)

4. db.connect()
   └─ if fails: startup test goes red, message shown, app continues
                but experiment/pipeline operations will fail
```

:::warning Silent failure
If `open_meta_repo()` raises any exception (network timeout, bad credentials, missing repo), the exception is caught and logged as a warning, but **no dialog is shown to the user**. The application continues to load but DVC will not function. Check the log file at `~/.pychron.<app>/logs/` if startup test `test_dvc_fetch_meta` fails with no visible error.
:::

## What Pychron creates on first run

When the MetaRepo is freshly initialized (first-ever setup), `DVC._defaults()` creates the following inside the MetaRepo directory:

```
<MetaRepoName>/
├── irradiation_holders/     ← directory
│   └── 24Spokes.txt         ← default 24-position geometry
├── productions/             ← directory
│   └── TRIGA.txt            ← placeholder production ratios
└── load_holders/            ← directory
    ├── 221.txt              ← default load holder
    └── 65.txt               ← default load holder
```

These defaults are committed to the MetaRepo automatically. Production ratios and irradiation geometries must then be populated manually through **Entry → Irradiation** before any analyses can be associated with irradiation positions.
