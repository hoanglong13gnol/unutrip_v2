# Local database dumps (gitignored)

Đặt file `.sql` lớn tại đây, ví dụ `unudata_v2.sql`, thay vì root monorepo.

```bash
# Import (MySQL local)
mysql -u root -p unudata < database/dumps/unudata_v2.sql
```

Sau import, chạy migrations nếu cần: `database/scripts/run_migrations.sh`.

Root repo **không** track `*.sql` dump (xem `.gitignore`).
