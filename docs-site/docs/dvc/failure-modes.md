---
id: failure-modes
title: DVC Failure Modes
sidebar_label: Failure Modes
sidebar_position: 4
---

# DVC Failure Modes

DVC has several failure scenarios where the system degrades silently rather than surfacing a clear error to the user. This page documents every known failure mode, its symptom, the code location responsible, and the recovery action.

## GitHub / GitLab unreachable

| Failure point | Symptom | Error handling | Recovery |
|---|---|---|---|
| MetaRepo clone at startup | `test_dvc_fetch_meta` fails; **no dialog shown** | `BaseException` caught in `DVC.initialize()`, logged as warning only | Check network, then restart Pychron |
| `meta_pull()` at startup | `test_dvc_fetch_meta` fails | `GitCommandError` propagates if `meta_pull` is called after a bad `open_meta_repo` | Same as above |
| `push_repository()` after acquisition | Non-fatal dialog: *"DVC/Git upload not successful. Cancel the experiment?"* | Caught as `GitCommandError` in `DVCPersister.post_measurement_save()` | Accept non-fatal → data is committed locally, push pending. Run **Tools → Share Changes** when network is restored. |
| `meta_push()` after acquisition | Same non-fatal dialog | Same catch | Same recovery |
| `gi.create_repo()` (new data repo creation) | **Silent success reported** even though nothing was created | `SSLError` sets `self._has_access = False`, method returns `True` | Manually create the repo on GitHub, then re-run the experiment setup |
| `gi.get_repos()` listing | Empty list returned | `SSLError` caught, `_has_access = False` | Repos won't populate in the browser; restart Pychron when network is available |

### The silent MetaRepo abort

This is the most important failure mode to understand. In `DVC.initialize()`:

```python
try:
    self.open_meta_repo()
except BaseException as e:
    self.warning("Error opening meta repo {}".format(e))
    return   # ← returns None, no dialog, no exception
```

If `open_meta_repo()` fails for **any reason** — network timeout, bad credentials, missing repo, SSL error — Pychron logs a one-line warning and continues loading. The startup test `test_dvc_fetch_meta` will show red, but there is no popup. **Always check the log file** at `~/.pychron.<app>/logs/pychron.log` when DVC isn't working.

---

## MySQL database unreachable

| Symptom | What happens | Recovery |
|---|---|---|
| `test_database` startup test red | `db.connect(warn=False)` returns `False`; `db.connection_error` string shown in startup test detail | Start MySQL, verify host/credentials in Preferences → DVC → Connection |
| Database error during acquisition | `DatabaseError` caught in `DVCPersister`; `("Fatal", "DatabaseError. see log")` put on exception queue | Stops the experiment. Fix MySQL connection, restart Pychron. |
| Mid-session connection drop | `OperationalError` raised on next `session_ctx()` call | Pychron does not auto-reconnect. Restart required. |

---

## Wrong or missing credentials

| Scenario | Symptom | Recovery |
|---|---|---|
| GitHub PAT expired or wrong | `CredentialException` raised inside `_get()` → uncaught in most call sites → startup test fails with traceback in log | Generate a new PAT with `repo` scope, update in Preferences → GitHub → Token |
| GitHub password auth | `401` → `CredentialException` | GitHub removed password auth in 2021. Use a PAT. |
| GitLab token wrong | Same as GitHub | Update token in Preferences → GitLab |
| No auth configured | `git clone` prompts interactively → hangs in CI/headless | Set `GIT_ASKPASS` or configure the credential helper before launching |

---

## MetaRepo missing or empty

| Scenario | Symptom | Recovery |
|---|---|---|
| `meta_repo_name` not set in preferences | Warning dialog on startup: *"Need to specify Meta Repository name"*, DVC returns without initializing | Set `meta_repo_name` in Preferences → DVC → Connection |
| MetaRepo dir doesn't exist locally, remote also missing | `open_meta_repo()` falls through to `git init` locally; warns: *"You need to clone your MetaData repository manually"* | Create the MetaRepo on GitHub/GitLab, then restart Pychron |
| MetaRepo freshly cloned but empty | `_defaults()` runs and creates placeholder files; `meta_commit` + `meta_push` | Populate irradiation data via **Entry → Irradiation** |

---

## Data repository missing locally

| Scenario | Symptom | Recovery |
|---|---|---|
| Repo directory doesn't exist before experiment run | `GitRepoManager.open_repo()` fails on a missing path | The automated run factory should clone the repo before `DVCPersister.initialize()` is called. If the clone fails silently, the persister operates on a broken repo handle and all file writes fail. Check network and re-run. |
| Repo has uncommitted changes (dirty state) | If `check_for_changes=true`, a warning is shown | Commit or stash changes manually via **Repositories → \<repo\> → Status** |

---

## Data repo `data_collection` branch sync failure

When `use_data_collection_branch=true` and a data repo has a remote `data_collection` branch, Pychron automatically merges it at load time (`sync_reduction_repo_from_data_collection`). If the merge fails:

- The failure is caught as `BaseException` and logged: *"This can be expected for local-only repos."*
- No dialog is shown. Data loads from the current local branch state.
- This can cause stale reduction results to be shown if the merge was expected to bring in new data.

**Recovery:** Pull and merge manually via the Repositories task, or disable `use_data_collection_branch` if not in use.

---

## Checking the log

All DVC warnings and errors are written to:

```
~/.pychron.<app>/logs/pychron.log
```

Search for `DVC`, `meta_repo`, `GitCommandError`, or `OperationalError` to find relevant entries.
