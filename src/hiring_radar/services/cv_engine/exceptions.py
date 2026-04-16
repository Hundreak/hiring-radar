from __future__ import annotations

from hiring_radar.services.cv_engine.models import ParserStageName


class CvEngineError(Exception):
    """Base exception for the v2 CV engine."""


class RecoverableStageError(CvEngineError):
    """Error that should emit a warning and allow the pipeline to continue."""

    def __init__(self, stage: ParserStageName, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


class FatalStageError(CvEngineError):
    """Error that should terminate the pipeline immediately."""

    def __init__(self, stage: ParserStageName, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


class UnsupportedDocumentError(FatalStageError):
    """Raised when the document type cannot be parsed by the engine."""


class EncryptedDocumentError(FatalStageError):
    """Raised when an encrypted document cannot be processed."""


class NormalizationError(RecoverableStageError):
    """Raised when text normalization partially fails."""
