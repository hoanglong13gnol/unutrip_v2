"""
Zip current data/ artifacts for release upload (Phase D).

Requires a prior build:
  python jobs/build_rag_artifacts.py --from-db

Usage:
  python jobs/package_rag_artifacts.py
  python jobs/package_rag_artifacts.py -o dist/unutrip-rag-artifacts.zip
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

from core.config import settings

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist" / "unutrip-rag-artifacts.zip"

PATHS = (
    "processed/places_rag_documents.jsonl",
    "processed/places_app.json",
    "indexes/bm25_index.pkl",
    "indexes/rag_artifacts_manifest.json",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    verify = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_rag_artifacts.py"), "--strict"],
        cwd=str(ROOT),
        check=False,
    )
    if verify.returncode != 0:
        raise SystemExit("Build and verify artifacts before packaging")

    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    data_root = ROOT / "data"

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in PATHS:
            src = data_root / rel
            if not src.is_file():
                if rel.endswith("places_app.json"):
                    continue
                raise FileNotFoundError(src)
            zf.write(src, arcname=f"data/{rel}")

    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
