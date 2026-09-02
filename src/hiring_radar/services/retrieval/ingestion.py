from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import RetrievalChunk, RetrievalDocument, RetrievalSource
from hiring_radar.services.retrieval.chunking import chunk_text
from hiring_radar.services.retrieval.embedding_jobs import enqueue_chunk_embedding_jobs

RETRIEVAL_STATUS_PENDING = "pending"
RETRIEVAL_STATUS_READY = "ready"
RETRIEVAL_STATUS_STALE = "stale"
RETRIEVAL_STATUS_FAILED = "failed"

SOURCE_TYPE_PROFILE = "profile"
SOURCE_TYPE_CV_UPLOAD = "cv_upload"
SOURCE_TYPE_AI_AUDIT = "ai_audit"

DOCUMENT_KIND_PROFILE_AGGREGATE = "profile_aggregate"
DOCUMENT_KIND_CV_TEXT = "cv_text"
DOCUMENT_KIND_AI_AUDIT = "ai_audit_summary"

INGESTION_ACTION_CREATED = "created"
INGESTION_ACTION_UPDATED = "updated"
INGESTION_ACTION_NOOP = "noop"
INGESTION_ACTION_SKIPPED = "skipped"
INGESTION_ACTION_FAILED = "failed"

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class PreparedRetrievalDocument:
    subscriber_id: int
    source_type: str
    source_ref: str
    title: str | None
    locale: str | None
    document_kind: str
    body_text: str
    metadata_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RetrievalIngestionResult:
    action: str
    source: RetrievalSource | None
    document: RetrievalDocument | None
    chunk_count: int
    reason: str | None = None

    @property
    def changed(self) -> bool:
        return self.action in {INGESTION_ACTION_CREATED, INGESTION_ACTION_UPDATED}



def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()



def stable_checksum(payload: Any) -> str:
    if isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    return hashlib.sha256(raw).hexdigest()



def build_profile_prepared_document(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    locale: str | None = None,
) -> PreparedRetrievalDocument:
    subscriber = repository.get_subscriber_by_id(subscriber_id)
    if subscriber is None or subscriber.id is None:
        raise RuntimeError("Subscriber not found for profile retrieval ingestion.")

    profile = repository.get_subscriber_profile(subscriber_id)
    experiences = repository.list_subscriber_experience_entries(subscriber_id)
    education = repository.list_subscriber_education_entries(subscriber_id)
    languages = repository.list_subscriber_language_entries(subscriber_id)
    skills = repository.list_subscriber_skill_details(subscriber_id)
    latest_cv_upload = repository.get_latest_subscriber_cv_upload(subscriber_id)

    sections: list[str] = []

    identity_lines = [
        f"Ad Soyad: {(subscriber.full_name or '').strip() or 'Belirtilmedi'}",
        f"E-posta: {subscriber.email}",
    ]
    if profile.phone:
        identity_lines.append(f"Telefon: {profile.phone}")
    if profile.headline:
        identity_lines.append(f"Başlık: {profile.headline}")
    if profile.summary:
        identity_lines.append(f"Özet: {profile.summary}")
    sections.append("# Temel Bilgiler\n" + "\n".join(identity_lines))

    preference_lines: list[str] = []
    if profile.target_roles:
        preference_lines.append("Hedef Roller: " + ", ".join(profile.target_roles))
    if profile.preferred_locations:
        preference_lines.append(
            "Tercih Edilen Lokasyonlar: " + ", ".join(profile.preferred_locations)
        )
    if profile.remote_preference:
        preference_lines.append(f"Çalışma Modu: {profile.remote_preference}")
    if latest_cv_upload is not None:
        preference_lines.append(
            f"Son CV: {latest_cv_upload.original_filename} ({latest_cv_upload.parse_status})"
        )
    if preference_lines:
        sections.append("# Tercihler\n" + "\n".join(preference_lines))

    if profile.skills:
        sections.append("# Yetenekler\n" + "\n".join(f"- {item}" for item in profile.skills))

    if skills:
        skill_lines = []
        for item in skills:
            line_parts = [f"- {item.skill_name}"]
            if item.category:
                line_parts.append(f"Kategori: {item.category}")
            if item.proficiency_hint:
                line_parts.append(f"Açıklama: {item.proficiency_hint}")
            if item.years_hint is not None:
                line_parts.append(f"Yıl: {item.years_hint}")
            if item.evidence_note:
                line_parts.append(f"Kanıt: {item.evidence_note}")
            skill_lines.append(" | ".join(line_parts))
        sections.append("# Yetenek Detayları\n" + "\n".join(skill_lines))

    if experiences:
        experience_lines = []
        for item in experiences:
            line = f"- {item.title}"
            if item.company_name:
                line += f" @ {item.company_name}"
            years: list[str] = []
            if item.start_year is not None:
                years.append(str(item.start_year))
            if item.end_year is not None:
                years.append(str(item.end_year))
            if years:
                line += f" ({' - '.join(years)})"
            if item.summary:
                line += f": {item.summary}"
            experience_lines.append(line)
        sections.append("# Deneyim\n" + "\n".join(experience_lines))

    if education:
        education_lines = []
        for item in education:
            line = f"- {item.school_name}"
            if item.degree_name:
                line += f" | {item.degree_name}"
            if item.field_of_study:
                line += f" | {item.field_of_study}"
            years: list[str] = []
            if item.start_year is not None:
                years.append(str(item.start_year))
            if item.end_year is not None:
                years.append(str(item.end_year))
            if years:
                line += f" ({' - '.join(years)})"
            education_lines.append(line)
        sections.append("# Eğitim\n" + "\n".join(education_lines))

    if languages:
        language_lines = []
        for item in languages:
            line = f"- {item.language_name}"
            if item.proficiency_level:
                line += f" | Seviye: {item.proficiency_level}"
            if item.notes:
                line += f" | Not: {item.notes}"
            language_lines.append(line)
        sections.append("# Diller\n" + "\n".join(language_lines))

    body_text = "\n\n".join(section for section in sections if section.strip())
    metadata_json = {
        "subscriber_email": subscriber.email,
        "experience_count": len(experiences),
        "education_count": len(education),
        "language_count": len(languages),
        "skill_count": len(profile.skills),
        "skill_detail_count": len(skills),
        "profile_updated_at": profile.updated_at,
        "cv_parse_status": latest_cv_upload.parse_status if latest_cv_upload is not None else None,
    }
    title = (subscriber.full_name or subscriber.email or f"subscriber-{subscriber_id}").strip()
    return PreparedRetrievalDocument(
        subscriber_id=subscriber_id,
        source_type=SOURCE_TYPE_PROFILE,
        source_ref=f"subscriber:{subscriber_id}:profile",
        title=f"Profile · {title}",
        locale=locale,
        document_kind=DOCUMENT_KIND_PROFILE_AGGREGATE,
        body_text=body_text,
        metadata_json=metadata_json,
    )



def build_cv_prepared_document(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    cv_upload_id: int,
    locale: str | None = None,
) -> PreparedRetrievalDocument | None:
    cv_upload = repository.get_subscriber_cv_upload_by_id(cv_upload_id)
    if cv_upload is None or cv_upload.subscriber_id != subscriber_id:
        return None

    extracted_text = (cv_upload.extracted_text or "").strip()
    if cv_upload.parse_status != "parsed" or not extracted_text:
        return PreparedRetrievalDocument(
            subscriber_id=subscriber_id,
            source_type=SOURCE_TYPE_CV_UPLOAD,
            source_ref=f"cv_upload:{cv_upload_id}",
            title=cv_upload.original_filename,
            locale=locale,
            document_kind=DOCUMENT_KIND_CV_TEXT,
            body_text="",
            metadata_json={
                "cv_upload_id": cv_upload_id,
                "parse_status": cv_upload.parse_status,
                "content_type": cv_upload.content_type,
                "file_size_bytes": cv_upload.file_size_bytes,
                "uploaded_at": cv_upload.uploaded_at,
                "parsed_at": cv_upload.parsed_at,
            },
        )

    return PreparedRetrievalDocument(
        subscriber_id=subscriber_id,
        source_type=SOURCE_TYPE_CV_UPLOAD,
        source_ref=f"cv_upload:{cv_upload_id}",
        title=cv_upload.original_filename,
        locale=locale,
        document_kind=DOCUMENT_KIND_CV_TEXT,
        body_text=extracted_text,
        metadata_json={
            "cv_upload_id": cv_upload_id,
            "parse_status": cv_upload.parse_status,
            "content_type": cv_upload.content_type,
            "file_size_bytes": cv_upload.file_size_bytes,
            "uploaded_at": cv_upload.uploaded_at,
            "parsed_at": cv_upload.parsed_at,
        },
    )



def build_ai_audit_prepared_document(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    locale: str | None = None,
    limit: int = 20,
) -> PreparedRetrievalDocument | None:
    events = repository.list_subscriber_ai_audit_logs(subscriber_id, limit=limit)
    if not events:
        return None

    lines = ["# AI Audit Trail"]
    for item in events:
        lines.append(
            " | ".join(
                part
                for part in [
                    f"Alan: {item.target_field}",
                    f"Aksiyon: {item.action_type}",
                    f"Panel: {item.source_panel}" if item.source_panel else None,
                    f"Durum: {item.persistence_status}",
                    f"Telemetry: {item.telemetry_ref}" if item.telemetry_ref else None,
                    f"Değerlendirme: {item.evaluation_status}" if item.evaluation_status else None,
                ]
                if part
            )
        )
    body_text = "\n".join(lines)
    return PreparedRetrievalDocument(
        subscriber_id=subscriber_id,
        source_type=SOURCE_TYPE_AI_AUDIT,
        source_ref=f"subscriber:{subscriber_id}:ai-audit",
        title="AI Audit Trail",
        locale=locale,
        document_kind=DOCUMENT_KIND_AI_AUDIT,
        body_text=body_text,
        metadata_json={"event_count": len(events)},
    )



def ingest_prepared_document(
    repository: HiringRadarRepository,
    prepared: PreparedRetrievalDocument,
    *,
    now: str | None = None,
) -> RetrievalIngestionResult:
    timestamp = now or utc_now_iso()
    source_checksum = stable_checksum(
        {
            "title": prepared.title,
            "locale": prepared.locale,
            "body": prepared.body_text,
            "metadata": prepared.metadata_json,
        }
    )
    document_checksum = stable_checksum(prepared.body_text)
    source = repository.get_retrieval_source_by_key(
        prepared.subscriber_id,
        prepared.source_type,
        prepared.source_ref,
    )
    source = repository.upsert_retrieval_source(
        prepared.subscriber_id,
        source_type=prepared.source_type,
        source_ref=prepared.source_ref,
        title=prepared.title,
        locale=prepared.locale,
        status=RETRIEVAL_STATUS_PENDING,
        checksum=source_checksum,
        metadata_json=prepared.metadata_json,
        updated_at=timestamp,
        last_ingested_at=source.last_ingested_at if source is not None else None,
        error_message=None,
    )

    existing_document = repository.get_retrieval_document_by_kind(
        source.id or 0,
        prepared.document_kind,
    )

    if not prepared.body_text.strip():
        source = repository.update_retrieval_source_lifecycle(
            source.id or 0,
            status=RETRIEVAL_STATUS_FAILED,
            updated_at=timestamp,
            error_message="No retrieval-ready text was produced for this source.",
        )
        if existing_document is not None and existing_document.id is not None:
            document = repository.update_retrieval_document_lifecycle(
                existing_document.id,
                status=RETRIEVAL_STATUS_FAILED,
                updated_at=timestamp,
                checksum=document_checksum,
                version=existing_document.version,
            )
        else:
            document = None
        return RetrievalIngestionResult(
            action=INGESTION_ACTION_SKIPPED,
            source=source,
            document=document,
            chunk_count=0,
            reason="empty_body",
        )

    if existing_document is not None and existing_document.checksum == document_checksum:
        document = repository.update_retrieval_document_lifecycle(
            existing_document.id or 0,
            status=RETRIEVAL_STATUS_READY,
            updated_at=timestamp,
            checksum=document_checksum,
            version=existing_document.version,
        )
        source = repository.update_retrieval_source_lifecycle(
            source.id or 0,
            status=RETRIEVAL_STATUS_READY,
            updated_at=timestamp,
            last_ingested_at=timestamp,
            error_message=None,
        )
        return RetrievalIngestionResult(
            action=INGESTION_ACTION_NOOP,
            source=source,
            document=document,
            chunk_count=len(repository.list_retrieval_chunks(document.id or 0)),
            reason="checksum_unchanged",
        )

    version = 1 if existing_document is None else existing_document.version + 1
    action = INGESTION_ACTION_CREATED if existing_document is None else INGESTION_ACTION_UPDATED

    document = repository.upsert_retrieval_document(
        source.id or 0,
        document_kind=prepared.document_kind,
        title=prepared.title,
        body_text=prepared.body_text,
        metadata_json=prepared.metadata_json,
        checksum=document_checksum,
        status=RETRIEVAL_STATUS_PENDING,
        version=version,
        updated_at=timestamp,
    )

    drafts = chunk_text(prepared.body_text)
    chunks = [
        RetrievalChunk(
            document_id=document.id or 0,
            chunk_index=index,
            content=draft.content,
            token_estimate=draft.token_estimate,
            metadata_json=draft.metadata_json,
            embedding_status="pending",
            created_at=timestamp,
        )
        for index, draft in enumerate(drafts)
    ]

    try:
        stored_chunks = repository.replace_retrieval_chunks(
            document.id or 0,
            chunks=chunks,
            created_at=timestamp,
        )
        document = repository.update_retrieval_document_lifecycle(
            document.id or 0,
            status=RETRIEVAL_STATUS_READY,
            updated_at=timestamp,
            checksum=document_checksum,
            version=version,
        )
        source = repository.update_retrieval_source_lifecycle(
            source.id or 0,
            status=RETRIEVAL_STATUS_READY,
            updated_at=timestamp,
            last_ingested_at=timestamp,
            error_message=None,
        )
        try:
            enqueue_chunk_embedding_jobs(
                repository,
                chunks=stored_chunks,
                created_at=timestamp,
            )
        except Exception:
            logger.exception(
                "Failed to enqueue retrieval embedding jobs.",
                extra={
                    "subscriber_id": prepared.subscriber_id,
                    "source_type": prepared.source_type,
                    "source_ref": prepared.source_ref,
                    "document_kind": prepared.document_kind,
                },
            )
    except Exception as exc:
        source = repository.update_retrieval_source_lifecycle(
            source.id or 0,
            status=RETRIEVAL_STATUS_FAILED,
            updated_at=timestamp,
            error_message=str(exc),
        )
        repository.update_retrieval_document_lifecycle(
            document.id or 0,
            status=RETRIEVAL_STATUS_FAILED,
            updated_at=timestamp,
            checksum=document_checksum,
            version=version,
        )
        raise

    return RetrievalIngestionResult(
        action=action,
        source=source,
        document=document,
        chunk_count=len(stored_chunks),
    )



def mark_retrieval_source_stale(
    repository: HiringRadarRepository,
    *,
    subscriber_id: int,
    source_type: str,
    source_ref: str,
    timestamp: str | None = None,
) -> RetrievalSource | None:
    source = repository.get_retrieval_source_by_key(subscriber_id, source_type, source_ref)
    if source is None or source.id is None:
        return None
    return repository.update_retrieval_source_lifecycle(
        source.id,
        status=RETRIEVAL_STATUS_STALE,
        updated_at=timestamp or utc_now_iso(),
        error_message=None,
    )
