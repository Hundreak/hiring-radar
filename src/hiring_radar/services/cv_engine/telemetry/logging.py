from __future__ import annotations

import json
import logging
from typing import Any

from hiring_radar.services.cv_engine.models import ParseContext, ParserResult, StageTelemetry


class CvEngineJsonFormatter(logging.Formatter):
    """JSON formatter for deterministic CV engine telemetry logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        event_name = getattr(record, 'event_name', None)
        if event_name is not None:
            payload['event_name'] = event_name

        extra_payload = getattr(record, 'payload', None)
        if isinstance(extra_payload, dict):
            payload.update(extra_payload)

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def build_cv_engine_logger(
    *,
    name: str = 'hiring_radar.cv_engine',
    level: int = logging.INFO,
) -> logging.Logger:
    """Build or retrieve a JSON-configured logger for the CV engine."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    has_json_handler = any(
        isinstance(handler.formatter, CvEngineJsonFormatter)
        for handler in logger.handlers
    )
    if not has_json_handler:
        handler = logging.StreamHandler()
        handler.setFormatter(CvEngineJsonFormatter())
        logger.addHandler(handler)

    return logger


def serialize_parse_result(result: ParserResult) -> dict[str, Any]:
    """Serialize a parser result into a stable logging payload."""
    context = result.context
    ingestion = context.ingestion
    extraction = context.extraction
    quality = context.quality

    return {
        'status': result.status.value,
        'filename': ingestion.filename,
        'source_path': ingestion.source_path,
        'extension': ingestion.extension,
        'mime_type': ingestion.mime_type,
        'file_size_bytes': ingestion.file_size_bytes,
        'fingerprint_sha256': ingestion.fingerprint_sha256,
        'encrypted': ingestion.encrypted,
        'used_ocr': extraction.used_ocr if extraction is not None else False,
        'extraction_method': extraction.extraction_method if extraction is not None else None,
        'page_count': extraction.page_count if extraction is not None else None,
        'detected_language': context.detected_language,
        'warning_count': len(context.warnings),
        'warnings': [warning.model_dump(mode='json') for warning in context.warnings],
        'quality': quality.model_dump(mode='json') if quality is not None else None,
        'stage_telemetry': [
            telemetry.model_dump(mode='json') for telemetry in context.stage_telemetry
        ],
    }


def log_stage_event(
    logger: logging.Logger,
    *,
    telemetry: StageTelemetry,
    source_path: str,
) -> None:
    """Emit one structured log event for a pipeline stage."""
    payload = {
        'source_path': source_path,
        'stage': telemetry.stage.value,
        'duration_ms': round(telemetry.duration_ms, 3),
        'succeeded': telemetry.succeeded,
        'skipped': telemetry.skipped,
        'metadata': telemetry.metadata,
    }
    logger.info(
        'cv_engine_stage_completed',
        extra={'event_name': 'cv_engine_stage_completed', 'payload': payload},
    )


def log_parse_result(logger: logging.Logger, *, result: ParserResult) -> None:
    """Emit one structured log event for a full parser result."""
    payload = serialize_parse_result(result)
    logger.info(
        'cv_engine_parse_finished',
        extra={'event_name': 'cv_engine_parse_finished', 'payload': payload},
    )
