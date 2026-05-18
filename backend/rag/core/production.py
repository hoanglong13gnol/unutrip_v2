"""Production safety checks for the RAG service (Phase 6)."""

from __future__ import annotations

import os

from core.security import get_admin_api_key, get_internal_api_key, is_debug_mode

_MIN_KEY_LEN = 16
_WEAK_KEY_FRAGMENTS = (
    "changeme",
    "change_me",
    "your_jwt",
    "secret_key",
    "password",
    "paste_your",
    "example",
    "test",
    "dev",
)


def is_production_env() -> bool:
    rag_env = os.getenv("RAG_ENV", "").strip().lower()
    node_env = os.getenv("NODE_ENV", "").strip().lower()
    return rag_env == "production" or node_env == "production"


def _is_weak_secret(value: str, *, min_len: int = _MIN_KEY_LEN) -> bool:
    s = (value or "").strip()
    if len(s) < min_len:
        return True
    lower = s.lower()
    return any(fragment in lower for fragment in _WEAK_KEY_FRAGMENTS)


def validate_production_config() -> list[str]:
    """Return human-readable config errors (empty when OK or not production)."""
    if not is_production_env():
        return []

    errors: list[str] = []

    internal = get_internal_api_key()
    if not internal:
        errors.append("RAG_INTERNAL_API_KEY is required in production")
    elif _is_weak_secret(internal):
        errors.append("RAG_INTERNAL_API_KEY is too short or looks like a placeholder")

    admin = get_admin_api_key()
    if not admin:
        errors.append("RAG_ADMIN_API_KEY is required in production")
    elif _is_weak_secret(admin):
        errors.append("RAG_ADMIN_API_KEY is too short or looks like a placeholder")
    elif internal and admin == internal:
        errors.append("RAG_ADMIN_API_KEY must differ from RAG_INTERNAL_API_KEY in production")

    if is_debug_mode():
        errors.append("RAG_DEBUG must be false in production")

    if os.getenv("ENABLE_GEMINI", "").strip().lower() in {"1", "true", "yes", "on"}:
        if not os.getenv("GEMINI_API_KEY", "").strip():
            errors.append("GEMINI_API_KEY is required when ENABLE_GEMINI=true in production")

    return errors


def assert_production_config() -> None:
    errors = validate_production_config()
    if errors:
        joined = "; ".join(errors)
        raise RuntimeError(f"RAG production config invalid: {joined}")
