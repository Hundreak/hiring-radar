from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from hiring_radar.services.ai.exceptions import LocalAiConfigurationError

_ALLOWED_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class LocalAiRuntimeConfig:
    enabled: bool = False
    runtime: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    default_model: str = ""
    health_timeout_seconds: int = 3
    request_timeout_seconds: int = 45
    max_retries: int = 1
    strict_local_only: bool = True
    audit_enabled: bool = True
    audit_log_dir: str = "data/ai_audit"
    audit_preview_chars: int = 240


def validate_local_ai_runtime_config(config: LocalAiRuntimeConfig) -> LocalAiRuntimeConfig:
    if config.health_timeout_seconds <= 0:
        raise LocalAiConfigurationError("AI_HEALTH_TIMEOUT_SECONDS must be positive.")
    if config.request_timeout_seconds <= 0:
        raise LocalAiConfigurationError("AI_REQUEST_TIMEOUT_SECONDS must be positive.")
    if config.max_retries < 0:
        raise LocalAiConfigurationError("AI_MAX_RETRIES cannot be negative.")
    if config.audit_preview_chars <= 0:
        raise LocalAiConfigurationError("AI_AUDIT_PREVIEW_CHARS must be positive.")

    if config.strict_local_only:
        parsed = urlparse(config.base_url)
        if parsed.hostname not in _ALLOWED_LOCAL_HOSTS:
            raise LocalAiConfigurationError(
                "Strict local AI mode requires AI_BASE_URL to point to a local host."
            )

    return config


def load_local_ai_runtime_config() -> LocalAiRuntimeConfig:
    config = LocalAiRuntimeConfig(
        enabled=_parse_bool(os.getenv("AI_ENABLED"), False),
        runtime=os.getenv("AI_RUNTIME", "ollama").strip() or "ollama",
        base_url=os.getenv("AI_BASE_URL", "http://127.0.0.1:11434").strip()
        or "http://127.0.0.1:11434",
        default_model=os.getenv("AI_DEFAULT_MODEL", "").strip(),
        health_timeout_seconds=int(os.getenv("AI_HEALTH_TIMEOUT_SECONDS", "3")),
        request_timeout_seconds=int(os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "45")),
        max_retries=int(os.getenv("AI_MAX_RETRIES", "1")),
        strict_local_only=_parse_bool(os.getenv("AI_STRICT_LOCAL_ONLY"), True),
        audit_enabled=_parse_bool(os.getenv("AI_AUDIT_ENABLED"), True),
        audit_log_dir=os.getenv("AI_AUDIT_LOG_DIR", "data/ai_audit").strip()
        or "data/ai_audit",
        audit_preview_chars=int(os.getenv("AI_AUDIT_PREVIEW_CHARS", "240")),
    )
    return validate_local_ai_runtime_config(config)


__all__ = [
    "LocalAiRuntimeConfig",
    "load_local_ai_runtime_config",
    "validate_local_ai_runtime_config",
]