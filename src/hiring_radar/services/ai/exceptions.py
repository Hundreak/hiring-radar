from __future__ import annotations


class LocalAiError(Exception):
    """Base class for local AI related errors."""


class LocalAiConfigurationError(ValueError, LocalAiError):
    """Raised when local AI configuration is invalid."""


class LocalAiRuntimeError(RuntimeError, LocalAiError):
    """Raised when the runtime itself fails."""


class LocalAiRuntimeMisconfiguredError(LocalAiConfigurationError):
    """Raised when runtime configuration is invalid or incomplete."""


class LocalAiRuntimeUnreachableError(LocalAiRuntimeError):
    """Raised when the local runtime cannot be reached."""


class LocalAiGenerationError(RuntimeError, LocalAiError):
    """Raised when a generation request fails."""


class LocalAiStructuredOutputError(LocalAiGenerationError):
    """Raised when structured output cannot be parsed or validated."""


# Backward-compatible aliases expected by earlier packets/tests.
AiRuntimeError = LocalAiRuntimeError
AiValidationError = LocalAiStructuredOutputError
LocalAiRequestError = LocalAiGenerationError

__all__ = [
    "AiRuntimeError",
    "AiValidationError",
    "LocalAiConfigurationError",
    "LocalAiError",
    "LocalAiGenerationError",
    "LocalAiRequestError",
    "LocalAiRuntimeError",
    "LocalAiRuntimeMisconfiguredError",
    "LocalAiRuntimeUnreachableError",
    "LocalAiStructuredOutputError",
]
