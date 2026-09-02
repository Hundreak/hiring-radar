from __future__ import annotations

import json
import time

import httpx

from hiring_radar.services.ai.config import LocalAiRuntimeConfig
from hiring_radar.services.ai.contracts import (
    AiChatGenerationRequest,
    AiChatGenerationResponse,
    AiHealthCheckResult,
    AiStructuredGenerationRequest,
    AiStructuredGenerationResponse,
)
from hiring_radar.services.ai.exceptions import (
    LocalAiGenerationError,
    LocalAiRuntimeUnreachableError,
    LocalAiStructuredOutputError,
)


class OllamaAdapter:
    def __init__(self, config: LocalAiRuntimeConfig) -> None:
        self._config = config

    def health(self) -> AiHealthCheckResult:
        if not self._config.enabled:
            return AiHealthCheckResult(
                enabled=False,
                runtime=self._config.runtime,
                base_url=self._config.base_url,
                configured_model=self._config.default_model or None,
                runtime_status="disabled",
                reachable=False,
                local_only_guard=self._config.strict_local_only,
                message="Local AI runtime is disabled by configuration.",
            )

        started = time.perf_counter()
        timeout = httpx.Timeout(self._config.health_timeout_seconds)

        try:
            with httpx.Client(base_url=self._config.base_url, timeout=timeout) as client:
                tags_response = client.get("/api/tags")
                tags_response.raise_for_status()
                tags_payload = tags_response.json()

                ps_response = client.get("/api/ps")
                ps_response.raise_for_status()
                ps_payload = ps_response.json()
        except Exception as exc:  # pragma: no cover
            raise LocalAiRuntimeUnreachableError(
                f"Failed to reach Ollama at {self._config.base_url!r}: {exc}"
            ) from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        available_models = [
            str(item.get("name", "")).strip()
            for item in tags_payload.get("models", [])
            if str(item.get("name", "")).strip()
        ]
        running_models = [
            str(item.get("model", item.get("name", ""))).strip()
            for item in ps_payload.get("models", [])
            if str(item.get("model", item.get("name", ""))).strip()
        ]

        configured_model = self._config.default_model or None
        message = "Local Ollama runtime is reachable."
        if configured_model and configured_model not in available_models:
            message = (
                f"Local Ollama runtime is reachable, but configured model "
                f"{configured_model!r} is not currently installed."
            )

        return AiHealthCheckResult(
            enabled=True,
            runtime=self._config.runtime,
            base_url=self._config.base_url,
            configured_model=configured_model,
            runtime_status="ready",
            reachable=True,
            local_only_guard=self._config.strict_local_only,
            response_time_ms=elapsed_ms,
            available_models=available_models,
            running_models=running_models,
            message=message,
        )

    def generate_chat(self, request: AiChatGenerationRequest) -> AiChatGenerationResponse:
        if not self._config.enabled:
            raise LocalAiGenerationError("Local AI runtime is disabled by configuration.")

        started = time.perf_counter()
        timeout = httpx.Timeout(request.timeout_seconds or self._config.request_timeout_seconds)
        payload = {
            "model": request.model or self._config.default_model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature},
        }

        try:
            with httpx.Client(base_url=self._config.base_url, timeout=timeout) as client:
                response = client.post("/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except Exception as exc:  # pragma: no cover
            raise LocalAiGenerationError(f"Local Ollama chat request failed: {exc}") from exc

        message = body.get("message", {}) if isinstance(body, dict) else {}
        raw_content = message.get("content", "") if isinstance(message, dict) else ""
        return AiChatGenerationResponse(
            model=str(body.get("model") or request.model or self._config.default_model),
            content=str(raw_content or ""),
            response_time_ms=int((time.perf_counter() - started) * 1000),
            done=bool(body.get("done", True)),
            done_reason=(str(body.get("done_reason")) if body.get("done_reason") else None),
        )

    def generate_structured(
        self,
        request: AiStructuredGenerationRequest,
    ) -> AiStructuredGenerationResponse:
        if not self._config.enabled:
            raise LocalAiGenerationError("Local AI runtime is disabled by configuration.")

        started = time.perf_counter()
        timeout = httpx.Timeout(request.timeout_seconds or self._config.request_timeout_seconds)
        payload = {
            "model": request.model or self._config.default_model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "format": request.output_json_schema,
            "options": {"temperature": request.temperature},
        }

        try:
            with httpx.Client(base_url=self._config.base_url, timeout=timeout) as client:
                response = client.post("/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except Exception as exc:  # pragma: no cover
            raise LocalAiGenerationError(
                f"Local Ollama generation request failed: {exc}"
            ) from exc

        message = body.get("message", {}) if isinstance(body, dict) else {}
        raw_content = message.get("content", "") if isinstance(message, dict) else ""
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise LocalAiStructuredOutputError(
                "Local Ollama returned an empty structured response."
            )

        try:
            parsed_content = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise LocalAiStructuredOutputError(
                f"Local Ollama returned non-JSON structured content: {exc}"
            ) from exc

        return AiStructuredGenerationResponse(
            model=str(body.get("model") or request.model or self._config.default_model),
            content=parsed_content,
            response_time_ms=int((time.perf_counter() - started) * 1000),
            done=bool(body.get("done", True)),
            done_reason=(str(body.get("done_reason")) if body.get("done_reason") else None),
        )
