---
id: first-run
title: First-Run Setup
sidebar_label: First-Run Setup
sidebar_position: 2
---

# First-Run Setup

DVC initialization runs automatically every time Pychron starts, triggered by the `DVCPlugin` startup tests `test_database` and `test_dvc_fetch_meta`. Both must pass before any DVC-dependent functionality — experiment acquisition, pipeline data reduction — is available. This page walks through setup from scratch, including choosing a git host and database backend.

## Step 1 — Choose Your Git Host

Pychron supports three git host backends. Only one can be active at a time.

| | GitHub | GitLab | LocalGit |
|---|---|---|---|
| **Best for** | Labs sharing data openly; NMGRL-style collaborative data | Labs that must keep data on-premise on an institution server | Development, testing, or fully offline labs |
| **Auth** | Personal Access Token with `repo` scope | Personal Access Token + instance URL | None — no remote |
| **Remote hosting** | github.com or GitHub Enterprise | Self-hosted GitLab instance | Local filesystem only |
| **Multi-lab data sharing** | Yes — fork/clone from org | Yes — via GitLab groups | No |
| **Network required at startup** | Yes | Yes | No |
| **`initialization.xml` plugin** | `GitHub` | `GitLab` | `LocalGit` |

## Step 2 — Choose Your Database

| | MySQL | SQLite |
|---|---|---|
| **Best for** | Any production lab running experiments | Development, testing, or single-analyst offline reduction |
| **Installation** | MySQL 8.x server required | None — file-based |
| **Multi-user** | Yes | No — concurrent access causes locking issues |
| **Schema migration** | Required: `alembic upgrade head` | Required: same `alembic upgrade head` command |
| **`PYCHRON_ALEMBIC_URL` format** | `mysql+pymysql://user:pass@host/dbname` | `sqlite:////absolute/path/to/file.sqlite3` |
| **Performance** | Fast for large analysis catalogs | Adequate for ≤ ~50,000 analyses |

## Step 3 — Prerequisites Checklist

Complete every applicable item before launching Pychron for the first time.

**All setups:**
- [ ] `DVC` plugin enabled in `initialization.xml`
- [ ] Exactly one of `GitHub`, `GitLab`, or `LocalGit` plugin enabled in `initialization.xml`
- [ ] `meta_repo_name` set in **Preferences → DVC → Connection** (e.g. `NMGRLMetaData`)

**GitHub:**
- [ ] MetaRepo repository exists in your GitHub organization (name must match `meta_repo_name`)
- [ ] PAT generated at **GitHub → Settings → Developer settings → Personal access tokens** with `repo` scope
- [ ] PAT entered in **Preferences → GitHub → Token** or saved to `~/.pychron.<app>/appdata/oauth.json`
- [ ] `organization` set in **Preferences → GitHub** and **Preferences → DVC → Connection**

**GitLab:**
- [ ] GitLab instance URL entered in **Preferences → GitLab → Host**
- [ ] PAT entered in **Preferences → GitLab → Token**
- [ ] MetaRepo group and repo created on the GitLab instance

**MySQL:**
- [ ] MySQL 8.x running on target host
- [ ] Database `pychronmeta` created
- [ ] `PYCHRON_ALEMBIC_URL` environment variable set
- [ ] Alembic schema migration completed

**SQLite:**
- [ ] `PYCHRON_ALEMBIC_URL` set to a SQLite path
- [ ] Alembic schema migration completed to create the schema

---

## Standard Path: GitHub + MySQL

This is the configuration used by NMGRL and most labs sharing data openly.

### 1. Create the MetaRepo on GitHub

In your GitHub organization, create a new repository. The name must match whatever you will set as `meta_repo_name` in preferences. It can be empty — Pychron populates it with defaults on first launch.

### 2. Generate a GitHub PAT

Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)** and create a token with `repo` scope. Copy the token — GitHub will not show it again.

### 3. Install MySQL and create the database

```bash
# macOS (Homebrew)
brew install mysql
brew services start mysql

# Create database
mysql -u root -e "CREATE DATABASE pychronmeta CHARACTER SET utf8mb4;"
```

### 4. Set `PYCHRON_ALEMBIC_URL`

Add to your shell profile (`~/.zshrc` or `~/.bashrc`) and reload:

```bash
export PYCHRON_ALEMBIC_URL="mysql+pymysql://root:Argon@localhost/pychronmeta"
```

Replace `root`, `Argon`, `localhost`, and `pychronmeta` with your actual credentials.

### 5. Run the schema migration

```bash
cd /path/to/pychron/alembic_dvc
alembic upgrade head
```

Re-run this command after any Pychron upgrade that ships new migrations.

### 6. Enable plugins in `initialization.xml`

In `~/.pychron.<app>/setupfiles/initialization.xml`, ensure both entries are present:

```xml
<plugin name="GitHub"/>
<plugin name="DVC"/>
```

### 7. Configure preferences

In **Preferences → DVC → Connection**, set `organization`, `meta_repo_name`, `kind = mysql`, and the MySQL host/username/password/dbname.

In **Preferences → GitHub**, paste the PAT from step 2 into the **Token** field.

In **Preferences → Experiment → DVC**, set `use_dvc_persistence = true`.

### 8. Launch Pychron

On first launch, DVC will automatically:

1. Clone the MetaRepo from GitHub to `~/.pychron.<app>/data/.dvc/<MetaRepoName>/`
2. Run `DVC._defaults()` to create and commit placeholder files (irradiation holders, production ratios, load holders)
3. Connect to MySQL — startup test `test_database` turns green
4. Pull the MetaRepo — startup test `test_dvc_fetch_meta` turns green

If either startup test stays red, check `~/.pychron.<app>/logs/pychron.log` for the cause. The most common culprit is a PAT with wrong scope or a MetaRepo name mismatch.

:::warning Silent failure on MetaRepo errors
If `open_meta_repo()` fails for any reason (network timeout, bad credentials, wrong repo name), Pychron logs a warning and continues loading — **no dialog is shown**. The startup test `test_dvc_fetch_meta` will be red, but there will be no visible popup. Always check the log.
:::

---

## Simplified Path: LocalGit + SQLite

No network, no MySQL, no GitHub account required. Use this for development, offline testing, or a single-user reduction workstation.

### 1. Enable plugins in `initialization.xml`

```xml
<plugin name="LocalGit"/>
<plugin name="DVC"/>
```

### 2. Set `PYCHRON_ALEMBIC_URL`

```bash
export PYCHRON_ALEMBIC_URL="sqlite:////Users/<you>/.pychron.<app>/data/pychronmeta.sqlite3"
```

### 3. Run the schema migration

```bash
cd /path/to/pychron/alembic_dvc
alembic upgrade head
```

### 4. Configure preferences

In **Preferences → DVC → Connection**, set:
- `kind`: `sqlite`
- `path`: same file path as in the `PYCHRON_ALEMBIC_URL` (without the `sqlite:////` prefix)
- `meta_repo_name`: any name you want (e.g. `LocalMeta`)

In **Preferences → Experiment → DVC**, set `use_dvc_persistence = true`.

### 5. Launch Pychron

On first launch, DVC will:

1. Run `git init` for the MetaRepo at `~/.pychron.<app>/data/.dvc/LocalMeta/`
2. Create and commit the default placeholder files
3. Connect to the SQLite file — startup test `test_database` turns green
4. Open the local MetaRepo — startup test `test_dvc_fetch_meta` turns green

No network access is required. Data repos are also created locally; no pushes occur.

:::warning LocalGit limitations
Data in LocalGit repos cannot be shared with other Pychron instances without manually copying directories. If your lab grows beyond a single workstation, migrate to GitHub or GitLab before accumulating significant data.
:::

## What Pychron Creates on First Run

When the MetaRepo is new, `DVC._defaults()` commits these placeholder files automatically:

```
<MetaRepoName>/
├── irradiation_holders/
│   └── 24Spokes.txt         ← default 24-position geometry
├── productions/
│   └── TRIGA.txt            ← placeholder production ratios
└── load_holders/
    ├── 221.txt
    └── 65.txt
```

Populate actual irradiation geometries and production ratios via **Entry → Irradiation** before running experiments.
