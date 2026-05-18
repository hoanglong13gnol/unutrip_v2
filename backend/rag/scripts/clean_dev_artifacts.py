#!/usr/bin/env python3
"""Remove local dev caches under backend/rag (safe to run anytime)."""

from __future__ import annotations

import shutil
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parents[1]

GLOB_REMOVE = [
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "unutrip_rag.egg-info",
    "reports",
]


def main() -> int:
    removed: list[str] = []
    for name in GLOB_REMOVE:
        path = RAG_ROOT / name
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed.append(str(path.relative_to(RAG_ROOT)) + "/")
        elif path.is_file():
            path.unlink(missing_ok=True)
            removed.append(str(path.relative_to(RAG_ROOT)))

    for pyc in RAG_ROOT.rglob("__pycache__"):
        if pyc.is_dir():
            shutil.rmtree(pyc, ignore_errors=True)
    removed.append("**/__pycache__/")

    if removed:
        print("Removed:")
        for item in removed:
            print(f"  - {item}")
    else:
        print("Nothing to clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
