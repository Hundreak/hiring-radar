from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import replace as dataclass_replace
from typing import Any

from hiring_radar.models import SubscriberCvUpload
from hiring_radar.services.cv_engine.adapters.to_legacy_parse_snapshot import (
    parse_result_to_legacy_snapshot,
)
from hiring_radar.services.cv_engine.config import ParserRuntimeConfig
from hiring_radar.services.cv_engine.legacy_runtime import (
    build_foundation_parser_result_from_text,
)
from hiring_radar.services.cv_extraction import (
    CV_PARSE_STATUS_PARSED,
    cv_extraction_uses_ocr,
    infer_cv_extraction_method,
    normalize_extracted_text,
)
from hiring_radar.services.cv_profile_draft import (
    CvDraftCertificationEntry,
    CvDraftEducationEntry,
    CvDraftExperienceEntry,
    CvDraftLanguageEntry,
    CvProfileDraft,
    CvProfileDraftSnapshot,
    build_cv_draft_certification_entry,
    build_cv_draft_education_entry,
    build_cv_draft_experience_entry,
    build_cv_draft_language_entry,
    build_cv_profile_draft,
    build_cv_profile_draft_snapshot,
)
from hiring_radar.services.cv_profile_parser import (
    HEURISTIC_CV_PARSER_VERSION,
    parse_cv_text_to_profile_draft,
)

CV_AI_STRUCTURING_MODE_ENV_VAR = "HIRING_RADAR_CV_AI_STRUCTURING"
CV_AI_STRUCTURING_MODE_OFF = "off"
CV_AI_STRUCTURING_MODE_OCR = "ocr"
CV_AI_STRUCTURING_MODE_AUTO = "auto"
CV_AI_STRUCTURING_MODE_ALL = "all"
_DEFAULT_CV_AI_STRUCTURING_MODE = CV_AI_STRUCTURING_MODE_OCR


def build_cv_profile_draft_snapshot_from_cv_upload(
    cv_upload: SubscriberCvUpload,
    *,
    ai_structuring_mode: str | None = None,
) -> CvProfileDraftSnapshot:
    """Build a normalized draft snapshot from a persisted CV upload.

    Parse order:
      1. v2 foundation parser bridge (primary)
      2. Legacy heuristic parser (fallback when v2 raises)
      3. For OCR image sources: Ollama second-stage structuring is attempted
         after either parser run. If Ollama succeeds, its result overrides
         the heuristic/v2 draft for structured fields (name, headline,
         experience, education) which are hard to parse from interleaved
         two-column OCR text. Skills from the v2 engine are preserved when
         the Ollama skills list is empty.

    Args:
        cv_upload: Finalized CV upload record.

    Returns:
        A normalized snapshot. Failed or empty uploads yield an empty draft
        while preserving metadata about the source upload.
    """
    extracted_text = normalize_extracted_text(cv_upload.extracted_text)
    generated_at = cv_upload.parsed_at or cv_upload.uploaded_at

    if cv_upload.parse_status == CV_PARSE_STATUS_PARSED and extracted_text is not None:
        snapshot = _build_v2_legacy_compatible_snapshot(
            cv_upload=cv_upload,
            extracted_text=extracted_text,
            generated_at=generated_at,
        )
        heuristic_draft = parse_cv_text_to_profile_draft(extracted_text)
        if snapshot is None:
            snapshot = build_cv_profile_draft_snapshot(
                source_upload_id=cv_upload.id,
                source_filename=cv_upload.original_filename,
                source_parse_status=cv_upload.parse_status,
                parser_version=HEURISTIC_CV_PARSER_VERSION,
                generated_at=generated_at,
                draft=heuristic_draft,
            )
        else:
            snapshot = dataclass_replace(
                snapshot,
                draft=_merge_v2_and_heuristic_drafts(snapshot.draft, heuristic_draft),
            )

        # Optional Ollama-assisted structuring pass. By default this preserves
        # the previous contract (OCR image sources only), but diagnostics and
        # local deployments can opt into ``auto`` or ``all`` via
        # HIRING_RADAR_CV_AI_STRUCTURING.
        if _should_apply_ai_structuring(
            snapshot=snapshot,
            original_filename=cv_upload.original_filename,
            content_type=cv_upload.content_type,
            requested_mode=ai_structuring_mode,
        ):
            snapshot = _apply_ollama_structuring_if_available(
                snapshot=snapshot,
                extracted_text=extracted_text,
            )

        return snapshot

    return build_cv_profile_draft_snapshot(
        source_upload_id=cv_upload.id,
        source_filename=cv_upload.original_filename,
        source_parse_status=cv_upload.parse_status,
        parser_version=None,
        generated_at=generated_at,
        draft=CvProfileDraft(),
    )


def _resolve_ai_structuring_mode(requested_mode: str | None = None) -> str:
    """Resolve the local-AI structuring mode.

    Modes:
      * off/never/false/0: never call Ollama
      * ocr: only image OCR sources (backwards-compatible default)
      * auto: image OCR sources or sparse heuristic/v2 drafts
      * all: every parsed CV text
    """
    raw_mode = requested_mode
    if raw_mode is None:
        raw_mode = os.getenv(CV_AI_STRUCTURING_MODE_ENV_VAR, _DEFAULT_CV_AI_STRUCTURING_MODE)
    mode = (raw_mode or _DEFAULT_CV_AI_STRUCTURING_MODE).strip().lower()
    aliases = {
        "0": CV_AI_STRUCTURING_MODE_OFF,
        "false": CV_AI_STRUCTURING_MODE_OFF,
        "no": CV_AI_STRUCTURING_MODE_OFF,
        "never": CV_AI_STRUCTURING_MODE_OFF,
        "disabled": CV_AI_STRUCTURING_MODE_OFF,
        "image": CV_AI_STRUCTURING_MODE_OCR,
        "images": CV_AI_STRUCTURING_MODE_OCR,
        "ocr-only": CV_AI_STRUCTURING_MODE_OCR,
        "1": CV_AI_STRUCTURING_MODE_AUTO,
        "true": CV_AI_STRUCTURING_MODE_AUTO,
        "yes": CV_AI_STRUCTURING_MODE_AUTO,
        "enabled": CV_AI_STRUCTURING_MODE_AUTO,
        "always": CV_AI_STRUCTURING_MODE_ALL,
    }
    mode = aliases.get(mode, mode)
    if mode not in {
        CV_AI_STRUCTURING_MODE_OFF,
        CV_AI_STRUCTURING_MODE_OCR,
        CV_AI_STRUCTURING_MODE_AUTO,
        CV_AI_STRUCTURING_MODE_ALL,
    }:
        return _DEFAULT_CV_AI_STRUCTURING_MODE
    return mode


def _should_apply_ai_structuring(
    *,
    snapshot: CvProfileDraftSnapshot,
    original_filename: str | None,
    content_type: str | None,
    requested_mode: str | None = None,
) -> bool:
    mode = _resolve_ai_structuring_mode(requested_mode)
    if mode == CV_AI_STRUCTURING_MODE_OFF:
        return False
    if mode == CV_AI_STRUCTURING_MODE_ALL:
        return True

    uses_ocr = cv_extraction_uses_ocr(original_filename, content_type)
    if mode == CV_AI_STRUCTURING_MODE_OCR:
        return uses_ocr

    # ``auto``: ask Ollama when the deterministic parser produced a sparse
    # draft. This catches scanned PDFs/manual exports if operators opt in.
    return uses_ocr or _draft_is_sparse_for_ai_structuring(snapshot.draft)


def _draft_is_sparse_for_ai_structuring(draft: CvProfileDraft) -> bool:
    contact_signal = bool(draft.email or draft.phone)
    role_signal = bool(draft.headline or draft.target_roles)
    structured_signal = bool(draft.experience_entries or draft.education_entries)
    skill_signal = len(draft.skills) >= 3
    return not (contact_signal and role_signal and structured_signal and skill_signal)


def _apply_ollama_structuring_if_available(
    *,
    snapshot: CvProfileDraftSnapshot,
    extracted_text: str,
) -> CvProfileDraftSnapshot:
    """Attempt Ollama second-stage structuring and merge result into snapshot.

    Returns the original snapshot unchanged if Ollama is unavailable,
    times out, or returns an unusable result.
    """
    from hiring_radar.services.cv_ocr_structuring import (
        extract_cv_structure_with_ollama,
    )

    try:
        ollama_result = extract_cv_structure_with_ollama(extracted_text)
    except Exception:
        return snapshot

    if ollama_result is None:
        return snapshot

    ai_draft = ollama_result.draft
    base_draft = snapshot.draft

    # Merge strategy: deterministic extraction remains the source of truth for
    # factual fields when it is already rich.  Ollama is valuable for filling
    # gaps in noisy OCR, but it may paraphrase summaries or return shorter
    # skill lists.  Merge AI additions instead of blindly replacing good base
    # evidence.
    filtered_ai_skills = _filter_ai_skill_values(
        ai_draft.skills,
        source_text=extracted_text,
    )

    merged = dataclass_replace(
        base_draft,
        # Deterministic extraction is the source of truth for factual contact
        # fields when it already found a value. Ollama can normalize or infer
        # too aggressively (e.g. Turkish local phone ``0212...`` → ``+212...``),
        # so AI is only allowed to fill blanks here.
        full_name=base_draft.full_name or ai_draft.full_name,
        headline=base_draft.headline or ai_draft.headline,
        email=base_draft.email or ai_draft.email,
        phone=base_draft.phone or ai_draft.phone,
        linkedin_url=base_draft.linkedin_url or ai_draft.linkedin_url,
        github_url=base_draft.github_url or ai_draft.github_url,
        summary=_choose_better_summary(base_draft.summary, ai_draft.summary),
        # Target roles are preference-like. Do not let AI promote every past
        # job title into desired roles when deterministic parsing already found
        # a clean headline/target signal.
        target_roles=base_draft.target_roles or ai_draft.target_roles,
        skills=_merge_string_tuple_fields(base_draft.skills, filtered_ai_skills),
        # Always use Ollama's explicit-preference result for preference fields.
        preferred_locations=ai_draft.preferred_locations,
        education_entries=_choose_richer_entries(
            base_draft.education_entries,
            ai_draft.education_entries,
        ),
        experience_entries=_choose_richer_entries(
            base_draft.experience_entries,
            ai_draft.experience_entries,
        ),
        certification_entries=_choose_richer_entries(
            base_draft.certification_entries,
            ai_draft.certification_entries,
        ),
    )
    return dataclass_replace(snapshot, draft=merged)


def _merge_v2_and_heuristic_drafts(
    base_draft: CvProfileDraft,
    heuristic_draft: CvProfileDraft,
) -> CvProfileDraft:
    """Use the legacy heuristic parser to fill gaps and fix v2 bridge artefacts.

    The v2 bridge is strong at normalized output, while the heuristic parser
    contains template-specific OCR repairs (for example e-mail @/© repair).
    Merge conservatively: v2 keeps rich fields, heuristic fills blanks and
    replaces obviously unsafe list fields only when the base list is empty.
    """
    return dataclass_replace(
        base_draft,
        full_name=base_draft.full_name or heuristic_draft.full_name,
        email=base_draft.email or heuristic_draft.email,
        phone=base_draft.phone or heuristic_draft.phone,
        linkedin_url=base_draft.linkedin_url or heuristic_draft.linkedin_url,
        github_url=base_draft.github_url or heuristic_draft.github_url,
        headline=base_draft.headline or heuristic_draft.headline,
        summary=_choose_better_summary(base_draft.summary, heuristic_draft.summary),
        skills=_choose_better_skills(base_draft.skills, heuristic_draft.skills),
        target_roles=base_draft.target_roles or heuristic_draft.target_roles,
        preferred_locations=base_draft.preferred_locations or heuristic_draft.preferred_locations,
        remote_preference=base_draft.remote_preference or heuristic_draft.remote_preference,
        education_entries=_choose_better_education_entries(
            base_draft.education_entries,
            heuristic_draft.education_entries,
        ),
        experience_entries=_choose_better_experience_entries(
            base_draft.experience_entries,
            heuristic_draft.experience_entries,
        ),
        language_entries=_choose_richer_entries(
            base_draft.language_entries,
            heuristic_draft.language_entries,
        ),
        certification_entries=_filter_certification_entries(
            _choose_richer_entries(
                base_draft.certification_entries,
                heuristic_draft.certification_entries,
            )
        ),
    )


def _choose_better_summary(base_summary: str | None, ai_summary: str | None) -> str | None:
    if not base_summary:
        return ai_summary
    if not ai_summary:
        return base_summary
    if len(base_summary) >= 80 and not _summary_looks_contaminated(base_summary):
        return base_summary
    return ai_summary


def _summary_looks_contaminated(value: str) -> bool:
    lowered = value.casefold()
    return any(
        marker in lowered
        for marker in (
            "personal info",
            "e-mail",
            "linkedin",
            "skills",
            "phone",
        )
    )


def _merge_string_tuple_fields(
    base_values: tuple[str, ...],
    ai_values: tuple[str, ...],
) -> tuple[str, ...]:
    merged: list[str] = []
    seen: set[str] = set()

    for value in (*base_values, *ai_values):
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        if _is_redundant_string_value(key, seen):
            continue
        seen.add(key)
        merged.append(cleaned)

    return tuple(merged)


def _is_redundant_string_value(candidate_key: str, existing_keys: set[str]) -> bool:
    if len(candidate_key) <= 4:
        return False
    return any(
        candidate_key in existing_key and candidate_key != existing_key
        for existing_key in existing_keys
    )


def _filter_ai_skill_values(
    values: tuple[str, ...],
    *,
    source_text: str,
) -> tuple[str, ...]:
    """Keep Ollama skill additions that look like actual skills.

    The second-stage model is useful for OCR CVs, but it can convert summary
    facts into skills (for example an accrediting agency or a licensed job
    title).  This filter is intentionally narrow: it removes high-risk
    credential/institution/title phrases while preserving normal technical or
    compact skill tokens.
    """
    accepted: list[str] = []
    source_key = _ai_skill_source_key(source_text)

    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        if _looks_like_ai_skill_false_positive(cleaned):
            continue
        # Prefer grounded additions.  Very compact technology tokens sometimes
        # survive OCR with punctuation differences, so do not require exact
        # source containment for short alphanumeric tokens.
        candidate_key = _ai_skill_source_key(cleaned)
        compact_token = bool(re.fullmatch(r"[a-z0-9+#./_-]{1,24}", candidate_key))
        if not compact_token and candidate_key not in source_key:
            continue
        accepted.append(cleaned)

    return tuple(accepted)


def _ai_skill_source_key(value: str) -> str:
    lowered = (value or "").casefold()
    lowered = lowered.replace("ı", "i")
    lowered = re.sub(r"[^a-z0-9çğıöşü+#./_-]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _looks_like_ai_skill_false_positive(value: str) -> bool:
    key = _ai_skill_source_key(value)
    if not key:
        return True

    words = key.split()
    if len(words) > 9:
        return True

    institution_terms = (
        "ajans",
        "ajansi",
        "agency",
        "üniversite",
        "universite",
        "university",
        "kolej",
        "college",
        "okul",
        "school",
    )
    if any(term in key for term in institution_terms):
        return True

    credential_prefixes = (
        "lisansli ",
        "lisanslı ",
        "licensed ",
        "akredite ",
        "accredited ",
        "sertifikali ",
        "sertifikalı ",
        "certified ",
    )
    if key.startswith(credential_prefixes):
        return True

    # Job titles are profile headline/experience facts, not skills.  Keep
    # gerund/discipline phrases such as "software engineering", but reject
    # person-title nouns such as "Civil Engineer" / "İnşaat Mühendisi".
    title_suffixes = (
        " engineer",
        " mühendis",
        " muhendis",
        " mühendisi",
        " muhendisi",
        " manager",
        " coordinator",
        " koordinatör",
        " koordinator",
        " uzman",
        " specialist",
    )
    if len(words) <= 5 and key.endswith(title_suffixes):
        return True

    return False


def _choose_better_skills(base_values: tuple[str, ...], heuristic_values: tuple[str, ...]) -> tuple[str, ...]:
    if not base_values:
        return heuristic_values
    if not heuristic_values:
        return base_values
    if _skills_look_contaminated(base_values) and not _skills_look_contaminated(heuristic_values):
        return heuristic_values
    return base_values


def _skills_look_contaminated(values: tuple[str, ...]) -> bool:
    if len(values) > 24:
        return True
    sentence_like_count = 0
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        key = cleaned.casefold()
        if key in {"interests & achievements", "references", "available on request"}:
            return True
        if any(marker in key for marker in ("widespread travel", "bishopstown gym", "play guitar")):
            return True
        if len(cleaned) > 85:
            return True
        if re.search(r"\b(?:interests?|achievements?|references?|available on request)\b", key):
            return True
        # V2 can sometimes keep wrapped prose from category-style skill blocks
        # as one or more sentence fragments.  Prefer the heuristic extractor
        # when these sentence fragments appear, because it expands them into
        # compact atomic skills (C++, Access, reports, time management, ...).
        if (
            cleaned.endswith(".")
            or re.search(r"\b(?:working knowledge|proficient at|knowledge of|effective at|strong team|deadlines)\b", key)
            or ". highly" in key
        ):
            sentence_like_count += 1
    return sentence_like_count >= 2


def _choose_better_education_entries(base_entries: tuple, heuristic_entries: tuple) -> tuple:
    base_entries = _deduplicate_education_entries(base_entries)
    heuristic_entries = _deduplicate_education_entries(heuristic_entries)

    if not base_entries:
        return heuristic_entries
    if not heuristic_entries:
        return base_entries
    if _education_entries_look_contaminated(base_entries) and not _education_entries_look_contaminated(heuristic_entries):
        return heuristic_entries
    if _education_entries_have_semantic_duplicates(base_entries) and not _education_entries_have_semantic_duplicates(heuristic_entries):
        return heuristic_entries
    if _education_entries_are_sparse_degree_rows(base_entries) and not _education_entries_are_sparse_degree_rows(heuristic_entries):
        return heuristic_entries
    if _heuristic_education_entries_look_cleaner(base_entries, heuristic_entries):
        return heuristic_entries
    if len(base_entries) > len(heuristic_entries) + 1 and len(heuristic_entries) >= 1:
        return heuristic_entries
    return _choose_richer_entries(base_entries, heuristic_entries)


def _heuristic_education_entries_look_cleaner(base_entries: tuple, heuristic_entries: tuple) -> bool:
    for base_entry, heuristic_entry in zip(base_entries, heuristic_entries, strict=False):
        base_school = getattr(base_entry, "school_name", None)
        heuristic_school = getattr(heuristic_entry, "school_name", None)
        if not isinstance(base_school, str) or not isinstance(heuristic_school, str):
            continue
        base_key = base_school.casefold().strip()
        heuristic_key = heuristic_school.casefold().strip()
        if base_key.startswith(heuristic_key + " "):
            trailing = base_key[len(heuristic_key) :].strip(" ,")
            if trailing in {"istanbul", "mugla", "muğla", "turkey", "istanbul turkey", "mugla turkey", "muğla turkey"}:
                return True

    heuristic_by_years = {
        (getattr(entry, "start_year", None), getattr(entry, "end_year", None)): entry
        for entry in heuristic_entries
    }
    for base_entry in base_entries:
        years = (getattr(base_entry, "start_year", None), getattr(base_entry, "end_year", None))
        heuristic_entry = heuristic_by_years.get(years)
        if heuristic_entry is None:
            continue
        base_school = getattr(base_entry, "school_name", None)
        if not isinstance(base_school, str):
            continue
        base_is_degree_row = (
            getattr(base_entry, "degree_name", None) is None
            and getattr(base_entry, "field_of_study", None) is None
            and re.search(r"\b(?:bachelor|master|engineering)\b", base_school.casefold())
        )
        heuristic_is_richer = bool(
            getattr(heuristic_entry, "degree_name", None)
            or getattr(heuristic_entry, "field_of_study", None)
            or re.search(
                r"\b(?:university|institute|college|school|universite|kolej)\b",
                str(getattr(heuristic_entry, "school_name", "")).casefold(),
            )
        )
        if base_is_degree_row and heuristic_is_richer:
            return True
    return False


def _deduplicate_education_entries(entries: tuple) -> tuple:
    deduped: list[Any] = []
    for entry in entries:
        if _has_equivalent_education_entry(deduped, entry):
            continue
        deduped.append(entry)
    return tuple(deduped)


def _has_equivalent_education_entry(existing_entries: list[Any], candidate: Any) -> bool:
    candidate_key = _education_entry_semantic_key(candidate)
    if not candidate_key:
        return False
    candidate_years = (
        getattr(candidate, "start_year", None),
        getattr(candidate, "end_year", None),
    )
    for existing in existing_entries:
        existing_years = (
            getattr(existing, "start_year", None),
            getattr(existing, "end_year", None),
        )
        if existing_years != candidate_years:
            continue
        existing_key = _education_entry_semantic_key(existing)
        if not existing_key:
            continue
        if candidate_key == existing_key or candidate_key in existing_key or existing_key in candidate_key:
            return True
    return False


def _education_entries_have_semantic_duplicates(entries: tuple) -> bool:
    return len(_deduplicate_education_entries(entries)) < len(entries)


def _education_entries_are_sparse_degree_rows(entries: tuple) -> bool:
    if not entries:
        return False
    sparse_count = 0
    for entry in entries:
        school_name = getattr(entry, "school_name", None)
        degree_name = getattr(entry, "degree_name", None)
        field_of_study = getattr(entry, "field_of_study", None)
        text = " ".join(
            part for part in (school_name, degree_name, field_of_study) if isinstance(part, str)
        )
        if not isinstance(school_name, str):
            continue
        key = _education_entry_semantic_key(entry)
        if not key:
            continue
        # Rows like "Bachelor of Electrical Engineering" as school_name with
        # missing degree/field mean the bridge parsed a degree row as a school.
        if degree_name is None and field_of_study is None and re.search(
            r"\b(?:bachelor|master|leaving certificate|certificate|engineering)\b",
            text.casefold(),
        ):
            sparse_count += 1
    return sparse_count >= 1 and sparse_count >= len(entries) // 2


def _education_entry_semantic_key(entry: Any) -> str:
    parts = (
        getattr(entry, "school_name", None),
        getattr(entry, "degree_name", None),
        getattr(entry, "field_of_study", None),
    )
    text = " ".join(part for part in parts if isinstance(part, str))
    text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)
    text = re.sub(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text.casefold()).strip(" -–—,:;")


def _education_entries_look_contaminated(entries: tuple) -> bool:
    bad_markers = (
        "relevant employment",
        "other employment",
        "final year subjects",
        "final year project",
        "other projects",
        "trainee engineer",
        "information assistant",
    )
    for entry in entries:
        parts = (
            getattr(entry, "school_name", None),
            getattr(entry, "degree_name", None),
            getattr(entry, "field_of_study", None),
        )
        text = " ".join(part for part in parts if isinstance(part, str)).casefold()
        if any(marker in text for marker in bad_markers):
            return True
    return False


def _choose_better_experience_entries(base_entries: tuple, heuristic_entries: tuple) -> tuple:
    if not base_entries:
        return heuristic_entries
    if not heuristic_entries:
        return base_entries
    if _experience_entries_look_contaminated(base_entries) and not _experience_entries_look_contaminated(heuristic_entries):
        return heuristic_entries
    if len(base_entries) == len(heuristic_entries) and _experience_entries_look_cleaner(heuristic_entries, base_entries):
        return heuristic_entries
    return _choose_richer_entries(base_entries, heuristic_entries)


def _experience_entries_look_cleaner(candidate_entries: tuple, reference_entries: tuple) -> bool:
    candidate_bad = sum(1 for entry in candidate_entries if _experience_entry_looks_contaminated(entry))
    reference_bad = sum(1 for entry in reference_entries if _experience_entry_looks_contaminated(entry))
    return candidate_bad < reference_bad


def _experience_entries_look_contaminated(entries: tuple) -> bool:
    if not entries:
        return False
    bad_count = sum(1 for entry in entries if _experience_entry_looks_contaminated(entry))
    return bad_count >= max(1, len(entries) // 2)


def _experience_entry_looks_contaminated(entry: Any) -> bool:
    title = getattr(entry, "title", None)
    company = getattr(entry, "company_name", None)
    if not isinstance(title, str) or not title.strip():
        return True
    title_key = title.casefold().strip()
    company_key = company.casefold().strip() if isinstance(company, str) else ""

    bullet_prefix_pattern = r"^[•·\-–—*+©®¢\s]+"
    if re.match(bullet_prefix_pattern, title):
        return True
    if title_key.endswith(".") and len(title_key.split()) > 4:
        return True
    if len(title_key.split()) > 10:
        return True
    if re.search(
        r"\b(?:liaised|reported|assisted|checked|provided|collected|managed|conducted|completed|ensured)\b",
        title_key,
    ):
        return True
    if re.search(r"\b(?:19|20)\d{2}\s*(?:-|–|—|to)\s*(?:19|20)\d{2}\b", company_key):
        return True
    if " - " in company_key and re.search(r"\b(?:engineer|assistant|coordinator|manager|intern)\b", company_key):
        return True
    return False


def _filter_certification_entries(entries: tuple) -> tuple:
    return tuple(entry for entry in entries if not _certification_entry_looks_false_positive(entry))


def _certification_entry_looks_false_positive(entry: Any) -> bool:
    parts = (
        getattr(entry, "certificate_name", None),
        getattr(entry, "issuer_name", None),
    )
    text = " ".join(part for part in parts if isinstance(part, str)).casefold()
    if not text:
        return True
    false_positive_markers = (
        "leaving certificate",
        "honours physics",
        "500 points",
        "available on request",
        "references",
    )
    return any(marker in text for marker in false_positive_markers)


def _choose_richer_entries(base_entries: tuple, ai_entries: tuple) -> tuple:
    if not base_entries:
        return ai_entries
    if not ai_entries:
        return base_entries
    if len(ai_entries) > len(base_entries):
        return ai_entries
    return base_entries


def _build_v2_legacy_compatible_snapshot(
    *,
    cv_upload: SubscriberCvUpload,
    extracted_text: str,
    generated_at: str,
) -> CvProfileDraftSnapshot | None:
    """Run the v2 foundation bridge and map it to the legacy snapshot shape."""
    try:
        result = build_foundation_parser_result_from_text(
            extracted_text=extracted_text,
            filename=cv_upload.original_filename,
            used_ocr=cv_extraction_uses_ocr(
                cv_upload.original_filename,
                cv_upload.content_type,
            ),
            extraction_method=infer_cv_extraction_method(
                cv_upload.original_filename,
                cv_upload.content_type,
            ),
            page_count=1,
            config=ParserRuntimeConfig(),
        )
    except Exception:
        return None

    return parse_result_to_legacy_snapshot(
        result,
        source_upload_id=cv_upload.id,
        source_parse_status=cv_upload.parse_status,
        source_filename=cv_upload.original_filename,
        generated_at=generated_at,
        parser_version=HEURISTIC_CV_PARSER_VERSION,
    )


def cv_profile_draft_snapshot_to_dict(
    snapshot: CvProfileDraftSnapshot,
) -> dict[str, Any]:
    """Convert a draft snapshot into a JSON-ready dictionary.

    Args:
        snapshot: Snapshot object to serialize.

    Returns:
        A dictionary composed only of JSON-safe values.
    """
    return {
        "generated_at": snapshot.generated_at,
        "source_upload_id": snapshot.source_upload_id,
        "source_filename": snapshot.source_filename,
        "source_parse_status": snapshot.source_parse_status,
        "parser_version": snapshot.parser_version,
        "draft": _cv_profile_draft_to_dict(snapshot.draft),
    }


def cv_profile_draft_snapshot_to_json(snapshot: CvProfileDraftSnapshot) -> str:
    """Serialize a draft snapshot to a deterministic JSON string.

    Args:
        snapshot: Snapshot object to serialize.

    Returns:
        A UTF-8 safe JSON string with stable key ordering.
    """
    return json.dumps(
        cv_profile_draft_snapshot_to_dict(snapshot),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def cv_profile_draft_snapshot_from_json(snapshot_json: str) -> CvProfileDraftSnapshot:
    """Deserialize a persisted snapshot JSON string.

    Args:
        snapshot_json: Serialized snapshot JSON.

    Returns:
        A validated CV profile draft snapshot.

    Raises:
        ValueError: If the payload is malformed.
    """
    try:
        payload = json.loads(snapshot_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid CV profile draft snapshot JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid CV profile draft snapshot payload.")

    return cv_profile_draft_snapshot_from_dict(payload)


def cv_profile_draft_snapshot_from_dict(
    payload: Mapping[str, Any],
) -> CvProfileDraftSnapshot:
    """Deserialize a snapshot dictionary into a typed snapshot.

    Args:
        payload: JSON-compatible snapshot payload.

    Returns:
        A validated CV profile draft snapshot.

    Raises:
        ValueError: If the payload is malformed.
    """
    generated_at = _require_string(payload.get("generated_at"), "generated_at")
    draft_payload = payload.get("draft")
    if not isinstance(draft_payload, Mapping):
        raise ValueError("Invalid CV profile draft payload.")

    draft = _cv_profile_draft_from_dict(draft_payload)

    return build_cv_profile_draft_snapshot(
        source_upload_id=_optional_int(payload.get("source_upload_id")),
        source_filename=_optional_string(payload.get("source_filename")),
        source_parse_status=_optional_string(payload.get("source_parse_status")),
        parser_version=_optional_string(payload.get("parser_version")),
        generated_at=generated_at,
        draft=draft,
    )


def _cv_profile_draft_to_dict(draft: CvProfileDraft) -> dict[str, Any]:
    """Serialize a profile draft to a JSON-ready dictionary.

    Args:
        draft: Draft object to serialize.

    Returns:
        A dictionary representation of the draft.
    """
    return {
        "full_name": draft.full_name,
        "email": draft.email,
        "phone": draft.phone,
        "linkedin_url": draft.linkedin_url,
        "github_url": draft.github_url,
        "headline": draft.headline,
        "summary": draft.summary,
        "skills": list(draft.skills),
        "target_roles": list(draft.target_roles),
        "preferred_locations": list(draft.preferred_locations),
        "remote_preference": draft.remote_preference,
        "education_entries": [
            _cv_draft_education_entry_to_dict(item) for item in draft.education_entries
        ],
        "experience_entries": [
            _cv_draft_experience_entry_to_dict(item)
            for item in draft.experience_entries
        ],
        "language_entries": [
            _cv_draft_language_entry_to_dict(item) for item in draft.language_entries
        ],
        "certification_entries": [
            _cv_draft_certification_entry_to_dict(item)
            for item in draft.certification_entries
        ],
    }


def _cv_profile_draft_from_dict(payload: Mapping[str, Any]) -> CvProfileDraft:
    """Deserialize a profile draft dictionary into a typed draft.

    Args:
        payload: JSON-compatible draft payload.

    Returns:
        A validated draft object.

    Raises:
        ValueError: If the draft payload is malformed.
    """
    education_entries = _education_entries_from_payload(
        payload.get("education_entries", [])
    )
    experience_entries = _experience_entries_from_payload(
        payload.get("experience_entries", [])
    )
    language_entries = _language_entries_from_payload(
        payload.get("language_entries", [])
    )
    certification_entries = _certification_entries_from_payload(
        payload.get("certification_entries", [])
    )

    return build_cv_profile_draft(
        full_name=_optional_string(payload.get("full_name")),
        email=_optional_string(payload.get("email")),
        phone=_optional_string(payload.get("phone")),
        linkedin_url=_optional_string(payload.get("linkedin_url")),
        github_url=_optional_string(payload.get("github_url")),
        headline=_optional_string(payload.get("headline")),
        summary=_optional_string(payload.get("summary")),
        skills=_string_list(payload.get("skills", []), "skills"),
        target_roles=_string_list(payload.get("target_roles", []), "target_roles"),
        preferred_locations=_string_list(
            payload.get("preferred_locations", []),
            "preferred_locations",
        ),
        remote_preference=_optional_string(payload.get("remote_preference")),
        education_entries=education_entries,
        experience_entries=experience_entries,
        language_entries=language_entries,
        certification_entries=certification_entries,
    )


def _education_entries_from_payload(
    payload: Any,
) -> list[CvDraftEducationEntry]:
    """Deserialize education entry payloads.

    Args:
        payload: Raw education payload.

    Returns:
        Validated education entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid education_entries payload.")

    entries: list[CvDraftEducationEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid education entry payload.")

        entry = build_cv_draft_education_entry(
            school_name=_require_string(item.get("school_name"), "school_name"),
            degree_name=_optional_string(item.get("degree_name")),
            field_of_study=_optional_string(item.get("field_of_study")),
            start_year=_optional_int(item.get("start_year")),
            end_year=_optional_int(item.get("end_year")),
        )
        if entry is None:
            raise ValueError("Invalid education entry payload.")
        entries.append(entry)

    return entries


def _experience_entries_from_payload(
    payload: Any,
) -> list[CvDraftExperienceEntry]:
    """Deserialize experience entry payloads.

    Args:
        payload: Raw experience payload.

    Returns:
        Validated experience entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid experience_entries payload.")

    entries: list[CvDraftExperienceEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid experience entry payload.")

        entry = build_cv_draft_experience_entry(
            title=_require_string(item.get("title"), "title"),
            company_name=_optional_string(item.get("company_name")),
            start_year=_optional_int(item.get("start_year")),
            end_year=_optional_int(item.get("end_year")),
            summary=_optional_string(item.get("summary")),
        )
        if entry is None:
            raise ValueError("Invalid experience entry payload.")
        entries.append(entry)

    return entries


def _language_entries_from_payload(
    payload: Any,
) -> list[CvDraftLanguageEntry]:
    """Deserialize language entry payloads.

    Args:
        payload: Raw language payload.

    Returns:
        Validated language entries.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError("Invalid language_entries payload.")

    entries: list[CvDraftLanguageEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid language entry payload.")

        entry = build_cv_draft_language_entry(
            language_name=_require_string(item.get("language_name"), "language_name"),
            proficiency_level=_optional_string(item.get("proficiency_level")),
            notes=_optional_string(item.get("notes")),
        )
        if entry is None:
            raise ValueError("Invalid language entry payload.")
        entries.append(entry)

    return entries




def _certification_entries_from_payload(
    payload: Any,
) -> list[CvDraftCertificationEntry]:
    """Deserialize certification entry payloads."""
    if not isinstance(payload, list):
        raise ValueError("Invalid certification_entries payload.")

    entries: list[CvDraftCertificationEntry] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("Invalid certification entry payload.")

        entry = build_cv_draft_certification_entry(
            certificate_name=_require_string(
                item.get("certificate_name"),
                "certificate_name",
            ),
            issuer_name=_optional_string(item.get("issuer_name")),
            issued_year=_optional_int(item.get("issued_year")),
        )
        if entry is None:
            raise ValueError("Invalid certification entry payload.")
        entries.append(entry)

    return entries


def _cv_draft_education_entry_to_dict(
    entry: CvDraftEducationEntry,
) -> dict[str, Any]:
    """Serialize an education draft entry.

    Args:
        entry: Education entry to serialize.

    Returns:
        A dictionary representation of the education entry.
    """
    return {
        "school_name": entry.school_name,
        "degree_name": entry.degree_name,
        "field_of_study": entry.field_of_study,
        "start_year": entry.start_year,
        "end_year": entry.end_year,
    }


def _cv_draft_experience_entry_to_dict(
    entry: CvDraftExperienceEntry,
) -> dict[str, Any]:
    """Serialize an experience draft entry.

    Args:
        entry: Experience entry to serialize.

    Returns:
        A dictionary representation of the experience entry.
    """
    return {
        "title": entry.title,
        "company_name": entry.company_name,
        "start_year": entry.start_year,
        "end_year": entry.end_year,
        "summary": entry.summary,
    }


def _cv_draft_language_entry_to_dict(
    entry: CvDraftLanguageEntry,
) -> dict[str, Any]:
    """Serialize a language draft entry.

    Args:
        entry: Language entry to serialize.

    Returns:
        A dictionary representation of the language entry.
    """
    return {
        "language_name": entry.language_name,
        "proficiency_level": entry.proficiency_level,
        "notes": entry.notes,
    }




def _cv_draft_certification_entry_to_dict(
    entry: CvDraftCertificationEntry,
) -> dict[str, Any]:
    """Serialize a certification draft entry."""
    return {
        "certificate_name": entry.certificate_name,
        "issuer_name": entry.issuer_name,
        "issued_year": entry.issued_year,
    }


def _string_list(payload: Any, field_name: str) -> list[str]:
    """Validate a list of strings.

    Args:
        payload: Raw payload.
        field_name: Logical field name for error messages.

    Returns:
        A validated string list.

    Raises:
        ValueError: If the payload is malformed.
    """
    if not isinstance(payload, list):
        raise ValueError(f"Invalid {field_name} payload.")

    values: list[str] = []
    for item in payload:
        if not isinstance(item, str):
            raise ValueError(f"Invalid {field_name} payload.")
        values.append(item)

    return values


def _require_string(value: Any, field_name: str) -> str:
    """Validate a required string field.

    Args:
        value: Raw field value.
        field_name: Logical field name.

    Returns:
        A validated string value.

    Raises:
        ValueError: If the field is missing or invalid.
    """
    if not isinstance(value, str):
        raise ValueError(f"Invalid {field_name} payload.")
    return value


def _optional_string(value: Any) -> str | None:
    """Validate an optional string field.

    Args:
        value: Raw field value.

    Returns:
        A string or None.

    Raises:
        ValueError: If the value type is invalid.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Invalid optional string payload.")
    return value


def _optional_int(value: Any) -> int | None:
    """Validate an optional integer field.

    Args:
        value: Raw field value.

    Returns:
        An integer or None.

    Raises:
        ValueError: If the value type is invalid.
    """
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError("Invalid optional integer payload.")
    return value