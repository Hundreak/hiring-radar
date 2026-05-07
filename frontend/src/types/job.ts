export interface JobMatchComponent {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  summary: string;
  matched_terms: string[];
  missing_terms: string[];
}

export interface JobMatchScoreBreakdownItem {
  component_key: string;
  label: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  impact: 'strong' | 'moderate' | 'weak';
  summary: string;
  evidence_terms: string[];
  missing_terms: string[];
}

export interface JobMatchEvidencePoint {
  code: string;
  title: string;
  detail: string;
  supporting_terms: string[];
}

export interface JobMatchGapItem {
  code: string;
  title: string;
  detail: string;
  severity: 'high' | 'medium' | 'low';
  missing_terms: string[];
}

export interface JobExternalSourceMetadata {
  source_url: string;
  final_url: string | null;
  source_domain: string | null;
  fetch_status: string;
  http_status: number | null;
  page_title: string | null;
  site_name: string | null;
  fetched_at: string | null;
  content_digest: string | null;
  text_char_count: number;
}

export interface JobExternalSourceInsights {
  enrichment_status: 'unavailable' | 'cached' | 'live' | 'error';
  site_specific_requirements: string[];
  company_culture_clues: string[];
  responsibility_clues: string[];
  technology_stack_terms: string[];
  original_source_metadata: JobExternalSourceMetadata;
  warning: string | null;
}



export interface JobAnalysisCoverage {
  score: number;
  level: 'strong' | 'moderate' | 'limited';
  summary: string;
  content_sources: string[];
  detected_signal_types: string[];
  warning: string | null;
}

export interface JobMatchExplanation {
  summary: string;
  fit_score: number;
  catalog_score: number;
  final_score: number;
  behavioral_affinity_score: number | null;
  matched_skill_terms: string[];
  missing_skill_terms: string[];
  matched_location_terms: string[];
  matching_score_breakdown: JobMatchScoreBreakdownItem[];
  key_evidence_points: JobMatchEvidencePoint[];
  gap_analysis: JobMatchGapItem[];
  top_reasons: string[];
  analysis_coverage: JobAnalysisCoverage;
  external_source_insights: JobExternalSourceInsights;
  components: JobMatchComponent[];
}

export interface JobListItem {
  id: number;
  job_kind?: 'legacy' | 'canonical';
  source_name: string;
  title: string;
  company_name: string;
  location: string | null;
  canonical_url: string;
  is_active: boolean;
  first_seen_at: string | null;
  last_seen_at: string | null;
  matched: boolean;
  match_score: number | null;
  matched_keywords?: string[] | null;
  workplace_type?: string | null;
  employment_type?: string | null;
  seniority?: string | null;
  posted_at?: string | null;
  explanation?: JobMatchExplanation | null;
}

export type JobRankingMode = 'legacy_keyword' | 'deterministic_matching';

export interface JobListResponse {
  items: JobListItem[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  query: string | null;
  only_matched: boolean;
  active_only: boolean;
  ranking_mode?: JobRankingMode;
}
