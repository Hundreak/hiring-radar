from __future__ import annotations

import json
from datetime import UTC, datetime

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CanonicalJob, CanonicalJobLink, JobSource, JobSourceRecord
from hiring_radar.services.jobs.contracts import CanonicalRefreshResult
from hiring_radar.services.jobs.normalization import (
    build_canonical_job_key,
    compute_description_completeness_score,
    extract_location_city,
    extract_location_country,
    infer_department_family,
    infer_employment_type,
    infer_role_category,
    infer_seniority,
    infer_workplace_type,
    normalize_company_name,
    normalize_job_title,
    normalize_location_text,
    normalize_url_for_dedup,
    strip_html,
)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    try:
        if normalized.endswith("Z"):
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        try:
            return datetime.fromisoformat(f"{normalized}T00:00:00+00:00")
        except ValueError:
            return None


def _score_age_days(age_days: int) -> float:
    if age_days <= 1:
        return 1.0
    if age_days <= 3:
        return 0.95
    if age_days <= 7:
        return 0.88
    if age_days <= 14:
        return 0.76
    if age_days <= 30:
        return 0.6
    if age_days <= 60:
        return 0.42
    return 0.25


def _compute_freshness_score(*, refreshed_at: str, last_seen_at: str | None, posted_at: str | None) -> float:
    anchor = _parse_datetime(refreshed_at)
    if anchor is None:
        return 0.5

    posted_dt = _parse_datetime(posted_at)
    last_seen_dt = _parse_datetime(last_seen_at)

    if posted_dt is None and last_seen_dt is None:
        return 0.5

    components: list[float] = []
    if posted_dt is not None:
        components.append(_score_age_days(max((anchor - posted_dt).days, 0)) * 0.7)
    if last_seen_dt is not None:
        components.append(_score_age_days(max((anchor - last_seen_dt).days, 0)) * 0.3)

    base_score = sum(components)
    if posted_dt is None:
        base_score = min(1.0, base_score + 0.35)
    if last_seen_dt is not None and max((anchor - last_seen_dt).days, 0) <= 1:
        base_score = min(1.0, base_score + 0.05)
    return round(max(0.2, min(1.0, base_score)), 4)


def _extract_payload_description(raw_payload_json: str) -> tuple[str | None, str | None]:
    try:
        payload = json.loads(raw_payload_json)
    except json.JSONDecodeError:
        return (None, None)

    if not isinstance(payload, dict):
        return (None, None)

    for html_key, text_key in (
        ("description", "description_plain"),
        ("description", "descriptionPlain"),
        ("content", "descriptionPlain"),
        ("content", "text"),
    ):
        html_value = payload.get(html_key)
        text_value = payload.get(text_key)
        if isinstance(html_value, str) and html_value.strip():
            html = html_value.strip()
            text = strip_html(text_value if isinstance(text_value, str) else html)
            return (text, html)
    for key in ("description_plain", "descriptionPlain", "text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            text = value.strip()
            return (strip_html(text), None)
    return (None, None)


def _source_type_trust_adjustment(source_type: str) -> float:
    normalized = source_type.casefold()
    if normalized in {"greenhouse", "lever", "ashby", "smartrecruiters"}:
        return 0.01
    if normalized in {"workday", "recruitee", "personio", "icims", "workable"}:
        return 0.005
    if normalized in {"company_careers", "company-careers", "custom_static", "career_page"}:
        return 0.0
    return -0.03


def _compute_source_trust_score(source: JobSource) -> float:
    adjusted = source.trust_score + _source_type_trust_adjustment(source.source_type)
    return round(max(0.2, min(1.0, adjusted)), 4)


def _compute_group_trust_score(group: list[tuple[JobSourceRecord, JobSource]]) -> float:
    base_scores = [_compute_source_trust_score(source) for _record, source in group]
    max_score = max(base_scores) if base_scores else 0.5
    diversity_bonus = min(0.02, 0.01 * max(len({source.source_type for _record, source in group}) - 1, 0))
    same_apply_url = {
        normalize_url_for_dedup(record.apply_url or record.canonical_url)
        for record, _source in group
        if record.apply_url or record.canonical_url
    }
    corroboration_bonus = 0.01 if len(group) > 1 and len(same_apply_url) == 1 else 0.0
    return round(min(1.0, max_score + diversity_bonus + corroboration_bonus), 4)


def _compute_record_quality(record: JobSourceRecord, source: JobSource, *, refreshed_at: str) -> tuple[float, float, float, float]:
    description_text, description_html = _extract_payload_description(record.raw_payload_json)
    completeness = compute_description_completeness_score(description_text, description_html)
    freshness = _compute_freshness_score(
        refreshed_at=refreshed_at,
        last_seen_at=record.last_seen_at,
        posted_at=record.posted_at,
    )
    source_quality = _compute_source_trust_score(source)
    url_bonus = 1.0 if record.apply_url or record.canonical_url else 0.0
    return (source_quality, completeness, freshness, url_bonus)


def _select_primary_record(
    group: list[tuple[JobSourceRecord, JobSource]],
    *,
    refreshed_at: str,
) -> tuple[JobSourceRecord, JobSource]:
    def sort_key(item: tuple[JobSourceRecord, JobSource]) -> tuple[float, float, float, float, float, float]:
        record, source = item
        source_quality, completeness, freshness, url_bonus = _compute_record_quality(
            record,
            source,
            refreshed_at=refreshed_at,
        )
        last_seen = _parse_datetime(record.last_seen_at)
        posted_at = _parse_datetime(record.posted_at)
        return (
            source_quality,
            completeness,
            freshness,
            url_bonus,
            last_seen.timestamp() if last_seen else 0.0,
            posted_at.timestamp() if posted_at else 0.0,
        )

    return max(group, key=sort_key)


def _build_merge_reason(group: list[tuple[JobSourceRecord, JobSource]]) -> str:
    normalized_apply_urls = {
        normalize_url_for_dedup(record.apply_url or record.canonical_url)
        for record, _source in group
        if record.apply_url or record.canonical_url
    }
    normalized_titles = {normalize_job_title(record.title) for record, _source in group}
    normalized_locations = {
        (normalize_location_text(record.location_text) or "").casefold()
        for record, _source in group
    }
    normalized_companies = {normalize_company_name(record.company_name) for record, _source in group}
    if len(group) == 1:
        return "single_source_record"
    if normalized_apply_urls and len(normalized_apply_urls) == 1 and len(normalized_titles) == 1:
        return "exact_apply_url_and_title"
    if normalized_apply_urls and len(normalized_apply_urls) == 1:
        return "exact_apply_url"
    if len(normalized_companies) == 1 and len(normalized_titles) == 1 and len(normalized_locations) == 1:
        return "normalized_company_title_location"
    return "title_company_cluster"


def _build_link_confidence(merge_reason: str, *, group_size: int) -> float:
    base = {
        "exact_apply_url_and_title": 0.99,
        "exact_apply_url": 0.97,
        "normalized_company_title_location": 0.94,
        "title_company_cluster": 0.88,
        "single_source_record": 0.9,
    }.get(merge_reason, 0.85)
    if group_size >= 3:
        base += 0.01
    return round(min(0.995, base), 4)


def _build_canonical_job(
    *,
    canonical_key: str,
    group: list[tuple[JobSourceRecord, JobSource]],
    refreshed_at: str,
) -> CanonicalJob:
    primary_record, primary_source = _select_primary_record(group, refreshed_at=refreshed_at)
    description_text, description_html = _extract_payload_description(primary_record.raw_payload_json)
    location_city = extract_location_city(primary_record.location_text)
    country = extract_location_country(primary_record.location_text) or primary_source.country_scope
    latest_last_seen = max(
        (record.last_seen_at for record, _source in group if record.last_seen_at),
        default=primary_record.last_seen_at,
    )
    latest_posted_at = max(
        (record.posted_at for record, _source in group if record.posted_at),
        default=primary_record.posted_at,
    )

    return CanonicalJob(
        canonical_key=canonical_key,
        normalized_title=normalize_job_title(primary_record.title),
        normalized_company_name=normalize_company_name(primary_record.company_name),
        display_title=primary_record.title,
        display_company_name=primary_record.company_name,
        location_city=location_city,
        district=None,
        country=country,
        workplace_type=infer_workplace_type(primary_record.location_text),
        employment_type=infer_employment_type(
            primary_record.title,
            primary_record.location_text,
            description_text,
        ),
        seniority=infer_seniority(primary_record.title, description_text),
        category=infer_role_category(primary_record.title, description_text),
        department=infer_department_family(primary_record.title, description_text),
        description_text=description_text,
        description_html=description_html,
        posted_at=latest_posted_at,
        apply_url=primary_record.apply_url or primary_record.canonical_url or canonical_key,
        trust_score=_compute_group_trust_score(group),
        freshness_score=_compute_freshness_score(
            refreshed_at=refreshed_at,
            last_seen_at=latest_last_seen,
            posted_at=latest_posted_at,
        ),
        is_active=True,
        created_at=refreshed_at,
        updated_at=refreshed_at,
    )


def refresh_canonical_jobs(
    repository: HiringRadarRepository,
    *,
    refreshed_at: str,
) -> CanonicalRefreshResult:
    sources = repository.list_job_sources(active_only=True)
    {source.id or 0: source for source in sources}
    active_records: list[tuple[JobSourceRecord, JobSource]] = []

    for source in sources:
        if source.id is None:
            continue
        records = repository.list_job_source_records(source_id=source.id, active_only=True)
        active_records.extend((record, source) for record in records)

    groups: dict[str, list[tuple[JobSourceRecord, JobSource]]] = {}
    for record, source in active_records:
        canonical_key = build_canonical_job_key(
            company_name=record.company_name,
            title=record.title,
            location_text=normalize_location_text(record.location_text),
            apply_url=record.apply_url,
            canonical_url=record.canonical_url,
            fallback_key=f"{source.source_type}:{source.source_name}:{record.external_job_id}",
        )
        groups.setdefault(canonical_key, []).append((record, source))

    stored_jobs: list[CanonicalJob] = []
    links_upserted = 0
    seen_canonical_keys: list[str] = []

    for canonical_key, group in groups.items():
        stored_job = repository.upsert_canonical_job(
            _build_canonical_job(canonical_key=canonical_key, group=group, refreshed_at=refreshed_at)
        )
        stored_jobs.append(stored_job)
        seen_canonical_keys.append(canonical_key)
        merge_reason = _build_merge_reason(group)
        confidence = _build_link_confidence(merge_reason, group_size=len(group))
        for record, _source in group:
            if record.id is None or stored_job.id is None:
                continue
            repository.upsert_canonical_job_link(
                CanonicalJobLink(
                    canonical_job_id=stored_job.id,
                    source_job_id=record.id,
                    merge_reason=merge_reason,
                    confidence=confidence,
                    created_at=refreshed_at,
                    updated_at=refreshed_at,
                )
            )
            links_upserted += 1

    links_pruned = repository.prune_canonical_job_links_for_inactive_source_records()
    deactivated_jobs = repository.mark_missing_canonical_jobs_inactive(
        seen_canonical_keys=seen_canonical_keys,
        updated_at=refreshed_at,
    )

    return CanonicalRefreshResult(
        total_active_records=len(active_records),
        grouped_jobs=len(groups),
        upserted_jobs=len(stored_jobs),
        deactivated_jobs=deactivated_jobs,
        links_upserted=links_upserted,
        links_pruned=links_pruned,
        canonical_jobs=tuple(stored_jobs),
        source_links_total=links_upserted - links_pruned,
    )
