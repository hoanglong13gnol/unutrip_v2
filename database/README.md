# Database (v2 canonical path)

**Source of truth:** `database/migrations/` (numbered SQL).  
**Deprecated:** `backend/nodejs/database.sql` — legacy bootstrap cho Docker DB trống.

**Local dumps:** file `.sql` lớn → `database/dumps/` (gitignored). Xem [`dumps/README.md`](dumps/README.md).

## Trạng thái runtime (Node)

API `/destinations/*` đọc **`app_places`** + **`place_images`** — không phải bảng legacy `destinations`.  
Legacy `destinations` chỉ còn trong bootstrap SQL, seed dev, và optional place-id fallback.

Chi tiết flags: [`docs/v2/PHASE7_NODE_ANDROID_PARITY.md`](../docs/v2/PHASE7_NODE_ANDROID_PARITY.md).

---

## Docker Compose (khuyến nghị)

```bash
cp .env.example .env
docker compose up -d --build
```

Service **`db-migrate`** chạy một lần sau MySQL healthy:

1. Nếu chưa có bảng `users` và `DATABASE_BOOTSTRAP_LEGACY=true` (default): import `database.sql`
2. Apply migrations `001` … `011` (skip có điều kiện — xem [`migrations/README.md`](migrations/README.md))

Backend Compose mặc định:

- `USE_V2_PLACE_TABLES=true`
- `PLACE_ID_LEGACY_FALLBACK=false`

---

## Ba cách khởi tạo DB

### A — Import dump có sẵn (dev/staging, khuyến nghị)

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS unudata CHARACTER SET utf8mb4;"
mysql -u root -p unudata < database/dumps/unudata_v2.sql

export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD= DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash database/scripts/run_migrations.sh
```

### B — Docker volume mới + legacy bootstrap

```bash
# .env: DATABASE_BOOTSTRAP_LEGACY=true (default)
docker compose up -d --build
```

- Tạo schema legacy tối thiểu từ `database.sql`
- Migrations 006–009 **skip** nếu không có dữ liệu `destinations` / `rag_places`
- Phù hợp smoke stack; **không** đủ data địa điểm cho app đầy đủ

### C — Fresh v2 (chưa có seed chính thức)

```bash
export DATABASE_BOOTSTRAP_LEGACY=false
# Cần bảng users tối thiểu trước
bash database/scripts/run_migrations.sh
# Populate app_places thủ công hoặc quick_populate script
```

---

## Troubleshooting bootstrap

| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| Migration 007–009 fail | DB trống, thiếu `destinations`/`rag_places` | Import dump (A) hoặc set bootstrap legacy + data |
| Backend 500 list destinations | `app_places` trống | Chạy 006 populate hoặc import dump |
| `itinerary_items` FK fail | Thiếu migration 011 | `run_migrations.sh` — file 011 idempotent |
| Place id AI không map | Thiếu `place_id_map` | Migration 007 + data; check flags v2 |
| RAG build `--from-db` fail | `rag_knowledge_base` trống | Migration 009 hoặc export pipeline |

**Quick bridge (dev):**  
`quick_populate_app_places_from_legacy_database_sql.sql` — copy `destinations` → `app_places` khi đã import legacy SQL nhưng skip 006.

---

## Local MySQL (XAMPP)

```bash
# 1. Import dump HOẶC database.sql
# 2. Migrate
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD=... DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false   # nếu đã có legacy data
bash database/scripts/run_migrations.sh
```

Local Node mặc định `USE_V2_PLACE_TABLES=false` — bật `true` sau khi có `app_places` + map.

---

## Validation

Sau populate legacy → v2:

```bash
mysql -u root -p unudata < database/migrations/010_v2_validation_queries.sql
```

---

## Migration order

Xem chi tiết locked decisions: [`migrations/README.md`](migrations/README.md).

```
001 app_places → 002 rag_knowledge_base → 003 place_images → 004 place_id_map
→ 005 indexes → 006–009 populate → 010 validation → 011 itineraries
```

---

## Liên kết

- [`docs/v2/BACKEND_ARCHITECTURE.md`](../docs/v2/BACKEND_ARCHITECTURE.md)
- [`scripts/run_migrations.sh`](scripts/run_migrations.sh)
- Root [`docker-compose.yml`](../docker-compose.yml)
