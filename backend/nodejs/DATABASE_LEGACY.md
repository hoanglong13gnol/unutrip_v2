# Legacy `database.sql` (deprecated)

`database.sql` in this folder is the **old monolithic schema** for XAMPP/phpMyAdmin (users, `destinations`, `rag_places`, …).

**Do not use it as the canonical schema for v2.**

| Goal | Use |
|------|-----|
| New environments | [`database/migrations/`](../../database/migrations/) via [`database/scripts/run_migrations.sh`](../../database/scripts/run_migrations.sh) |
| Docker stack | `docker compose up` (includes `db-migrate` service) |
| Docs | [`database/README.md`](../../database/README.md) |

`database.sql` remains only as an optional **bootstrap** when `DATABASE_BOOTSTRAP_LEGACY=true` and the database has no `users` table yet.
