"""Quick check: which DB has v2 RAG tables."""
from __future__ import annotations

import os

import pymysql
from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT, ".env"))

HOST = os.getenv("DB_HOST", "127.0.0.1")
PORT = int(os.getenv("DB_PORT", "3306"))
USER = os.getenv("DB_USER", "root")
PASSWORD = os.getenv("DB_PASSWORD", "")


def scan_all() -> None:
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD)
    cur = conn.cursor()
    cur.execute("SHOW DATABASES")
    skip = {"information_schema", "performance_schema", "mysql", "sys", "phpmyadmin"}
    for (db,) in cur.fetchall():
        if db in skip:
            continue
        try:
            cur.execute(f"USE `{db}`")
            cur.execute("SHOW TABLES LIKE 'rag_knowledge_base'")
            if not cur.fetchone():
                continue
            cur.execute("SELECT COUNT(*) FROM rag_knowledge_base")
            kb = int(cur.fetchone()[0])
            cur.execute("SHOW TABLES LIKE 'app_places'")
            places = -1
            if cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM app_places")
                places = int(cur.fetchone()[0])
            print(f"OK {db}: rag_knowledge_base={kb}, app_places={places}")
        except Exception as exc:
            print(f"SKIP {db}: {exc}")
    conn.close()


def probe_configured() -> None:
    db = os.getenv("DB_NAME", "unutrip_v2")
    conn = pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD, database=db,
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM rag_knowledge_base")
    kb = int(cur.fetchone()[0])
    cur.execute("SHOW TABLES LIKE 'app_places'")
    places = -1
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) FROM app_places")
        places = int(cur.fetchone()[0])
    print(f"CONFIGURED {db}: rag_knowledge_base={kb}, app_places={places}")
    conn.close()


if __name__ == "__main__":
    print(f"Host {HOST}:{PORT} user={USER}")
    scan_all()
    db = os.getenv("DB_NAME")
    if db:
        try:
            probe_configured()
        except Exception as exc:
            print(f"CONFIGURED {db}: FAIL {exc}")
