---
id: installation
title: Installation Guide
sidebar_label: Installation
sidebar_position: 1
---

# Installation Guide

:::info This guide covers the 2026 toolchain on the `main` branch
Pychron now uses [`uv`](https://docs.astral.sh/uv/) for Python environment and package management, targeting Python 3.12. If you found an older guide elsewhere, discard it and follow this page.
:::

:::warning The Anaconda/conda install guides are outdated
`docs/user_guide/getting_started/install_mac.rst` and `install_pc.rst` in the legacy documentation describe a `conda create` workflow targeting Python 3.5–3.6. That path no longer works — dependencies have moved on and the conda packages are unmaintained. Do not follow those guides.
:::

## System Requirements

| Requirement | Detail |
|---|---|
| **Operating system** | macOS 12 Monterey or later (primary development platform); Windows 10/11 supported; Ubuntu 22.04+ supported |
| **Python** | 3.12 — managed automatically by `uv` if not already installed |
| **Git** | 2.35 or later |
| **Disk space** | ~2 GB for the repo, dependencies, and initial DVC data |
| **MySQL** | 8.x, for the DVC database (SQLite supported for development/offline) |
| **Network** | Required at first launch if using GitHub or GitLab as DVC git host |

## Step 1 — Install Git

**macOS:**
```bash
# Check if git is installed
git --version

# If not, install via Xcode Command Line Tools
xcode-select --install
```

**Windows:** Download and install [Git for Windows](https://git-scm.com/download/win). During setup, choose "Use Git from the Windows Command Prompt" and "Checkout as-is, commit Unix-style line endings."

## Step 2 — Install `uv`

`uv` is a fast Python package and environment manager that replaces both `pip` and `conda` for Pychron.

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell or run:
source ~/.zshrc   # or ~/.bashrc
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:
```bash
uv --version
```

## Step 3 — Clone the Repository

```bash
git clone https://github.com/NMGRL/pychron.git
cd pychron
```

## Step 4 — Install Dependencies

```bash
uv sync
```

This creates a `.venv/` directory inside the repo and installs all core dependencies. Python 3.12 is downloaded automatically by `uv` if not already on your system.

For hardware-facing lab computers, also install the hardware group:

```bash
uv sync --group hardware   # pyserial, pymodbus, PyVISA, LabJackPython
```

For development work:

```bash
uv sync --group dev        # black, mypy, pytest, ruff
```

## Step 5 — Set Environment Variables

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`, or Windows system environment) and reload:

```bash
# Required for database schema migrations (MySQL example)
export PYCHRON_ALEMBIC_URL="mysql+pymysql://root:Argon@localhost/pychronmeta"

# Optional: skip the user-login dialog on startup (single-user labs)
export PYCHRON_USE_LOGIN=0
```

For SQLite (development / offline):
```bash
export PYCHRON_ALEMBIC_URL="sqlite:////Users/<you>/.pychron.experiment/data/pychronmeta.sqlite3"
```

## Step 6 — Bootstrap the Application Directory

```bash
uv run pychron-bootstrap
```

`pychron-bootstrap` creates the application data directory structure at `~/.pychron.<appname>/` and writes the initial configuration files. Specifically it creates:

- `~/.pychron.<appname>/setupfiles/initialization.xml` — plugin configuration (edit this to select which hardware and services load)
- `~/.pychron.<appname>/setupfiles/startup_tests.yaml` — defines which startup tests run on launch
- `~/.pychron.<appname>/preferences.ini` — all user preferences (also editable through the Pychron Preferences UI)
- `~/.pychron.<appname>/appdata/` — directory for OAuth tokens and other runtime state
- `~/.pychron.<appname>/logs/` — log file directory

You will be prompted to choose an application name (`experiment`, `pipeline`, `valve`, etc.). This becomes the `<appname>` suffix in the paths above.

## Step 7 — Validate the Environment

```bash
uv run pychron-doctor
```

`pychron-doctor` performs pre-flight checks and reports problems before you ever launch the application. It verifies:

- Python version is 3.12
- All core dependencies are importable
- `PYCHRON_ALEMBIC_URL` is set and the target database is reachable
- Alembic schema migrations are current (`alembic upgrade head` if not)
- Application data directory structure exists (created by `pychron-bootstrap`)
- Git is installed and the MetaRepo path is accessible (if configured)

Fix every item `pychron-doctor` flags red before proceeding. A clean run looks like:

```
✓ Python 3.12.x
✓ Core dependencies
✓ PYCHRON_ALEMBIC_URL set
✓ Database reachable
✓ Schema up to date
✓ App data directory
```

## Step 8 — Run the Schema Migration

If `pychron-doctor` reports the schema is not current (or if this is a first-time MySQL setup):

```bash
cd alembic_dvc
alembic upgrade head
cd ..
```

Re-run `pychron-doctor` afterward to confirm the schema check passes.

## Common Failure Points

| Symptom | Likely cause | Fix |
|---|---|---|
| `uv: command not found` after install | Shell profile not reloaded | `source ~/.zshrc` or open a new terminal |
| `uv sync` fails with SSL errors (macOS) | macOS system Python SSL certs not trusted | Run `/Applications/Python\ 3.12/Install\ Certificates.command` or `pip install certifi` |
| `pychron-doctor` reports wrong Python version | `uv` picked up a system Python instead of 3.12 | Run `uv python install 3.12` then `uv sync` again |
| `PYCHRON_ALEMBIC_URL` not found | Variable set in shell but not exported | Add `export` prefix; confirm with `echo $PYCHRON_ALEMBIC_URL` |
| MySQL connection refused | MySQL not running | `brew services start mysql` (macOS) or `systemctl start mysql` (Linux) |
| `Access denied for user 'root'` | Wrong MySQL password in `PYCHRON_ALEMBIC_URL` | Update the URL or reset the MySQL root password |
| `Unknown database 'pychronmeta'` | Database not created | `mysql -u root -e "CREATE DATABASE pychronmeta CHARACTER SET utf8mb4;"` |
| Windows: import errors on first run | Compiled extension missing for architecture | Run `uv sync --reinstall` to rebuild platform wheels |
| `initialization.xml` not found on launch | `pychron-bootstrap` not run | Run `uv run pychron-bootstrap` |

## First Launch Verification

Once `pychron-doctor` reports all green, launch the application:

```bash
# Data reduction workstation
uv run pychron --app pipeline

# Acquisition computer
uv run pychron --app experiment

# Extraction line only
uv run pychron --app valve
```

On first launch, Pychron will:

1. Read `initialization.xml` and load the configured plugins
2. Clone or open the MetaRepo (if DVC and a git host plugin are enabled)
3. Connect to the database
4. Run startup tests — you will see a brief results panel

A healthy first launch shows both `test_database` and `test_dvc_fetch_meta` in green. If either is red, see [DVC Failure Modes](../dvc/failure-modes) for diagnosis steps.

## Next Steps

- [Quick Start](./quick-start) — Verify hardware, configure your first experiment, and confirm the full write path works
- [DVC First-Run Setup](../dvc/first-run) — Full DVC configuration walkthrough if you skipped it
