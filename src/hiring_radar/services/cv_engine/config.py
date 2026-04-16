from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QualityScoringConfig(BaseModel):
    """Configuration for deterministic parse quality scoring."""

    model_config = ConfigDict(extra="forbid")

    text_length_thresholds: list[tuple[int, int]] = Field(
        default_factory=lambda: [(2200, 38), (1200, 28), (600, 18), (250, 8)]
    )
    line_count_thresholds: list[tuple[int, int]] = Field(
        default_factory=lambda: [(90, 20), (55, 14), (25, 8), (10, 4)]
    )
    section_count_thresholds: list[tuple[int, int]] = Field(
        default_factory=lambda: [(6, 14), (4, 9), (2, 5)]
    )
    field_weights: dict[str, int] = Field(
        default_factory=lambda: {
            "full_name": 6,
            "emails": 5,
            "phone_numbers": 4,
            "summary": 8,
            "skills": 10,
            "experience_lines": 12,
            "section_names": 6,
            "links": 2,
            "projects": 3,
        }
    )
    ocr_penalty: int = Field(default=12, ge=0, le=100)
    warning_penalty: int = Field(default=4, ge=0, le=100)
    low_average_confidence_penalty: int = Field(default=10, ge=0, le=100)
    medium_average_confidence_penalty: int = Field(default=4, ge=0, le=100)
    semantic_richness_bonus: int = Field(default=5, ge=0, le=100)
    high_threshold: int = Field(default=70, ge=0, le=100)
    medium_threshold: int = Field(default=40, ge=0, le=100)


class LayoutAnalysisConfig(BaseModel):
    """Configuration for lightweight PDF layout analysis."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    minimum_block_text_length: int = Field(default=2, ge=0)
    minimum_block_height: float = Field(default=4.0, ge=0.0)
    full_width_ratio: float = Field(default=0.68, gt=0.0, le=1.0)
    sidebar_width_ratio: float = Field(default=0.35, gt=0.0, le=1.0)
    column_merge_gap_ratio: float = Field(default=0.14, gt=0.0, le=1.0)
    max_columns: int = Field(default=3, ge=1, le=6)


class SectionDetectionConfig(BaseModel):
    """Configuration for heading scoring and section detection."""

    model_config = ConfigDict(extra="forbid")

    minimum_heading_score: float = Field(default=0.58, ge=0.0, le=1.0)
    uppercase_bonus: float = Field(default=0.22, ge=0.0, le=1.0)
    short_line_bonus: float = Field(default=0.12, ge=0.0, le=1.0)
    fuzzy_alias_min_ratio: float = Field(default=0.72, ge=0.0, le=1.0)
    max_heading_words: int = Field(default=7, ge=1)


class ExperienceParsingConfig(BaseModel):
    """Configuration for title/company/location/date heuristics."""

    model_config = ConfigDict(extra="forbid")

    max_candidate_lines: int = Field(default=4, ge=1)
    prefer_reverse_chronological: bool = True
    minimum_title_alpha_ratio: float = Field(default=0.55, ge=0.0, le=1.0)


class SkillExtractionConfig(BaseModel):
    """Configuration for section-aware skill extraction."""

    model_config = ConfigDict(extra="forbid")

    minimum_skill_length: int = Field(default=2, ge=1)
    section_boosts: dict[str, float] = Field(
        default_factory=lambda: {
            "skills": 0.35,
            "projects": 0.18,
            "experience": 0.12,
            "summary": 0.08,
            "header": 0.05,
        }
    )
    default_confidence: float = Field(default=0.62, ge=0.0, le=1.0)
    word_boundary_required: bool = True
    ambiguous_skill_penalty: float = Field(default=0.2, ge=0.0, le=1.0)
    context_bonus: float = Field(default=0.08, ge=0.0, le=1.0)
    duplicate_skill_decay: float = Field(default=0.04, ge=0.0, le=0.2)


class LanguageDetectionConfig(BaseModel):
    """Configuration for lightweight language detection."""

    model_config = ConfigDict(extra="forbid")

    supported_languages: tuple[str, ...] = ("tr", "en", "de")
    fallback_language: str = "en"
    enable_library_backend: bool = True


class ConfidenceScoringConfig(BaseModel):
    """Configuration for semantic field confidence scoring."""

    model_config = ConfigDict(extra="forbid")

    high_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    medium_threshold: float = Field(default=0.58, ge=0.0, le=1.0)
    base_score: float = Field(default=0.45, ge=0.0, le=1.0)
    section_match_bonus: float = Field(default=0.15, ge=0.0, le=0.4)
    catalog_match_bonus: float = Field(default=0.12, ge=0.0, le=0.4)
    context_bonus: float = Field(default=0.08, ge=0.0, le=0.2)
    multi_signal_bonus: float = Field(default=0.1, ge=0.0, le=0.2)
    ambiguity_penalty: float = Field(default=0.18, ge=0.0, le=0.4)
    ocr_penalty: float = Field(default=0.08, ge=0.0, le=0.3)
    layout_bonus: float = Field(default=0.05, ge=0.0, le=0.15)
    sparse_text_penalty: float = Field(default=0.08, ge=0.0, le=0.2)


class SemanticResolutionConfig(BaseModel):
    """Configuration for semantic enrichment and provenance generation."""

    model_config = ConfigDict(extra="forbid")

    enable_projects: bool = True
    enable_certifications: bool = True
    enable_links: bool = True
    role_signal_min_confidence: float = Field(default=0.52, ge=0.0, le=1.0)
    organization_signal_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    location_signal_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    maximum_skill_candidates_per_section: int = Field(default=40, ge=1, le=200)


class DocumentVersioningConfig(BaseModel):
    """Configuration for duplicate and CV version detection."""

    model_config = ConfigDict(extra="forbid")

    exact_duplicate_similarity_threshold: float = Field(default=0.995, ge=0.0, le=1.0)
    updated_version_similarity_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    related_variant_similarity_threshold: float = Field(default=0.72, ge=0.0, le=1.0)
    minimum_person_signals_for_strong_match: int = Field(default=1, ge=0, le=3)
    simhash_bits: int = Field(default=64, ge=16, le=256)


class ParseCacheConfig(BaseModel):
    """Configuration for deterministic parse caching and reuse."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    namespace: str = "cv_engine"
    minimum_similarity_for_partial_reuse: float = Field(default=0.82, ge=0.0, le=1.0)
    prefer_same_person_candidates: bool = True
    max_candidates_per_lookup: int = Field(default=10, ge=1, le=1000)
    allow_section_level_reuse: bool = True


class AtsScoringConfig(BaseModel):
    """Configuration for ATS compatibility scoring."""

    model_config = ConfigDict(extra="forbid")

    base_score: int = Field(default=100, ge=0, le=100)
    required_sections: tuple[str, ...] = ("header", "experience", "skills")
    strong_bonus: int = Field(default=6, ge=0, le=20)
    moderate_bonus: int = Field(default=3, ge=0, le=20)
    missing_section_penalty: int = Field(default=8, ge=0, le=30)
    missing_contact_penalty: int = Field(default=14, ge=0, le=40)
    sparse_experience_penalty: int = Field(default=10, ge=0, le=30)
    low_skill_density_penalty: int = Field(default=8, ge=0, le=30)
    ocr_penalty: int = Field(default=12, ge=0, le=30)
    multi_column_penalty: int = Field(default=6, ge=0, le=20)
    complex_layout_penalty: int = Field(default=10, ge=0, le=30)
    low_quality_penalty: int = Field(default=12, ge=0, le=30)
    medium_quality_penalty: int = Field(default=6, ge=0, le=30)
    no_dates_penalty: int = Field(default=8, ge=0, le=20)
    high_threshold: int = Field(default=78, ge=0, le=100)
    medium_threshold: int = Field(default=55, ge=0, le=100)


class RedactionConfig(BaseModel):
    """Configuration for PII redaction and anonymization."""

    model_config = ConfigDict(extra="forbid")

    redact_full_name: bool = True
    redact_emails: bool = True
    redact_phone_numbers: bool = True
    redact_addresses: bool = True
    redact_social_handles: bool = True
    redact_links: bool = False
    preserve_domains: bool = True
    preserve_country_names: bool = True
    minimum_name_length: int = Field(default=4, ge=2, le=100)
    max_address_lines: int = Field(default=3, ge=0, le=20)


class BatchProcessingConfig(BaseModel):
    """Configuration for streaming batch parse workloads."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    max_batch_size: int = Field(default=500, ge=1, le=100000)
    default_priority: int = Field(default=100, ge=0, le=10000)
    dead_letter_enabled: bool = True
    retry_policy_name: str = "default"


class ComplianceRuntimeConfig(BaseModel):
    """Configuration for enterprise compliance runtime hooks."""

    model_config = ConfigDict(extra="forbid")

    enable_health_reporting: bool = True
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_parse_audit: bool = True


class ParserRuntimeConfig(BaseModel):
    """Top-level configuration for the CV engine foundation."""

    model_config = ConfigDict(extra="forbid")

    layout_analysis: LayoutAnalysisConfig = Field(default_factory=LayoutAnalysisConfig)
    quality_scoring: QualityScoringConfig = Field(default_factory=QualityScoringConfig)
    section_detection: SectionDetectionConfig = Field(default_factory=SectionDetectionConfig)
    experience_parsing: ExperienceParsingConfig = Field(default_factory=ExperienceParsingConfig)
    skill_extraction: SkillExtractionConfig = Field(default_factory=SkillExtractionConfig)
    language_detection: LanguageDetectionConfig = Field(default_factory=LanguageDetectionConfig)
    confidence_scoring: ConfidenceScoringConfig = Field(default_factory=ConfidenceScoringConfig)
    semantic_resolution: SemanticResolutionConfig = Field(default_factory=SemanticResolutionConfig)
    document_versioning: DocumentVersioningConfig = Field(default_factory=DocumentVersioningConfig)
    parse_cache: ParseCacheConfig = Field(default_factory=ParseCacheConfig)
    ats_scoring: AtsScoringConfig = Field(default_factory=AtsScoringConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    batch_processing: BatchProcessingConfig = Field(default_factory=BatchProcessingConfig)
    compliance_runtime: ComplianceRuntimeConfig = Field(default_factory=ComplianceRuntimeConfig)
    emit_stage_timings: bool = True
    continue_on_recoverable_errors: bool = True
