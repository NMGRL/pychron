---
id: offline-mode
title: Working Offline
sidebar_label: Offline Mode
sidebar_position: 5
---

# Working Offline

Pychron's offline mode allows labs to run data reduction without network access to GitHub or GitLab. It works by cloning required repositories to local disk, exporting the central MySQL database to a SQLite file, and reconfiguring DVC to read from those local copies. The tool that orchestrates this is `WorkOffline` (`pychron/dvc/work_offline.py`), accessible via **Tools → Work Offline**.

Offline mode is **read-oriented** — existing analyses can be loaded and reduced, but new acquisition commits and pushes will queue locally until you reconnect and run **Tools → Share Changes**.

## When to Use Offline Mode

- Fieldwork or travel where the lab's GitHub/GitLab instance is unreachable
- Network maintenance periods
- Laptops without persistent VPN access to an institution GitLab server

## The Offline Setup Process

Run this while you still have network access. The `WorkOffline` tool performs these four steps:

1. **Select repositories** — Choose which data repositories to clone from the GitHub/GitLab repo list. The MetaRepo is always included.
2. **Clone and update** — Clones each selected repo to `~/.pychron.<app>/data/.dvc/repositories/` and pulls the latest MetaRepo state.
3. **Export database** — Copies the central MySQL database to a SQLite snapshot at `~/.pychron.<app>/data/offline_db/index.sqlite3`.
4. **Switch connection** — Calls `switch_to_offline_database()`, which updates the active DVC connection profile to `kind=sqlite` pointing at the snapshot file and saves preferences.

After step 4, Pychron uses only local files — no network calls are made.

:::warning `WorkOffline` requires network access to run
The tool must list repositories from GitHub/GitLab to let you select what to clone. You cannot run `WorkOffline` after you have already lost connectivity. Plan offline sessions in advance.
:::

## Switching Back to Online Mode

When network access is restored:

1. Go to **Preferences → DVC → Connection** and switch the active profile back to `kind=mysql` (or select your MySQL profile).
2. Run **Tools → Share Changes** to push any commits that accumulated on the `data_collection` branch or data repos while offline.
3. Run **Tools → Upload Database** if you created new samples, irradiations, or projects offline that need to be written back to the central MySQL instance.

## `data_collection` Branch Sync Failure While Offline

If `use_data_collection_branch=true` and the network is down, Pychron's `sync_repo_from_data_collection()` will fail silently every time a data repository is opened for reduction:

- The merge attempt is caught as `BaseException` and logged as: *"This can be expected for local-only repos."*
- No dialog is shown. Reduction proceeds from the local branch state.
- If new acquisition commits were pushed to `origin/data_collection` by another workstation before you went offline, those commits will not be present in your local copy and your reduction results will not include them.

**Mitigation:** Before going offline, do a manual `git pull` in each data repo you plan to reduce, so local branches are up to date. If you see unexpected gaps in offline reduction results, this is the most likely cause.

## Known Limitations

:::warning `offline_index.py` is dead code — SQLite sync is manual
`pychron/dvc/offline_index.py` is entirely commented out (268 lines). An earlier design envisioned a purpose-built SQLite index for offline browsing — it was never completed. The current offline database is a point-in-time copy of MySQL made at export time. It is not updated automatically while offline.

Specifically:
- New analyses acquired offline are committed to local git repos but **are not inserted into the offline SQLite database**. They will not appear in the analysis browser until MySQL is updated after reconnecting.
- There is no incremental sync. If MySQL data changed while you were offline (another user ran analyses), those changes will not appear in the SQLite snapshot until you run **Tools → Work Offline** again.
:::
