export type ProfileValueSource = 'extracted' | 'user' | 'merged';

export type CompletionSectionStatus = 'done' | 'partial' | 'missing';

export type EmploymentType =
  | 'full_time'
  | 'part_time'
  | 'contract'
  | 'freelance'
  | 'internship'
  | 'temporary'
  | 'other';

export type WorkMode = 'onsite' | 'hybrid' | 'remote';

export type LanguageProficiency =
  | 'beginner'
  | 'elementary'
  | 'intermediate'
  | 'upper_intermediate'
  | 'advanced'
  | 'professional_working'
  | 'full_professional'
  | 'native_or_bilingual';

export type SuggestionImpactLevel = 'low' | 'medium' | 'high';

export type AiAuditFinalizeContext = {
  audit_event_ids: string[];
};

export type ProfileTextField = {
  value: string | null;
  source_type: ProfileValueSource;
  source_confidence: number | null;
  is_user_edited: boolean;
  raw_origin_ref: string | null;
  last_confirmed_at: string | null;
};

export type ProfileAvatarSummary = {
  asset_id: string | null;
  url: string | null;
  status: string;
};

export type ProfileCompletionSection = {
  key: string;
  label: string;
  status: CompletionSectionStatus;
};

export type ProfileCompletenessSummary = {
  score: number;
  sections: ProfileCompletionSection[];
};

export type LastCvParseSummary = {
  parse_run_id: string | null;
  parsed_at: string | null;
  source_file_name: string | null;
};

export type ProfileExperienceRecord = {
  id: string | null;
  title: string;
  company_name: string;
  location: string | null;
  employment_type: EmploymentType | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  skills_used: string[];
  display_order: number;
  source_type: ProfileValueSource;
  source_confidence: number | null;
  is_user_edited: boolean;
  is_suppressed: boolean;
};

export type ProfileEducationRecord = {
  id: string | null;
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  start_date: string | null;
  end_date: string | null;
  grade: string | null;
  description: string | null;
  display_order: number;
  source_type: ProfileValueSource;
  source_confidence: number | null;
  is_user_edited: boolean;
  is_suppressed: boolean;
};

export type ProfileLanguageRecord = {
  id: string | null;
  language_name: string;
  proficiency_level: LanguageProficiency | null;
  certificate_name: string | null;
  display_order: number;
  source_type: ProfileValueSource;
  source_confidence: number | null;
  is_user_edited: boolean;
  is_suppressed: boolean;
};

export type ProfileSkillRecord = {
  id: string | null;
  skill_name: string;
  category: string | null;
  proficiency_hint: string | null;
  years_hint: number | null;
  display_order: number;
  source_type: ProfileValueSource;
  source_confidence: number | null;
  is_user_edited: boolean;
  is_suppressed: boolean;
};

export type ProfilePreferencesRecord = {
  preferred_locations: string[];
  work_modes: WorkMode[];
  target_roles: string[];
  salary_expectation: string | null;
  relocation: boolean | null;
};

export type CandidateProfileAggregate = {
  id: string;
  user_id: string;
  full_name: ProfileTextField;
  headline: ProfileTextField;
  summary: ProfileTextField;
  primary_email: ProfileTextField;
  phone: ProfileTextField;
  avatar: ProfileAvatarSummary;
  preferences: ProfilePreferencesRecord;
  completeness: ProfileCompletenessSummary;
  experiences: ProfileExperienceRecord[];
  education: ProfileEducationRecord[];
  languages: ProfileLanguageRecord[];
  skills: ProfileSkillRecord[];
  last_cv_parse: LastCvParseSummary | null;
  created_at: string;
  updated_at: string;
};

export type ProfileSuggestionItem = {
  id: string;
  title: string;
  description: string;
  impact_level: SuggestionImpactLevel;
  action_type: string | null;
  target_section: string | null;
};

export type ProfileSuggestionsBundle = {
  highlights: ProfileSuggestionItem[];
  critical_gaps: ProfileSuggestionItem[];
  quick_wins: ProfileSuggestionItem[];
};

export type UserProfileAggregateResponse = {
  profile: CandidateProfileAggregate;
  suggestions: ProfileSuggestionsBundle;
};

export type UpdateBasicInfoRequest = {
  full_name?: string | null;
  headline?: string | null;
  primary_email?: string | null;
  phone?: string | null;
  summary?: string | null;
  ai_audit_context?: AiAuditFinalizeContext | null;
};

export type UpdatePreferencesRequest = {
  preferred_locations: string[];
  work_modes: WorkMode[];
  target_roles: string[];
  salary_expectation?: string | null;
  relocation?: boolean | null;
  ai_audit_context?: AiAuditFinalizeContext | null;
};

export type CreateExperienceRequest = {
  title: string;
  company_name: string;
  location?: string | null;
  employment_type?: EmploymentType | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  description?: string | null;
  skills_used?: string[];
};

export type UpdateExperienceRequest = {
  title?: string | null;
  company_name?: string | null;
  location?: string | null;
  employment_type?: EmploymentType | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean | null;
  description?: string | null;
  skills_used?: string[] | null;
  display_order?: number | null;
};

export type CreateEducationRequest = {
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  grade?: string | null;
  description?: string | null;
};

export type UpdateEducationRequest = {
  institution?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  grade?: string | null;
  description?: string | null;
  display_order?: number | null;
};

export type CreateLanguageRequest = {
  language_name: string;
  proficiency_level?: LanguageProficiency | null;
  certificate_name?: string | null;
};

export type UpdateLanguageRequest = {
  language_name?: string | null;
  proficiency_level?: LanguageProficiency | null;
  certificate_name?: string | null;
  display_order?: number | null;
};

export type CreateSkillRequest = {
  skill_name: string;
  category?: string | null;
  proficiency_hint?: string | null;
  years_hint?: number | null;
  evidence_note?: string | null;
  ai_audit_context?: AiAuditFinalizeContext | null;
};

export type UpdateSkillRequest = {
  skill_name?: string | null;
  category?: string | null;
  proficiency_hint?: string | null;
  years_hint?: number | null;
  evidence_note?: string | null;
  display_order?: number | null;
  ai_audit_context?: AiAuditFinalizeContext | null;
};

export type ProfileAvatarUploadResponse = {
  asset_id: string;
  url: string;
  status: string;
};