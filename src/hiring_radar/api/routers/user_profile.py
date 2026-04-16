from __future__ import annotations

import json
import logging
import secrets
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError

from hiring_radar.api.dependencies import get_current_user_session, get_repository
from hiring_radar.api.schemas.profile_contract import (
    CreateEducationRequest,
    CreateExperienceRequest,
    CreateLanguageRequest,
    UpdateBasicInfoRequest,
    UpdateExperienceRequest,
    UpdateLanguageRequest,
    UpdatePreferencesRequest,
    UserProfileAggregateResponse,
    ProfileSuggestionsBundle,
)
from hiring_radar.api.schemas.user_profile import (
    UserCvApplySelectedRequest,
    UserCvApplySelectedResponse,
    UserCvEnterpriseMetadataResponse,
    UserCvFieldConfidenceResponse,
    UserCvFieldReviewInsightResponse,
    UserCvParseSnapshotResponse,
    UserCvProfileApplyPlanResponse,
    UserCvProfileConfidenceReportResponse,
    UserCvReviewSummaryResponse,
    UserCvUploadExtractionMetadataResponse,
    UserCvUploadResponse,
    UserCvWorkspaceContextResponse,
    UserEducationEntryResponse,
    UserExperienceEntryResponse,
    UserLanguageCertificateResponse,
    UserLanguageEntryResponse,
    UserProfileAvatarUploadResponse,
    UserSkillDetailResponse,
    UserProfileCompletenessResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import (
    SubscriberCvParseRun,
    SubscriberCvUpload,
    SubscriberEducationEntry,
    SubscriberExperienceEntry,
    SubscriberLanguageCertificate,
    SubscriberLanguageEntry,
    SubscriberSkillDetail,
)
from hiring_radar.services.cv_engine.compliance.audit import (
    build_apply_audit_metadata_json,
    build_parse_run_metadata_json,
)
from hiring_radar.services.cv_engine.enterprise.api_metadata import (
    build_cv_enterprise_metadata,
)
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_FAILED,
    CV_PARSE_STATUS_PENDING,
    CvExtractionError,
    cv_extraction_uses_ocr,
    derive_cv_extraction_fallback_reason,
    derive_cv_extraction_quality,
    derive_cv_extraction_recommended_next_action,
    derive_cv_extraction_review_hints,
    derive_cv_parse_status_detail,
    extract_text_from_cv_file,
    infer_cv_extraction_method,
    infer_cv_file_format,
    is_cv_extraction_safe_for_default_apply,
    should_cv_extraction_require_manual_review,
)
from hiring_radar.services.cv_parse_pipeline import (
    build_cv_profile_draft_snapshot_from_cv_upload,
    cv_profile_draft_snapshot_from_json,
    cv_profile_draft_snapshot_to_json,
)
from hiring_radar.services.cv_profile_apply_execution import (
    applied_execution_result_to_dict,
    apply_selected_cv_profile_operations,
    build_cv_selected_apply_operations,
    derive_parse_run_apply_status,
    selected_apply_operations_to_dict,
)
from hiring_radar.services.cv_profile_apply_plan import build_cv_profile_apply_plan
from hiring_radar.services.cv_profile_confidence import (
    build_cv_profile_confidence_report,
)
from hiring_radar.services.cv_review_insights import (
    build_cv_field_review_insights,
    build_cv_review_summary,
)
from hiring_radar.services.retrieval.orchestration import (
    refresh_cv_upload_retrieval_safe,
    refresh_profile_and_cv_retrieval_safe,
    refresh_profile_retrieval_safe,
)
from hiring_radar.services.profile_aggregate import build_user_profile_aggregate_response
from hiring_radar.services.profile_completeness import (
    calculate_subscriber_profile_completeness,
)
from hiring_radar.services.profile_uploads import (
    InvalidUploadError,
    resolve_profile_storage_path,
    store_profile_file,
    validate_avatar_upload,
    validate_cv_upload,
    validate_language_certificate_upload,
    validate_skill_evidence_upload,
)
from hiring_radar.services.user_auth import UserSession

router = APIRouter(prefix="/api/user/profile", tags=["user-profile"])

logger = logging.getLogger(__name__)


def _resolve_retrieval_locale(subscriber) -> str | None:
    return "tr"


def _sync_profile_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> None:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    locale = _resolve_retrieval_locale(subscriber)
    refresh_profile_retrieval_safe(
        repository,
        subscriber_id=subscriber_id,
        locale=locale,
    )


def _sync_cv_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int,
) -> None:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    locale = _resolve_retrieval_locale(subscriber)
    refresh_cv_upload_retrieval_safe(
        repository,
        subscriber_id=subscriber_id,
        cv_upload_id=cv_upload_id,
        locale=locale,
    )


def _sync_profile_and_cv_retrieval_safe(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int | None = None,
) -> None:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    locale = _resolve_retrieval_locale(subscriber)
    refresh_profile_and_cv_retrieval_safe(
        repository,
        subscriber_id=subscriber_id,
        cv_upload_id=cv_upload_id,
        locale=locale,
    )


def _build_profile_aggregate_with_retrieval_sync(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> UserProfileAggregateResponse:
    _sync_profile_retrieval_safe(
        repository,
        subscriber_id=subscriber_id,
    )
    return _get_user_profile_aggregate_response(
        repository,
        subscriber_id=subscriber_id,
    )

UserSessionDep = Annotated[UserSession, Depends(get_current_user_session)]
RepositoryDep = Annotated[HiringRadarRepository, Depends(get_repository)]


class UpdateEducationRequest(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    description: str | None = None


class CreateSkillRequest(BaseModel):
    skill_name: str
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = None
    evidence_note: str | None = None


class UpdateSkillRequest(BaseModel):
    skill_name: str | None = None
    category: str | None = None
    proficiency_hint: str | None = None
    years_hint: int | None = None
    evidence_note: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _clean_string_list(values: list[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for value in values:
        item = value.strip()
        if item:
            cleaned.append(item)
    return tuple(cleaned)


def _normalize_skill_name(value: str) -> str:
    return value.strip().lower()


def _serialize_skill_detail(detail: SubscriberSkillDetail) -> UserSkillDetailResponse:
    return UserSkillDetailResponse(
        id=detail.id,
        skill_name=detail.skill_name,
        category=detail.category,
        proficiency_hint=detail.proficiency_hint,
        years_hint=detail.years_hint,
        evidence_note=detail.evidence_note,
        evidence_file_name=detail.evidence_file_name,
        uploaded_at=detail.uploaded_at,
    )


def _parse_skill_id(skill_id: str, skills: tuple[str, ...] | list[str]) -> int:
    normalized = skill_id.strip()
    if normalized.startswith("skill_"):
        normalized = normalized.split("_", 1)[1]

    if not normalized.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill id is invalid.",
        )

    index = int(normalized)
    if index < 0 or index >= len(skills):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill entry not found.",
        )

    return index


def _upsert_profile_with_skills(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    skills: tuple[str, ...],
    updated_at: str,
) -> None:
    existing_profile = repository.get_subscriber_profile(subscriber_id)
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=existing_profile.phone,
        headline=existing_profile.headline,
        summary=existing_profile.summary,
        target_roles=existing_profile.target_roles,
        skills=skills,
        preferred_locations=existing_profile.preferred_locations,
        remote_preference=existing_profile.remote_preference,
        cv_filename=existing_profile.cv_filename,
        cv_uploaded_at=existing_profile.cv_uploaded_at,
        updated_at=updated_at,
    )


def _build_cv_extraction_metadata_response(
    *,
    filename: str | None,
    content_type: str | None,
    parse_status: str | None,
    extracted_text: str | None = None,
) -> UserCvUploadExtractionMetadataResponse:
    """Build typed extraction metadata for any CV-related response."""
    normalized_parse_status = (parse_status or "").strip() or "unknown"

    return UserCvUploadExtractionMetadataResponse(
        file_format=infer_cv_file_format(filename, content_type),
        extraction_method=infer_cv_extraction_method(filename, content_type),
        uses_ocr=cv_extraction_uses_ocr(filename, content_type),
        parse_status_detail=derive_cv_parse_status_detail(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
        ),
        extraction_quality=derive_cv_extraction_quality(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        ),
        review_hints=list(
            derive_cv_extraction_review_hints(
                parse_status=normalized_parse_status,
                filename=filename,
                content_type=content_type,
                extracted_text=extracted_text,
            )
        ),
        needs_manual_review=should_cv_extraction_require_manual_review(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        ),
        is_safe_for_default_apply=is_cv_extraction_safe_for_default_apply(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        ),
        fallback_reason=derive_cv_extraction_fallback_reason(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        ),
        recommended_next_action=derive_cv_extraction_recommended_next_action(
            parse_status=normalized_parse_status,
            filename=filename,
            content_type=content_type,
            extracted_text=extracted_text,
        ),
    )


def _build_cv_enterprise_metadata_response(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload: SubscriberCvUpload,
) -> UserCvEnterpriseMetadataResponse | None:
    """Build additive enterprise metadata for a persisted CV upload."""
    payload = build_cv_enterprise_metadata(
        repository,
        subscriber_id=subscriber_id,
        cv_upload=cv_upload,
    )
    if payload is None:
        return None
    return UserCvEnterpriseMetadataResponse.model_validate(payload)


def _serialize_cv_upload_response(
    cv_upload,
    *,
    repository: HiringRadarRepository | None = None,
    subscriber_id: int | None = None,
) -> UserCvUploadResponse:
    """Serialize a persisted CV upload with derived extraction metadata."""
    enterprise_metadata = None
    if repository is not None and subscriber_id is not None:
        enterprise_metadata = _build_cv_enterprise_metadata_response(
            repository,
            subscriber_id=subscriber_id,
            cv_upload=cv_upload,
        )

    return UserCvUploadResponse(
        id=cv_upload.id,
        original_filename=cv_upload.original_filename,
        content_type=cv_upload.content_type,
        file_size_bytes=cv_upload.file_size_bytes,
        parse_status=cv_upload.parse_status,
        uploaded_at=cv_upload.uploaded_at,
        parsed_at=cv_upload.parsed_at,
        extraction_metadata=_build_cv_extraction_metadata_response(
            filename=cv_upload.original_filename,
            content_type=cv_upload.content_type,
            parse_status=cv_upload.parse_status,
            extracted_text=cv_upload.extracted_text,
        ),
        enterprise_metadata=enterprise_metadata,
    )


def _serialize_profile(
    *,
    subscriber,
    profile,
    education_entries,
    experience_entries,
    language_entries,
    language_certificates,
    latest_cv_upload,
    repository: HiringRadarRepository,
) -> UserProfileResponse:
    completeness = calculate_subscriber_profile_completeness(
        subscriber=subscriber,
        profile=profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
    )

    resolved_cv_filename = profile.cv_filename or (
        latest_cv_upload.original_filename if latest_cv_upload is not None else None
    )
    resolved_cv_uploaded_at = profile.cv_uploaded_at or (
        latest_cv_upload.uploaded_at if latest_cv_upload is not None else None
    )

    return UserProfileResponse(
        subscriber_id=subscriber.id or 0,
        email=subscriber.email,
        full_name=subscriber.full_name,
        phone=profile.phone,
        headline=profile.headline,
        summary=profile.summary,
        target_roles=list(profile.target_roles),
        skills=list(profile.skills),
        preferred_locations=list(profile.preferred_locations),
        remote_preference=profile.remote_preference,
        cv_filename=resolved_cv_filename,
        cv_uploaded_at=resolved_cv_uploaded_at,
        education_entries=[
            UserEducationEntryResponse(
                id=item.id,
                school_name=item.school_name,
                degree_name=item.degree_name,
                field_of_study=item.field_of_study,
                start_year=item.start_year,
                end_year=item.end_year,
                display_order=item.display_order,
            )
            for item in education_entries
        ],
        experience_entries=[
            UserExperienceEntryResponse(
                id=item.id,
                title=item.title,
                company_name=item.company_name,
                start_year=item.start_year,
                end_year=item.end_year,
                summary=item.summary,
                display_order=item.display_order,
            )
            for item in experience_entries
        ],
        language_entries=[
            UserLanguageEntryResponse(
                id=item.id,
                language_name=item.language_name,
                proficiency_level=item.proficiency_level,
                notes=item.notes,
                display_order=item.display_order,
            )
            for item in language_entries
        ],
        language_certificates=[
            UserLanguageCertificateResponse(
                id=item.id,
                language_entry_id=item.language_entry_id,
                certificate_name=item.certificate_name,
                issuer_name=item.issuer_name,
                file_name=item.file_name,
                uploaded_at=item.uploaded_at,
            )
            for item in language_certificates
        ],
        latest_cv_upload=(
            _serialize_cv_upload_response(
                latest_cv_upload,
                repository=repository,
                subscriber_id=subscriber.id or 0,
            )
            if latest_cv_upload is not None
            else None
        ),
        completeness=UserProfileCompletenessResponse(
            score=completeness.score,
            completed_items=list(completeness.completed_items),
            missing_items=list(completeness.missing_items),
        ),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )




def _get_serialized_cv_workspace_context(
    repository: HiringRadarRepository,
    subscriber_id: int,
) -> UserCvWorkspaceContextResponse:
    latest_cv_upload = repository.get_latest_subscriber_cv_upload(subscriber_id)
    language_certificates = repository.list_subscriber_language_certificates(subscriber_id)

    return UserCvWorkspaceContextResponse(
        latest_cv_upload=(
            _serialize_cv_upload_response(
                latest_cv_upload,
                repository=repository,
                subscriber_id=subscriber_id,
            )
            if latest_cv_upload is not None
            else None
        ),
        language_certificates=[
            UserLanguageCertificateResponse(
                id=item.id,
                language_entry_id=item.language_entry_id,
                certificate_name=item.certificate_name,
                issuer_name=item.issuer_name,
                file_name=item.file_name,
                uploaded_at=item.uploaded_at,
            )
            for item in language_certificates
        ],
    )


def _get_serialized_profile(
    repository: HiringRadarRepository,
    subscriber_id: int,
) -> UserProfileResponse:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    profile = repository.get_subscriber_profile(subscriber_id)
    education_entries = repository.list_subscriber_education_entries(subscriber_id)
    experience_entries = repository.list_subscriber_experience_entries(subscriber_id)
    language_entries = repository.list_subscriber_language_entries(subscriber_id)
    language_certificates = repository.list_subscriber_language_certificates(subscriber_id)
    latest_cv_upload = repository.get_latest_subscriber_cv_upload(subscriber_id)

    return _serialize_profile(
        subscriber=subscriber,
        profile=profile,
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
        language_certificates=language_certificates,
        latest_cv_upload=latest_cv_upload,
        repository=repository,
    )


def _update_profile_cv_metadata(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_filename: str,
    cv_uploaded_at: str,
    updated_at: str,
) -> None:
    existing = repository.get_subscriber_profile(subscriber_id)
    repository.upsert_subscriber_profile(
        subscriber_id,
        phone=existing.phone,
        headline=existing.headline,
        summary=existing.summary,
        target_roles=existing.target_roles,
        skills=existing.skills,
        preferred_locations=existing.preferred_locations,
        remote_preference=existing.remote_preference,
        cv_filename=cv_filename,
        cv_uploaded_at=cv_uploaded_at,
        updated_at=updated_at,
    )


def _finalize_cv_upload_parse(
    repository: HiringRadarRepository,
    *,
    cv_upload_id: int,
    extracted_text: str | None,
    parse_status: str,
    parsed_at: str,
):
    updated_upload = repository.update_subscriber_cv_upload_parse_result(
        cv_upload_id,
        extracted_text=extracted_text,
        parse_status=parse_status,
        parsed_at=parsed_at,
        updated_at=parsed_at,
    )
    if updated_upload is None:
        raise RuntimeError("Failed to update CV upload parse result.")

    return updated_upload


def _persist_cv_parse_snapshot(
    repository: HiringRadarRepository,
    *,
    cv_upload: SubscriberCvUpload,
) -> None:
    """Persist a versioned parse snapshot for a finalized CV upload."""
    if cv_upload.id is None:
        raise RuntimeError("Cannot persist a parse snapshot without an upload id.")

    snapshot = build_cv_profile_draft_snapshot_from_cv_upload(cv_upload)
    enterprise_metadata = build_cv_enterprise_metadata(
        repository,
        subscriber_id=cv_upload.subscriber_id,
        cv_upload=cv_upload,
    )
    parse_metadata_json = build_parse_run_metadata_json(
        parser_version=snapshot.parser_version,
        source_upload_id=cv_upload.id,
        source_filename=snapshot.source_filename,
        source_parse_status=snapshot.source_parse_status or cv_upload.parse_status,
        generated_at=snapshot.generated_at,
        enterprise_metadata=enterprise_metadata,
    )
    repository.create_subscriber_cv_parse_run(
        cv_upload.subscriber_id,
        cv_upload_id=cv_upload.id,
        parser_version=snapshot.parser_version,
        source_parse_status=snapshot.source_parse_status or cv_upload.parse_status,
        snapshot_json=cv_profile_draft_snapshot_to_json(snapshot),
        created_at=snapshot.generated_at,
        metadata_json=parse_metadata_json,
    )


def _serialize_cv_field_confidence_response(field) -> UserCvFieldConfidenceResponse:
    return UserCvFieldConfidenceResponse(
        field_name=field.field_name,
        level=field.level,
        has_value=field.has_value,
        item_count=field.item_count,
        signals=list(field.signals),
    )


def _serialize_cv_profile_confidence_report_response(
    report,
) -> UserCvProfileConfidenceReportResponse:
    return UserCvProfileConfidenceReportResponse(
        headline=_serialize_cv_field_confidence_response(report.headline),
        summary=_serialize_cv_field_confidence_response(report.summary),
        skills=_serialize_cv_field_confidence_response(report.skills),
        target_roles=_serialize_cv_field_confidence_response(report.target_roles),
        preferred_locations=_serialize_cv_field_confidence_response(
            report.preferred_locations
        ),
        remote_preference=_serialize_cv_field_confidence_response(
            report.remote_preference
        ),
        education_entries=_serialize_cv_field_confidence_response(
            report.education_entries
        ),
        experience_entries=_serialize_cv_field_confidence_response(
            report.experience_entries
        ),
        language_entries=_serialize_cv_field_confidence_response(
            report.language_entries
        ),
    )


def _serialize_cv_field_review_response_bundle(
    *,
    confidence_report,
    extraction_metadata: UserCvUploadExtractionMetadataResponse,
) -> tuple[list[UserCvFieldReviewInsightResponse], UserCvReviewSummaryResponse]:
    insights = build_cv_field_review_insights(
        confidence_report=confidence_report,
        needs_manual_review=extraction_metadata.needs_manual_review,
        uses_ocr=extraction_metadata.uses_ocr,
        review_hints=tuple(extraction_metadata.review_hints),
    )
    summary = build_cv_review_summary(
        insights=insights,
        manual_review_flow=extraction_metadata.needs_manual_review,
    )

    return (
        [
            UserCvFieldReviewInsightResponse(
                field_name=item.field_name,
                severity=item.severity,
                reason_codes=list(item.reason_codes),
                confidence_level=item.confidence_level,
                has_value=item.has_value,
                item_count=item.item_count,
            )
            for item in insights
        ],
        UserCvReviewSummaryResponse(
            total_field_count=summary.total_field_count,
            safe_field_count=summary.safe_field_count,
            review_recommended_count=summary.review_recommended_count,
            review_required_count=summary.review_required_count,
            highest_severity=summary.highest_severity,
            focus_field_names=list(summary.focus_field_names),
            manual_review_flow=summary.manual_review_flow,
        ),
    )


def _serialize_cv_parse_snapshot_response(
    parse_run: SubscriberCvParseRun,
    *,
    repository: HiringRadarRepository,
) -> UserCvParseSnapshotResponse:
    if parse_run.id is None:
        raise HTTPException(
            status_code=500,
            detail="Stored CV parse snapshot is missing its identifier.",
        )

    snapshot = _deserialize_cv_parse_snapshot(parse_run)
    confidence_report = build_cv_profile_confidence_report(snapshot)
    extraction_metadata = _build_cv_extraction_metadata_response(
        filename=snapshot.source_filename,
        content_type=None,
        parse_status=snapshot.source_parse_status,
        extracted_text=(
            "\n".join(
                [
                    snapshot.draft.headline or "",
                    snapshot.draft.summary or "",
                    *snapshot.draft.skills,
                    *snapshot.draft.target_roles,
                    *snapshot.draft.preferred_locations,
                ]
            ).strip()
            or None
        ),
    )
    field_review, review_summary = _serialize_cv_field_review_response_bundle(
        confidence_report=confidence_report,
        extraction_metadata=extraction_metadata,
    )
    source_upload = repository.get_subscriber_cv_upload_by_id(parse_run.cv_upload_id)
    enterprise_metadata = (
        _build_cv_enterprise_metadata_response(
            repository,
            subscriber_id=parse_run.subscriber_id,
            cv_upload=source_upload,
        )
        if source_upload is not None
        else None
    )

    try:
        return UserCvParseSnapshotResponse.model_validate(
            {
                "parse_run_id": parse_run.id,
                "generated_at": snapshot.generated_at,
                "source_upload_id": snapshot.source_upload_id,
                "source_filename": snapshot.source_filename,
                "source_parse_status": snapshot.source_parse_status,
                "parser_version": snapshot.parser_version,
                "extraction_metadata": extraction_metadata.model_dump(),
                "confidence": _serialize_cv_profile_confidence_report_response(
                    confidence_report
                ).model_dump(),
                "field_review": [item.model_dump() for item in field_review],
                "review_summary": review_summary.model_dump(),
                "enterprise_metadata": (
                    None if enterprise_metadata is None else enterprise_metadata.model_dump()
                ),
                "draft": {
                    "headline": snapshot.draft.headline,
                    "summary": snapshot.draft.summary,
                    "skills": list(snapshot.draft.skills),
                    "target_roles": list(snapshot.draft.target_roles),
                    "preferred_locations": list(snapshot.draft.preferred_locations),
                    "remote_preference": snapshot.draft.remote_preference,
                    "education_entries": [
                        {
                            "school_name": item.school_name,
                            "degree_name": item.degree_name,
                            "field_of_study": item.field_of_study,
                            "start_year": item.start_year,
                            "end_year": item.end_year,
                        }
                        for item in snapshot.draft.education_entries
                    ],
                    "experience_entries": [
                        {
                            "title": item.title,
                            "company_name": item.company_name,
                            "start_year": item.start_year,
                            "end_year": item.end_year,
                            "summary": item.summary,
                        }
                        for item in snapshot.draft.experience_entries
                    ],
                    "language_entries": [
                        {
                            "language_name": item.language_name,
                            "proficiency_level": item.proficiency_level,
                            "notes": item.notes,
                        }
                        for item in snapshot.draft.language_entries
                    ],
                },
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored CV parse snapshot is invalid.",
        ) from exc


def _deserialize_cv_parse_snapshot(parse_run: SubscriberCvParseRun):
    try:
        return cv_profile_draft_snapshot_from_json(parse_run.snapshot_json)
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored CV parse snapshot is invalid.",
        ) from exc


def _build_apply_plan_extraction_text(apply_plan) -> str | None:
    parts: list[str] = [
        apply_plan.headline.suggested_value or "",
        apply_plan.summary.suggested_value or "",
        *apply_plan.skills.suggested_items,
        *apply_plan.target_roles.suggested_items,
        *apply_plan.preferred_locations.suggested_items,
    ]

    parts.extend(
        item.draft_entry.school_name
        for item in apply_plan.education_entries
        if item.draft_entry.school_name
    )
    parts.extend(
        item.draft_entry.degree_name or ""
        for item in apply_plan.education_entries
        if item.draft_entry.degree_name
    )
    parts.extend(
        item.draft_entry.title
        for item in apply_plan.experience_entries
        if item.draft_entry.title
    )
    parts.extend(
        item.draft_entry.company_name or ""
        for item in apply_plan.experience_entries
        if item.draft_entry.company_name
    )
    parts.extend(
        item.draft_entry.summary or ""
        for item in apply_plan.experience_entries
        if item.draft_entry.summary
    )
    parts.extend(
        item.draft_entry.language_name
        for item in apply_plan.language_entries
        if item.draft_entry.language_name
    )
    parts.extend(
        item.draft_entry.proficiency_level or ""
        for item in apply_plan.language_entries
        if item.draft_entry.proficiency_level
    )

    combined = "\n".join(part for part in parts if part).strip()
    return combined or None


def _serialize_cv_profile_apply_plan_response(
    *,
    repository: HiringRadarRepository,
    parse_run: SubscriberCvParseRun,
    apply_plan,
    confidence_report,
    generated_at: str,
    source_upload_id: int | None,
    source_filename: str | None,
    source_parse_status: str | None,
    parser_version: str | None,
) -> UserCvProfileApplyPlanResponse:
    if parse_run.id is None:
        raise HTTPException(
            status_code=500,
            detail="Stored CV parse snapshot is missing its identifier.",
        )

    extraction_metadata = _build_cv_extraction_metadata_response(
        filename=source_filename,
        content_type=None,
        parse_status=source_parse_status,
        extracted_text=_build_apply_plan_extraction_text(apply_plan),
    )
    field_review, review_summary = _serialize_cv_field_review_response_bundle(
        confidence_report=confidence_report,
        extraction_metadata=extraction_metadata,
    )
    source_upload = repository.get_subscriber_cv_upload_by_id(parse_run.cv_upload_id)
    enterprise_metadata = (
        _build_cv_enterprise_metadata_response(
            repository,
            subscriber_id=parse_run.subscriber_id,
            cv_upload=source_upload,
        )
        if source_upload is not None
        else None
    )

    try:
        return UserCvProfileApplyPlanResponse.model_validate(
            {
                "parse_run_id": parse_run.id,
                "generated_at": generated_at,
                "source_upload_id": source_upload_id,
                "source_filename": source_filename,
                "source_parse_status": source_parse_status,
                "parser_version": parser_version,
                "extraction_metadata": extraction_metadata.model_dump(),
                "has_actionable_changes": apply_plan.has_actionable_changes(),
                "default_selected_change_count": (
                    apply_plan.default_selected_change_count()
                ),
                "confidence": _serialize_cv_profile_confidence_report_response(
                    confidence_report
                ).model_dump(),
                "field_review": [item.model_dump() for item in field_review],
                "review_summary": review_summary.model_dump(),
                "enterprise_metadata": (
                    None if enterprise_metadata is None else enterprise_metadata.model_dump()
                ),
                "headline": {
                    "field_name": apply_plan.headline.field_name,
                    "current_value": apply_plan.headline.current_value,
                    "suggested_value": apply_plan.headline.suggested_value,
                    "action": apply_plan.headline.action,
                    "default_selected": apply_plan.headline.default_selected,
                },
                "summary": {
                    "field_name": apply_plan.summary.field_name,
                    "current_value": apply_plan.summary.current_value,
                    "suggested_value": apply_plan.summary.suggested_value,
                    "action": apply_plan.summary.action,
                    "default_selected": apply_plan.summary.default_selected,
                },
                "remote_preference": {
                    "field_name": apply_plan.remote_preference.field_name,
                    "current_value": apply_plan.remote_preference.current_value,
                    "suggested_value": apply_plan.remote_preference.suggested_value,
                    "action": apply_plan.remote_preference.action,
                    "default_selected": apply_plan.remote_preference.default_selected,
                },
                "skills": {
                    "field_name": apply_plan.skills.field_name,
                    "current_items": list(apply_plan.skills.current_items),
                    "suggested_items": list(apply_plan.skills.suggested_items),
                    "items_to_add": list(apply_plan.skills.items_to_add),
                    "action": apply_plan.skills.action,
                    "default_selected": apply_plan.skills.default_selected,
                },
                "target_roles": {
                    "field_name": apply_plan.target_roles.field_name,
                    "current_items": list(apply_plan.target_roles.current_items),
                    "suggested_items": list(apply_plan.target_roles.suggested_items),
                    "items_to_add": list(apply_plan.target_roles.items_to_add),
                    "action": apply_plan.target_roles.action,
                    "default_selected": apply_plan.target_roles.default_selected,
                },
                "preferred_locations": {
                    "field_name": apply_plan.preferred_locations.field_name,
                    "current_items": list(
                        apply_plan.preferred_locations.current_items
                    ),
                    "suggested_items": list(
                        apply_plan.preferred_locations.suggested_items
                    ),
                    "items_to_add": list(
                        apply_plan.preferred_locations.items_to_add
                    ),
                    "action": apply_plan.preferred_locations.action,
                    "default_selected": apply_plan.preferred_locations.default_selected,
                },
                "education_entries": [
                    {
                        "draft_entry": {
                            "school_name": item.draft_entry.school_name,
                            "degree_name": item.draft_entry.degree_name,
                            "field_of_study": item.draft_entry.field_of_study,
                            "start_year": item.draft_entry.start_year,
                            "end_year": item.draft_entry.end_year,
                        },
                        "matched_existing_id": item.matched_existing_id,
                        "action": item.action,
                        "default_selected": item.default_selected,
                    }
                    for item in apply_plan.education_entries
                ],
                "experience_entries": [
                    {
                        "draft_entry": {
                            "title": item.draft_entry.title,
                            "company_name": item.draft_entry.company_name,
                            "start_year": item.draft_entry.start_year,
                            "end_year": item.draft_entry.end_year,
                            "summary": item.draft_entry.summary,
                        },
                        "matched_existing_id": item.matched_existing_id,
                        "action": item.action,
                        "default_selected": item.default_selected,
                    }
                    for item in apply_plan.experience_entries
                ],
                "language_entries": [
                    {
                        "draft_entry": {
                            "language_name": item.draft_entry.language_name,
                            "proficiency_level": item.draft_entry.proficiency_level,
                            "notes": item.draft_entry.notes,
                        },
                        "matched_existing_id": item.matched_existing_id,
                        "action": item.action,
                        "default_selected": item.default_selected,
                    }
                    for item in apply_plan.language_entries
                ],
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail="Computed CV apply plan is invalid.",
        ) from exc


def _build_cv_apply_operator_context(
    *,
    parse_run: SubscriberCvParseRun,
    source_cv_upload: SubscriberCvUpload,
    extraction_metadata: UserCvUploadExtractionMetadataResponse,
    manual_review_acknowledged: bool,
) -> dict[str, Any]:
    return {
        "source_upload_id": parse_run.cv_upload_id,
        "source_filename": source_cv_upload.original_filename,
        "source_parse_status": source_cv_upload.parse_status,
        "needs_manual_review": extraction_metadata.needs_manual_review,
        "manual_review_acknowledged": manual_review_acknowledged,
        "is_safe_for_default_apply": extraction_metadata.is_safe_for_default_apply,
        "fallback_reason": extraction_metadata.fallback_reason,
        "recommended_next_action": extraction_metadata.recommended_next_action,
    }


def _build_cv_apply_selected_audit_payload(
    *,
    selection,
    operator_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "selection": selected_apply_operations_to_dict(selection),
        "operator_context": operator_context,
    }


def _build_cv_apply_result_audit_payload(
    *,
    execution_result,
    operator_context: dict[str, Any],
    resulting_parse_run_apply_status: str,
    remaining_actionable_change_count: int,
) -> dict[str, Any]:
    return {
        "execution_result": applied_execution_result_to_dict(execution_result),
        "operator_context": operator_context,
        "post_apply_summary": {
            "resulting_parse_run_apply_status": resulting_parse_run_apply_status,
            "remaining_actionable_change_count": remaining_actionable_change_count,
        },
    }


def _count_selected_apply_operations(selection) -> int:
    return (
        len(selection.scalar_fields)
        + len(selection.list_fields)
        + len(selection.education_entry_indexes)
        + len(selection.experience_entry_indexes)
        + len(selection.language_entry_indexes)
    )


def _get_user_owned_cv_parse_run(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    parse_run_id: int,
) -> SubscriberCvParseRun:
    parse_run = repository.get_subscriber_cv_parse_run_by_id(parse_run_id)
    if parse_run is None or parse_run.subscriber_id != subscriber_id:
        raise HTTPException(
            status_code=404,
            detail="CV parse snapshot not found.",
        )

    return parse_run


def _extract_year_from_partial_date(value: str | None, field_name: str) -> int | None:
    cleaned = _clean_optional_string(value)
    if cleaned is None:
        return None

    year_text = cleaned[:4]
    if len(year_text) != 4 or not year_text.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must start with a 4-digit year.",
        )

    return int(year_text)


def _get_user_profile_aggregate_response(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    legacy_profile = repository.get_subscriber_profile(subscriber.id)
    experience_entries = repository.list_subscriber_experience_entries(subscriber.id)
    education_entries = repository.list_subscriber_education_entries(subscriber.id)
    language_entries = repository.list_subscriber_language_entries(subscriber.id)

    return build_user_profile_aggregate_response(
        user_id=str(subscriber.id),
        email=subscriber.email,
        full_name=subscriber.full_name,
        legacy_profile=legacy_profile,
        experience_entries=experience_entries,
        education_entries=education_entries,
        language_entries=language_entries,
    )


@router.get("", response_model=UserProfileResponse)
def get_user_profile(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileResponse:
    return _get_serialized_profile(repository, user_session.subscriber_id)


@router.put("", response_model=UserProfileResponse)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    updated_at = _utc_now_iso()

    repository.update_subscriber_fields_by_id(
        user_session.subscriber_id,
        fields={"full_name": _clean_optional_string(payload.full_name)},
        updated_at=updated_at,
    )

    current_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    repository.upsert_subscriber_profile(
        user_session.subscriber_id,
        phone=_clean_optional_string(payload.phone),
        headline=_clean_optional_string(payload.headline),
        summary=_clean_optional_string(payload.summary),
        target_roles=_clean_string_list(payload.target_roles),
        skills=_clean_string_list(payload.skills),
        preferred_locations=_clean_string_list(payload.preferred_locations),
        remote_preference=_clean_optional_string(payload.remote_preference),
        cv_filename=current_profile.cv_filename,
        cv_uploaded_at=current_profile.cv_uploaded_at,
        updated_at=updated_at,
    )

    repository.replace_subscriber_education_entries(
        user_session.subscriber_id,
        entries=[
            SubscriberEducationEntry(
                school_name=item.school_name.strip(),
                degree_name=_clean_optional_string(item.degree_name),
                field_of_study=_clean_optional_string(item.field_of_study),
                start_year=item.start_year,
                end_year=item.end_year,
            )
            for item in payload.education_entries
            if item.school_name.strip()
        ],
        updated_at=updated_at,
    )

    repository.replace_subscriber_experience_entries(
        user_session.subscriber_id,
        entries=[
            SubscriberExperienceEntry(
                title=item.title.strip(),
                company_name=_clean_optional_string(item.company_name),
                start_year=item.start_year,
                end_year=item.end_year,
                summary=_clean_optional_string(item.summary),
            )
            for item in payload.experience_entries
            if item.title.strip()
        ],
        updated_at=updated_at,
    )

    repository.replace_subscriber_language_entries(
        user_session.subscriber_id,
        entries=[
            SubscriberLanguageEntry(
                language_name=item.language_name.strip(),
                proficiency_level=_clean_optional_string(item.proficiency_level),
                notes=_clean_optional_string(item.notes),
            )
            for item in payload.language_entries
            if item.language_name.strip()
        ],
        updated_at=updated_at,
    )

    _sync_profile_retrieval_safe(
        repository,
        subscriber_id=user_session.subscriber_id,
    )

    return _get_serialized_profile(repository, user_session.subscriber_id)


@router.get("/cv/latest-parse", response_model=UserCvParseSnapshotResponse | None)
def get_latest_user_cv_parse_snapshot(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserCvParseSnapshotResponse | None:
    parse_run = repository.get_latest_subscriber_cv_parse_run(
        user_session.subscriber_id
    )
    if parse_run is None:
        return None

    return _serialize_cv_parse_snapshot_response(
        parse_run,
        repository=repository,
    )


@router.get(
    "/cv/latest-apply-plan",
    response_model=UserCvProfileApplyPlanResponse | None,
)
def get_latest_user_cv_profile_apply_plan(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserCvProfileApplyPlanResponse | None:
    parse_run = repository.get_latest_subscriber_cv_parse_run(
        user_session.subscriber_id
    )
    if parse_run is None:
        return None

    snapshot = _deserialize_cv_parse_snapshot(parse_run)
    profile = repository.get_subscriber_profile(user_session.subscriber_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Subscriber profile not found.",
        )

    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=profile,
        education_entries=repository.list_subscriber_education_entries(
            user_session.subscriber_id
        ),
        experience_entries=repository.list_subscriber_experience_entries(
            user_session.subscriber_id
        ),
        language_entries=repository.list_subscriber_language_entries(
            user_session.subscriber_id
        ),
    )

    confidence_report = build_cv_profile_confidence_report(snapshot)

    return _serialize_cv_profile_apply_plan_response(
        repository=repository,
        parse_run=parse_run,
        apply_plan=apply_plan,
        confidence_report=confidence_report,
        generated_at=snapshot.generated_at,
        source_upload_id=snapshot.source_upload_id,
        source_filename=snapshot.source_filename,
        source_parse_status=snapshot.source_parse_status,
        parser_version=snapshot.parser_version,
    )


@router.post(
    "/cv/apply-selected",
    response_model=UserCvApplySelectedResponse,
)
def apply_selected_user_cv_profile_operations(
    payload: UserCvApplySelectedRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserCvApplySelectedResponse:
    parse_run = _get_user_owned_cv_parse_run(
        repository,
        subscriber_id=user_session.subscriber_id,
        parse_run_id=payload.parse_run_id,
    )
    snapshot = _deserialize_cv_parse_snapshot(parse_run)

    current_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    current_education_entries = repository.list_subscriber_education_entries(
        user_session.subscriber_id
    )
    current_experience_entries = repository.list_subscriber_experience_entries(
        user_session.subscriber_id
    )
    current_language_entries = repository.list_subscriber_language_entries(
        user_session.subscriber_id
    )

    apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=current_profile,
        education_entries=current_education_entries,
        experience_entries=current_experience_entries,
        language_entries=current_language_entries,
    )

    try:
        selection = build_cv_selected_apply_operations(
            scalar_fields=payload.scalar_fields,
            list_fields=payload.list_fields,
            education_entry_indexes=payload.education_entry_indexes,
            experience_entry_indexes=payload.experience_entry_indexes,
            language_entry_indexes=payload.language_entry_indexes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    source_cv_upload = repository.get_subscriber_cv_upload_by_id(
        parse_run.cv_upload_id
    )
    if source_cv_upload is None:
        raise HTTPException(
            status_code=404,
            detail="Source CV upload not found for parse run.",
        )

    extraction_metadata = _build_cv_extraction_metadata_response(
        filename=source_cv_upload.original_filename,
        content_type=source_cv_upload.content_type,
        parse_status=source_cv_upload.parse_status,
        extracted_text=source_cv_upload.extracted_text,
    )

    if (
        extraction_metadata.needs_manual_review
        and not payload.manual_review_acknowledged
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Manual review acknowledgement is required before applying "
                "CV changes for this extraction result."
            ),
        )

    try:
        execution_result = apply_selected_cv_profile_operations(
            apply_plan=apply_plan,
            selection=selection,
            profile=current_profile,
            education_entries=current_education_entries,
            experience_entries=current_experience_entries,
            language_entries=current_language_entries,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    updated_at = _utc_now_iso()

    repository.upsert_subscriber_profile(
        user_session.subscriber_id,
        phone=execution_result.profile.phone,
        headline=execution_result.profile.headline,
        summary=execution_result.profile.summary,
        target_roles=execution_result.profile.target_roles,
        skills=execution_result.profile.skills,
        preferred_locations=execution_result.profile.preferred_locations,
        remote_preference=execution_result.profile.remote_preference,
        cv_filename=execution_result.profile.cv_filename,
        cv_uploaded_at=execution_result.profile.cv_uploaded_at,
        updated_at=updated_at,
    )

    repository.replace_subscriber_education_entries(
        user_session.subscriber_id,
        entries=list(execution_result.education_entries),
        updated_at=updated_at,
    )
    repository.replace_subscriber_experience_entries(
        user_session.subscriber_id,
        entries=list(execution_result.experience_entries),
        updated_at=updated_at,
    )
    repository.replace_subscriber_language_entries(
        user_session.subscriber_id,
        entries=list(execution_result.language_entries),
        updated_at=updated_at,
    )

    updated_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    updated_education_entries = repository.list_subscriber_education_entries(
        user_session.subscriber_id
    )
    updated_experience_entries = repository.list_subscriber_experience_entries(
        user_session.subscriber_id
    )
    updated_language_entries = repository.list_subscriber_language_entries(
        user_session.subscriber_id
    )

    post_apply_plan = build_cv_profile_apply_plan(
        snapshot=snapshot,
        profile=updated_profile,
        education_entries=updated_education_entries,
        experience_entries=updated_experience_entries,
        language_entries=updated_language_entries,
    )
    remaining_actionable_change_count = post_apply_plan.actionable_change_count()
    resulting_parse_run_apply_status = derive_parse_run_apply_status(
        remaining_actionable_change_count=remaining_actionable_change_count
    )

    updated_parse_run = repository.update_subscriber_cv_parse_run_apply_state(
        parse_run.id or 0,
        apply_status=resulting_parse_run_apply_status,
        applied_change_count=(
            parse_run.applied_change_count + execution_result.applied_change_count
        ),
        applied_at=updated_at,
        updated_at=updated_at,
    )
    if updated_parse_run is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update CV parse run apply state.",
        )

    operator_context = _build_cv_apply_operator_context(
        parse_run=parse_run,
        source_cv_upload=source_cv_upload,
        extraction_metadata=extraction_metadata,
        manual_review_acknowledged=payload.manual_review_acknowledged,
    )

    audit = repository.create_subscriber_cv_apply_audit(
        user_session.subscriber_id,
        parse_run_id=parse_run.id or 0,
        selected_operations_json=json.dumps(
            _build_cv_apply_selected_audit_payload(
                selection=selection,
                operator_context=operator_context,
            ),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        applied_operations_json=json.dumps(
            _build_cv_apply_result_audit_payload(
                execution_result=execution_result,
                operator_context=operator_context,
                resulting_parse_run_apply_status=resulting_parse_run_apply_status,
                remaining_actionable_change_count=remaining_actionable_change_count,
            ),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        applied_change_count=execution_result.applied_change_count,
        resulting_apply_status=resulting_parse_run_apply_status,
        remaining_actionable_change_count=remaining_actionable_change_count,
        created_at=updated_at,
        metadata_json=build_apply_audit_metadata_json(
            parse_run_metadata_json=parse_run.metadata_json,
            operator_context=operator_context,
            selected_operation_count=_count_selected_apply_operations(selection),
            applied_change_count=execution_result.applied_change_count,
            resulting_apply_status=resulting_parse_run_apply_status,
            remaining_actionable_change_count=remaining_actionable_change_count,
        ),
    )

    _sync_profile_and_cv_retrieval_safe(
        repository,
        subscriber_id=user_session.subscriber_id,
        cv_upload_id=source_cv_upload.id,
    )

    return UserCvApplySelectedResponse(
        parse_run_id=parse_run.id or 0,
        apply_audit_id=audit.id or 0,
        resulting_parse_run_apply_status=resulting_parse_run_apply_status,
        remaining_actionable_change_count=remaining_actionable_change_count,
        applied_change_count=execution_result.applied_change_count,
        applied_scalar_fields=list(execution_result.applied_scalar_fields),
        applied_list_fields=list(execution_result.applied_list_fields),
        applied_education_entry_indexes=list(
            execution_result.applied_education_entry_indexes
        ),
        applied_experience_entry_indexes=list(
            execution_result.applied_experience_entry_indexes
        ),
        applied_language_entry_indexes=list(
            execution_result.applied_language_entry_indexes
        ),
        profile=_get_serialized_profile(repository, user_session.subscriber_id),
    )


@router.post("/upload/cv", response_model=UserCvUploadResponse)
async def upload_user_cv(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    file: Annotated[UploadFile, File(...)],
) -> UserCvUploadResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    try:
        payload = await file.read()
        validate_cv_upload(
            filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=len(payload),
        )
        stored = store_profile_file(
            subscriber_id=user_session.subscriber_id,
            category="cv",
            original_filename=file.filename or "cv",
            content=payload,
        )
        uploaded_at = _utc_now_iso()
        cv_upload = repository.create_subscriber_cv_upload(
            user_session.subscriber_id,
            original_filename=file.filename or stored.original_filename,
            storage_path=stored.storage_path,
            content_type=file.content_type,
            file_size_bytes=stored.file_size_bytes,
            extracted_text=None,
            parse_status=CV_PARSE_STATUS_PENDING,
            uploaded_at=uploaded_at,
            parsed_at=None,
        )
        if cv_upload.id is None:
            raise RuntimeError("Failed to create CV upload record.")

        parsed_at = _utc_now_iso()
        try:
            extraction_result = extract_text_from_cv_file(stored.absolute_path)
            cv_upload = _finalize_cv_upload_parse(
                repository,
                cv_upload_id=cv_upload.id,
                extracted_text=extraction_result.extracted_text,
                parse_status=extraction_result.parse_status,
                parsed_at=parsed_at,
            )
        except CvExtractionError:
            cv_upload = _finalize_cv_upload_parse(
                repository,
                cv_upload_id=cv_upload.id,
                extracted_text=None,
                parse_status=CV_PARSE_STATUS_FAILED,
                parsed_at=parsed_at,
            )

        _persist_cv_parse_snapshot(repository, cv_upload=cv_upload)

        _update_profile_cv_metadata(
            repository,
            subscriber_id=user_session.subscriber_id,
            cv_filename=cv_upload.original_filename,
            cv_uploaded_at=cv_upload.uploaded_at or uploaded_at,
            updated_at=uploaded_at,
        )
        _sync_profile_and_cv_retrieval_safe(
            repository,
            subscriber_id=user_session.subscriber_id,
            cv_upload_id=cv_upload.id,
        )
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    return _serialize_cv_upload_response(
        cv_upload,
        repository=repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post("/upload/avatar", response_model=UserProfileAvatarUploadResponse)
async def upload_user_profile_avatar(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    file: Annotated[UploadFile, File(...)],
) -> UserProfileAvatarUploadResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)

    try:
        payload = await file.read()
        validate_avatar_upload(
            filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=len(payload),
        )
        stored = store_profile_file(
            subscriber_id=user_session.subscriber_id,
            category="avatar",
            original_filename=file.filename or "avatar",
            content=payload,
        )
        asset_id = secrets.token_hex(16)
        updated_at = _utc_now_iso()
        avatar_url = f"/api/user/profile/avatar/{asset_id}"
        repository.upsert_subscriber_profile(
            user_session.subscriber_id,
            phone=existing_profile.phone,
            headline=existing_profile.headline,
            summary=existing_profile.summary,
            target_roles=existing_profile.target_roles,
            skills=existing_profile.skills,
            preferred_locations=existing_profile.preferred_locations,
            remote_preference=existing_profile.remote_preference,
            cv_filename=existing_profile.cv_filename,
            cv_uploaded_at=existing_profile.cv_uploaded_at,
            avatar_asset_id=asset_id,
            avatar_storage_path=stored.storage_path,
            avatar_content_type=file.content_type,
            avatar_url=avatar_url,
            updated_at=updated_at,
        )
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    return UserProfileAvatarUploadResponse(
        asset_id=asset_id,
        url=avatar_url,
        status="ready",
    )


@router.get("/avatar/{asset_id}")
def get_user_profile_avatar(
    asset_id: str,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> FileResponse:
    profile = repository.get_subscriber_profile(user_session.subscriber_id)
    if profile.avatar_asset_id != asset_id or not profile.avatar_storage_path:
        raise HTTPException(status_code=404, detail="Avatar not found.")

    file_path = resolve_profile_storage_path(profile.avatar_storage_path)
    return FileResponse(file_path, media_type=profile.avatar_content_type or "image/jpeg")


@router.post(
    "/upload/language-certificate",
    response_model=UserLanguageCertificateResponse,
)
async def upload_language_certificate(
    user_session: UserSessionDep,
    repository: RepositoryDep,
    file: Annotated[UploadFile, File(...)],
    certificate_name: Annotated[str, Form(...)],
    issuer_name: Annotated[str | None, Form()] = None,
    language_entry_id: Annotated[int | None, Form()] = None,
) -> UserLanguageCertificateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None:
        raise HTTPException(status_code=404, detail="Subscriber not found.")

    normalized_certificate_name = certificate_name.strip()
    if not normalized_certificate_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate name is required.",
        )

    try:
        payload = await file.read()
        validate_language_certificate_upload(
            filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=len(payload),
        )
        stored = store_profile_file(
            subscriber_id=user_session.subscriber_id,
            category="language_certificates",
            original_filename=file.filename or "certificate",
            content=payload,
        )
        uploaded_at = _utc_now_iso()
        existing_certificates = repository.list_subscriber_language_certificates(
            user_session.subscriber_id
        )
        updated_certificates = repository.replace_subscriber_language_certificates(
            user_session.subscriber_id,
            certificates=[
                *existing_certificates,
                SubscriberLanguageCertificate(
                    language_entry_id=language_entry_id,
                    certificate_name=normalized_certificate_name,
                    issuer_name=_clean_optional_string(issuer_name),
                    file_name=file.filename or stored.original_filename,
                    storage_path=stored.storage_path,
                    uploaded_at=uploaded_at,
                ),
            ],
            updated_at=uploaded_at,
        )
        certificate = updated_certificates[-1]
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    return UserLanguageCertificateResponse(
        id=certificate.id,
        language_entry_id=certificate.language_entry_id,
        certificate_name=certificate.certificate_name,
        issuer_name=certificate.issuer_name,
        file_name=certificate.file_name,
        uploaded_at=certificate.uploaded_at,
    )


@router.get(
    "/cv/workspace-context",
    response_model=UserCvWorkspaceContextResponse,
)
def get_user_cv_workspace_context(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserCvWorkspaceContextResponse:
    return _get_serialized_cv_workspace_context(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.get(
    "/aggregate",
    response_model=UserProfileAggregateResponse,
)
def get_user_profile_aggregate(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    return _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.patch(
    "/basic-info",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_basic_info(
    payload: UpdateBasicInfoRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    updated_at = _utc_now_iso()

    cleaned_full_name = _clean_optional_string(payload.full_name)
    cleaned_headline = _clean_optional_string(payload.headline)
    cleaned_phone = _clean_optional_string(payload.phone)
    cleaned_summary = _clean_optional_string(payload.summary)
    cleaned_primary_email = _clean_optional_string(payload.primary_email)

    if cleaned_primary_email is not None and cleaned_primary_email != subscriber.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primary email cannot be changed from this endpoint.",
        )

    if payload.full_name is not None:
        repository.update_subscriber_fields_by_id(
            user_session.subscriber_id,
            fields={"full_name": cleaned_full_name},
            updated_at=updated_at,
        )

    repository.upsert_subscriber_profile(
        user_session.subscriber_id,
        phone=cleaned_phone if payload.phone is not None else existing_profile.phone,
        headline=(
            cleaned_headline if payload.headline is not None else existing_profile.headline
        ),
        summary=cleaned_summary if payload.summary is not None else existing_profile.summary,
        target_roles=existing_profile.target_roles,
        skills=existing_profile.skills,
        preferred_locations=existing_profile.preferred_locations,
        remote_preference=existing_profile.remote_preference,
        cv_filename=existing_profile.cv_filename,
        cv_uploaded_at=existing_profile.cv_uploaded_at,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.patch(
    "/preferences",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_preferences(
    payload: UpdatePreferencesRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    updated_at = _utc_now_iso()

    remote_preference_value = None
    if payload.work_modes:
        remote_preference_value = ",".join(payload.work_modes)

    repository.upsert_subscriber_profile(
        user_session.subscriber_id,
        phone=existing_profile.phone,
        headline=existing_profile.headline,
        summary=existing_profile.summary,
        target_roles=_clean_string_list(payload.target_roles),
        skills=existing_profile.skills,
        preferred_locations=_clean_string_list(payload.preferred_locations),
        remote_preference=remote_preference_value,
        cv_filename=existing_profile.cv_filename,
        cv_uploaded_at=existing_profile.cv_uploaded_at,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post(
    "/experiences",
    response_model=UserProfileAggregateResponse,
)
def create_user_profile_experience(
    payload: CreateExperienceRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    title = _clean_optional_string(payload.title)
    company_name = _clean_optional_string(payload.company_name)

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experience title is required.",
        )

    if not company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name is required.",
        )

    start_year = _extract_year_from_partial_date(payload.start_date, "start_date")
    end_year = None if payload.is_current else _extract_year_from_partial_date(
        payload.end_date,
        "end_date",
    )

    updated_at = _utc_now_iso()
    existing_entries = repository.list_subscriber_experience_entries(
        user_session.subscriber_id
    )

    repository.replace_subscriber_experience_entries(
        user_session.subscriber_id,
        entries=[
            *existing_entries,
            SubscriberExperienceEntry(
                title=title,
                company_name=company_name,
                start_year=start_year,
                end_year=end_year,
                summary=_clean_optional_string(payload.description),
            ),
        ],
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.patch(
    "/experiences/{experience_id}",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_experience(
    experience_id: int,
    payload: UpdateExperienceRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_experience_entries(
        user_session.subscriber_id
    )
    target_entry = next(
        (item for item in existing_entries if item.id == experience_id),
        None,
    )
    if target_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience entry not found.",
        )

    updated_title = (
        target_entry.title
        if payload.title is None
        else _clean_optional_string(payload.title)
    )
    updated_company_name = (
        target_entry.company_name
        if payload.company_name is None
        else _clean_optional_string(payload.company_name)
    )

    if not updated_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experience title is required.",
        )

    if not updated_company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name is required.",
        )

    current_is_current = target_entry.end_year is None
    updated_is_current = (
        current_is_current if payload.is_current is None else payload.is_current
    )

    updated_start_year = (
        target_entry.start_year
        if payload.start_date is None
        else _extract_year_from_partial_date(payload.start_date, "start_date")
    )

    if updated_is_current:
        updated_end_year = None
    else:
        updated_end_year = (
            target_entry.end_year
            if payload.end_date is None
            else _extract_year_from_partial_date(payload.end_date, "end_date")
        )

    updated_summary = (
        target_entry.summary
        if payload.description is None
        else _clean_optional_string(payload.description)
    )

    rebuilt_entries: list[SubscriberExperienceEntry] = []
    for item in existing_entries:
        if item.id == experience_id:
            rebuilt_entries.append(
                SubscriberExperienceEntry(
                    title=updated_title,
                    company_name=updated_company_name,
                    start_year=updated_start_year,
                    end_year=updated_end_year,
                    summary=updated_summary,
                )
            )
        else:
            rebuilt_entries.append(
                SubscriberExperienceEntry(
                    title=item.title,
                    company_name=item.company_name,
                    start_year=item.start_year,
                    end_year=item.end_year,
                    summary=item.summary,
                )
            )

    updated_at = _utc_now_iso()
    repository.replace_subscriber_experience_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.delete(
    "/experiences/{experience_id}",
    response_model=UserProfileAggregateResponse,
)
def delete_user_profile_experience(
    experience_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_experience_entries(
        user_session.subscriber_id
    )
    remaining_entries = [
        item for item in existing_entries if item.id != experience_id
    ]

    if len(remaining_entries) == len(existing_entries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience entry not found.",
        )

    rebuilt_entries = [
        SubscriberExperienceEntry(
            title=item.title,
            company_name=item.company_name,
            start_year=item.start_year,
            end_year=item.end_year,
            summary=item.summary,
        )
        for item in remaining_entries
    ]

    updated_at = _utc_now_iso()
    repository.replace_subscriber_experience_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post(
    "/languages",
    response_model=UserProfileAggregateResponse,
)
def create_user_profile_language(
    payload: CreateLanguageRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    language_name = _clean_optional_string(payload.language_name)
    if not language_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language name is required.",
        )

    updated_at = _utc_now_iso()
    existing_entries = repository.list_subscriber_language_entries(
        user_session.subscriber_id
    )

    repository.replace_subscriber_language_entries(
        user_session.subscriber_id,
        entries=[
            *existing_entries,
            SubscriberLanguageEntry(
                language_name=language_name,
                proficiency_level=_clean_optional_string(payload.proficiency_level),
                notes=_clean_optional_string(payload.certificate_name),
            ),
        ],
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.patch(
    "/languages/{language_id}",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_language(
    language_id: int,
    payload: UpdateLanguageRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_language_entries(
        user_session.subscriber_id
    )
    target_entry = next(
        (item for item in existing_entries if item.id == language_id),
        None,
    )
    if target_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language entry not found.",
        )

    updated_language_name = (
        target_entry.language_name
        if payload.language_name is None
        else _clean_optional_string(payload.language_name)
    )
    if not updated_language_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language name is required.",
        )

    updated_proficiency_level = (
        target_entry.proficiency_level
        if payload.proficiency_level is None
        else _clean_optional_string(payload.proficiency_level)
    )

    updated_notes = (
        target_entry.notes
        if payload.certificate_name is None
        else _clean_optional_string(payload.certificate_name)
    )

    rebuilt_entries: list[SubscriberLanguageEntry] = []
    for item in existing_entries:
        if item.id == language_id:
            rebuilt_entries.append(
                SubscriberLanguageEntry(
                    language_name=updated_language_name,
                    proficiency_level=updated_proficiency_level,
                    notes=updated_notes,
                )
            )
        else:
            rebuilt_entries.append(
                SubscriberLanguageEntry(
                    language_name=item.language_name,
                    proficiency_level=item.proficiency_level,
                    notes=item.notes,
                )
            )

    updated_at = _utc_now_iso()
    repository.replace_subscriber_language_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.delete(
    "/languages/{language_id}",
    response_model=UserProfileAggregateResponse,
)
def delete_user_profile_language(
    language_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_language_entries(
        user_session.subscriber_id
    )
    remaining_entries = [item for item in existing_entries if item.id != language_id]

    if len(remaining_entries) == len(existing_entries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language entry not found.",
        )

    rebuilt_entries = [
        SubscriberLanguageEntry(
            language_name=item.language_name,
            proficiency_level=item.proficiency_level,
            notes=item.notes,
        )
        for item in remaining_entries
    ]

    updated_at = _utc_now_iso()
    repository.replace_subscriber_language_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post(
    "/education",
    response_model=UserProfileAggregateResponse,
)
def create_user_profile_education(
    payload: CreateEducationRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    school_name = _clean_optional_string(payload.institution)
    if not school_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution is required.",
        )

    degree_name = _clean_optional_string(payload.degree)
    field_of_study = _clean_optional_string(payload.field_of_study)
    start_year = _extract_year_from_partial_date(payload.start_date, "start_date")
    end_year = _extract_year_from_partial_date(payload.end_date, "end_date")

    updated_at = _utc_now_iso()
    existing_entries = repository.list_subscriber_education_entries(
        user_session.subscriber_id
    )

    repository.replace_subscriber_education_entries(
        user_session.subscriber_id,
        entries=[
            *existing_entries,
            SubscriberEducationEntry(
                school_name=school_name,
                degree_name=degree_name,
                field_of_study=field_of_study,
                start_year=start_year,
                end_year=end_year,
            ),
        ],
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )

@router.patch(
    "/education/{education_id}",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_education(
    education_id: int,
    payload: UpdateEducationRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_education_entries(
        user_session.subscriber_id
    )
    target_entry = next((item for item in existing_entries if item.id == education_id), None)
    if target_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found.",
        )

    updated_school_name = (
        target_entry.school_name
        if payload.institution is None
        else _clean_optional_string(payload.institution)
    )
    if not updated_school_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution is required.",
        )

    updated_degree_name = (
        target_entry.degree_name if payload.degree is None else _clean_optional_string(payload.degree)
    )
    updated_field_of_study = (
        target_entry.field_of_study
        if payload.field_of_study is None
        else _clean_optional_string(payload.field_of_study)
    )
    updated_start_year = (
        target_entry.start_year
        if payload.start_date is None
        else _extract_year_from_partial_date(payload.start_date, "start_date")
    )
    updated_end_year = (
        target_entry.end_year
        if payload.end_date is None
        else _extract_year_from_partial_date(payload.end_date, "end_date")
    )

    rebuilt_entries = [
        SubscriberEducationEntry(
            school_name=updated_school_name if item.id == education_id else item.school_name,
            degree_name=updated_degree_name if item.id == education_id else item.degree_name,
            field_of_study=(updated_field_of_study if item.id == education_id else item.field_of_study),
            start_year=updated_start_year if item.id == education_id else item.start_year,
            end_year=updated_end_year if item.id == education_id else item.end_year,
        )
        for item in existing_entries
    ]

    updated_at = _utc_now_iso()
    repository.replace_subscriber_education_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.delete(
    "/education/{education_id}",
    response_model=UserProfileAggregateResponse,
)
def delete_user_profile_education(
    education_id: int,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_entries = repository.list_subscriber_education_entries(
        user_session.subscriber_id
    )
    remaining_entries = [item for item in existing_entries if item.id != education_id]

    if len(remaining_entries) == len(existing_entries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found.",
        )

    rebuilt_entries = [
        SubscriberEducationEntry(
            school_name=item.school_name,
            degree_name=item.degree_name,
            field_of_study=item.field_of_study,
            start_year=item.start_year,
            end_year=item.end_year,
        )
        for item in remaining_entries
    ]

    updated_at = _utc_now_iso()
    repository.replace_subscriber_education_entries(
        user_session.subscriber_id,
        entries=rebuilt_entries,
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.get(
    "/skills/details",
    response_model=list[UserSkillDetailResponse],
)
def list_user_profile_skill_details(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> list[UserSkillDetailResponse]:
    return [
        _serialize_skill_detail(item)
        for item in repository.list_subscriber_skill_details(user_session.subscriber_id)
    ]


@router.post(
    "/skills",
    response_model=UserProfileAggregateResponse,
)
def create_user_profile_skill(
    payload: CreateSkillRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    skill_name = _clean_optional_string(payload.skill_name)
    if not skill_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill name is required.",
        )

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    existing_skills = tuple(existing_profile.skills)
    if skill_name.lower() in {item.lower() for item in existing_skills}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already exists.",
        )

    updated_at = _utc_now_iso()
    _upsert_profile_with_skills(
        repository,
        subscriber_id=user_session.subscriber_id,
        skills=(*existing_skills, skill_name),
        updated_at=updated_at,
    )
    repository.upsert_subscriber_skill_detail(
        user_session.subscriber_id,
        skill_name=skill_name,
        category=_clean_optional_string(payload.category),
        proficiency_hint=_clean_optional_string(payload.proficiency_hint),
        years_hint=payload.years_hint,
        evidence_note=_clean_optional_string(payload.evidence_note),
        updated_at=updated_at,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.patch(
    "/skills/{skill_id}",
    response_model=UserProfileAggregateResponse,
)
def patch_user_profile_skill(
    skill_id: str,
    payload: UpdateSkillRequest,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    existing_skills = list(existing_profile.skills)
    target_index = _parse_skill_id(skill_id, existing_skills)
    old_skill_name = existing_skills[target_index]

    updated_skill_name = (
        existing_skills[target_index]
        if payload.skill_name is None
        else _clean_optional_string(payload.skill_name)
    )
    if not updated_skill_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill name is required.",
        )

    duplicate_names = {
        item.lower() for index, item in enumerate(existing_skills) if index != target_index
    }
    if updated_skill_name.lower() in duplicate_names:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already exists.",
        )

    existing_skills[target_index] = updated_skill_name

    updated_at = _utc_now_iso()
    _upsert_profile_with_skills(
        repository,
        subscriber_id=user_session.subscriber_id,
        skills=tuple(existing_skills),
        updated_at=updated_at,
    )

    existing_detail = repository.get_subscriber_skill_detail_by_name(
        user_session.subscriber_id,
        old_skill_name,
    )
    if old_skill_name != updated_skill_name:
        repository.rename_subscriber_skill_detail(
            user_session.subscriber_id,
            old_skill_name=old_skill_name,
            new_skill_name=updated_skill_name,
            updated_at=updated_at,
        )
        existing_detail = repository.get_subscriber_skill_detail_by_name(
            user_session.subscriber_id,
            updated_skill_name,
        )

    repository.upsert_subscriber_skill_detail(
        user_session.subscriber_id,
        skill_name=updated_skill_name,
        category=(existing_detail.category if existing_detail is not None and payload.category is None else _clean_optional_string(payload.category)),
        proficiency_hint=(existing_detail.proficiency_hint if existing_detail is not None and payload.proficiency_hint is None else _clean_optional_string(payload.proficiency_hint)),
        years_hint=(existing_detail.years_hint if existing_detail is not None and payload.years_hint is None else payload.years_hint),
        evidence_note=(existing_detail.evidence_note if existing_detail is not None and payload.evidence_note is None else _clean_optional_string(payload.evidence_note)),
        updated_at=updated_at,
        evidence_file_name=existing_detail.evidence_file_name if existing_detail is not None else None,
        evidence_storage_path=existing_detail.evidence_storage_path if existing_detail is not None else None,
        uploaded_at=existing_detail.uploaded_at if existing_detail is not None else None,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.post(
    "/skills/{skill_id}/evidence",
    response_model=UserSkillDetailResponse,
)
async def upload_user_profile_skill_evidence(
    skill_id: str,
    user_session: UserSessionDep,
    repository: RepositoryDep,
    file: Annotated[UploadFile, File(...)],
    evidence_note: Annotated[str | None, Form()] = None,
) -> UserSkillDetailResponse:
    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    existing_skills = list(existing_profile.skills)
    target_index = _parse_skill_id(skill_id, existing_skills)
    skill_name = existing_skills[target_index]

    try:
        payload = await file.read()
        validate_skill_evidence_upload(
            filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=len(payload),
        )
        stored = store_profile_file(
            subscriber_id=user_session.subscriber_id,
            category="skill_evidence",
            original_filename=file.filename or f"{skill_name}-evidence",
            content=payload,
        )
        updated_at = _utc_now_iso()
        current_detail = repository.get_subscriber_skill_detail_by_name(
            user_session.subscriber_id,
            skill_name,
        )
        detail = repository.upsert_subscriber_skill_detail(
            user_session.subscriber_id,
            skill_name=skill_name,
            category=current_detail.category if current_detail is not None else None,
            proficiency_hint=current_detail.proficiency_hint if current_detail is not None else None,
            years_hint=current_detail.years_hint if current_detail is not None else None,
            evidence_note=_clean_optional_string(evidence_note) if evidence_note is not None else (current_detail.evidence_note if current_detail is not None else None),
            updated_at=updated_at,
            evidence_file_name=file.filename or stored.original_filename,
            evidence_storage_path=stored.storage_path,
            uploaded_at=updated_at,
        )
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    _sync_profile_retrieval_safe(
        repository,
        subscriber_id=user_session.subscriber_id,
    )

    return _serialize_skill_detail(detail)


@router.delete(
    "/skills/{skill_id}",
    response_model=UserProfileAggregateResponse,
)
def delete_user_profile_skill(
    skill_id: str,
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> UserProfileAggregateResponse:
    subscriber = repository.get_subscriber_by_id(user_session.subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user could not be found.",
        )

    existing_profile = repository.get_subscriber_profile(user_session.subscriber_id)
    existing_skills = list(existing_profile.skills)
    target_index = _parse_skill_id(skill_id, existing_skills)
    removed_skill_name = existing_skills[target_index]
    del existing_skills[target_index]

    updated_at = _utc_now_iso()
    _upsert_profile_with_skills(
        repository,
        subscriber_id=user_session.subscriber_id,
        skills=tuple(existing_skills),
        updated_at=updated_at,
    )
    repository.delete_subscriber_skill_detail(
        user_session.subscriber_id,
        skill_name=removed_skill_name,
    )

    return _build_profile_aggregate_with_retrieval_sync(
        repository,
        subscriber_id=user_session.subscriber_id,
    )


@router.get(
    "/suggestions",
    response_model=ProfileSuggestionsBundle,
)
def get_user_profile_suggestions(
    user_session: UserSessionDep,
    repository: RepositoryDep,
) -> ProfileSuggestionsBundle:
    aggregate = _get_user_profile_aggregate_response(
        repository,
        subscriber_id=user_session.subscriber_id,
    )
    return aggregate.suggestions