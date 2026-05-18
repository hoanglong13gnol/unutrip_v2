"""Prometheus metrics (optional, Phase 6)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.config import settings

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

_metrics_installed = False

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    HTTP_REQUESTS = Counter(
        "rag_http_requests_total",
        "HTTP requests",
        ["method", "path_group", "status"],
    )
    HTTP_LATENCY = Histogram(
        "rag_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "path_group"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
    )
    GEMINI_REQUESTS = Counter(
        "rag_gemini_requests_total",
        "Gemini generate calls",
        ["outcome"],
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    HTTP_REQUESTS = None
    HTTP_LATENCY = None
    GEMINI_REQUESTS = None
    CONTENT_TYPE_LATEST = "text/plain"


def metrics_enabled() -> bool:
    return settings.enable_metrics and _PROMETHEUS_AVAILABLE


def path_group(path: str) -> str:
    if path.startswith("/v1/"):
        path = path[3:]
    if path.startswith("/rag/"):
        return "/rag/*"
    if path.startswith("/admin/"):
        return "/admin/*"
    if path.startswith("/ai/"):
        return "/ai/*"
    if path in {"/health", "/health/ready", "/metrics", "/runtime/status"}:
        return path
    return "other"


def record_http_request(method: str, path: str, status: int, duration_s: float) -> None:
    if not metrics_enabled():
        return
    group = path_group(path)
    HTTP_REQUESTS.labels(method=method, path_group=group, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, path_group=group).observe(duration_s)


def record_gemini_outcome(outcome: str) -> None:
    if metrics_enabled():
        GEMINI_REQUESTS.labels(outcome=outcome).inc()


def install_metrics_route(app) -> None:
    global _metrics_installed
    if _metrics_installed or not metrics_enabled():
        return

    from fastapi import Response

    @app.get("/metrics", include_in_schema=False)
    def prometheus_metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    _metrics_installed = True


class MetricsMiddleware:
    """ASGI-style timing wrapper used from BaseHTTPMiddleware subclass."""

    @staticmethod
    async def observe(request: Request, call_next) -> Response:
        if not metrics_enabled():
            return await call_next(request)

        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started
        record_http_request(request.method, request.url.path, response.status_code, duration)
        return response
