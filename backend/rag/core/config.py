import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_HERE = Path(__file__).resolve()
RAG_DIR = _HERE.parents[1]


def _infer_project_root() -> Path:
    """Docker image uses flat /svc/layout; repo clone has backend/rag/core/... under repo root."""
    override = os.getenv("UNUTRIP_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    for dir_path in _HERE.parents:
        if (dir_path / "docker-compose.yml").is_file():
            return dir_path
    # Container: no compose file baked in; Compose injects env from host .env
    return RAG_DIR


PROJECT_ROOT = _infer_project_root()
_dotenv_file = PROJECT_ROOT / ".env"
if _dotenv_file.is_file():
    load_dotenv(_dotenv_file)
else:
    load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return float(value)
    except Exception:
        return default


def optional_stripped_url(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not str(value).strip():
        return default
    return str(value).strip()


class Settings(BaseModel):
    project_name: str = "UnuTrip RAG v2"
    api_version: str = "0.3.0"

    root_dir: Path = RAG_DIR
    project_root: Path = PROJECT_ROOT

    raw_data_dir: Path = root_dir / "data" / "raw"
    processed_data_dir: Path = root_dir / "data" / "processed"
    indexes_dir: Path = root_dir / "data" / "indexes"
    reports_dir: Path = root_dir / "reports"

    dataset_file: Path = raw_data_dir / "dataset_vip_fixed.xlsx"
    dataset_sheet: str = "places_core_dedup_by_id"

    places_master_file: Path = processed_data_dir / "places_master.parquet"
    places_app_file: Path = processed_data_dir / "places_app.json"
    places_itinerary_file: Path = processed_data_dir / "places_itinerary.json"
    rag_documents_file: Path = processed_data_dir / "places_rag_documents.jsonl"

    ai_runtime_mode: str = os.getenv("AI_RUNTIME_MODE", "mock")
    enable_gemini: bool = env_bool("ENABLE_GEMINI", False)

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_timeout_seconds: int = env_int("GEMINI_TIMEOUT_SECONDS", 45)

    # Retrieval / ops
    enable_rrf_fusion: bool = env_bool("RAG_ENABLE_RRF", True)
    enable_rerank: bool = env_bool("RAG_ENABLE_RERANK", True)
    enable_vector_retrieval: bool = env_bool("RAG_ENABLE_VECTOR", False)
    embedding_model: str = env_str(
        "RAG_EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2",
    )
    vector_candidate_top_k: int = env_int("RAG_VECTOR_TOP_K", 120)
    rrf_k: float = env_float("RAG_RRF_K", 60.0)
    enable_cross_encoder: bool = env_bool("RAG_ENABLE_CROSS_ENCODER", False)
    cross_encoder_model: str = env_str(
        "RAG_CROSS_ENCODER_MODEL",
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    )
    rerank_candidate_pool: int = env_int("RAG_RERANK_CANDIDATE_POOL", 48)
    rate_limit_per_minute: int = env_int("RAG_RATE_LIMIT_PER_MINUTE", 120)
    gemini_circuit_failure_threshold: int = env_int("RAG_GEMINI_CIRCUIT_FAILURES", 4)
    gemini_circuit_cooldown_seconds: int = env_int("RAG_GEMINI_CIRCUIT_COOLDOWN_SECONDS", 90)
    log_json: bool = env_bool("RAG_LOG_JSON", False)
    rag_env: str = env_str("RAG_ENV", "development")
    ready_requires_index: bool = env_bool("RAG_READY_REQUIRES_INDEX", True)
    enable_metrics: bool = env_bool("RAG_ENABLE_METRICS", False)
    gemini_executor_workers: int = env_int("RAG_GEMINI_EXECUTOR_WORKERS", 4)

    # Production artifacts (Phase D): volume mount dir or release .zip URL
    artifact_bundle_url: str | None = optional_stripped_url("RAG_ARTIFACT_BUNDLE_URL")
    artifact_source_dir: Path | None = None
    artifact_fetch_on_startup: bool = env_bool("RAG_FETCH_ARTIFACTS_ON_START", False)

    # Redis (optional): rate limit + Gemini response cache across replicas
    redis_url: str | None = optional_stripped_url("REDIS_URL")
    redis_key_prefix: str = env_str("REDIS_KEY_PREFIX", "unutrip:rag:")
    gemini_response_cache_ttl_seconds: int = env_int("GEMINI_CACHE_TTL_SECONDS", 86400)


def _artifact_source_dir_from_env() -> Path | None:
    raw = os.getenv("RAG_ARTIFACT_SOURCE_DIR", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


settings = Settings(artifact_source_dir=_artifact_source_dir_from_env())


def vector_retrieval_active() -> bool:
    """True when dense vector recall is enabled and the embedding artifact exists."""
    if not settings.enable_vector_retrieval:
        return False
    from retrieval.vector_retriever import VectorRetriever

    return VectorRetriever.index_exists()


def get_log_level() -> str:
    return os.getenv("RAG_LOG_LEVEL", "INFO").strip().upper() or "INFO"
