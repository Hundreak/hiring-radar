from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


@dataclass(frozen=True, slots=True)
class LocalAiRuntimeConfig:
    enabled: bool = False
    runtime: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    default_model: str = ""
    health_timeout_seconds: float = 3.0
    request_timeout_seconds: float = 45.0
    max_retries: int = 1
    strict_local_only: bool = True
    audit_enabled: bool = True
    audit_log_dir: str = "data/ai_audit"
    audit_preview_chars: int = 240

    def validate(self) -> None:
        runtime_normalized = self.runtime.strip().lower()
        if runtime_normalized not in {"ollama"}:
            raise ValueError(
                f"Unsupported local AI runtime: {self.runtime!r}. "
                "This bootstrap package currently supports only 'ollama'."
            )

        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "AI_BASE_URL must be a valid absolute HTTP(S) URL, "
                f"got {self.base_url!r}."
            )

        if self.strict_local_only and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError(
                "Strict local AI mode is enabled, but AI_BASE_URL does not point "
                f"to localhost: {self.base_url!r}."
            )

        if self.health_timeout_seconds <= 0:
            raise ValueError("AI_HEALTH_TIMEOUT_SECONDS must be > 0.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("AI_REQUEST_TIMEOUT_SECONDS must be > 0.")
        if self.max_retries < 0:
            raise ValueError("AI_MAX_RETRIES must be >= 0.")
        if not self.audit_log_dir.strip():
            raise ValueError("AI_AUDIT_LOG_DIR must not be empty.")
        if self.audit_preview_chars < 0:
            raise ValueError("AI_AUDIT_PREVIEW_CHARS must be >= 0.")


def load_local_ai_runtime_config() -> LocalAiRuntimeConfig:
    config = LocalAiRuntimeConfig(
        enabled=_read_bool("AI_ENABLED", False),
        runtime=os.getenv("AI_RUNTIME", "ollama").strip().lower(),
        base_url=os.getenv("AI_BASE_URL", "http://127.0.0.1:11434").strip(),
        default_model=os.getenv("AI_DEFAULT_MODEL", "").strip(),
        health_timeout_seconds=_read_float("AI_HEALTH_TIMEOUT_SECONDS", 3.0),
        request_timeout_seconds=_read_float("AI_REQUEST_TIMEOUT_SECONDS", 45.0),
        max_retries=_read_int("AI_MAX_RETRIES", 1),
        strict_local_only=_read_bool("AI_STRICT_LOCAL_ONLY", True),
        audit_enabled=_read_bool("AI_AUDIT_ENABLED", True),
        audit_log_dir=os.getenv("AI_AUDIT_LOG_DIR", "data/ai_audit").strip(),
        audit_preview_chars=_read_int("AI_AUDIT_PREVIEW_CHARS", 240),
    )
    config.validate()
    return config
