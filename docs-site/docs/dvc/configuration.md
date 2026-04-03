---
id: configuration
title: Configuration Reference
sidebar_label: Configuration
sidebar_position: 3
---

# Configuration Reference

DVC configuration is split across four preference groups, two git host preference groups, and two environment variables. All preferences are stored in Enthought's `apptools.preferences` system and can be set via the Pychron Preferences UI or by editing `~/.pychron.<app>/preferences.ini` directly. Fields marked **Required** will cause DVC to fail silently or with a dialog if missing.

## DVC Connection (`pychron.dvc.connection`)

Set in **Preferences → DVC → Connection**. Multiple connection profiles ("favorites") can be defined; only the one with `default=true` and `enabled=true` is used at startup.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | — | — | Display name for this connection profile |
| `kind` | string | Yes | `mysql` | `"mysql"` or `"sqlite"` |
| `host` | string | Yes (MySQL) | `localhost` | Database host |
| `username` | string | Yes (MySQL) | `root` | Database username |
| `password` | string | Yes (MySQL) | `Argon` | Database password |
| `dbname` | string | Yes | `pychronmeta` | Database name |
| `path` | string | Yes (SQLite) | — | Absolute path to SQLite file |
| `enabled` | bool | — | `true` | Whether this profile is active |
| `default` | bool | — | `false` | Whether this is the startup profile |
| `timeout` | int | — | — | Database connection timeout in seconds |
| `organization` | string | Yes | — | GitHub/GitLab organization or group name (e.g. `NMGRL`) |
| `meta_repo_name` | string | **Required** | — | Name of the MetaRepo repository (e.g. `NMGRLMetaData`). If empty, DVC will show a warning and abort initialization. |
| `meta_repo_dir` | path | — | — | Override local MetaRepo path. Accepts absolute path, `~`-relative path, or bare name (joined to `<dvc_dir>/`). Takes precedence over `meta_repo_name` for the local path. |
| `repository_root` | path | — | — | Override data repository root. Same resolution rules as `meta_repo_dir`. Defaults to `<dvc_dir>/repositories/`. |

## DVC General (`pychron.dvc`)

Set in **Preferences → DVC**.

| Field | Default | Description |
|---|---|---|
| `use_auto_pull` | `true` | Automatically `git pull` the MetaRepo and data repos on startup without prompting. Set to `false` to be prompted before each pull. |
| `use_auto_push` | `false` | Automatically push data repos when a PushNode runs, without a confirmation dialog. |
| `use_default_commit_author` | `false` | Use a fixed commit author for all git commits instead of the currently logged-in Pychron user. |
| `update_currents_enabled` | `false` | Enable updating "current values" in the pipeline. Rarely needed. |
| `use_cocktail_irradiation` | `false` | Use `cocktail.json` in the MetaRepo for flux and chronology instead of per-irradiation files. |
| `use_cache` | `false` | Cache loaded analyses in memory to speed up repeated pipeline runs. |
| `max_cache_size` | `0` | Maximum analyses to keep in the memory cache. `0` disables caching even when `use_cache=true`. |

## DVC Experiment (`pychron.dvc.experiment`)

Set in **Preferences → Experiment → DVC**.

:::danger `use_dvc_persistence` must be `true`
If `use_dvc_persistence` is `false` (the default), Pychron uses legacy persistence and **no DVC JSON files are written during acquisition**. Data will not be committed to git and cannot be reduced through the DVC pipeline. Set this to `true` on every acquisition computer before running experiments.
:::

| Field | Default | Description |
|---|---|---|
| `use_dvc_persistence` | `false` | **Must be `true`** for acquisition data to be written to git. |
| `use_dvc_overlap_save` | `false` | Allow the persister to save one analysis while the next is already running (overlap save). |
| `dvc_save_timeout_minutes` | `0` | How long to wait for an overlap save before aborting. Only active when `use_dvc_overlap_save=true`. |
| `use_data_collection_branch` | `false` | Write acquisition commits to a dedicated `data_collection` branch instead of the default branch. When enabled, `sync_repo_from_data_collection()` merges this branch back into the current branch when a data repo is loaded for reduction. |

## DVC Repository (`pychron.dvc.repository`)

Set in **Preferences → Repositories**.

| Field | Default | Description |
|---|---|---|
| `check_for_changes` | `false` | Check each data repository for uncommitted local changes when opened. |
| `auto_fetch` | `false` | Automatically `git fetch` from the remote when a local data repository is selected. Disable if network latency is causing UI slowdowns. |

## GitHub (`pychron.github`)

Set in **Preferences → GitHub**.

| Field | Required | Description |
|---|---|---|
| `organization` | Yes | GitHub organization name. Must match `organization` in the DVC connection profile. |
| `oauth_token` | **Required** | Personal Access Token (PAT) with `repo` scope. GitHub password authentication was removed in 2021 and is no longer supported. |
| `default_remote_name` | — | Git remote name. Default: `origin`. |
| `disable_authentication_message` | — | Suppress the Windows-specific authentication reminder dialog on startup. |

The token can also be stored in `~/.pychron.<app>/appdata/oauth.json` as:

```json
{"access_token": "<token>"}
```

The file is checked before the preference value. If both exist, the file takes precedence.

## GitLab (`pychron.gitlab`)

Set in **Preferences → GitLab**.

| Field | Required | Description |
|---|---|---|
| `host` | Yes | Full URL to the GitLab instance, e.g. `http://gitlab.lab.edu`. |
| `organization` | Yes | GitLab group name. |
| `oauth_token` | Yes | GitLab personal access token (sent as `Bearer <token>` in API requests). |
| `default_remote_name` | — | Git remote name. Default: `origin`. |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PYCHRON_ALEMBIC_URL` | **Required** | SQLAlchemy URL for database schema migrations. MySQL: `mysql+pymysql://root:Argon@localhost/pychronmeta`. SQLite: `sqlite:////absolute/path/to/file.sqlite3`. Set in your shell profile before launching Pychron. |
| `PYCHRON_USE_LOGIN` | — | Set to `0` to skip the user-login dialog at startup. Useful for single-user labs. |
| `GIT_ASKPASS` | — | Set automatically at runtime by `GitHostService` to inject credentials into git operations. Do not set this manually — Pychron manages it. |

## Key File Paths

| Path | What it is |
|---|---|
| `~/.pychron.<app>/data/.dvc/` | Root DVC directory (`paths.dvc_dir`) |
| `~/.pychron.<app>/data/.dvc/<MetaRepoName>/` | MetaRepo local clone |
| `~/.pychron.<app>/data/.dvc/repositories/` | Data repositories root |
| `~/.pychron.<app>/data/offline_db/index.sqlite3` | Offline SQLite database |
| `~/.pychron.<app>/preferences.ini` | All Pychron preferences (human-editable) |
| `~/.pychron.<app>/appdata/oauth.json` | GitHub OAuth token file cache |
| `~/.pychron.<app>/logs/pychron.log` | Runtime log — first place to check on DVC failures |
