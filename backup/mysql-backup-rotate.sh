#!/usr/bin/env bash
set -euo pipefail

MYSQLDUMP_EXE="${MYSQLDUMP_EXE:-mysqldump}"
DEFAULTS_FILE="${DEFAULTS_FILE:-$HOME/.mysql-backup.cnf}"
DATABASE="${DATABASE:-your_database}"
BACKUP_ROOT="${BACKUP_ROOT:-$HOME/mysql_backups}"
KEEP_DAILY="${KEEP_DAILY:-14}"
KEEP_WEEKLY="${KEEP_WEEKLY:-8}"
KEEP_MONTHLY="${KEEP_MONTHLY:-24}"
KEEP_YEARLY="${KEEP_YEARLY:-10}"

ensure_dir() {
  local path="$1"
  mkdir -p "$path"
}

trim_rotation() {
  local path="$1"
  local keep="$2"
  local count=0

  if [[ ! -d "$path" ]]; then
    return 0
  fi

  while IFS= read -r file; do
    count=$((count + 1))
    if (( count > keep )); then
      rm -f "$file"
    fi
  done < <(ls -1t "$path"/*.sql.gz 2>/dev/null || true)
}

daily_path="$BACKUP_ROOT/daily"
weekly_path="$BACKUP_ROOT/weekly"
monthly_path="$BACKUP_ROOT/monthly"
yearly_path="$BACKUP_ROOT/yearly"

ensure_dir "$daily_path"
ensure_dir "$weekly_path"
ensure_dir "$monthly_path"
ensure_dir "$yearly_path"

stamp="$(date '+%Y-%m-%d_%H%M%S')"
file_name="${DATABASE}-${stamp}.sql.gz"
daily_file="$daily_path/$file_name"

"$MYSQLDUMP_EXE" \
  "--defaults-extra-file=$DEFAULTS_FILE" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  "$DATABASE" | gzip -9 > "$daily_file"

day_of_week="$(date '+%u')"
day_of_month="$(date '+%d')"
month="$(date '+%m')"

if [[ "$day_of_week" == "7" ]]; then
  cp -f "$daily_file" "$weekly_path/$file_name"
fi

if [[ "$day_of_month" == "01" ]]; then
  cp -f "$daily_file" "$monthly_path/$file_name"
fi

if [[ "$month" == "01" && "$day_of_month" == "01" ]]; then
  cp -f "$daily_file" "$yearly_path/$file_name"
fi

trim_rotation "$daily_path" "$KEEP_DAILY"
trim_rotation "$weekly_path" "$KEEP_WEEKLY"
trim_rotation "$monthly_path" "$KEEP_MONTHLY"
trim_rotation "$yearly_path" "$KEEP_YEARLY"

echo "Backup complete: $daily_file"
