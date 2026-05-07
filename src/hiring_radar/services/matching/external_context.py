from __future__ import annotations

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import JobExternalContextSnapshot
from hiring_radar.services.matching.contracts import ExternalSourceInsights, ExternalSourceMetadata


def _snapshot_to_insights(snapshot: JobExternalContextSnapshot) -> ExternalSourceInsights:
    metadata_json = snapshot.source_metadata_json or {}
    metadata = ExternalSourceMetadata(
        source_url=snapshot.source_url,
        final_url=snapshot.final_url,
        source_domain=snapshot.source_domain,
        fetch_status=snapshot.fetch_status,
        http_status=snapshot.http_status,
        page_title=snapshot.page_title or metadata_json.get("page_title"),
        site_name=snapshot.site_name or metadata_json.get("site_name"),
        fetched_at=snapshot.fetched_at,
        content_digest=snapshot.content_digest,
        text_char_count=int(metadata_json.get("text_char_count") or len(snapshot.clean_text or "")),
        provider_name=metadata_json.get("provider_name"),
        acquisition_method=metadata_json.get("acquisition_method"),
        provider_confidence=float(metadata_json["provider_confidence"]) if metadata_json.get("provider_confidence") is not None else None,
    )
    section_lines = metadata_json.get("section_lines") if isinstance(metadata_json.get("section_lines"), dict) else {}
    section_blocks = metadata_json.get("section_blocks") if isinstance(metadata_json.get("section_blocks"), dict) else {}
    raw_capture_metadata = metadata_json.get("raw_capture_metadata") if isinstance(metadata_json.get("raw_capture_metadata"), dict) else {}
    return ExternalSourceInsights(
        enrichment_status="cached",
        site_specific_requirements=snapshot.site_specific_requirements,
        company_culture_clues=snapshot.company_culture_clues,
        responsibility_clues=snapshot.responsibility_clues,
        technology_stack_terms=snapshot.technology_stack_terms,
        original_source_metadata=metadata,
        clean_text=snapshot.clean_text,
        meta_description=snapshot.meta_description,
        section_lines={key: tuple(str(item) for item in items) for key, items in section_lines.items() if isinstance(items, list)},
        section_blocks={key: tuple(str(item) for item in items) for key, items in section_blocks.items() if isinstance(items, list)},
        raw_capture_metadata=raw_capture_metadata,
        warning=snapshot.warning,
    )


def build_cached_external_source_insights(
    repository: HiringRadarRepository,
    *,
    source_url: str | None,
) -> ExternalSourceInsights:
    normalized_source_url = (source_url or "").strip()
    if not normalized_source_url:
        return ExternalSourceInsights()

    snapshot = repository.get_job_external_context_snapshot_by_url(normalized_source_url)
    if snapshot is None:
        return ExternalSourceInsights(
            enrichment_status="unavailable",
            original_source_metadata=ExternalSourceMetadata(source_url=normalized_source_url),
        )

    return _snapshot_to_insights(snapshot)
