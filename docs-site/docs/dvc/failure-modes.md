---
id: failure-modes
title: Failure Modes
sidebar_label: Failure Modes
sidebar_position: 4
---

# Failure Modes

DVC has several failure scenarios where the system degrades silently rather than surfacing a clear error. This page documents every known failure mode, its symptom, the responsible code path, and the recovery action.

:::tip Data is never lost
DVC is designed so that a failure to push or sync never destroys data. Acquisitions are committed to the local git repository first; network failures only delay the push. Any commits queued while offline can be pushed later via **Tools → Share Changes**.
:::

## GitHub / GitLab Unreachable

| Failure point | Symptom | Recovery |
|---|---|---|
| MetaRepo clone at startup | `test_dvc_fetch_meta` turns red; **no dialog shown** | Check network and restart Pychron |
| `meta_pull()` at startup | Same red startup test | Check network and restart |
| `push_repository()` after acquisition | Non-fatal dialog: *"DVC/Git upload not successful. Cancel the experiment?"* | Accept non-fatal — data is committed locally. Push when network is restored via **Tools → Share Changes**. |
| `meta_push()` after acquisition | Same non-fatal dialog | Same recovery |
| `gi.create_repo()` (new data repo creation) | **Silent success reported** even though the repo was not created; `SSLError` sets `_has_access = False` | Manually create the repo on GitHub/GitLab, then re-run experiment setup |
| `gi.get_repos()` listing | Repo browser shows empty list | Restart Pychron once network is restored |

### The silent MetaRepo abort

This is the most critical failure mode for new lab setups. In `DVC.initialize()`:

```python
try:
    self.open_meta_repo()
except BaseException as e:
    self.warning("Error opening meta repo {}".format(e))
    return   # ← no dialog, no exception — returns None silently
```

If `open_meta_repo()` fails for **any reason** — network timeout, bad credentials, missing repo, SSL certificate error — Pychron logs a one-line warning and continues loading. The application appears to start normally. The only visible indication is that the startup test `test_dvc_fetch_meta` stays red.

**Always check `~/.pychron.<app>/logs/pychron.log`** and search for `"Error opening meta repo"` when DVC isn't working after startup.

### Credential failures

| Scenario | Symptom | Recovery |
|---|---|---|
| GitHub PAT expired or wrong scope | `CredentialException` in log; `test_dvc_fetch_meta` red | Generate a new PAT with `repo` scope, update in **Preferences → GitHub → Token** |
| GitHub password auth attempted | `401` → `CredentialException` | GitHub removed password auth in 2021. Use a PAT. |
| GitLab token wrong or expired | Same as GitHub | Update token in **Preferences → GitLab** |
| No auth configured | `git clone` hangs waiting for interactive input | Configure a credential helper or set the PAT before launching |

---

## Missing or Misconfigured MetaRepo

| Scenario | Symptom | Recovery |
|---|---|---|
| `meta_repo_name` not set | Warning dialog on startup: *"Need to specify Meta Repository name"*; DVC aborts initialization | Set `meta_repo_name` in **Preferences → DVC → Connection** |
| MetaRepo exists locally but remote is gone | `meta_pull()` fails with `GitCommandError`; no remote to pull from | Re-create the remote repo on GitHub/GitLab and push the local clone |
| MetaRepo not on remote, not local either | `open_meta_repo()` falls through to `git init` locally; warning: *"You need to clone your MetaData repository manually"* | Create the MetaRepo on GitHub/GitLab and restart Pychron, or clone manually to `<dvc_dir>/<MetaRepoName>/` |
| MetaRepo freshly cloned, empty | `DVC._defaults()` auto-creates placeholder files and commits them | Populate irradiation data via **Entry → Irradiation** |
| Wrong `organization` in preferences | Repo lookup returns nothing; clone URL is `None`; `open_meta_repo()` inits locally instead | Correct the organization name in both **Preferences → DVC → Connection** and **Preferences → GitHub/GitLab** |

---

## Database Failures

| Scenario | Symptom | Recovery |
|---|---|---|
| MySQL not running at startup | `test_database` turns red; `db.connection_error` string shown in startup test detail | Start MySQL: `brew services start mysql` (macOS) or `systemctl start mysql` (Linux) |
| Wrong MySQL credentials | Same red `test_database` | Correct host/username/password in **Preferences → DVC → Connection** |
| `pychronmeta` database missing | `OperationalError: Unknown database 'pychronmeta'` in log | `mysql -u root -e "CREATE DATABASE pychronmeta CHARACTER SET utf8mb4;"` then re-run `alembic upgrade head` |
| Schema not migrated | `OperationalError: Table 'X' doesn't exist` | `cd alembic_dvc && alembic upgrade head` |
| Mid-session MySQL disconnect | `OperationalError` on next query; Pychron does not auto-reconnect | Restart Pychron after MySQL recovers |
| Database error during acquisition | `DVCPersister` catches `DatabaseError`; experiment is halted with *"Fatal — DatabaseError, see log"* | Fix MySQL connection, restart Pychron, and re-queue the experiment |

### `data_collection` branch sync failure

When `use_data_collection_branch=true`, Pychron calls `sync_repo_from_data_collection()` each time a data repo is loaded for reduction. This merges the `origin/data_collection` branch into the current branch. If the merge fails:

- The failure is caught as `BaseException` and logged as: *"This can be expected for local-only repos."*
- No dialog is shown. Data reduction proceeds from the current local branch state.
- If a merge was expected to deliver new acquisition data, reduction results will be stale.

**Recovery:** Pull and merge manually via the Repositories task, or set `use_data_collection_branch=false` if not actively using the branch separation workflow.

---

## Checking the Log

All DVC warnings and errors are written to:

```
~/.pychron.<app>/logs/pychron.log
```

Useful search terms: `DVC`, `meta_repo`, `Error opening meta repo`, `GitCommandError`, `OperationalError`, `CredentialException`.
