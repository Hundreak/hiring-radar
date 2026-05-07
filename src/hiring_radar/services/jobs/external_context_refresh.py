from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import JobExternalContextSnapshot, JobRecord, JobSource, JobSourceRecord
from hiring_radar.services.ai.web_context import WebContextService
from hiring_radar.services.jobs.canonicalization import refresh_canonical_jobs
from hiring_radar.services.jobs.feature_engine import refresh_matching_readiness_features
from hiring_radar.services.jobs.normalization import normalize_company_name, normalize_job_title, normalize_url_for_dedup

_LEVER_ID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_TRACKING_PARAMS_RE = re.compile(r"([?&](?:utm_[^=&]+|via|gh_jid|gh_src|lever-[^=&]+)=[^&]*)", re.IGNORECASE)


@dataclass(slots=True)
class ExternalContextHydrationResult:
    source_url: str
    final_url: str | None
    hydration_status: str
    fetch_status: str
    http_status: int | None
    page_title: str | None
    site_name: str | None
    text_char_count: int
    clean_text_chars: int
    content_digest: str | None
    requirement_count: int
    responsibility_count: int
    culture_count: int
    tech_term_count: int
    matched_canonical_job_ids: tuple[int, ...]
    refreshed_feature_count: int
    normalized_lookup_url: str
    provider_name: str | None
    extracted_provider_id: str | None
    matched_legacy_job_ids: tuple[int, ...]
    matched_source_record_ids: tuple[int, ...]
    bootstrap_created_sources: int
    bootstrap_created_source_records: int
    bootstrap_created_canonical_jobs: int
    linkage_reason_codes: tuple[str, ...]
    snapshot: JobExternalContextSnapshot | None = None

    @property
    def matched_canonical_jobs(self) -> int:
        return len(self.matched_canonical_job_ids)

    @property
    def requirements(self) -> int:
        return self.requirement_count

    @property
    def responsibilities(self) -> int:
        return self.responsibility_count

    @property
    def culture(self) -> int:
        return self.culture_count

    @property
    def tech_terms(self) -> int:
        return self.tech_term_count


def _utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _strip_tracking(url: str | None) -> str:
    value = (url or '').strip()
    if not value:
        return ''
    cleaned = _TRACKING_PARAMS_RE.sub('', value)
    if cleaned.endswith('?'):
        cleaned = cleaned[:-1]
    return cleaned


def _normalized_url(url: str | None) -> str:
    return normalize_url_for_dedup(_strip_tracking(url))


def _extract_provider_name(url: str | None) -> str | None:
    value = (url or '').strip().casefold()
    if 'jobs.lever.co' in value:
        return 'lever'
    if 'greenhouse.io' in value or 'job-boards.greenhouse.io' in value:
        return 'greenhouse'
    return None


def _extract_provider_id(url: str | None, *, source_job_id: str | None = None) -> str | None:
    if source_job_id and source_job_id.strip():
        return source_job_id.strip()
    value = (url or '').strip()
    if not value:
        return None
    match = _LEVER_ID_RE.search(value)
    if match:
        return match.group(0)
    parsed = urlparse(value)
    path = parsed.path.rstrip('/')
    if not path:
        return None
    parts = [part for part in path.split('/') if part]
    return parts[-1] if parts else None


def _infer_account_slug(url: str | None, *, source_name: str) -> str:
    parsed = urlparse(url or '')
    parts = [part for part in parsed.path.split('/') if part]
    if 'lever.co' in (parsed.netloc or '').casefold() and parts:
        return parts[0]
    if source_name:
        pieces = source_name.split('-')
        if pieces:
            return pieces[0].casefold()
    return 'default'


def _infer_base_url(url: str | None, *, source_type: str, source_name: str) -> str | None:
    value = (url or '').strip()
    if not value:
        return None
    parsed = urlparse(value)
    parts = [part for part in parsed.path.split('/') if part]
    if source_type == 'lever' and parts:
        return f"{parsed.scheme}://{parsed.netloc}/{parts[0]}"
    return f"{parsed.scheme}://{parsed.netloc}{('/' + parts[0]) if parts else ''}"


def _snapshot_payload(snapshot: JobExternalContextSnapshot, legacy_job: JobRecord) -> str:
    metadata = dict(snapshot.source_metadata_json or {})
    description_plain = snapshot.clean_text or ''
    payload = {
        'title': legacy_job.title,
        'company_name': legacy_job.company_name,
        'canonical_url': snapshot.final_url or snapshot.source_url or legacy_job.canonical_url,
        'apply_url': snapshot.final_url or legacy_job.canonical_url,
        'descriptionPlain': description_plain,
        'description_plain': description_plain,
        'content': description_plain,
        'site_specific_requirements': list(snapshot.site_specific_requirements),
        'responsibility_clues': list(snapshot.responsibility_clues),
        'company_culture_clues': list(snapshot.company_culture_clues),
        'technology_stack_terms': list(snapshot.technology_stack_terms),
        'source_metadata': metadata,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _load_snapshot(repository: HiringRadarRepository, source_url: str, final_url: str | None = None) -> JobExternalContextSnapshot | None:
    normalized_source = _normalized_url(source_url)
    candidates = [normalized_source]
    if final_url:
        normalized_final = _normalized_url(final_url)
        if normalized_final and normalized_final not in candidates:
            candidates.append(normalized_final)
    for candidate in candidates:
        if not candidate:
            continue
        snapshot = repository.get_job_external_context_snapshot_by_url(candidate)
        if snapshot is not None:
            return snapshot
    return None


def _fetch_source_record_ids(repository: HiringRadarRepository, *, normalized_url: str, provider_id: str | None, title: str | None, company_name: str | None) -> tuple[int, ...]:
    normalized_title = normalize_job_title(title)
    normalized_company = normalize_company_name(company_name)
    rows = repository.connection.execute(
        """
        SELECT DISTINCT jsr.id, jsr.apply_url, jsr.canonical_url, jsr.external_job_id, jsr.title, jsr.company_name
        FROM job_source_records jsr
        ORDER BY jsr.id ASC
        """
    ).fetchall()
    matches: list[int] = []
    for row in rows:
        if normalized_url and (
            _normalized_url(row['apply_url']) == normalized_url
            or _normalized_url(row['canonical_url']) == normalized_url
        ):
            matches.append(int(row['id']))
            continue
        external_job_id = (row['external_job_id'] or '').strip()
        if provider_id and external_job_id and external_job_id.casefold() == provider_id.casefold():
            matches.append(int(row['id']))
            continue
        if provider_id and (
            provider_id.casefold() in (row['apply_url'] or '').casefold()
            or provider_id.casefold() in (row['canonical_url'] or '').casefold()
        ):
            matches.append(int(row['id']))
            continue
        if normalized_title and normalized_company and normalize_job_title(row['title']) == normalized_title and normalize_company_name(row['company_name']) == normalized_company:
            matches.append(int(row['id']))
    return tuple(dict.fromkeys(matches))


def _fetch_canonical_job_ids(repository: HiringRadarRepository, *, source_record_ids: tuple[int, ...], normalized_url: str, provider_id: str | None, title: str | None, company_name: str | None) -> tuple[int, ...]:
    matches: list[int] = []
    if source_record_ids:
        placeholders = ','.join('?' * len(source_record_ids))
        rows = repository.connection.execute(
            f"""
            SELECT DISTINCT cjl.canonical_job_id
            FROM canonical_job_links cjl
            WHERE cjl.source_job_id IN ({placeholders})
            ORDER BY cjl.canonical_job_id ASC
            """,
            tuple(source_record_ids),
        ).fetchall()
        matches.extend(int(row['canonical_job_id']) for row in rows)
    normalized_title = normalize_job_title(title)
    normalized_company = normalize_company_name(company_name)
    rows = repository.connection.execute(
        """
        SELECT id, apply_url, normalized_title, normalized_company_name, display_title, display_company_name
        FROM canonical_jobs
        WHERE is_active = 1
        ORDER BY id ASC
        """
    ).fetchall()
    for row in rows:
        apply_url = row['apply_url'] or ''
        if normalized_url and _normalized_url(apply_url) == normalized_url:
            matches.append(int(row['id']))
            continue
        if provider_id and provider_id.casefold() in apply_url.casefold():
            matches.append(int(row['id']))
            continue
        if normalized_title and normalized_company and row['normalized_title'] == normalized_title and row['normalized_company_name'] == normalized_company:
            matches.append(int(row['id']))
    return tuple(dict.fromkeys(matches))


def _matched_legacy_jobs(repository: HiringRadarRepository, *, source_url: str, final_url: str | None, provider_id: str | None, snapshot: JobExternalContextSnapshot | None) -> tuple[JobRecord, ...]:
    normalized_source = _normalized_url(source_url)
    normalized_final = _normalized_url(final_url)
    snapshot_title = (snapshot.page_title if snapshot is not None else None) or ''
    title_tokens = [token.strip() for token in re.split(r'\s+-\s+', snapshot_title) if token.strip()]
    normalized_snapshot_title = normalize_job_title(title_tokens[-1] if title_tokens else snapshot_title)
    normalized_snapshot_company = normalize_company_name(title_tokens[0] if len(title_tokens) >= 2 else None)
    matches: list[JobRecord] = []
    for job in repository.list_jobs():
        if normalized_source and _normalized_url(job.canonical_url) == normalized_source:
            matches.append(job)
            continue
        if normalized_final and _normalized_url(job.canonical_url) == normalized_final:
            matches.append(job)
            continue
        if provider_id and job.source_job_id and job.source_job_id.casefold() == provider_id.casefold():
            matches.append(job)
            continue
        if provider_id and provider_id.casefold() in (job.canonical_url or '').casefold():
            matches.append(job)
            continue
        if normalized_snapshot_title and normalized_snapshot_company and normalize_job_title(job.title) == normalized_snapshot_title and normalize_company_name(job.company_name) == normalized_snapshot_company:
            matches.append(job)
    unique: dict[int, JobRecord] = {}
    for job in matches:
        if job.id is not None:
            unique[job.id] = job
    return tuple(unique.values())


def _ensure_job_source(repository: HiringRadarRepository, legacy_job: JobRecord, *, source_url: str, fetched_at: str) -> tuple[JobSource, bool]:
    account_slug = _infer_account_slug(source_url, source_name=legacy_job.source_name)
    existing = repository.get_job_source(
        source_type=legacy_job.source_type,
        source_name=legacy_job.source_name,
        account_slug=account_slug,
    )
    created = existing is None
    source = repository.upsert_job_source(
        JobSource(
            source_type=legacy_job.source_type,
            source_name=legacy_job.source_name,
            account_slug=account_slug,
            base_url=_infer_base_url(source_url, source_type=legacy_job.source_type, source_name=legacy_job.source_name),
            trust_score=0.95 if legacy_job.source_type in {'lever', 'greenhouse'} else 0.9,
            country_scope=None,
            is_active=True,
            created_at=fetched_at,
            updated_at=fetched_at,
        )
    )
    return source, created


def _ensure_source_record(
    repository: HiringRadarRepository,
    *,
    source: JobSource,
    legacy_job: JobRecord,
    snapshot: JobExternalContextSnapshot,
    fetched_at: str,
    provider_id: str | None,
) -> tuple[JobSourceRecord, bool]:
    external_job_id = (legacy_job.source_job_id or provider_id or legacy_job.fingerprint).strip()
    existing = repository.get_job_source_record(source_id=source.id or 0, external_job_id=external_job_id)
    created = existing is None
    raw_payload_json = _snapshot_payload(snapshot, legacy_job)
    record = repository.upsert_job_source_record(
        JobSourceRecord(
            source_id=source.id or 0,
            external_job_id=external_job_id,
            external_company_id=None,
            raw_payload_json=raw_payload_json,
            raw_payload_hash=snapshot.content_digest or sha256(raw_payload_json.encode('utf-8')).hexdigest(),
            canonical_url=snapshot.final_url or snapshot.source_url or legacy_job.canonical_url,
            title=legacy_job.title,
            company_name=legacy_job.company_name,
            location_text=legacy_job.location,
            posted_at=legacy_job.posted_at or legacy_job.raw_posted_at,
            apply_url=snapshot.final_url or snapshot.source_url or legacy_job.canonical_url,
            fetched_at=fetched_at,
            first_seen_at=fetched_at,
            last_seen_at=fetched_at,
            is_active=True,
        )
    )
    return record, created


def _build_reason_codes(*codes: str) -> tuple[str, ...]:
    ordered: list[str] = []
    for code in codes:
        if code and code not in ordered:
            ordered.append(code)
    return tuple(ordered)


def hydrate_job_url(
    repository: HiringRadarRepository,
    *,
    source_url: str,
    observed_at: str | None = None,
    force_refresh: bool = False,
) -> ExternalContextHydrationResult:
    observed = observed_at or _utcnow_iso()
    service = WebContextService(repository=repository)
    insights = _run_async(
        service.get_external_source_insights(
            source_url=source_url,
            observed_at=observed,
            force_refresh=force_refresh,
        )
    )
    metadata = getattr(insights, 'original_source_metadata', None)
    final_url = getattr(metadata, 'final_url', None) if metadata is not None else None
    snapshot = _load_snapshot(repository, source_url, final_url=final_url)
    if snapshot is None:
        return ExternalContextHydrationResult(
            source_url=source_url,
            final_url=final_url,
            hydration_status=getattr(insights, 'enrichment_status', 'unavailable'),
            fetch_status='unavailable',
            http_status=None,
            page_title=None,
            site_name=None,
            text_char_count=0,
            clean_text_chars=0,
            content_digest=None,
            requirement_count=0,
            responsibility_count=0,
            culture_count=0,
            tech_term_count=0,
            matched_canonical_job_ids=(),
            refreshed_feature_count=0,
            normalized_lookup_url=_normalized_url(source_url),
            provider_name=_extract_provider_name(source_url),
            extracted_provider_id=_extract_provider_id(source_url),
            matched_legacy_job_ids=(),
            matched_source_record_ids=(),
            bootstrap_created_sources=0,
            bootstrap_created_source_records=0,
            bootstrap_created_canonical_jobs=0,
            linkage_reason_codes=('ERR_SNAPSHOT_MISSING',),
            snapshot=None,
        )

    provider_name = (snapshot.source_metadata_json or {}).get('provider_name') or _extract_provider_name(snapshot.final_url or snapshot.source_url)
    provider_id = _extract_provider_id(snapshot.final_url or snapshot.source_url)
    normalized_lookup_url = _normalized_url(snapshot.final_url or snapshot.source_url)
    matched_legacy_jobs = _matched_legacy_jobs(
        repository,
        source_url=snapshot.source_url,
        final_url=snapshot.final_url,
        provider_id=provider_id,
        snapshot=snapshot,
    )
    matched_legacy_job_ids = tuple(job.id for job in matched_legacy_jobs if job.id is not None)

    matched_source_record_ids = _fetch_source_record_ids(
        repository,
        normalized_url=normalized_lookup_url,
        provider_id=provider_id,
        title=matched_legacy_jobs[0].title if matched_legacy_jobs else snapshot.page_title,
        company_name=matched_legacy_jobs[0].company_name if matched_legacy_jobs else None,
    )
    matched_canonical_job_ids = _fetch_canonical_job_ids(
        repository,
        source_record_ids=matched_source_record_ids,
        normalized_url=normalized_lookup_url,
        provider_id=provider_id,
        title=matched_legacy_jobs[0].title if matched_legacy_jobs else snapshot.page_title,
        company_name=matched_legacy_jobs[0].company_name if matched_legacy_jobs else None,
    )

    bootstrap_created_sources = 0
    bootstrap_created_source_records = 0
    bootstrap_created_canonical_jobs = 0
    reason_codes: list[str] = []

    if matched_legacy_job_ids:
        reason_codes.append('LEGACY_MATCH_FOUND')
    else:
        reason_codes.append('ERR_NO_LEGACY_MATCH')

    if not matched_source_record_ids and matched_legacy_jobs:
        for legacy_job in matched_legacy_jobs:
            source, source_created = _ensure_job_source(repository, legacy_job, source_url=snapshot.final_url or snapshot.source_url, fetched_at=observed)
            if source_created:
                bootstrap_created_sources += 1
                reason_codes.append('BOOTSTRAP_SOURCE_CREATED')
            record, record_created = _ensure_source_record(
                repository,
                source=source,
                legacy_job=legacy_job,
                snapshot=snapshot,
                fetched_at=observed,
                provider_id=provider_id,
            )
            if record_created:
                bootstrap_created_source_records += 1
                reason_codes.append('BOOTSTRAP_SOURCE_RECORD_CREATED')
        refresh_result = refresh_canonical_jobs(repository, refreshed_at=observed)
        bootstrap_created_canonical_jobs = refresh_result.upserted_jobs
        if refresh_result.upserted_jobs:
            reason_codes.append('BOOTSTRAP_CANONICAL_CREATED')
        matched_source_record_ids = _fetch_source_record_ids(
            repository,
            normalized_url=normalized_lookup_url,
            provider_id=provider_id,
            title=matched_legacy_jobs[0].title if matched_legacy_jobs else snapshot.page_title,
            company_name=matched_legacy_jobs[0].company_name if matched_legacy_jobs else None,
        )
        matched_canonical_job_ids = _fetch_canonical_job_ids(
            repository,
            source_record_ids=matched_source_record_ids,
            normalized_url=normalized_lookup_url,
            provider_id=provider_id,
            title=matched_legacy_jobs[0].title if matched_legacy_jobs else snapshot.page_title,
            company_name=matched_legacy_jobs[0].company_name if matched_legacy_jobs else None,
        )
    elif matched_source_record_ids:
        reason_codes.append('SOURCE_RECORD_MATCH_FOUND')

    refreshed_feature_count = 0
    if matched_canonical_job_ids:
        reason_codes.append('CANONICAL_MATCH_FOUND')
        feature_result = refresh_matching_readiness_features(
            repository,
            refreshed_at=observed,
            canonical_job_ids=matched_canonical_job_ids,
        )
        refreshed_feature_count = feature_result.refreshed_features
        if refreshed_feature_count:
            reason_codes.append('FEATURE_REFRESHED')
    else:
        reason_codes.append('ERR_NO_CANONICAL_MATCH')

    return ExternalContextHydrationResult(
        source_url=snapshot.source_url,
        final_url=snapshot.final_url,
        hydration_status=getattr(insights, 'enrichment_status', 'unavailable'),
        fetch_status=snapshot.fetch_status,
        http_status=snapshot.http_status,
        page_title=snapshot.page_title,
        site_name=snapshot.site_name,
        text_char_count=len(snapshot.clean_text or ''),
        clean_text_chars=len(snapshot.clean_text or ''),
        content_digest=snapshot.content_digest,
        requirement_count=len(snapshot.site_specific_requirements),
        responsibility_count=len(snapshot.responsibility_clues),
        culture_count=len(snapshot.company_culture_clues),
        tech_term_count=len(snapshot.technology_stack_terms),
        matched_canonical_job_ids=matched_canonical_job_ids,
        refreshed_feature_count=refreshed_feature_count,
        normalized_lookup_url=normalized_lookup_url,
        provider_name=provider_name,
        extracted_provider_id=provider_id,
        matched_legacy_job_ids=matched_legacy_job_ids,
        matched_source_record_ids=matched_source_record_ids,
        bootstrap_created_sources=bootstrap_created_sources,
        bootstrap_created_source_records=bootstrap_created_source_records,
        bootstrap_created_canonical_jobs=bootstrap_created_canonical_jobs,
        linkage_reason_codes=_build_reason_codes(*reason_codes),
        snapshot=snapshot,
    )


def hydrate_external_job_url(*args: Any, **kwargs: Any) -> ExternalContextHydrationResult:
    return hydrate_job_url(*args, **kwargs)


def hydrate_job_page_snapshot(*args: Any, **kwargs: Any) -> ExternalContextHydrationResult:
    return hydrate_job_url(*args, **kwargs)


def refresh_external_context_for_jobs(
    repository: HiringRadarRepository,
    *,
    source_urls: list[str],
    observed_at: str | None = None,
    force_refresh: bool = False,
) -> tuple[ExternalContextHydrationResult, ...]:
    observed = observed_at or _utcnow_iso()
    return tuple(
        hydrate_job_url(
            repository,
            source_url=source_url,
            observed_at=observed,
            force_refresh=force_refresh,
        )
        for source_url in source_urls
    )
    
    
from typing import Any


def refresh_external_context_for_job_urls(*args: Any, **kwargs: Any):
    """Backward-compatible alias for older callers."""
    return refresh_external_context_for_jobs(*args, **kwargs)
