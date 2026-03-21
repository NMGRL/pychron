#!/usr/bin/env bash
set -euo pipefail

MYSQL_EXE="${MYSQL_EXE:-mysql}"
DEFAULTS_FILE="${DEFAULTS_FILE:-$HOME/.mysql-backup.cnf}"
DATABASE="${DATABASE:-your_database}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/mysql_backups}"
ROTATION="${ROTATION:-daily}"
BACKUP_FILE="${BACKUP_FILE:-}"

usage() {
  cat <<EOF
Usage:
  $0 [--database DB] [--backup-root DIR] [--rotation daily|weekly|monthly|yearly|all] [--backup-file FILE]

Environment variable alternatives:
  MYSQL_EXE, DEFAULTS_FILE, DATABASE, BACKUP_ROOT, ROTATION, BACKUP_FILE
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --database)
      DATABASE="$2"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="$2"
      shift 2
      ;;
    --rotation)
      ROTATION="$2"
      shift 2
      ;;
    --backup-file)
      BACKUP_FILE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

newest_from_dir() {
  local dir="$1"
  ls -1t "$dir"/*.sql.gz 2>/dev/null | head -n 1 || true
}

if [[ -z "$BACKUP_FILE" ]]; then
  case "$ROTATION" in
    daily|weekly|monthly|yearly)
      BACKUP_FILE="$(newest_from_dir "$BACKUP_ROOT/$ROTATION")"
      ;;
    all)
      BACKUP_FILE="$(
        {
          newest_from_dir "$BACKUP_ROOT/daily"
          newest_from_dir "$BACKUP_ROOT/weekly"
          newest_from_dir "$BACKUP_ROOT/monthly"
          newest_from_dir "$BACKUP_ROOT/yearly"
        } | awk 'NF' | xargs ls -1t 2>/dev/null | head -n 1
      )"
      ;;
    *)
      echo "Invalid rotation: $ROTATION" >&2
      exit 1
      ;;
  esac
fi

if [[ -z "$BACKUP_FILE" || ! -f "$BACKUP_FILE" ]]; then
  echo "No backup file found." >&2
  exit 1
fi

gunzip -c "$BACKUP_FILE" | "$MYSQL_EXE" "--defaults-extra-file=$DEFAULTS_FILE" "$DATABASE"

echo "Restore complete from: $BACKUP_FILE"
