"""RAG artifact / processed file presence checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.artifacts import manifest_status_block
from core.config import settings

REQUIRED_RAG_FILE_KEYS = (
    "places_master",
    "places_app",
    "places_itinerary",
    "rag_documents",
    "bm25_index",
)


def file_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "size_mb": round(path.stat().st_size / 1024 / 1024, 2) if exists else 0,
    }


def rag_file_paths() -> dict[str, Path]:
    places_app_reviewed = settings.processed_data_dir / "places_app_reviewed.json"
    return {
        "places_master": settings.places_master_file,
        "places_app": settings.places_app_file,
        "places_app_reviewed": places_app_reviewed,
        "places_itinerary": settings.places_itinerary_file,
        "rag_documents": settings.rag_documents_file,
        "bm25_index": settings.indexes_dir / "bm25_index.pkl",
    }


def build_rag_files_status() -> dict[str, Any]:
    paths = rag_file_paths()
    files = {name: file_status(path) for name, path in paths.items()}
    ready = all(files[key]["exists"] for key in REQUIRED_RAG_FILE_KEYS)
    return {"ready": ready, "files": files}


def rag_status_payload() -> dict[str, Any]:
    status = build_rag_files_status()
    return {
        "service": "UnuTrip RAG v2",
        "ready": status["ready"],
        "files": status["files"],
        "artifacts": manifest_status_block(),
    }
