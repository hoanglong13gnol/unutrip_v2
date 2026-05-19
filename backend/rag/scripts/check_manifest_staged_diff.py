#!/usr/bin/env python3
"""
Pre-commit / CI: reject staged manifest edits that only change built_at_utc.

Commit manifest when corpus_sha256, bm25_sha256, or document_count change intentionally.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MANIFEST = Path("data/indexes/rag_artifacts_manifest.json")
CONTENT_KEYS = ("corpus_sha256", "bm25_sha256", "document_count", "corpus_path", "bm25_index_path")


def _git(*args: str) -> str | None:
    try:
        out = subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True)
        return out.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _load_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main() -> int:
    repo_root = _git("rev-parse", "--show-toplevel")
    if not repo_root:
        return 0

    manifest = Path(repo_root) / "backend" / "rag" / MANIFEST
    if not manifest.exists():
        return 0

    rel = f"backend/rag/{MANIFEST.as_posix()}"
    staged = _git("-C", repo_root, "diff", "--cached", "--name-only", "--", rel)
    if not staged:
        return 0

    head_raw = _git("-C", repo_root, "show", f"HEAD:{rel}")
    index_raw = _git("-C", repo_root, "show", f":{rel}") or manifest.read_text(encoding="utf-8")

    head = _load_json(head_raw)
    staged_doc = _load_json(index_raw)
    if not staged_doc:
        print("ERROR: staged manifest is not valid JSON", file=sys.stderr)
        return 1

    if head is None:
        return 0

    head_content = {k: head.get(k) for k in CONTENT_KEYS}
    staged_content = {k: staged_doc.get(k) for k in CONTENT_KEYS}
    if head_content == staged_content and head.get("built_at_utc") != staged_doc.get("built_at_utc"):
        print(
            "ERROR: manifest staged with only built_at_utc change.\n"
            "  Rebuild artifacts and commit hash/count changes, or unstage:\n"
            "  git restore --staged backend/rag/data/indexes/rag_artifacts_manifest.json",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
