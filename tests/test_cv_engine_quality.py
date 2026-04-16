from __future__ import annotations

import io
import json
import logging

from hiring_radar.services.cv_engine.adapters.to_legacy_parse_snapshot import (
    parse_result_to_legacy_snapshot,
)
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.models import (
    DocumentIngestionArtifact,
    ExtractionArtifact,
    NormalizedTextArtifact,
    ParseContext,
    ParsedCvData,
    ParsedDateRange,
    ParsedExperienceLine,
    ParsedSkill,
    ParserResult,
    ParserStatus,
    QualityBand,
    SectionBlock,
    SectionDetectionArtifact,
    SectionName,
)
from hiring_radar.services.cv_engine.scoring.quality import (
    DeterministicQualityScoringStrategy,
)
from hiring_radar.services.cv_engine.telemetry.logging import (
    CvEngineJsonFormatter,
    log_parse_result,
)
from hiring_radar.services.cv_engine.warnings import WarningCode, build_warning


def test_deterministic_quality_scoring_strategy_applies_positive_and_negative_signals() -> None:
    config = ParserRuntimeConfig()
    context = ParseContext(
        ingestion=DocumentIngestionArtifact(
            source_path='alice_cv.pdf',
            filename='alice_cv.pdf',
            extension='.pdf',
            mime_type='application/pdf',
            file_size_bytes=2048,
        ),
        extraction=ExtractionArtifact(
            text="Alice Example\nSenior Backend Engineer\nPython FastAPI PostgreSQL",
            extraction_method='pdf_text',
            used_ocr=True,
            page_count=1,
        ),
        normalized=NormalizedTextArtifact(
            text='\n'.join(['Alice Example'] * 60),
            lines=['Alice Example'] * 60,
        ),
        sections=SectionDetectionArtifact(
            sections=[
                SectionBlock(name=SectionName.SUMMARY, lines=['summary']),
                SectionBlock(name=SectionName.EXPERIENCE, lines=['experience']),
                SectionBlock(name=SectionName.SKILLS, lines=['skills']),
            ]
        ),
        parsed_data=ParsedCvData(
            full_name='Alice Example',
            emails=['alice@example.com'],
            phone_numbers=['+49 111 222'],
            summary='Built resilient backend systems.',
            skills=[
                ParsedSkill(
                    canonical_name='Python',
                    matched_text='Python',
                    source_section=SectionName.SKILLS,
                    confidence=0.92,
                    category='programming',
                )
            ],
            experience_lines=[
                ParsedExperienceLine(
                    title='Senior Backend Engineer',
                    company_name='ACME',
                    date_range=ParsedDateRange(start_year=2021, end_year=2024),
                    confidence=0.84,
                )
            ],
            section_names=[SectionName.SUMMARY, SectionName.EXPERIENCE, SectionName.SKILLS],
        ),
        warnings=[
            build_warning(
                code=WarningCode.LANGUAGE_DETECTION_FALLBACK,
                message='Fallback language detector was used.',
                stage='language_detection',
            )
        ],
    )

    result = DeterministicQualityScoringStrategy().score(context=context, config=config)

    assert result.band in {QualityBand.MEDIUM, QualityBand.HIGH}
    assert result.score > 0
    assert result.contributing_factors['text_length'] > 0
    assert result.contributing_factors['line_count'] > 0
    assert result.contributing_factors['skills'] == config.quality_scoring.field_weights['skills']
    assert result.contributing_factors['ocr_penalty'] == -config.quality_scoring.ocr_penalty
    assert result.contributing_factors['warning_penalty'] == -config.quality_scoring.warning_penalty


def test_parse_result_to_legacy_snapshot_builds_current_profile_draft_shape() -> None:
    context = ParseContext(
        ingestion=DocumentIngestionArtifact(
            source_path='alice_cv.pdf',
            filename='alice_cv.pdf',
            extension='.pdf',
            mime_type='application/pdf',
            file_size_bytes=2048,
        ),
        parsed_data=ParsedCvData(
            summary='Backend engineer with FastAPI experience.',
            locations=['Berlin'],
            skills=[
                ParsedSkill(
                    canonical_name='Python',
                    matched_text='Python',
                    source_section=SectionName.SKILLS,
                    confidence=0.9,
                    category='programming',
                ),
                ParsedSkill(
                    canonical_name='FastAPI',
                    matched_text='FastAPI',
                    source_section=SectionName.SKILLS,
                    confidence=0.88,
                    category='framework',
                ),
            ],
            experience_lines=[
                ParsedExperienceLine(
                    title='Senior Backend Engineer',
                    company_name='ACME',
                    date_range=ParsedDateRange(start_year=2020, end_year=2024),
                    summary_lines=['Built matching systems.'],
                    confidence=0.82,
                )
            ],
            metadata={
                'target_roles': ['Backend Engineer'],
                'remote_preference': 'remote',
                'education_entries': [
                    {
                        'school_name': 'METU',
                        'degree_name': 'BSc Electrical Engineering',
                        'field_of_study': None,
                        'start_year': 2012,
                        'end_year': 2017,
                    }
                ],
                'language_entries': [
                    {
                        'language_name': 'English',
                        'proficiency_level': 'C1',
                        'notes': None,
                    }
                ],
            },
        ),
    )
    result = ParserResult(status=ParserStatus.SUCCEEDED, context=context)

    snapshot = parse_result_to_legacy_snapshot(result, source_upload_id=42)

    assert snapshot.source_upload_id == 42
    assert snapshot.source_filename == 'alice_cv.pdf'
    assert snapshot.source_parse_status == 'parsed'
    assert snapshot.parser_version == 'cv_engine_v2'
    assert snapshot.draft.summary == 'Backend engineer with FastAPI experience.'
    assert snapshot.draft.skills == ('Python', 'FastAPI')
    assert snapshot.draft.target_roles == ('Backend Engineer',)
    assert snapshot.draft.preferred_locations == ('Berlin',)
    assert snapshot.draft.remote_preference == 'remote'
    assert len(snapshot.draft.education_entries) == 1
    assert snapshot.draft.education_entries[0].school_name == 'METU'
    assert len(snapshot.draft.experience_entries) == 1
    assert snapshot.draft.experience_entries[0].company_name == 'ACME'
    assert len(snapshot.draft.language_entries) == 1
    assert snapshot.draft.language_entries[0].language_name == 'English'


def test_log_parse_result_emits_json_payload() -> None:
    context = ParseContext(
        ingestion=DocumentIngestionArtifact(
            source_path='alice_cv.pdf',
            filename='alice_cv.pdf',
            extension='.pdf',
            mime_type='application/pdf',
            file_size_bytes=2048,
        )
    )
    result = ParserResult(status=ParserStatus.SUCCEEDED, context=context)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(CvEngineJsonFormatter())
    logger = logging.getLogger('tests.cv_engine.telemetry')
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_parse_result(logger, result=result)

    payload = json.loads(stream.getvalue().strip())
    assert payload['event_name'] == 'cv_engine_parse_finished'
    assert payload['status'] == 'succeeded'
    assert payload['filename'] == 'alice_cv.pdf'
