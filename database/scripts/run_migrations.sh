#!/usr/bin/env bash
# Apply database/migrations in order. Safe to re-run (migrations use IF NOT EXISTS / upserts).
#
# Env:
#   MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, DB_NAME
#   DATABASE_BOOTSTRAP_LEGACY=true  — import backend/nodejs/database.sql when `users` missing
#   MIGRATIONS_DIR=/migrations      — default in Docker
#   LEGACY_SQL=/legacy/database.sql
#   SKIP_MIGRATION_VALIDATION=true — skip 010 validation SELECTs

set -euo pipefail

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
DB_NAME="${DB_NAME:-unudata}"
BOOTSTRAP_LEGACY="${DATABASE_BOOTSTRAP_LEGACY:-false}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DATABASE="$(cd "$SCRIPT_DIR/.." && pwd)"
MIGRATIONS_DIR="${MIGRATIONS_DIR:-$REPO_DATABASE/migrations}"
LEGACY_SQL="${LEGACY_SQL:-$REPO_DATABASE/../backend/nodejs/database.sql}"
SKIP_VALIDATION="${SKIP_MIGRATION_VALIDATION:-false}"

mysql_cmd() {
  export MYSQL_PWD="$MYSQL_PASSWORD"
  mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" "$DB_NAME" "$@"
}

wait_mysql() {
  for _ in $(seq 1 60); do
    if mysql_cmd -e "SELECT 1" &>/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "ERROR: MySQL not ready at $MYSQL_HOST:$MYSQL_PORT" >&2
  exit 1
}

table_exists() {
  local table="$1"
  mysql_cmd -Nse \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name='${table}'"
}

run_sql_file() {
  local file="$1"
  echo "+ $(basename "$file")"
  mysql_cmd <"$file"
}

wait_mysql

if [[ "$(table_exists users)" == "0" ]]; then
  if [[ "$BOOTSTRAP_LEGACY" == "true" && -f "$LEGACY_SQL" ]]; then
    echo "+ bootstrap legacy schema: $LEGACY_SQL"
    run_sql_file "$LEGACY_SQL"
  else
    echo "ERROR: table \`users\` missing. Set DATABASE_BOOTSTRAP_LEGACY=true or import schema first." >&2
    exit 1
  fi
fi

shopt -s nullglob
files=("$MIGRATIONS_DIR"/[0-9][0-9][0-9]_*.sql)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "ERROR: no migrations in $MIGRATIONS_DIR" >&2
  exit 1
fi

for file in "${files[@]}"; do
  base="$(basename "$file")"
  case "$base" in
    006_*|007_*|008_*|009_*)
      if [[ "$(table_exists destinations)" == "0" ]]; then
        echo "~ skip $base (no legacy \`destinations\`)"
        continue
      fi
      ;;
    010_*)
      if [[ "$SKIP_VALIDATION" == "true" ]] || [[ "$(table_exists destinations)" == "0" ]]; then
        echo "~ skip $base (validation needs legacy tables)"
        continue
      fi
      ;;
  esac
  run_sql_file "$file"
done

echo "OK migrations applied to ${DB_NAME} on ${MYSQL_HOST}"
