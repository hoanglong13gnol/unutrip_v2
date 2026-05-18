# Database (v2 canonical path)

**Source of truth:** `database/migrations/` (numbered SQL).  
**Deprecated:** `backend/nodejs/database.sql` — legacy XAMPP monolith; only used as optional bootstrap for empty Docker DBs.

## Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up -d --build
```

Service `db-migrate` runs once after MySQL is healthy:

1. If `users` is missing and `DATABASE_BOOTSTRAP_LEGACY=true` (default): import `database.sql`
2. Apply `migrations/001` … `011` (skips `006`–`009` when no `destinations`; skips `010` without legacy data)

Backend in Compose defaults to **`USE_V2_PLACE_TABLES=true`** (no `destinations` fallback in place-id resolution).

## Local MySQL (existing XAMPP dump)

```bash
# 1. Import your dump OR legacy database.sql
# 2. Apply v2 migrations
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=... DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash database/scripts/run_migrations.sh
```

## Fresh v2 without legacy rows

Set `DATABASE_BOOTSTRAP_LEGACY=false` and ensure `users` exists (minimal seed). Migrations `006`–`009` are skipped automatically; populate `app_places` via your own seed or RAG export pipeline.

## Validation

After full legacy → v2 populate:

```bash
mysql ... unudata < database/migrations/010_v2_validation_queries.sql
```

## Quick bridge (dev only)

`quick_populate_app_places_from_legacy_database_sql.sql` — copies `destinations` → `app_places` when you already imported legacy SQL but skipped `006`.

See `migrations/README.md` for locked decisions and file order.
