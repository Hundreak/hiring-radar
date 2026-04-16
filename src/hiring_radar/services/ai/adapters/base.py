from __future__ import annotations

from typing import Protocol

from hiring_radar.services.ai.contracts import (
    AiHealthCheckResult,
    AiStructuredGenerationRequest,
    AiStructuredGenerationResponse,
)


class LocalAiAdapter(Protocol):
    def health(self) -> AiHealthCheckResult:
        """Return a high-level runtime health summary."""

    def generate_structured(
        self,
        request: AiStructuredGenerationRequest,
    ) -> AiStructuredGenerationResponse:
        """Return a validated structured response from the local runtime."""
