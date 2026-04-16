from __future__ import annotations

from dataclasses import dataclass

from hiring_radar.services.ai.adapters.ollama_adapter import OllamaAdapter
from hiring_radar.services.ai.config import LocalAiRuntimeConfig, load_local_ai_runtime_config
from hiring_radar.services.ai.contracts import (
    AiChatGenerationRequest,
    AiChatGenerationResponse,
    AiHealthCheckResult,
    AiStructuredGenerationRequest,
    AiStructuredGenerationResponse,
)
from hiring_radar.services.ai.exceptions import (
    LocalAiRuntimeError,
    LocalAiRuntimeMisconfiguredError,
    LocalAiRuntimeUnreachableError,
)


@dataclass(slots=True)
class LocalAiRuntimeService:
    config: LocalAiRuntimeConfig
    _adapter: OllamaAdapter

    def health(self) -> AiHealthCheckResult:
        try:
            return self._adapter.health()
        except LocalAiRuntimeUnreachableError as exc:
            return AiHealthCheckResult(
                enabled=self.config.enabled,
                runtime=self.config.runtime,
                base_url=self.config.base_url,
                configured_model=self.config.default_model or None,
                runtime_status="unreachable",
                reachable=False,
                local_only_guard=self.config.strict_local_only,
                message=str(exc),
            )
        except LocalAiRuntimeError as exc:
            return AiHealthCheckResult(
                enabled=self.config.enabled,
                runtime=self.config.runtime,
                base_url=self.config.base_url,
                configured_model=self.config.default_model or None,
                runtime_status="error",
                reachable=False,
                local_only_guard=self.config.strict_local_only,
                message=str(exc),
            )
        except Exception as exc:  # pragma: no cover
            return AiHealthCheckResult(
                enabled=self.config.enabled,
                runtime=self.config.runtime,
                base_url=self.config.base_url,
                configured_model=self.config.default_model or None,
                runtime_status="error",
                reachable=False,
                local_only_guard=self.config.strict_local_only,
                message=f"Unexpected local AI runtime error: {exc}",
            )

    def generate_chat(self, request: AiChatGenerationRequest) -> AiChatGenerationResponse:
        return self._adapter.generate_chat(request)

    def generate_structured(
        self,
        request: AiStructuredGenerationRequest,
    ) -> AiStructuredGenerationResponse:
        return self._adapter.generate_structured(request)


def build_local_ai_runtime_service(
    config: LocalAiRuntimeConfig | None = None,
) -> LocalAiRuntimeService:
    resolved_config = config or load_local_ai_runtime_config()

    if resolved_config.runtime != "ollama":
        raise LocalAiRuntimeMisconfiguredError(
            f"Unsupported local runtime {resolved_config.runtime!r}."
        )

    return LocalAiRuntimeService(
        config=resolved_config,
        _adapter=OllamaAdapter(resolved_config),
    )
