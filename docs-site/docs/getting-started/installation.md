---
id: installation
title: Installation Guide
sidebar_label: Installation
sidebar_position: 1
---

# Installation Guide

Pychron's current installation toolchain uses [`uv`](https://docs.astral.sh/uv/) as the package and environment manager with Python 3.12. The legacy Anaconda/conda path documented in older guides is no longer supported — any documentation referencing `conda create`, Python 3.5–3.6, or `pip install -r requirements.txt` from a `conda` environment is out of date. The install process has three phases: cloning the repository and installing dependencies with `uv sync`, running `pychron-bootstrap` to initialize the application directory structure and write a startup launcher, and running `pychron-doctor` to validate that the environment, configuration files, and database connections are all healthy before the first launch.

## Prerequisites

- macOS 12+, Ubuntu 22.04+, or Windows 10+ (macOS is the primary development platform)
- Python 3.12 (managed automatically by `uv` if not present)
- Git
- MySQL 8.x (for the DVC database; SQLite is supported for offline/single-user setups)

## Install steps

```bash
# 1. Clone the repository
git clone https://github.com/NMGRL/pychron.git
cd pychron

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install all dependencies
uv sync

# 4. Bootstrap the application data directory
uv run pychron-bootstrap

# 5. Validate the environment
uv run pychron-doctor
```

## Environment variables

Set these in your shell profile before launching Pychron:

| Variable | Required | Description |
|---|---|---|
| `PYCHRON_ALEMBIC_URL` | Yes (MySQL) | SQLAlchemy URL for database migrations, e.g. `mysql+pymysql://root:Argon@localhost/pychronmeta` |
| `PYCHRON_USE_LOGIN` | No | Set to `0` to skip the user-login dialog on startup |

## Dependency groups

`pyproject.toml` defines optional groups beyond the core install:

```bash
uv sync --group dev       # development tools (black, mypy, pytest)
uv sync --group hardware  # pyserial, pymodbus, PyVISA
uv sync --group labspy    # LabSpy monitoring integration
```

## Next step

After installation, follow the [Quick Start](./quick-start) guide to launch Pychron for the first time and verify that it connects to your hardware and data store.
