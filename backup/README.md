# MySQL Backup Scripts

This folder contains scripts for Windows, macOS, and Linux:

- `mysql-backup-rotate.ps1` and `mysql-restore-latest.ps1` for Windows 11 (PowerShell)
- `windows-zdrive-backup.ps1` for copying `setupfiles`, `scripts`, `data`, `.appdata`, `experiments`, `preferences`, and `queue_conditionals` to a Z: drive
- `mysql-backup-rotate.sh` and `mysql-restore-latest.sh` for macOS/Linux (Bash)

All backup scripts support:

- Daily backups
- Weekly rotation (Sunday)
- Monthly rotation (1st day of month)
- Yearly rotation (January 1st)
- Retention cleanup for each rotation

## Credentials file

Use a MySQL defaults file with restricted permissions.

Windows example (`C:\secure\mysql-backup.cnf`):

```ini
[client]
user=backup_user
password=YOUR_PASSWORD
host=127.0.0.1
port=3306
```

macOS/Linux example (`~/.mysql-backup.cnf`):

```ini
[client]
user=backup_user
password=YOUR_PASSWORD
host=127.0.0.1
port=3306
```

On macOS/Linux, run `chmod 600 ~/.mysql-backup.cnf`.

## Windows usage

Backup:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup\mysql-backup-rotate.ps1 `
  -Database "your_database" `
  -RootBackupDirectory "D:\MySQLBackups"
```

Z: drive file backup:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup\windows-zdrive-backup.ps1 `
  -SourceRoot "C:\path\to\repo" `
  -DestinationRoot "Z:\pychron_umelbourne"
```

Restore latest daily:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup\mysql-restore-latest.ps1 `
  -Database "your_database" `
  -RootBackupDirectory "D:\MySQLBackups" `
  -Rotation daily
```

Restore latest across all rotations:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup\mysql-restore-latest.ps1 `
  -Database "your_database" `
  -RootBackupDirectory "D:\MySQLBackups" `
  -Rotation all
```

Schedule nightly in Task Scheduler (for example 2:00 AM):

- Program/script: `powershell.exe`
- Arguments:

```text
-ExecutionPolicy Bypass -File "C:\path\to\repo\backup\mysql-backup-rotate.ps1" -Database "your_database" -RootBackupDirectory "D:\MySQLBackups"
```

You can also set `MYSQL_BACKUP_ROOT` and omit `-RootBackupDirectory`.

Schedule the Z: drive backup nightly in Task Scheduler (for example 2:30 AM):

- Program/script: `powershell.exe`
- Arguments:

```text
-ExecutionPolicy Bypass -File "C:\path\to\repo\backup\windows-zdrive-backup.ps1" -SourceRoot "C:\path\to\repo" -DestinationRoot "Z:\pychron"
```

## macOS/Linux usage

Make scripts executable:

```bash
chmod +x ./backup/mysql-backup-rotate.sh ./backup/mysql-restore-latest.sh
```

Backup:

```bash
DATABASE="your_database" BACKUP_ROOT="$HOME/mysql_backups" ./backup/mysql-backup-rotate.sh
```

Restore latest daily:

```bash
DATABASE="your_database" BACKUP_ROOT="$HOME/mysql_backups" ROTATION="daily" ./backup/mysql-restore-latest.sh
```

Restore latest across all rotations:

```bash
DATABASE="your_database" BACKUP_ROOT="$HOME/mysql_backups" ROTATION="all" ./backup/mysql-restore-latest.sh
```

Run daily with `cron` or `systemd timers` depending on your system.

Cron example (daily at 2:00 AM):

```cron
0 2 * * * DATABASE="your_database" BACKUP_ROOT="$HOME/mysql_backups" /path/to/repo/backup/mysql-backup-rotate.sh >> /var/log/mysql-backup.log 2>&1
```

## Default retention

- Daily: 14
- Weekly: 8
- Monthly: 24
- Yearly: 10
