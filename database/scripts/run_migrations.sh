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
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_DATABASE="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [[ -n "${MIGRATIONS_DIR:-}" ]]; then
  REPO_DATABASE="$(cd "$(dirname "$MIGRATIONS_DIR")" && pwd)"
else
  echo "ERROR: cannot resolve REPO_DATABASE (set MIGRATIONS_DIR or run from repo script path)" >&2
  exit 1
fi
MIGRATIONS_DIR="${MIGRATIONS_DIR:-$REPO_DATABASE/migrations}"
LEGACY_SQL="${LEGACY_SQL:-$REPO_DATABASE/../backend/nodejs/database.sql}"
SKIP_VALIDATION="${SKIP_MIGRATION_VALIDATION:-false}"
QUICK_POPULATE_SQL="${QUICK_POPULATE_SQL:-$REPO_DATABASE/quick_populate_app_places_from_legacy_database_sql.sql}"
SEEDS_DIR="${SEEDS_DIR:-$REPO_DATABASE/seeds}"

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

column_exists() {
  local table="$1"
  local column="$2"
  mysql_cmd -Nse \
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='${DB_NAME}' AND table_name='${table}' AND column_name='${column}'"
}

row_count() {
  local table="$1"
  mysql_cmd -Nse "SELECT COUNT(*) FROM \`${table}\`"
}

migration_applied() {
  local filename="$1"
  mysql_cmd -Nse \
    "SELECT COUNT(*) FROM schema_migrations WHERE filename='${filename}'"
}

record_migration() {
  local filename="$1"
  mysql_cmd -e "INSERT IGNORE INTO schema_migrations (filename) VALUES ('${filename}')"
}

ensure_schema_migrations_table() {
  if [[ "$(table_exists schema_migrations)" != "0" ]]; then
    return 0
  fi
  local bootstrap="$MIGRATIONS_DIR/012_schema_migrations.sql"
  if [[ ! -f "$bootstrap" ]]; then
    echo "WARNING: schema_migrations missing and $bootstrap not found; tracking disabled" >&2
    return 0
  fi
  echo "+ bootstrap schema_migrations"
  run_sql_file "$bootstrap"
  record_migration "012_schema_migrations.sql"
}

# Full v2 data migrations (006–009) need extended legacy schema or rag_places.
destinations_is_v2_ready() {
  if [[ "$(table_exists destinations)" == "0" ]]; then
    return 1
  fi
  if [[ "$(column_exists destinations short_description)" != "0" ]] \
    && [[ "$(column_exists destinations rag_place_id)" != "0" ]]; then
    return 0
  fi
  if [[ "$(table_exists rag_places)" != "0" ]]; then
    return 0
  fi
  return 1
}

itinerary_items_fk_target() {
  mysql_cmd -Nse \
    "SELECT REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE \
     WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='itinerary_items' \
       AND COLUMN_NAME='destination_id' AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1"
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

ensure_schema_migrations_table

for file in "${files[@]}"; do
  base="$(basename "$file")"
  if [[ "$(table_exists schema_migrations)" != "0" ]] && [[ "$(migration_applied "$base")" != "0" ]]; then
    echo "= skip (already applied): $base"
    continue
  fi
  case "$base" in
    006_*|007_*|008_*|009_*)
      if [[ "$(table_exists destinations)" == "0" ]]; then
        echo "~ skip $base (no legacy \`destinations\`)"
        continue
      fi
      if ! destinations_is_v2_ready; then
        echo "~ skip $base (minimal legacy \`destinations\` schema)"
        continue
      fi
      ;;
    010_*)
      if [[ "$SKIP_VALIDATION" == "true" ]] || [[ "$(table_exists destinations)" == "0" ]] || ! destinations_is_v2_ready; then
        echo "~ skip $base (validation needs v2 legacy tables)"
        continue
      fi
      ;;
    011_*)
      if [[ "$(table_exists itinerary_items)" != "0" ]]; then
        fk_target="$(itinerary_items_fk_target)"
        if [[ "$fk_target" == "destinations" ]]; then
          echo "WARNING: itinerary_items.destination_id FK -> destinations (legacy); skip $base"
          continue
        fi
      fi
      ;;
  esac
  run_sql_file "$file"
  if [[ "$(table_exists schema_migrations)" != "0" ]]; then
    record_migration "$base"
  fi
done

if [[ "$(table_exists destinations)" != "0" ]] \
  && [[ "$(row_count destinations)" != "0" ]] \
  && [[ "$(table_exists app_places)" != "0" ]] \
  && [[ "$(row_count app_places)" == "0" ]] \
  && ! destinations_is_v2_ready \
  && [[ -f "$QUICK_POPULATE_SQL" ]]; then
  echo "+ quick populate app_places from legacy destinations"
  run_sql_file "$QUICK_POPULATE_SQL"
fi

if [[ "$(table_exists app_places)" != "0" ]] \
  && [[ "$(row_count app_places)" == "0" ]] \
  && [[ -d "$SEEDS_DIR" ]]; then
  shopt -s nullglob
  seed_files=("$SEEDS_DIR"/[0-9][0-9][0-9]_*.sql)
  if [[ ${#seed_files[@]} -gt 0 ]]; then
    echo "+ seed minimal demo app_places (empty table fallback)"
    for seed in "${seed_files[@]}"; do
      run_sql_file "$seed"
    done
  fi
fi

echo "OK migrations applied to ${DB_NAME} on ${MYSQL_HOST}"
