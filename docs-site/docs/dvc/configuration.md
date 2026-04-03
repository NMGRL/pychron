---
id: configuration
title: DVC Configuration Reference
sidebar_label: Configuration Reference
sidebar_position: 3
---

# DVC Configuration Reference

DVC configuration is split across four preference groups, one git host preference group, and two environment variables. All preferences are stored in Enthought's `apptools.preferences` system under the paths shown below — they can be set via the Pychron Preferences UI or by directly editing the preferences file at `~/.pychron.<app>/preferences.ini`. Fields marked **Required** will cause DVC to fail silently or visibly if missing.

## DVC Connection preferences (`pychron.dvc.connection`)

Set in **Preferences → DVC → Connection**. Stored as a comma-separated string per connection profile (`DVCConnectionItem`). Multiple profiles ("favorites") can be defined; only the one with `default=true` and `enabled=true` is used at startup.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | — | — | Display name for this connection profile |
| `kind` | string | Yes | `mysql` | `"mysql"` or `"sqlite"` |
| `username` | string | Yes (MySQL) | `root` | Database username |
| `host` | string | Yes (MySQL) | `localhost` | Database host |
| `dbname` | string | Yes | `pychronmeta` | Database name |
| `password` | string | Yes (MySQL) | `Argon` | Database password |
| `enabled` | bool | — | `true` | Whether this profile is active |
| `default` | bool | — | `false` | Whether this is the startup profile |
| `path` | string | Yes (SQLite) | — | Absolute path to SQLite file |
| `organization` | string | Yes | — | GitHub/GitLab organization name (e.g. `NMGRL`) |
| `meta_repo_name` | string | **Required** | — | Name of the MetaRepo repository (e.g. `NMGRLMetaData`) |
| `meta_repo_dir` | path | — | — | Override for MetaRepo location. Accepts absolute path, `~`-relative path, or bare name (joined to `<dvc_dir>/`). If set, takes precedence over `meta_repo_name` for the local path. |
| `repository_root` | path | — | — | Override for data repository root directory. Same resolution rules as `meta_repo_dir`. If not set, defaults to `<dvc_dir>/repositories/`. |
| `timeout` | int | — | — | Database connection timeout in seconds |

## DVC general preferences (`pychron.dvc`)

Set in **Preferences → DVC**.

| Field | Default | Description |
|---|---|---|
| `use_auto_pull` | `true` | Automatically `git pull` MetaRepo and data repos on initialize without asking. Set to `false` to be prompted before pulling. |
| `use_auto_push` | `false` | Automatically push data repos when a PushNode is used, without a confirmation dialog. |
| `use_default_commit_author` | `false` | Use a fixed author for all git commits instead of the currently logged-in Pychron user. |
| `update_currents_enabled` | `false` | Enable updating "current values" in the pipeline (rarely needed). |
| `use_cocktail_irradiation` | `false` | Use `cocktail.json` in the MetaRepo for irradiation flux and chronology instead of per-irradiation files. |
| `use_cache` | `false` | Cache loaded analyses in memory to speed up repeated pipeline runs. |
| `max_cache_size` | `0` | Maximum number of analyses to keep in memory cache. Setting to `0` disables caching even if `use_cache=true`. |

## DVC experiment preferences (`pychron.dvc.experiment`)

Set in **Preferences → Experiment → DVC**.

| Field | Default | Description |
|---|---|---|
| `use_dvc_persistence` | `false` | **Must be `true`** for Pychron to write analysis data to git during acquisition. If `false`, legacy persistence is used and no DVC JSON files are created. |
| `use_dvc_overlap_save` | `false` | Allow the persister to save one analysis while the next is already running. |
| `dvc_save_timeout_minutes` | `0` | How long to wait for an overlap save to complete before aborting. Only active when `use_dvc_overlap_save=true`. |

## DVC repository preferences (`pychron.dvc.repository`)

Set in **Preferences → Repositories**.

| Field | Default | Description |
|---|---|---|
| `check_for_changes` | `false` | Check each data repository for uncommitted local changes when it is opened. |
| `auto_fetch` | `false` | Automatically `git fetch` from the remote when a local data repository is selected. Disable if network latency is causing UI slowdowns. |

## GitHub preferences (`pychron.github`)

Set in **Preferences → GitHub**.

| Field | Required | Description |
|---|---|---|
| `organization` | Yes | GitHub organization name. Must match `organization` in the DVC connection profile. |
| `oauth_token` | **Required** | GitHub Personal Access Token (PAT) with `repo` scope. Password auth was removed by GitHub in 2021 and is no longer supported. |
| `default_remote_name` | — | Git remote name to use. Default: `origin`. |
| `disable_authentication_message` | — | Suppress the Windows-specific authentication reminder dialog on startup. |

The token can also be stored in `~/.pychron.<app>/appdata/oauth.json` as `{"access_token": "<token>"}`. The file is checked before the preference value.

## GitLab preferences (`pychron.gitlab`)

Set in **Preferences → GitLab**.

| Field | Required | Description |
|---|---|---|
| `host` | Yes | Full URL to the GitLab instance, e.g. `http://gitlab.lab.edu`. |
| `organization` | Yes | GitLab group name. |
| `oauth_token` | Yes | GitLab personal access token (sent as `Bearer <token>`). |
| `default_remote_name` | — | Git remote name. Default: `origin`. |

## Environment variables

Set in your shell profile (`~/.zshrc`, `~/.bashrc`, or Windows system environment).

| Variable | Required | Description |
|---|---|---|
| `PYCHRON_ALEMBIC_URL` | **Required** (MySQL) | SQLAlchemy connection URL for database schema migrations. Example: `mysql+pymysql://root:Argon@localhost/pychronmeta`. Written to your shell profile by `app_utils/install.py` during setup. |
| `PYCHRON_USE_LOGIN` | — | Set to `0` to skip the user-login dialog. Useful for single-user labs. |
| `GIT_ASKPASS` | — | Set automatically at runtime by `GitHostService.set_authentication()` to inject credentials into git operations. Do not set manually. |

## Key file paths

| Path | What it is |
|---|---|
| `~/.pychron.<app>/data/.dvc/` | Root DVC directory (`paths.dvc_dir`) |
| `~/.pychron.<app>/data/.dvc/<MetaRepoName>/` | MetaRepo local clone (`paths.meta_root`) |
| `~/.pychron.<app>/data/.dvc/repositories/` | Data repositories root (`paths.repository_dataset_dir`) |
| `~/.pychron.<app>/data/offline_db/index.sqlite3` | Offline SQLite database |
| `~/.pychron.<app>/appdata/oauth.json` | GitHub OAuth token cache |
