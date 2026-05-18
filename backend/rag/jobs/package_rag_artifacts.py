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
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

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

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    sha_path = out.with_suffix(out.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {out.name}\n", encoding="utf-8")

    manifest_path = data_root / "indexes" / "rag_artifacts_manifest.json"
    manifest = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    release_meta = {
        "packaged_at_utc": datetime.now(UTC).isoformat(),
        "zip_name": out.name,
        "zip_bytes": out.stat().st_size,
        "zip_sha256": digest,
        "document_count": manifest.get("document_count"),
        "corpus_sha256": manifest.get("corpus_sha256"),
        "bm25_sha256": manifest.get("bm25_sha256"),
        "bundle_layout": "data/processed/* + data/indexes/* inside zip",
        "deploy_env": "RAG_ARTIFACT_BUNDLE_URL=https://<host>/path/to/" + out.name,
    }
    meta_path = out.with_name(out.name + ".RELEASE.json")
    meta_path.write_text(json.dumps(release_meta, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"SHA256 {digest}")
    print(f"Wrote {sha_path.name}, {meta_path.name}")


if __name__ == "__main__":
    main()
