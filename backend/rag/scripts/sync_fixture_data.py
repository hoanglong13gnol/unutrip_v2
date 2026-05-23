"""
Copy tracked CI fixtures into data/processed (Phase 4 reproducible pipeline).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import settings
from core.fixture_paths import FIXTURE_CORPUS, FIXTURE_PLACES_APP


def sync_fixture_data(*, corpus_only: bool = False, places_only: bool = False) -> None:
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)

    if not places_only:
        if not FIXTURE_CORPUS.is_file():
            raise FileNotFoundError(f"Missing fixture corpus: {FIXTURE_CORPUS}")
        shutil.copy2(FIXTURE_CORPUS, settings.rag_documents_file)
        print(f"Copied corpus -> {settings.rag_documents_file}")

    if not corpus_only:
        if not FIXTURE_PLACES_APP.is_file():
            raise FileNotFoundError(f"Missing fixture places_app: {FIXTURE_PLACES_APP}")
        shutil.copy2(FIXTURE_PLACES_APP, settings.places_app_file)
        print(f"Copied places_app -> {settings.places_app_file}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-only", action="store_true")
    ap.add_argument("--places-only", action="store_true")
    args = ap.parse_args()
    sync_fixture_data(corpus_only=args.corpus_only, places_only=args.places_only)


if __name__ == "__main__":
    main()
