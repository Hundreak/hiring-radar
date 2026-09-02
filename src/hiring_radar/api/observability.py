"""API observability primitives.

This module keeps the production diagnostics layer dependency-free. It adds a
stable request id to every API response, emits structured access logs and returns
non-leaky envelopes for unexpected server errors.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import traceback
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from hiring_radar.security_runtime import bool_env

DEFAULT_REQUEST_ID_HEADER = "X-Request-ID"
DEFAULT_RESPONSE_TIME_HEADER = "X-Response-Time-Ms"
DEFAULT_UNHANDLED_ERROR_DETAIL = "Internal server error."
REQUEST_ID_MAX_LENGTH = 128
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:/=-]{1,128}$")

request_id_context: ContextVar[str | None] = ContextVar("hiring_radar_request_id", default=None)
request_start_context: ContextVar[float | None] = ContextVar("hiring_radar_request_start", default=None)

ACCESS_LOGGER_NAME = "hiring_radar.api.request"
ERROR_LOGGER_NAME = "hiring_radar.api.error"
access_logger = logging.getLogger(ACCESS_LOGGER_NAME)
error_logger = logging.getLogger(ERROR_LOGGER_NAME)


@dataclass(frozen=True, slots=True)
class ObservabilitySettings:
    enabled: bool = True
    request_id_header: str = DEFAULT_REQUEST_ID_HEADER
    response_time_header: str = DEFAULT_RESPONSE_TIME_HEADER
    trust_incoming_request_id: bool = True
    log_requests: bool = True
    log_slow_requests: bool = True
    slow_request_threshold_ms: int = 750
    expose_response_time_header: bool = True
    json_logs: bool = True


def _env_int(name: str, *, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return value


def load_observability_settings() -> ObservabilitySettings:
    return ObservabilitySettings(
        enabled=bool_env("HIRING_RADAR_OBSERVABILITY_ENABLED", default=True),
        request_id_header=os.getenv("HIRING_RADAR_REQUEST_ID_HEADER", DEFAULT_REQUEST_ID_HEADER),
        response_time_header=os.getenv("HIRING_RADAR_RESPONSE_TIME_HEADER", DEFAULT_RESPONSE_TIME_HEADER),
        trust_incoming_request_id=bool_env("HIRING_RADAR_TRUST_INCOMING_REQUEST_ID", default=True),
        log_requests=bool_env("HIRING_RADAR_LOG_REQUESTS", default=True),
        log_slow_requests=bool_env("HIRING_RADAR_LOG_SLOW_REQUESTS", default=True),
        slow_request_threshold_ms=_env_int(
            "HIRING_RADAR_SLOW_REQUEST_THRESHOLD_MS",
            default=750,
            minimum=1,
        ),
        expose_response_time_header=bool_env("HIRING_RADAR_EXPOSE_RESPONSE_TIME_HEADER", default=True),
        json_logs=bool_env("HIRING_RADAR_JSON_LOGS", default=True),
    )


def generate_request_id() -> str:
    return uuid4().hex


def sanitize_request_id(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > REQUEST_ID_MAX_LENGTH:
        return None
    if not REQUEST_ID_PATTERN.match(cleaned):
        return None
    return cleaned


def resolve_request_id(request: Request, *, settings: ObservabilitySettings | None = None) -> str:
    resolved = settings or load_observability_settings()
    incoming = None
    if resolved.trust_incoming_request_id:
        incoming = sanitize_request_id(request.headers.get(resolved.request_id_header))
    return incoming or generate_request_id()


def get_current_request_id() -> str | None:
    return request_id_context.get()


def _client_host(request: Request) -> str | None:
    return request.client.host if request.client else None


def _log_extra(
    *,
    request_id: str,
    request: Request,
    status_code: int | None = None,
    duration_ms: float | None = None,
    slow: bool | None = None,
    error_type: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query,
        "client_host": _client_host(request),
    }
    if status_code is not None:
        payload["status_code"] = status_code
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 2)
    if slow is not None:
        payload["slow"] = slow
    if error_type:
        payload["error_type"] = error_type
    return payload


def _duration_since(start: float) -> float:
    return (time.perf_counter() - start) * 1000


class ApiJsonLogFormatter(logging.Formatter):
    """Small JSON formatter for API logs.

    It is intentionally conservative: only stable, scalar fields are copied from
    the log record so request logs stay safe and low-noise.
    """

    extra_fields = (
        "request_id",
        "method",
        "path",
        "query",
        "status_code",
        "duration_ms",
        "slow",
        "client_host",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - logging API signature
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for field in self.extra_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                if value not in (None, ""):
                    payload[field] = value
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info)).strip()
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_api_observability_logging(settings: ObservabilitySettings | None = None) -> None:
    """Configure JSON logging for API request/error loggers when requested.

    The function is idempotent and only attaches handlers to the dedicated API
    loggers when they do not already have one. Existing application logging
    remains untouched.
    """

    resolved = settings or load_observability_settings()
    if not resolved.json_logs:
        return

    formatter = ApiJsonLogFormatter()
    for logger in (access_logger, error_logger):
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            for handler in logger.handlers:
                handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.propagate = False


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach request ids, response timings and structured request logs."""

    def __init__(self, app: ASGIApp, *, settings: ObservabilitySettings | None = None) -> None:
        super().__init__(app)
        self.settings = settings or load_observability_settings()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not self.settings.enabled:
            return await call_next(request)

        request_id = resolve_request_id(request, settings=self.settings)
        request.state.request_id = request_id
        request_id_token = request_id_context.set(request_id)
        start = time.perf_counter()
        start_token = request_start_context.set(start)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:  # pragma: no cover - exercised through TestClient with raise_server_exceptions=False
            duration_ms = _duration_since(start)
            request.state.observability_exception_logged = True
            error_logger.exception(
                "api.request.unhandled_exception",
                extra=_log_extra(
                    request_id=request_id,
                    request=request,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    duration_ms=duration_ms,
                    slow=duration_ms >= self.settings.slow_request_threshold_ms,
                    error_type=exc.__class__.__name__,
                ),
            )
            response = JSONResponse(
                {
                    "detail": DEFAULT_UNHANDLED_ERROR_DETAIL,
                    "request_id": request_id,
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            status_code = response.status_code
            return response
        finally:
            duration_ms = _duration_since(start)
            slow = duration_ms >= self.settings.slow_request_threshold_ms

            if response is not None:
                response.headers[self.settings.request_id_header] = request_id
                if self.settings.expose_response_time_header:
                    response.headers[self.settings.response_time_header] = f"{duration_ms:.2f}"

            if self.settings.log_requests or (self.settings.log_slow_requests and slow):
                log_level = logging.WARNING if slow and self.settings.log_slow_requests else logging.INFO
                access_logger.log(
                    log_level,
                    "api.request.completed",
                    extra=_log_extra(
                        request_id=request_id,
                        request=request,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        slow=slow,
                    ),
                )

            request_start_context.reset(start_token)
            request_id_context.reset(request_id_token)
