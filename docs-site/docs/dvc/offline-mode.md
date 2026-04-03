---
id: offline-mode
title: Working Offline
sidebar_label: Offline Mode
sidebar_position: 5
---

# Working Offline

Pychron's offline mode allows labs to run data reduction without network access to GitHub or GitLab. It works by cloning the required data and MetaRepo repositories to local disk, exporting the central MySQL database to a SQLite file, and reconfiguring DVC to read from those local copies. The tool that orchestrates this is `WorkOffline` (`pychron/dvc/work_offline.py`), accessible via **Tools → Work Offline**.

## When to use offline mode

- Fieldwork or travel where the lab's GitHub/GitLab instance is unreachable
- Network maintenance periods
- Laptops that don't have persistent VPN access to the institution's GitLab server

Offline mode is **read-oriented** — you can load and reduce existing analyses, but new acquisitions and pushes will be queued until you reconnect and run **Tools → Share Changes**.

## The offline setup process

The `WorkOffline` tool performs these steps:

1. **Select repositories** — Choose which data repositories to clone (from the GitHub/GitLab repo list). The MetaRepo is always included.
2. **Clone repositories** — Clones each selected repo to `~/.pychron.<app>/data/.dvc/repositories/`.
3. **Update MetaRepo** — Pulls the latest MetaRepo state.
4. **Export database** — Copies the MySQL database to a SQLite file at `~/.pychron.<app>/data/offline_db/index.sqlite3`.
5. **Switch preferences** — Calls `switch_to_offline_database()` which sets `pychron.dvc.connection.kind = "sqlite"` and `pychron.dvc.connection.path = <sqlite_path>` in the preference store, then saves.

After step 5, Pychron uses the local SQLite database and local git repositories for all operations — no network calls are made.

## Switching back to online mode

When network access is restored:

1. Go to **Preferences → DVC → Connection** and switch the connection `kind` back to `"mysql"` (or select the MySQL connection profile).
2. Run **Tools → Share Changes** to push any commits that accumulated on the `data_collection` branch or on local data repos while offline.
3. Run **Tools → Upload Database** if you added samples, irradiations, or projects while offline that need to be synced to the central MySQL instance.

## Known limitations

- `pychron/dvc/offline_index.py` is entirely commented out (268 lines of dead code). An earlier design envisioned a separate SQLite index for offline analysis browsing — this was never completed. The current offline database is a straight SQLite copy of MySQL, not a purpose-built index.
- New analyses acquired offline are committed to the local git repos but are not in the offline SQLite database. They will not appear in the analysis browser until the MySQL database is updated after reconnecting.
- The `WorkOffline` UI requires an active connection to GitHub/GitLab to list available repositories for cloning. Plan offline sessions in advance while connected.
