"""Shared thread pool for blocking Gemini SDK calls (Phase 6)."""

from __future__ import annotations

import atexit
import threading
from concurrent.futures import ThreadPoolExecutor

from core.config import settings

_lock = threading.Lock()
_executor: ThreadPoolExecutor | None = None


def get_gemini_executor() -> ThreadPoolExecutor:
    global _executor
    with _lock:
        if _executor is None:
            workers = max(1, settings.gemini_executor_workers)
            _executor = ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix="rag-gemini",
            )
        return _executor


def shutdown_gemini_executor(*, wait: bool = False) -> None:
    global _executor
    with _lock:
        if _executor is not None:
            _executor.shutdown(wait=wait, cancel_futures=not wait)
            _executor = None


atexit.register(lambda: shutdown_gemini_executor(wait=False))
