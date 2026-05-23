# Local database dumps (gitignored)

Đặt file `.sql` lớn tại đây — **không** commit vào git.

## Ví dụ

```bash
# Tạo DB
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS unudata CHARACTER SET utf8mb4;"

# Import
mysql -u root -p unudata < database/dumps/unudata_v2.sql

# Apply v2 migrations (nếu dump chưa đủ schema mới)
export MYSQL_HOST=127.0.0.1 MYSQL_USER=root MYSQL_PASSWORD= DB_NAME=unudata
export DATABASE_BOOTSTRAP_LEGACY=false
bash database/scripts/run_migrations.sh
```

## Quy ước tên

| File gợi ý | Mục đích |
|------------|----------|
| `unudata_v2.sql` | Full dump staging/dev |
| `unudata_v2_test` | DB name thường dùng khi test RAG `--from-db` |

Xem [`docs/v2/NAMING.md`](../../docs/v2/NAMING.md).

Root repo gitignore `*.sql` dump lớn — chỉ giữ README này tracked.

Chi tiết bootstrap: [`../README.md`](../README.md)
