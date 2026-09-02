'use client';

import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import type {ChangeEvent, ReactNode} from 'react';
import Image from 'next/image';
import {BriefcaseBusiness, GraduationCap, HeartPulse, Languages, Sparkles, Upload, Wrench} from 'lucide-react';
import {useParams} from 'next/navigation';

import {AiHeadlineSummaryPanel} from '@/components/profile/ai-headline-summary-panel';
import {AiRoleFocusPanel} from '@/components/profile/ai-role-focus-panel';
import {AiSkillEvidencePanel} from '@/components/profile/ai-skill-evidence-panel';
import {AvatarCropDialog} from '@/components/profile/avatar-crop-dialog';
import {CvUploadModule} from '@/components/profile/cv-upload-module';
import {ProfileHealthDrawer} from '@/components/profile/profile-health-drawer';
import {profileWorkspaceCopy as copy} from '@/components/profile/profile-workspace-copy';
import type {ProfileWorkspaceCopy as Copy} from '@/components/profile/profile-workspace-copy';
import {
  Chip,
  EditorActions,
  EditorCard,
  EmptyState,
  EntityCard,
  Field,
  InputField,
  LoadingView,
  OverviewCard,
  OverviewListCard,
  PrimaryButton,
  SecondaryButton,
  SectionHeader,
  SelectField,
  Surface,
  TextAreaField,
} from '@/components/profile/profile-workspace-primitives';
import {ComboboxField, type ComboboxOption} from '@/components/ui/combobox-field';
import {FileSelectButton} from '@/components/ui/file-select-button';
import {FeedbackBanner} from '@/components/ui/feedback-banner';
import {ApiError, api, suggestProfileSkillEvidence} from '@/lib/api';
import type {AiHeadlineSummaryResponse, AiRoleFocusResponse, AiSkillEvidenceResponse} from '@/types/ai';
import type {
  CreateEducationRequest,
  CreateExperienceRequest,
  CreateLanguageRequest,
  CreateSkillRequest,
  LanguageProficiency,
  ProfileEducationRecord,
  ProfileExperienceRecord,
  ProfileLanguageRecord,
  ProfileSkillRecord,
  UpdateEducationRequest,
  UpdateExperienceRequest,
  UpdateLanguageRequest,
  UpdateSkillRequest,
  UserProfileAggregateResponse,
  WorkMode,
} from '@/types/profile';
import type {
  RemotePreference,
  SupportedLocale,
  UserCvWorkspaceContext,
  UserCvWorkspaceProfile,
  UserSkillDetail,
} from '@/types/user';
import {DEFAULT_SKILL_CATEGORIES, findUniversityByName, OFFICIAL_TURKISH_UNIVERSITY_NAMES, TURKISH_UNIVERSITY_OPTIONS} from '@/data/turkish-universities';

type BasicDraft = {full_name: string; phone: string; headline: string; summary: string};
type PreferencesDraft = {
  target_roles: string;
  preferred_locations: string;
  work_modes: WorkMode[];
  salary_expectation: string;
  relocation: 'unset' | 'yes' | 'no';
};
type ExperienceDraft = {
  title: string;
  company_name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description: string;
};
type EducationDraft = {
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string;
};
type LanguageDraft = {
  language_name: string;
  proficiency_level: LanguageProficiency | '';
  certificate_name: string;
  issuer_name: string;
  certificate_file: File | null;
};
type SkillDraft = {
  skill_name: string;
  category: string;
  proficiency_hint: string;
  years_hint: string;
  evidence_note: string;
  evidence_file: File | null;
};

type EditorState<T> = {mode: 'create' | 'edit'; targetId: string | null; values: T};

type RefreshWorkspaceOptions = {
  suppressError?: boolean;
  syncProfileDrafts?: boolean;
};

type RefreshWorkspaceResult = {
  aggregateResult: UserProfileAggregateResponse;
  cvContextResult: UserCvWorkspaceContext;
  skillDetailsResult: UserSkillDetail[];
};

type AiAuditMarker = {
  eventId: number;
  targetField: string;
  targetEntityId: string | null;
  persistenceStatus: 'unsaved' | 'saved';
  actionType: string;
  sourcePanel: string | null;
  telemetryRef: string | null;
  beforeSnapshot: unknown;
  afterSnapshot: unknown;
  updatedAt: string | null;
};

type AiAuditMarkerMap = Record<string, AiAuditMarker>;

type PersistedAiReviewState = {
  basicDraft: BasicDraft;
  preferencesDraft: PreferencesDraft;
  skillEditor: EditorState<Omit<SkillDraft, 'evidence_file'>> | null;
  markers: AiAuditMarkerMap;
};

const AI_REVIEW_SESSION_KEY = 'noytera:profile-ai-review-state';

const languageLevelOptions: Array<{value: LanguageProficiency; label: string}> = [
  {value: 'beginner', label: 'Beginner'},
  {value: 'elementary', label: 'Elementary'},
  {value: 'intermediate', label: 'Intermediate'},
  {value: 'upper_intermediate', label: 'Upper Intermediate'},
  {value: 'advanced', label: 'Advanced'},
  {value: 'professional_working', label: 'Professional Working'},
  {value: 'full_professional', label: 'Full Professional'},
  {value: 'native_or_bilingual', label: 'Native / Bilingual'},
];

function normalizeLocale(value: string | string[] | undefined): SupportedLocale {
  const resolved = Array.isArray(value) ? value[0] : value;
  if (resolved === 'en' || resolved === 'de') return resolved;
  return 'tr';
}

function splitList(value: string) {
  return value
    .split(/\n|,/) 
    .map((item) => item.trim())
    .filter(Boolean);
}

function toNullable(value: string) {
  const cleaned = value.trim();
  return cleaned ? cleaned : null;
}

function parseYear(value: string) {
  const cleaned = value.trim();
  if (!cleaned) return null;
  const digits = cleaned.match(/\d{4}/)?.[0] ?? cleaned;
  const parsed = Number.parseInt(digits, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function initials(name: string | null) {
  if (!name) return 'HR';
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('') || 'HR';
}

function workModeLabel(t: Copy, mode: WorkMode) {
  if (mode === 'hybrid') return t.hybrid;
  if (mode === 'onsite') return t.onsite;
  return t.remote;
}

function buildBasicDraft(profile: UserProfileAggregateResponse['profile']): BasicDraft {
  return {
    full_name: profile.full_name.value ?? '',
    phone: profile.phone.value ?? '',
    headline: profile.headline.value ?? '',
    summary: profile.summary.value ?? '',
  };
}

function buildPreferencesDraft(profile: UserProfileAggregateResponse['profile']): PreferencesDraft {
  return {
    target_roles: profile.preferences.target_roles.join('\n'),
    preferred_locations: profile.preferences.preferred_locations.join('\n'),
    work_modes: profile.preferences.work_modes,
    salary_expectation: profile.preferences.salary_expectation ?? '',
    relocation:
      profile.preferences.relocation === null
        ? 'unset'
        : profile.preferences.relocation
          ? 'yes'
          : 'no',
  };
}

function emptyExperienceDraft(): ExperienceDraft {
  return {title: '', company_name: '', start_date: '', end_date: '', is_current: false, description: ''};
}

function emptyEducationDraft(): EducationDraft {
  return {institution: '', degree: '', field_of_study: '', start_date: '', end_date: ''};
}

function emptyLanguageDraft(): LanguageDraft {
  return {language_name: '', proficiency_level: '', certificate_name: '', issuer_name: '', certificate_file: null};
}

function emptySkillDraft(): SkillDraft {
  return {skill_name: '', category: '', proficiency_hint: '', years_hint: '', evidence_note: '', evidence_file: null};
}

function draftFromExperience(item: ProfileExperienceRecord): ExperienceDraft {
  return {
    title: item.title,
    company_name: item.company_name,
    start_date: item.start_date ?? '',
    end_date: item.end_date ?? '',
    is_current: item.is_current,
    description: item.description ?? '',
  };
}

function draftFromEducation(item: ProfileEducationRecord): EducationDraft {
  return {
    institution: item.institution,
    degree: item.degree ?? '',
    field_of_study: item.field_of_study ?? '',
    start_date: item.start_date ?? '',
    end_date: item.end_date ?? '',
  };
}

function draftFromLanguage(item: ProfileLanguageRecord): LanguageDraft {
  return {
    language_name: item.language_name,
    proficiency_level: (item.proficiency_level ?? '') as LanguageDraft['proficiency_level'],
    certificate_name: item.certificate_name ?? '',
    issuer_name: '',
    certificate_file: null,
  };
}

function draftFromSkill(item: ProfileSkillRecord, detail?: UserSkillDetail | null): SkillDraft {
  return {
    skill_name: item.skill_name,
    category: detail?.category ?? item.category ?? '',
    proficiency_hint: detail?.proficiency_hint ?? item.proficiency_hint ?? '',
    years_hint: detail?.years_hint?.toString() ?? item.years_hint?.toString() ?? '',
    evidence_note: detail?.evidence_note ?? '',
    evidence_file: null,
  };
}

function numericIdFromString(id: string | null) {
  if (!id) return null;
  const normalized = id.replace(/^\D+_?/, '');
  const parsed = Number.parseInt(normalized, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function resolveLegacyRemotePreference(workModes: WorkMode[]): RemotePreference {
  if (workModes.includes('remote')) return 'remote';
  if (workModes.includes('hybrid')) return 'hybrid';
  if (workModes.includes('onsite')) return 'onsite';
  return null;
}

function buildCvWorkspaceProfile(
  profile: UserProfileAggregateResponse['profile'],
  context: UserCvWorkspaceContext,
): UserCvWorkspaceProfile {
  return {
    full_name: profile.full_name.value,
    email: profile.primary_email.value || '',
    phone: profile.phone.value,
    headline: profile.headline.value,
    summary: profile.summary.value,
    target_roles: profile.preferences.target_roles,
    skills: profile.skills.map((item) => item.skill_name),
    preferred_locations: profile.preferences.preferred_locations,
    remote_preference: resolveLegacyRemotePreference(profile.preferences.work_modes),
    education_entries: profile.education.map((item) => ({
      id: numericIdFromString(item.id),
      school_name: item.institution,
      degree_name: item.degree,
      field_of_study: item.field_of_study,
      start_year: parseYear(item.start_date ?? ''),
      end_year: parseYear(item.end_date ?? ''),
      display_order: item.display_order,
    })),
    experience_entries: profile.experiences.map((item) => ({
      id: numericIdFromString(item.id),
      title: item.title,
      company_name: item.company_name,
      start_year: parseYear(item.start_date ?? ''),
      end_year: parseYear(item.end_date ?? ''),
      summary: item.description,
      display_order: item.display_order,
    })),
    language_entries: profile.languages.map((item) => ({
      id: numericIdFromString(item.id),
      language_name: item.language_name,
      proficiency_level: item.proficiency_level,
      notes: item.certificate_name,
      display_order: item.display_order,
    })),
    language_certificates: context.language_certificates,
    completeness: {
      score: profile.completeness.score,
      completed_items: profile.completeness.sections.filter((item) => item.status === 'done').map((item) => item.label),
      missing_items: profile.completeness.sections.filter((item) => item.status !== 'done').map((item) => item.label),
    },
    latest_cv_upload: context.latest_cv_upload,
  };
}

function emitProfileSurfaceUpdate(payload: {fullName?: string | null; avatarUrl?: string | null}) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent('noytera:profile-surface-updated', {
      detail: {
        fullName: payload.fullName ?? null,
        avatarUrl: payload.avatarUrl ?? null,
      },
    }),
  );
}

export default function ProfileAggregateWorkspace() {
  const params = useParams<{locale: string}>();
  const locale = normalizeLocale(params?.locale);
  const t = copy[locale];
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const [cropDialogOpen, setCropDialogOpen] = useState(false);
  const [avatarSourceUrl, setAvatarSourceUrl] = useState<string | null>(null);
  const [avatarSourceName, setAvatarSourceName] = useState<string | null>(null);
  const [profileHealthOpen, setProfileHealthOpen] = useState(false);

  const [aggregate, setAggregate] = useState<UserProfileAggregateResponse | null>(null);
  const [cvWorkspaceContext, setCvWorkspaceContext] = useState<UserCvWorkspaceContext | null>(null);
  const [skillDetails, setSkillDetails] = useState<UserSkillDetail[]>([]);
  const [basicDraft, setBasicDraft] = useState<BasicDraft>({full_name: '', phone: '', headline: '', summary: ''});
  const [preferencesDraft, setPreferencesDraft] = useState<PreferencesDraft>({target_roles: '', preferred_locations: '', work_modes: [], salary_expectation: '', relocation: 'unset'});
  const [experienceEditor, setExperienceEditor] = useState<EditorState<ExperienceDraft> | null>(null);
  const [educationEditor, setEducationEditor] = useState<EditorState<EducationDraft> | null>(null);
  const [languageEditor, setLanguageEditor] = useState<EditorState<LanguageDraft> | null>(null);
  const [skillEditor, setSkillEditor] = useState<EditorState<SkillDraft> | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [headlineSummaryOpen, setHeadlineSummaryOpen] = useState(false);
  const [headlineSummaryLoading, setHeadlineSummaryLoading] = useState(false);
  const [headlineSummaryError, setHeadlineSummaryError] = useState<string | null>(null);
  const [headlineSummaryResult, setHeadlineSummaryResult] = useState<AiHeadlineSummaryResponse | null>(null);
  const [roleFocusOpen, setRoleFocusOpen] = useState(false);
  const [roleFocusLoading, setRoleFocusLoading] = useState(false);
  const [roleFocusError, setRoleFocusError] = useState<string | null>(null);
  const [roleFocusResult, setRoleFocusResult] = useState<AiRoleFocusResponse | null>(null);
  const [skillEvidenceOpen, setSkillEvidenceOpen] = useState(false);
  const [skillEvidenceLoading, setSkillEvidenceLoading] = useState(false);
  const [skillEvidenceError, setSkillEvidenceError] = useState<string | null>(null);
  const [skillEvidenceResult, setSkillEvidenceResult] = useState<AiSkillEvidenceResponse | null>(null);
  const [aiAuditMarkers, setAiAuditMarkers] = useState<AiAuditMarkerMap>({});
  const sessionRestoredRef = useRef(false);

  const applyWorkspaceAggregate = useCallback(
    (
      aggregateResult: UserProfileAggregateResponse,
      options: {syncProfileDrafts?: boolean} = {},
    ) => {
      setAggregate(aggregateResult);
      emitProfileSurfaceUpdate({
        fullName: aggregateResult.profile.full_name.value,
        avatarUrl: aggregateResult.profile.avatar.url,
      });

      if (options.syncProfileDrafts ?? true) {
        setBasicDraft(buildBasicDraft(aggregateResult.profile));
        setPreferencesDraft(buildPreferencesDraft(aggregateResult.profile));
      }
    },
    [],
  );

  const refreshWorkspace = useCallback(
    async (
      mode: 'initial' | 'refresh' = 'refresh',
      options: RefreshWorkspaceOptions = {},
    ): Promise<RefreshWorkspaceResult | null> => {
      if (mode === 'initial') {
        setLoading(true);
      }

      if (!options.suppressError) {
        setErrorMessage(null);
      }

      try {
        const [aggregateResult, cvContextResult, skillDetailsResult] = await Promise.all([
          api.getUserProfileAggregate(),
          api.getUserCvWorkspaceContext(),
          api.getUserProfileSkillDetails().catch(() => []),
        ]);

        applyWorkspaceAggregate(aggregateResult, {
          syncProfileDrafts:
            options.syncProfileDrafts ?? mode === 'initial',
        });
        setCvWorkspaceContext(cvContextResult);
        setSkillDetails(skillDetailsResult);

        return {aggregateResult, cvContextResult, skillDetailsResult};
      } catch (reason) {
        if (!options.suppressError) {
          setErrorMessage(
            reason instanceof Error ? reason.message || t.genericError : t.genericError,
          );
        }
        return null;
      } finally {
        if (mode === 'initial') {
          setLoading(false);
        }
      }
    },
    [applyWorkspaceAggregate, t.genericError],
  );

  useEffect(() => {
    void refreshWorkspace('initial');
  }, [refreshWorkspace]);

  const hasSkillEditor = Boolean(skillEditor);

  useEffect(() => {
    if (!hasSkillEditor) {
      setSkillEvidenceOpen(false);
      setSkillEvidenceLoading(false);
      setSkillEvidenceError(null);
      setSkillEvidenceResult(null);
      return;
    }

    setSkillEvidenceError(null);
    setSkillEvidenceResult(null);
  }, [hasSkillEditor, skillEditor?.mode, skillEditor?.targetId]);

  useEffect(() => {
    if (loading || sessionRestoredRef.current || typeof window === 'undefined') {
      return;
    }
    sessionRestoredRef.current = true;
    const raw = window.sessionStorage.getItem(AI_REVIEW_SESSION_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as PersistedAiReviewState;
      if (parsed.basicDraft) setBasicDraft(parsed.basicDraft);
      if (parsed.preferencesDraft) setPreferencesDraft(parsed.preferencesDraft);
      if (parsed.skillEditor) {
        setSkillEditor({
          mode: parsed.skillEditor.mode,
          targetId: parsed.skillEditor.targetId,
          values: {...parsed.skillEditor.values, evidence_file: null},
        });
      }
      if (parsed.markers) setAiAuditMarkers(parsed.markers);
    } catch {
      window.sessionStorage.removeItem(AI_REVIEW_SESSION_KEY);
    }
  }, [loading]);

  useEffect(() => {
    if (loading || typeof window === 'undefined') return;
    const payload: PersistedAiReviewState = {
      basicDraft,
      preferencesDraft,
      skillEditor: skillEditor
        ? {
            mode: skillEditor.mode,
            targetId: skillEditor.targetId,
            values: {
              skill_name: skillEditor.values.skill_name,
              category: skillEditor.values.category,
              proficiency_hint: skillEditor.values.proficiency_hint,
              years_hint: skillEditor.values.years_hint,
              evidence_note: skillEditor.values.evidence_note,
            },
          }
        : null,
      markers: aiAuditMarkers,
    };
    window.sessionStorage.setItem(AI_REVIEW_SESSION_KEY, JSON.stringify(payload));
  }, [loading, basicDraft, preferencesDraft, skillEditor, aiAuditMarkers]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = (event: BeforeUnloadEvent) => {
      const hasUnsavedAi = Object.values(aiAuditMarkers).some((item) => item.persistenceStatus === 'unsaved');
      if (!hasUnsavedAi) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [aiAuditMarkers]);

  useEffect(() => {
    return () => {
      if (avatarSourceUrl) {
        URL.revokeObjectURL(avatarSourceUrl);
      }
    };
  }, [avatarSourceUrl]);

  const profile = aggregate?.profile ?? null;
  const suggestions = aggregate?.suggestions ?? null;
  const completionScore = profile?.completeness.score ?? 0;
  const progressWidth = `${Math.min(Math.max(completionScore, 0), 100)}%`;

  const skillDetailsMap = useMemo(() => {
    return new Map(skillDetails.map((item) => [item.skill_name.trim().toLocaleLowerCase('tr-TR'), item]));
  }, [skillDetails]);

  const cvModuleProfile = useMemo(() => {
    if (!profile || !cvWorkspaceContext) return null;
    return buildCvWorkspaceProfile(profile, cvWorkspaceContext);
  }, [cvWorkspaceContext, profile]);

  const overview = useMemo(() => {
    if (!profile) return null;
    return {
      fullName: basicDraft.full_name.trim() || profile.full_name.value || '',
      headline: basicDraft.headline.trim() || profile.headline.value || '',
      summary: basicDraft.summary.trim() || profile.summary.value || '',
      targetRoles: splitList(preferencesDraft.target_roles),
      preferredLocations: splitList(preferencesDraft.preferred_locations),
      workModes: preferencesDraft.work_modes,
      skills: profile.skills.map((item) => item.skill_name),
    };
  }, [basicDraft, preferencesDraft, profile]);

  const universityOptions = useMemo<ComboboxOption[]>(() => {
    const curatedMap = new Map(
      TURKISH_UNIVERSITY_OPTIONS.map((item) => [item.name.trim().toLocaleLowerCase('tr-TR'), item] as const),
    );

    return OFFICIAL_TURKISH_UNIVERSITY_NAMES.map((name) => {
      const curated = curatedMap.get(name.trim().toLocaleLowerCase('tr-TR'));
      return {
        value: name,
        label: name,
        hint: curated ? `${curated.city} · ${curated.type === 'devlet' ? 'Devlet' : 'Vakıf'}` : 'Serbest giriş de desteklenir',
      };
    });
  }, []);

  const departmentOptions = useMemo<ComboboxOption[]>(() => {
    const selected = findUniversityByName(educationEditor?.values.institution ?? '');
    if (!selected) return [];
    return selected.departments.map((item) => ({value: item, label: item, hint: selected.name}));
  }, [educationEditor?.values.institution]);

  const commitAggregateMutation = useCallback(
    async (
      aggregateResult: UserProfileAggregateResponse,
      options: {
        successMessage?: string | null;
        syncProfileDrafts?: boolean;
        closeEditor?: () => void;
      } = {},
    ) => {
      applyWorkspaceAggregate(aggregateResult, {
        syncProfileDrafts: options.syncProfileDrafts ?? false,
      });
      options.closeEditor?.();
      await refreshWorkspace('refresh', {
        suppressError: true,
        syncProfileDrafts: options.syncProfileDrafts ?? false,
      });
      if (options.successMessage) {
        setMessage(options.successMessage);
      }
    },
    [applyWorkspaceAggregate, refreshWorkspace],
  );

  const applyAvatarUploadPreview = useCallback(
    (assetId: string, url: string, status: string) => {
      setAggregate((current) => {
        if (!current) return current;
        return {
          ...current,
          profile: {
            ...current.profile,
            avatar: {
              ...current.profile.avatar,
              asset_id: assetId,
              url,
              status,
            },
          },
        };
      });

      emitProfileSurfaceUpdate({
        fullName: basicDraft.full_name.trim() || aggregate?.profile.full_name.value || null,
        avatarUrl: url,
      });
    },
    [aggregate?.profile.full_name.value, basicDraft.full_name],
  );

  async function runBusyAction(key: string, action: () => Promise<void>) {
    setBusyKey(key);
    setErrorMessage(null);
    setMessage(null);
    try {
      await action();
    } catch (reason) {
      if (reason instanceof ApiError) {
        setErrorMessage(reason.detail || reason.message || t.genericError);
      } else if (reason instanceof Error) {
        setErrorMessage(reason.message || t.genericError);
      } else {
        setErrorMessage(t.genericError);
      }
    } finally {
      setBusyKey(null);
    }
  }

  function mergeSkillDetail(item: ProfileSkillRecord) {
    return skillDetailsMap.get(item.skill_name.trim().toLocaleLowerCase('tr-TR')) ?? null;
  }

  function markerKeyFor(field: string, entityId?: string | null) {
    return entityId ? `${field}:${entityId.trim().toLocaleLowerCase(locale)}` : field;
  }

  function hasUnsavedMarker(keys: string[]) {
    return keys.some((key) => aiAuditMarkers[key]?.persistenceStatus === 'unsaved');
  }

  function buildSavedSnapshot(field: string, entityId?: string | null): unknown {
    if (!aggregate) return null;
    if (field === 'headline') return aggregate.profile.headline.value ?? null;
    if (field === 'summary') return aggregate.profile.summary.value ?? null;
    if (field === 'target_roles') return aggregate.profile.preferences.target_roles;
    const normalizedEntity = entityId?.trim().toLocaleLowerCase(locale) ?? null;
    if (field === 'skill.proficiency_hint' && normalizedEntity) {
      const detail = skillDetails.find((item) => item.skill_name.trim().toLocaleLowerCase(locale) === normalizedEntity);
      return detail?.proficiency_hint ?? skillEditor?.values.proficiency_hint ?? null;
    }
    if (field === 'skill.evidence_note' && normalizedEntity) {
      const detail = skillDetails.find((item) => item.skill_name.trim().toLocaleLowerCase(locale) === normalizedEntity);
      return detail?.evidence_note ?? skillEditor?.values.evidence_note ?? null;
    }
    return null;
  }

  async function recordAiApplyEvent(input: {
    field: string;
    entityId?: string | null;
    actionType: 'replace' | 'append';
    sourcePanel: string;
    beforeSnapshot: unknown;
    afterSnapshot: unknown;
    telemetryRef?: string | null;
  }) {
    const event = await api.createUserProfileAiAuditEvent({
      telemetry_ref: input.telemetryRef ?? null,
      target_field: input.field,
      target_entity_id: input.entityId ?? null,
      action_type: input.actionType,
      source_panel: input.sourcePanel,
      before_snapshot: input.beforeSnapshot,
      after_snapshot: input.afterSnapshot,
      persistence_status: 'unsaved',
      metadata: {locale},
    });

    const key = markerKeyFor(input.field, input.entityId ?? null);
    setAiAuditMarkers((current) => ({
      ...current,
      [key]: {
        eventId: event.id,
        targetField: input.field,
        targetEntityId: input.entityId ?? null,
        persistenceStatus: event.persistence_status === 'saved' ? 'saved' : 'unsaved',
        actionType: input.actionType,
        sourcePanel: input.sourcePanel,
        telemetryRef: event.telemetry_ref,
        beforeSnapshot: event.before_snapshot,
        afterSnapshot: event.after_snapshot,
        updatedAt: event.updated_at,
      },
    }));
  }

  async function finalizeAiMarkers(keys: string[], savedSnapshotResolver: (marker: AiAuditMarker) => unknown) {
    const nextEntries = await Promise.all(
      keys.map(async (key) => {
        const marker = aiAuditMarkers[key];
        if (!marker || marker.persistenceStatus !== 'unsaved') {
          return [key, marker] as const;
        }
        const finalized = await api.finalizeUserProfileAiAuditEvent(marker.eventId, {
          persistence_status: 'saved',
          saved_snapshot: savedSnapshotResolver(marker),
          metadata: {locale, finalized_from: 'profile-workspace'},
        });
        const nextMarker: AiAuditMarker = {
          ...marker,
          persistenceStatus: 'saved',
          afterSnapshot: finalized.after_snapshot,
          updatedAt: finalized.updated_at,
        };
        return [key, nextMarker] as const;
      }),
    );
    setAiAuditMarkers((current) => {
      const updated = {...current};
      for (const [key, marker] of nextEntries) {
        if (!marker) continue;
        updated[key] = marker;
      }
      return updated;
    });
  }

  async function revertAiMarker(key: string) {
    const marker = aiAuditMarkers[key];
    if (!marker) return;
    if (marker.persistenceStatus === 'saved') {
      const result = await api.revertUserProfileAiAuditEvent(marker.eventId);
      applyWorkspaceAggregate(result.aggregate, {syncProfileDrafts: true});
      const refreshedSkillDetails = await api.getUserProfileSkillDetails().catch(() => skillDetails);
      setSkillDetails(refreshedSkillDetails);
      setAiAuditMarkers((current) => {
        const next = {...current};
        delete next[key];
        return next;
      });
      setMessage(locale === 'en' ? 'The AI change was reverted.' : locale === 'de' ? 'Die KI-Änderung wurde rückgängig gemacht.' : 'AI değişikliği geri alındı.');
      return;
    }

    if (marker.targetField === 'headline') {
      setBasicDraft((current) => ({...current, headline: typeof marker.beforeSnapshot === 'string' ? marker.beforeSnapshot : ''}));
    } else if (marker.targetField === 'summary') {
      setBasicDraft((current) => ({...current, summary: typeof marker.beforeSnapshot === 'string' ? marker.beforeSnapshot : ''}));
    } else if (marker.targetField === 'target_roles') {
      const before = Array.isArray(marker.beforeSnapshot) ? marker.beforeSnapshot.map((item) => String(item)) : [];
      setPreferencesDraft((current) => ({...current, target_roles: before.join('\n')}));
    } else if (marker.targetField === 'skill.proficiency_hint') {
      setSkillEditor((current) => current ? {...current, values: {...current.values, proficiency_hint: typeof marker.beforeSnapshot === 'string' ? marker.beforeSnapshot : ''}} : current);
    } else if (marker.targetField === 'skill.evidence_note') {
      setSkillEditor((current) => current ? {...current, values: {...current.values, evidence_note: typeof marker.beforeSnapshot === 'string' ? marker.beforeSnapshot : ''}} : current);
    }

    await api.finalizeUserProfileAiAuditEvent(marker.eventId, {
      persistence_status: 'unsaved',
      evaluation_status: 'reverted',
      metadata: {locale, reverted_locally: true},
    }).catch(() => undefined);

    setAiAuditMarkers((current) => {
      const next = {...current};
      delete next[key];
      return next;
    });
    setMessage(locale === 'en' ? 'The draft returned to the previous value.' : locale === 'de' ? 'Der Entwurf wurde auf den vorherigen Wert zurückgesetzt.' : 'Taslak önceki değere döndürüldü.');
  }

  function buildMarkerNode(key: string) {
    const marker = aiAuditMarkers[key];
    if (!marker) return null;
    const badgeLabel = marker.persistenceStatus === 'saved'
      ? (locale === 'en' ? 'Updated by AI' : locale === 'de' ? 'Mit KI aktualisiert' : 'AI ile güncellendi')
      : (locale === 'en' ? 'Applied · Unsaved' : locale === 'de' ? 'Übernommen · Ungespeichert' : 'Uygulandı · Kaydedilmedi');
    const revertLabel = locale === 'en' ? 'Undo' : locale === 'de' ? 'Zurücknehmen' : 'Geri al';
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium ${marker.persistenceStatus === 'saved' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>{badgeLabel}</span>
        <button type="button" className="text-xs font-medium text-foreground underline-offset-2 hover:underline" onClick={() => void revertAiMarker(key)}>{revertLabel}</button>
      </div>
    );
  }

  function confirmPanelClose(keys: string[], onClose: () => void) {
    if (!hasUnsavedMarker(keys) || typeof window === 'undefined') {
      onClose();
      return;
    }
    const messageText = locale === 'en'
      ? 'You have AI-applied changes that are not saved yet. Close the panel anyway?'
      : locale === 'de'
        ? 'Du hast KI-Änderungen, die noch nicht gespeichert wurden. Panel trotzdem schließen?'
        : 'Henüz kaydedilmemiş AI değişikliklerin var. Panel yine de kapatılsın mı?';
    if (window.confirm(messageText)) {
      onClose();
    }
  }


  function toggleWorkMode(mode: WorkMode) {
    setPreferencesDraft((current) => ({
      ...current,
      work_modes: current.work_modes.includes(mode)
        ? current.work_modes.filter((item) => item !== mode)
        : [...current.work_modes, mode],
    }));
  }

  function getHeadlineSummaryAppliedMessage(kind: 'headline' | 'summary') {
    if (locale === 'en') {
      return kind === 'headline'
        ? 'The headline suggestion was added to the draft.'
        : 'The summary suggestion was added to the draft.';
    }
    if (locale === 'de') {
      return kind === 'headline'
        ? 'Der Titelvorschlag wurde in den Entwurf übernommen.'
        : 'Der Kurzprofil-Vorschlag wurde in den Entwurf übernommen.';
    }
    return kind === 'headline'
      ? 'Başlık önerisi taslağa eklendi.'
      : 'Özet önerisi taslağa eklendi.';
  }

  async function loadHeadlineSummarySuggestions() {
    setHeadlineSummaryOpen(true);
    setHeadlineSummaryLoading(true);
    setHeadlineSummaryError(null);

    try {
      const result = await api.suggestProfileHeadlineSummary({
        locale,
        headline_option_count: 3,
        summary_option_count: 3,
      });
      setHeadlineSummaryResult(result);
    } catch (reason) {
      if (reason instanceof ApiError) {
        setHeadlineSummaryError(reason.detail || reason.message || t.genericError);
      } else if (reason instanceof Error) {
        setHeadlineSummaryError(reason.message || t.genericError);
      } else {
        setHeadlineSummaryError(t.genericError);
      }
    } finally {
      setHeadlineSummaryLoading(false);
    }
  }

  async function applyHeadlineSuggestion(title: string) {
    await recordAiApplyEvent({
      field: 'headline',
      actionType: 'replace',
      sourcePanel: 'headline-summary',
      beforeSnapshot: basicDraft.headline,
      afterSnapshot: title,
      telemetryRef: headlineSummaryResult?.telemetry_ref ?? null,
    });
    setBasicDraft((current) => ({...current, headline: title}));
    setMessage(getHeadlineSummaryAppliedMessage('headline'));
  }

  async function applySummarySuggestion(summary: string) {
    await recordAiApplyEvent({
      field: 'summary',
      actionType: 'replace',
      sourcePanel: 'headline-summary',
      beforeSnapshot: basicDraft.summary,
      afterSnapshot: summary,
      telemetryRef: headlineSummaryResult?.telemetry_ref ?? null,
    });
    setBasicDraft((current) => ({...current, summary}));
    setMessage(getHeadlineSummaryAppliedMessage('summary'));
  }


  function getRoleFocusAppliedMessage(kind: 'single' | 'all'): string {
    if (locale === 'en') {
      return kind === 'single'
        ? 'The suggested target role was added to your draft preferences.'
        : 'Suggested target roles were added to your draft preferences.';
    }

    if (locale === 'de') {
      return kind === 'single'
        ? 'Die vorgeschlagene Zielrolle wurde zu deinen Entwurfspräferenzen hinzugefügt.'
        : 'Die vorgeschlagenen Zielrollen wurden zu deinen Entwurfspräferenzen hinzugefügt.';
    }

    return kind === 'single'
      ? 'Önerilen hedef rol taslak tercihlerine eklendi.'
      : 'Önerilen hedef roller taslak tercihlerine eklendi.';
  }

  async function loadRoleFocusSuggestions() {
    setRoleFocusOpen(true);
    setRoleFocusLoading(true);
    setRoleFocusError(null);

    try {
      const result = await api.suggestProfileRoleFocus({
        locale,
        suggestion_count: 4,
      });
      setRoleFocusResult(result);
    } catch (reason) {
      if (reason instanceof ApiError) {
        setRoleFocusError(reason.detail || reason.message || t.genericError);
      } else if (reason instanceof Error) {
        setRoleFocusError(reason.message || t.genericError);
      } else {
        setRoleFocusError(t.genericError);
      }
    } finally {
      setRoleFocusLoading(false);
    }
  }

  function mergeRoleNamesIntoDraft(roleNames: string[]) {
    const existing = splitList(preferencesDraft.target_roles);
    const seen = new Set(existing.map((item) => item.toLocaleLowerCase(locale)));
    const merged = [...existing];

    for (const roleName of roleNames) {
      const normalized = roleName.trim();
      if (!normalized) continue;
      const key = normalized.toLocaleLowerCase(locale);
      if (seen.has(key)) continue;
      seen.add(key);
      merged.push(normalized);
    }

    setPreferencesDraft((current) => ({
      ...current,
      target_roles: merged.join('\n'),
    }));
  }

  async function applyRoleFocusSuggestion(roleName: string) {
    const existing = splitList(preferencesDraft.target_roles);
    const merged = Array.from(new Set([...existing, roleName.trim()].filter(Boolean)));
    await recordAiApplyEvent({
      field: 'target_roles',
      actionType: 'append',
      sourcePanel: 'role-focus',
      beforeSnapshot: existing,
      afterSnapshot: merged,
      telemetryRef: roleFocusResult?.telemetry_ref ?? null,
    });
    mergeRoleNamesIntoDraft([roleName]);
    setMessage(getRoleFocusAppliedMessage('single'));
  }

  async function applyAllRoleFocusSuggestions(roleNames: string[]) {
    const existing = splitList(preferencesDraft.target_roles);
    const merged = Array.from(new Set([...existing, ...roleNames.map((item) => item.trim())].filter(Boolean)));
    await recordAiApplyEvent({
      field: 'target_roles',
      actionType: 'append',
      sourcePanel: 'role-focus',
      beforeSnapshot: existing,
      afterSnapshot: merged,
      telemetryRef: roleFocusResult?.telemetry_ref ?? null,
    });
    mergeRoleNamesIntoDraft(roleNames);
    setMessage(getRoleFocusAppliedMessage('all'));
  }



  function getSkillEvidenceAppliedMessage(kind: 'description' | 'note' | 'proofs'): string {
    if (locale === 'en') {
      if (kind === 'description') return 'The suggested skill description was added to your draft.';
      if (kind === 'note') return 'The suggested evidence note was added to your draft.';
      return 'Proof ideas were appended to your draft evidence note.';
    }

    if (locale === 'de') {
      if (kind === 'description') return 'Die vorgeschlagene Kompetenzbeschreibung wurde dem Entwurf hinzugefügt.';
      if (kind === 'note') return 'Die vorgeschlagene Nachweisnotiz wurde dem Entwurf hinzugefügt.';
      return 'Nachweisideen wurden an die Entwurfsnotiz angehängt.';
    }

    if (kind === 'description') return 'Önerilen beceri açıklaması taslağa eklendi.';
    if (kind === 'note') return 'Önerilen kanıt notu taslağa eklendi.';
    return 'Kanıt fikirleri taslak not alanına eklendi.';
  }

  async function loadSkillEvidenceSuggestions() {
    const currentSkillName = skillEditor?.values.skill_name.trim() ?? '';
    if (!currentSkillName) {
      setMessage(
        locale === 'en'
          ? 'Enter a skill name before requesting AI support.'
          : locale === 'de'
            ? 'Gib zuerst einen Kompetenznamen ein, bevor du KI-Unterstützung anforderst.'
            : 'AI desteği almadan önce bir beceri adı gir.',
      );
      return;
    }

    setSkillEvidenceOpen(true);
    setSkillEvidenceLoading(true);
    setSkillEvidenceError(null);

    try {
      const result = await suggestProfileSkillEvidence({
        locale,
        skill_name: currentSkillName,
        category: skillEditor?.values.category || null,
        existing_evidence_note: skillEditor?.values.evidence_note || null,
      });
      setSkillEvidenceResult(result);
    } catch (reason) {
      if (reason instanceof ApiError) {
        setSkillEvidenceError(reason.detail || reason.message || t.genericError);
      } else if (reason instanceof Error) {
        setSkillEvidenceError(reason.message || t.genericError);
      } else {
        setSkillEvidenceError(t.genericError);
      }
    } finally {
      setSkillEvidenceLoading(false);
    }
  }

  async function applySkillDescriptionSuggestion(value: string) {
    const targetSkillName = skillEditor?.values.skill_name.trim() || skillEditor?.targetId || null;
    await recordAiApplyEvent({
      field: 'skill.proficiency_hint',
      entityId: targetSkillName,
      actionType: 'replace',
      sourcePanel: 'skill-evidence',
      beforeSnapshot: skillEditor?.values.proficiency_hint ?? '',
      afterSnapshot: value,
      telemetryRef: skillEvidenceResult?.telemetry_ref ?? null,
    });
    setSkillEditor((current) =>
      current
        ? {
            ...current,
            values: {
              ...current.values,
              proficiency_hint: value,
            },
          }
        : current,
    );
    setMessage(getSkillEvidenceAppliedMessage('description'));
  }

  async function applySkillEvidenceNoteSuggestion(value: string) {
    const targetSkillName = skillEditor?.values.skill_name.trim() || skillEditor?.targetId || null;
    await recordAiApplyEvent({
      field: 'skill.evidence_note',
      entityId: targetSkillName,
      actionType: 'replace',
      sourcePanel: 'skill-evidence',
      beforeSnapshot: skillEditor?.values.evidence_note ?? '',
      afterSnapshot: value,
      telemetryRef: skillEvidenceResult?.telemetry_ref ?? null,
    });
    setSkillEditor((current) =>
      current
        ? {
            ...current,
            values: {
              ...current.values,
              evidence_note: value,
            },
          }
        : current,
    );
    setMessage(getSkillEvidenceAppliedMessage('note'));
  }

  function appendSkillProofIdeas(ideas: string[]) {
    const addition = ideas.filter(Boolean).map((item) => `• ${item}`).join('\n');
    setSkillEditor((current) => {
      if (!current) return current;
      const existing = current.values.evidence_note.trim();
      const nextNote = existing ? `${existing}\n\n${addition}` : addition;
      return {
        ...current,
        values: {
          ...current.values,
          evidence_note: nextNote,
        },
      };
    });
    setMessage(getSkillEvidenceAppliedMessage('proofs'));
  }

  async function saveBasics() {

    await runBusyAction('save-basics', async () => {
      const aggregateResult = await api.patchUserProfileBasicInfo({
        full_name: toNullable(basicDraft.full_name),
        phone: toNullable(basicDraft.phone),
        headline: toNullable(basicDraft.headline),
        summary: toNullable(basicDraft.summary),
      });
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.savedBasics,
        syncProfileDrafts: true,
      });
      await finalizeAiMarkers(['headline', 'summary'], (marker) => buildSavedSnapshot(marker.targetField, marker.targetEntityId));
    });
  }

  async function savePreferences() {
    await runBusyAction('save-preferences', async () => {
      const aggregateResult = await api.patchUserProfilePreferences({
        target_roles: splitList(preferencesDraft.target_roles),
        preferred_locations: splitList(preferencesDraft.preferred_locations),
        work_modes: preferencesDraft.work_modes,
        salary_expectation: toNullable(preferencesDraft.salary_expectation),
        relocation: preferencesDraft.relocation === 'unset' ? null : preferencesDraft.relocation === 'yes',
      });
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.savedPreferences,
        syncProfileDrafts: true,
      });
      await finalizeAiMarkers(['target_roles'], (marker) => buildSavedSnapshot(marker.targetField, marker.targetEntityId));
    });
  }

  function onAvatarChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    if (avatarSourceUrl) {
      URL.revokeObjectURL(avatarSourceUrl);
    }

    setAvatarSourceUrl(URL.createObjectURL(file));
    setAvatarSourceName(file.name);
    setCropDialogOpen(true);
  }

  async function submitCroppedAvatar(file: File) {
    await runBusyAction('avatar', async () => {
      const uploadResult = await api.uploadProfileAvatar(file);
      applyAvatarUploadPreview(uploadResult.asset_id, uploadResult.url, uploadResult.status);
      setCropDialogOpen(false);
      if (avatarSourceUrl) {
        URL.revokeObjectURL(avatarSourceUrl);
      }
      setAvatarSourceUrl(null);
      setAvatarSourceName(null);
      await refreshWorkspace('refresh', {
        suppressError: true,
        syncProfileDrafts: false,
      });
      setMessage(t.profilePhotoSaved);
    });
  }

  async function saveExperience() {
    if (!experienceEditor) return;

    const editorState = experienceEditor;
    const payload: CreateExperienceRequest | UpdateExperienceRequest = {
      title: editorState.values.title.trim(),
      company_name: editorState.values.company_name.trim(),
      start_date: toNullable(editorState.values.start_date),
      end_date: editorState.values.is_current ? null : toNullable(editorState.values.end_date),
      is_current: editorState.values.is_current,
      description: toNullable(editorState.values.description),
    };

    await runBusyAction('save-experience', async () => {
      const aggregateResult =
        editorState.mode === 'create'
          ? await api.createUserProfileExperience(payload as CreateExperienceRequest)
          : await api.patchUserProfileExperience(
              editorState.targetId ?? '',
              payload as UpdateExperienceRequest,
            );

      await commitAggregateMutation(aggregateResult, {
        successMessage: t.savedExperience,
        syncProfileDrafts: false,
        closeEditor: () => setExperienceEditor(null),
      });
    });
  }

  async function deleteExperience(id: string) {
    await runBusyAction(`delete-experience-${id}`, async () => {
      const aggregateResult = await api.deleteUserProfileExperience(id);
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.deletedExperience,
        syncProfileDrafts: false,
        closeEditor: () => setExperienceEditor(null),
      });
    });
  }

  async function saveEducation() {
    if (!educationEditor) return;

    const editorState = educationEditor;
    const payload: CreateEducationRequest | UpdateEducationRequest = {
      institution: editorState.values.institution.trim(),
      degree: toNullable(editorState.values.degree),
      field_of_study: toNullable(editorState.values.field_of_study),
      start_date: toNullable(editorState.values.start_date),
      end_date: toNullable(editorState.values.end_date),
    };

    await runBusyAction('save-education', async () => {
      const aggregateResult =
        editorState.mode === 'create'
          ? await api.createUserProfileEducation(payload as CreateEducationRequest)
          : await api.patchUserProfileEducation(
              editorState.targetId ?? '',
              payload as UpdateEducationRequest,
            );

      await commitAggregateMutation(aggregateResult, {
        successMessage: t.savedEducation,
        syncProfileDrafts: false,
        closeEditor: () => setEducationEditor(null),
      });
    });
  }

  async function deleteEducation(id: string) {
    await runBusyAction(`delete-education-${id}`, async () => {
      const aggregateResult = await api.deleteUserProfileEducation(id);
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.deletedEducation,
        syncProfileDrafts: false,
        closeEditor: () => setEducationEditor(null),
      });
    });
  }

  async function saveLanguage() {
    if (!languageEditor) return;

    const editorState = languageEditor;

    await runBusyAction('save-language', async () => {
      const payload: CreateLanguageRequest | UpdateLanguageRequest = {
        language_name: editorState.values.language_name.trim(),
        proficiency_level: editorState.values.proficiency_level || null,
        certificate_name: toNullable(editorState.values.certificate_name),
      };

      const aggregateResult =
        editorState.mode === 'create'
          ? await api.createUserProfileLanguage(payload as CreateLanguageRequest)
          : await api.patchUserProfileLanguage(
              editorState.targetId ?? '',
              payload as UpdateLanguageRequest,
            );

      const targetLanguageId = aggregateResult.profile.languages
        .filter(
          (item) =>
            item.language_name.trim().toLocaleLowerCase('tr-TR') ===
            editorState.values.language_name.trim().toLocaleLowerCase('tr-TR'),
        )
        .at(-1)?.id;

      let successMessage = t.savedLanguage;

      if (editorState.values.certificate_file) {
        try {
          await api.uploadLanguageCertificate({
            file: editorState.values.certificate_file,
            certificate_name:
              editorState.values.certificate_name.trim() ||
              `${editorState.values.language_name.trim()} Belgesi`,
            issuer_name: toNullable(editorState.values.issuer_name),
            language_entry_id: numericIdFromString(targetLanguageId ?? null),
          });
          successMessage = t.savedLanguageWithDocument;
        } catch (reason) {
          console.warn('Language certificate upload failed after language save.', reason);
          successMessage = t.savedLanguageWithoutDocument;
        }
      }

      await commitAggregateMutation(aggregateResult, {
        successMessage,
        syncProfileDrafts: false,
        closeEditor: () => setLanguageEditor(null),
      });
    });
  }

  async function deleteLanguage(id: string) {
    await runBusyAction(`delete-language-${id}`, async () => {
      const aggregateResult = await api.deleteUserProfileLanguage(id);
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.deletedLanguage,
        syncProfileDrafts: false,
        closeEditor: () => setLanguageEditor(null),
      });
    });
  }

  async function saveSkill() {
    if (!skillEditor) return;

    const editorState = skillEditor;

    await runBusyAction('save-skill', async () => {
      const payload: CreateSkillRequest | UpdateSkillRequest = {
        skill_name: editorState.values.skill_name.trim(),
        category: toNullable(editorState.values.category),
        proficiency_hint: toNullable(editorState.values.proficiency_hint),
        years_hint: parseYear(editorState.values.years_hint),
        evidence_note: toNullable(editorState.values.evidence_note),
      };

      const aggregateResult =
        editorState.mode === 'create'
          ? await api.createUserProfileSkill(payload as CreateSkillRequest)
          : await api.patchUserProfileSkill(
              editorState.targetId ?? '',
              payload as UpdateSkillRequest,
            );

      const targetSkillId = aggregateResult.profile.skills.find(
        (item) =>
          item.skill_name.trim().toLocaleLowerCase('tr-TR') ===
          editorState.values.skill_name.trim().toLocaleLowerCase('tr-TR'),
      )?.id;

      let successMessage = t.savedSkill;

      if (editorState.values.evidence_file && targetSkillId) {
        try {
          await api.uploadUserProfileSkillEvidence({
            skillId: targetSkillId,
            file: editorState.values.evidence_file,
            evidence_note: toNullable(editorState.values.evidence_note),
          });
          successMessage = t.savedSkillWithEvidence;
        } catch (reason) {
          console.warn('Skill evidence upload failed after skill save.', reason);
          successMessage = t.savedSkillWithoutEvidence;
        }
      }

      await commitAggregateMutation(aggregateResult, {
        successMessage,
        syncProfileDrafts: false,
        closeEditor: () => setSkillEditor(null),
      });
      await refreshWorkspace('refresh', {suppressError: true, syncProfileDrafts: false});
      const skillNameKey = editorState.values.skill_name.trim();
      await finalizeAiMarkers([
        markerKeyFor('skill.proficiency_hint', skillNameKey),
        markerKeyFor('skill.evidence_note', skillNameKey),
      ], (marker) => buildSavedSnapshot(marker.targetField, skillNameKey));
    });
  }

  async function deleteSkill(id: string) {
    await runBusyAction(`delete-skill-${id}`, async () => {
      const aggregateResult = await api.deleteUserProfileSkill(id);
      await commitAggregateMutation(aggregateResult, {
        successMessage: t.deletedSkill,
        syncProfileDrafts: false,
        closeEditor: () => setSkillEditor(null),
      });
    });
  }

  if (loading || !profile || !overview) {
    return <LoadingView copy={t} />;
  }

  const avatarName = overview.fullName || profile.full_name.value || null;

  return (
    <div className="space-y-8 pb-10">
      <section className="rounded-[28px] border border-border bg-gradient-to-br from-foreground/[0.04] via-background to-background p-6 shadow-[0_20px_80px_-42px_rgba(15,23,42,0.35)] sm:p-8">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="space-y-3">
            <div className="inline-flex rounded-full border border-border bg-background/80 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground backdrop-blur">
              {t.eyebrow}
            </div>
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">{t.title}</h1>
              <p className="max-w-4xl text-sm leading-7 text-muted-foreground sm:text-base">{t.subtitle}</p>
            </div>
          </div>

          <div className="min-w-[260px] rounded-[22px] border border-border bg-background/80 p-4 shadow-sm backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div className="text-sm font-medium text-foreground">{t.profileCompletion}</div>
              <div className="text-sm font-semibold text-foreground">%{completionScore}</div>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-foreground transition-all duration-500" style={{width: progressWidth}} />
            </div>
            <SecondaryButton className="mt-4 w-full" onClick={() => setProfileHealthOpen(true)}>
              <HeartPulse className="mr-2 size-4" />
              {t.healthDrawerButton}
            </SecondaryButton>
          </div>
        </div>
      </section>

      <Surface>
        <SectionHeader
          title={t.profilePhotoTitle}
          body={t.profilePhotoBody}
          action={
            <>
              <input ref={avatarInputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={onAvatarChange} />
              <SecondaryButton onClick={() => avatarInputRef.current?.click()} disabled={busyKey === 'avatar'}>
                <Upload className="mr-2 size-4" />
                {busyKey === 'avatar' ? t.uploadingProfilePhoto : t.uploadProfilePhoto}
              </SecondaryButton>
            </>
          }
        />

        <div className="mt-6 grid gap-6 md:grid-cols-[180px_1fr]">
          <div className="flex flex-col items-center justify-center rounded-[24px] border border-border bg-muted/20 p-5 text-center">
            {profile.avatar.url ? (
              <Image src={profile.avatar.url} alt={avatarName ?? 'Profile avatar'} width={112} height={112} className="h-28 w-28 rounded-full object-cover" unoptimized />
            ) : (
              <div className="flex h-28 w-28 items-center justify-center rounded-full border border-border bg-background text-2xl font-semibold text-foreground">{initials(avatarName)}</div>
            )}
            <div className="mt-4 text-sm font-medium text-foreground">{avatarName ?? t.noProfilePhoto}</div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-border bg-muted/20 p-4">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{t.email}</div>
              <div className="mt-2 text-sm text-foreground">{profile.primary_email.value || '—'}</div>
            </div>
            <div className="rounded-2xl border border-border bg-muted/20 p-4">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{t.phone}</div>
              <div className="mt-2 text-sm text-foreground">{profile.phone.value || '—'}</div>
            </div>
            <div className="rounded-2xl border border-border bg-muted/20 p-4 md:col-span-2">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{t.headline}</div>
              <div className="mt-2 text-sm text-foreground">{overview.headline || t.previewEmpty}</div>
            </div>
          </div>
        </div>
      </Surface>

      {cvModuleProfile ? (
        <CvUploadModule
          locale={locale}
          profile={cvModuleProfile}
          suggestions={suggestions}
          onWorkspaceRefresh={() =>
            refreshWorkspace('refresh', {
              suppressError: true,
              syncProfileDrafts: false,
            })
          }
        />
      ) : null}

      {message ? (
        <FeedbackBanner tone="success" onDismiss={() => setMessage(null)}>
          {message}
        </FeedbackBanner>
      ) : null}
      {errorMessage ? (
        <FeedbackBanner tone="error" onDismiss={() => setErrorMessage(null)}>
          {errorMessage}
        </FeedbackBanner>
      ) : null}

      <Surface>
        <SectionHeader title={t.profileOverviewTitle} />
        <div className="mt-6 grid gap-4 xl:grid-cols-2">
          <OverviewCard title={t.fullName}>{overview.fullName || t.previewEmpty}</OverviewCard>
          <OverviewCard title={t.headline}>{overview.headline || t.previewEmpty}</OverviewCard>
          <OverviewCard title={t.summary} className="xl:col-span-2">
            {overview.summary || t.previewEmpty}
          </OverviewCard>
          <OverviewListCard title={t.targetRoles} items={overview.targetRoles} emptyLabel={t.previewEmpty} />
          <OverviewListCard title={t.preferredLocations} items={overview.preferredLocations} emptyLabel={t.previewEmpty} />
          <OverviewListCard title={t.workModes} items={overview.workModes.map((item) => workModeLabel(t, item))} emptyLabel={t.previewEmpty} />
          <OverviewListCard title={t.skillsTitle} items={overview.skills} emptyLabel={t.previewEmpty} />
        </div>
      </Surface>

      <Surface>
        <SectionHeader
          title={t.basicsTitle}
          body={t.basicsBody}
          action={
            <div className="flex flex-wrap items-center gap-3">
              <SecondaryButton onClick={() => void loadHeadlineSummarySuggestions()} disabled={busyKey !== null || headlineSummaryLoading}>
                <Sparkles className="mr-2 size-4" />
                {locale === 'en'
                  ? 'Suggest headline & summary'
                  : locale === 'de'
                    ? 'Titel & Kurzprofil vorschlagen'
                    : 'Başlık ve özet öner'}
              </SecondaryButton>
              <PrimaryButton onClick={saveBasics} disabled={busyKey !== null}>
                {busyKey === 'save-basics' ? t.saving : t.saveBasics}
              </PrimaryButton>
            </div>
          }
        />
        {headlineSummaryOpen ? (
          <AiHeadlineSummaryPanel
            locale={locale}
            isLoading={headlineSummaryLoading}
            errorMessage={headlineSummaryError}
            response={headlineSummaryResult}
            onClose={() => confirmPanelClose(['headline', 'summary'], () => setHeadlineSummaryOpen(false))}
            onRefresh={() => void loadHeadlineSummarySuggestions()}
            onApplyHeadline={applyHeadlineSuggestion}
            onApplySummary={applySummarySuggestion}
          />
        ) : null}
        <div className="mt-6 grid gap-4">
          <Field label={t.fullName}><InputField value={basicDraft.full_name} onChange={(event) => setBasicDraft((current) => ({...current, full_name: event.target.value}))} /></Field>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t.email}><InputField value={profile.primary_email.value || ''} disabled /></Field>
            <Field label={t.phone}><InputField value={basicDraft.phone} onChange={(event) => setBasicDraft((current) => ({...current, phone: event.target.value}))} /></Field>
          </div>
          <Field label={t.headline} marker={buildMarkerNode('headline')}><InputField value={basicDraft.headline} onChange={(event) => setBasicDraft((current) => ({...current, headline: event.target.value}))} /></Field>
          <Field label={t.summary} marker={buildMarkerNode('summary')}><TextAreaField value={basicDraft.summary} onChange={(event) => setBasicDraft((current) => ({...current, summary: event.target.value}))} rows={5} /></Field>
        </div>
      </Surface>

      <Surface>
        <SectionHeader
          title={t.preferencesTitle}
          body={t.preferencesBody}
          action={
            <div className="flex flex-wrap items-center gap-3">
              <SecondaryButton onClick={() => void loadRoleFocusSuggestions()} disabled={busyKey !== null || roleFocusLoading}>
                {locale === 'en'
                  ? 'Suggest role focus'
                  : locale === 'de'
                    ? 'Rollenfokus vorschlagen'
                    : 'Rol odağı öner'}
              </SecondaryButton>
              <PrimaryButton onClick={savePreferences} disabled={busyKey !== null}>
                {busyKey === 'save-preferences' ? t.saving : t.savePreferences}
              </PrimaryButton>
            </div>
          }
        />
        {roleFocusOpen ? (
          <AiRoleFocusPanel
            locale={locale}
            isLoading={roleFocusLoading}
            errorMessage={roleFocusError}
            response={roleFocusResult}
            onClose={() => confirmPanelClose(['target_roles'], () => setRoleFocusOpen(false))}
            onRefresh={() => void loadRoleFocusSuggestions()}
            onApplyRole={applyRoleFocusSuggestion}
            onApplyAll={applyAllRoleFocusSuggestions}
          />
        ) : null}
        <div className="mt-6 grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t.targetRoles} marker={buildMarkerNode('target_roles')}><TextAreaField value={preferencesDraft.target_roles} onChange={(event) => setPreferencesDraft((current) => ({...current, target_roles: event.target.value}))} rows={4} /></Field>
            <Field label={t.preferredLocations}><TextAreaField value={preferencesDraft.preferred_locations} onChange={(event) => setPreferencesDraft((current) => ({...current, preferred_locations: event.target.value}))} rows={4} /></Field>
          </div>
          <Field label={t.workModes}>
            <div className="flex flex-wrap gap-2">
              {(['remote', 'hybrid', 'onsite'] as WorkMode[]).map((mode) => {
                const active = preferencesDraft.work_modes.includes(mode);
                return (
                  <button key={mode} type="button" onClick={() => toggleWorkMode(mode)} className={`inline-flex h-11 items-center rounded-2xl border px-4 text-sm font-medium transition ${active ? 'border-foreground bg-foreground text-background' : 'border-border bg-background text-foreground hover:bg-muted/40'}`}>
                    {workModeLabel(t, mode)}
                  </button>
                );
              })}
            </div>
          </Field>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t.salaryExpectation}><InputField value={preferencesDraft.salary_expectation} onChange={(event) => setPreferencesDraft((current) => ({...current, salary_expectation: event.target.value}))} /></Field>
            <Field label={t.relocation}>
              <SelectField value={preferencesDraft.relocation} onChange={(event) => setPreferencesDraft((current) => ({...current, relocation: event.target.value as PreferencesDraft['relocation']}))}>
                <option value="unset">{t.relocationUnset}</option>
                <option value="yes">{t.relocationYes}</option>
                <option value="no">{t.relocationNo}</option>
              </SelectField>
            </Field>
          </div>
        </div>
      </Surface>

      <Surface>
        <SectionHeader title={t.experiencesTitle} action={<SecondaryButton onClick={() => setExperienceEditor({mode: 'create', targetId: null, values: emptyExperienceDraft()})} disabled={busyKey !== null}>{t.addExperience}</SecondaryButton>} />
        <div className="mt-6 space-y-4">
          {profile.experiences.length === 0 && experienceEditor === null ? <EmptyState>{t.noExperiences}</EmptyState> : null}
          {profile.experiences.map((item) => {
            const editing = experienceEditor?.mode === 'edit' && experienceEditor.targetId === item.id;
            if (editing && experienceEditor) {
              return (
                <EditorCard key={item.id ?? `exp-${item.display_order}`}>
                  <ExperienceEditorForm values={experienceEditor.values} setValues={(updater) => setExperienceEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} />
                  <EditorActions onSave={saveExperience} onCancel={() => setExperienceEditor(null)} busy={busyKey === 'save-experience'} saveLabel={t.update} t={t} />
                </EditorCard>
              );
            }
            return (
              <EntityCard key={item.id ?? `exp-${item.display_order}`} icon={<BriefcaseBusiness className="size-5" />} title={item.title} subtitle={[item.company_name, item.start_date ?? '—', item.is_current ? t.currentBadge : item.end_date ?? '—'].filter(Boolean).join(' · ')} description={item.description ?? undefined} chips={item.is_current ? [t.currentBadge] : []} onEdit={() => setExperienceEditor({mode: 'edit', targetId: item.id, values: draftFromExperience(item)})} onDelete={item.id ? () => void deleteExperience(item.id ?? '') : undefined} deleting={busyKey === `delete-experience-${item.id}`} t={t} />
            );
          })}
          {experienceEditor?.mode === 'create' ? (
            <EditorCard>
              <ExperienceEditorForm values={experienceEditor.values} setValues={(updater) => setExperienceEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} />
              <EditorActions onSave={saveExperience} onCancel={() => setExperienceEditor(null)} busy={busyKey === 'save-experience'} saveLabel={t.save} t={t} />
            </EditorCard>
          ) : null}
        </div>
      </Surface>

      <Surface>
        <SectionHeader title={t.educationTitle} action={<SecondaryButton onClick={() => setEducationEditor({mode: 'create', targetId: null, values: emptyEducationDraft()})} disabled={busyKey !== null}>{t.addEducation}</SecondaryButton>} />
        <div className="mt-2 text-xs text-muted-foreground">{t.manualEntryNote}</div>
        <div className="mt-4 space-y-4">
          {profile.education.length === 0 && educationEditor === null ? <EmptyState>{t.noEducation}</EmptyState> : null}
          {profile.education.map((item) => {
            const editing = educationEditor?.mode === 'edit' && educationEditor.targetId === item.id;
            if (editing && educationEditor) {
              return (
                <EditorCard key={item.id ?? `edu-${item.display_order}`}>
                  <EducationEditorForm values={educationEditor.values} setValues={(updater) => setEducationEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} universityOptions={universityOptions} departmentOptions={departmentOptions} />
                  <EditorActions onSave={saveEducation} onCancel={() => setEducationEditor(null)} busy={busyKey === 'save-education'} saveLabel={t.update} t={t} />
                </EditorCard>
              );
            }
            return (
              <EntityCard key={item.id ?? `edu-${item.display_order}`} icon={<GraduationCap className="size-5" />} title={item.institution} subtitle={[item.degree, item.field_of_study].filter(Boolean).join(' · ') || t.previewEmpty} description={[item.start_date ?? '—', item.end_date ?? '—'].join(' · ')} onEdit={() => setEducationEditor({mode: 'edit', targetId: item.id, values: draftFromEducation(item)})} onDelete={item.id ? () => void deleteEducation(item.id ?? '') : undefined} deleting={busyKey === `delete-education-${item.id}`} t={t} />
            );
          })}
          {educationEditor?.mode === 'create' ? (
            <EditorCard>
              <EducationEditorForm values={educationEditor.values} setValues={(updater) => setEducationEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} universityOptions={universityOptions} departmentOptions={departmentOptions} />
              <EditorActions onSave={saveEducation} onCancel={() => setEducationEditor(null)} busy={busyKey === 'save-education'} saveLabel={t.save} t={t} />
            </EditorCard>
          ) : null}
        </div>
      </Surface>

      <Surface>
        <SectionHeader title={t.languagesTitle} action={<SecondaryButton onClick={() => setLanguageEditor({mode: 'create', targetId: null, values: emptyLanguageDraft()})} disabled={busyKey !== null}>{t.addLanguage}</SecondaryButton>} />
        <div className="mt-6 space-y-4">
          {profile.languages.length === 0 && languageEditor === null ? <EmptyState>{t.noLanguages}</EmptyState> : null}
          {profile.languages.map((item) => {
            const editing = languageEditor?.mode === 'edit' && languageEditor.targetId === item.id;
            if (editing && languageEditor) {
              return (
                <EditorCard key={item.id ?? `lang-${item.display_order}`}>
                  <LanguageEditorForm values={languageEditor.values} setValues={(updater) => setLanguageEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} />
                  <EditorActions onSave={saveLanguage} onCancel={() => setLanguageEditor(null)} busy={busyKey === 'save-language'} saveLabel={t.update} t={t} />
                </EditorCard>
              );
            }
            return (
              <EntityCard key={item.id ?? `lang-${item.display_order}`} icon={<Languages className="size-5" />} title={item.language_name} subtitle={[item.proficiency_level, item.certificate_name].filter(Boolean).join(' · ') || t.previewEmpty} description={undefined} onEdit={() => setLanguageEditor({mode: 'edit', targetId: item.id, values: draftFromLanguage(item)})} onDelete={item.id ? () => void deleteLanguage(item.id ?? '') : undefined} deleting={busyKey === `delete-language-${item.id}`} t={t} />
            );
          })}
          {languageEditor?.mode === 'create' ? (
            <EditorCard>
              <LanguageEditorForm values={languageEditor.values} setValues={(updater) => setLanguageEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} />
              <EditorActions onSave={saveLanguage} onCancel={() => setLanguageEditor(null)} busy={busyKey === 'save-language'} saveLabel={t.save} t={t} />
            </EditorCard>
          ) : null}
        </div>
      </Surface>

      <Surface>
        <SectionHeader title={t.skillsTitle} action={<SecondaryButton onClick={() => setSkillEditor({mode: 'create', targetId: null, values: emptySkillDraft()})} disabled={busyKey !== null}>{t.addSkill}</SecondaryButton>} />
        <div className="mt-6 space-y-4">
          {profile.skills.length === 0 && skillEditor === null ? <EmptyState>{t.noSkills}</EmptyState> : null}
          {profile.skills.map((item) => {
            const detail = mergeSkillDetail(item);
            const editing = skillEditor?.mode === 'edit' && skillEditor.targetId === item.id;
            if (editing && skillEditor) {
              return (
                <EditorCard key={item.id ?? `skill-${item.display_order}`}>
                  <SkillEditorForm values={skillEditor.values} setValues={(updater) => setSkillEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} proficiencyMarker={buildMarkerNode(markerKeyFor('skill.proficiency_hint', skillEditor.values.skill_name || skillEditor.targetId))} evidenceMarker={buildMarkerNode(markerKeyFor('skill.evidence_note', skillEditor.values.skill_name || skillEditor.targetId))} />
                  <div className="mt-4 rounded-2xl border border-violet-500/15 bg-violet-500/[0.06] p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="text-sm font-semibold text-foreground">AI desteği</div>
                        <div className="text-xs leading-6 text-muted-foreground">
                          {locale === 'en'
                            ? 'Generate stronger skill phrasing and evidence ideas without saving automatically.'
                            : locale === 'de'
                              ? 'Erzeuge stärkere Kompetenzformulierungen und Nachweisideen, ohne automatisch zu speichern.'
                              : 'Otomatik kaydetmeden daha güçlü beceri ifadesi ve kanıt fikirleri üret.'}
                        </div>
                      </div>
                      <SecondaryButton onClick={() => void loadSkillEvidenceSuggestions()} disabled={busyKey !== null || skillEvidenceLoading}>
                        <Sparkles className="mr-2 size-4" />
                        {locale === 'en' ? 'Suggest description & proof' : locale === 'de' ? 'Beschreibung & Nachweis vorschlagen' : 'Açıklama ve kanıt öner'}
                      </SecondaryButton>
                    </div>
                    {skillEvidenceOpen ? (
                      <AiSkillEvidencePanel
                        locale={locale}
                        isLoading={skillEvidenceLoading}
                        errorMessage={skillEvidenceError}
                        response={skillEvidenceResult}
                        onClose={() => confirmPanelClose([markerKeyFor('skill.proficiency_hint', skillEditor?.values.skill_name ?? skillEditor?.targetId), markerKeyFor('skill.evidence_note', skillEditor?.values.skill_name ?? skillEditor?.targetId)], () => setSkillEvidenceOpen(false))}
                        onRefresh={() => void loadSkillEvidenceSuggestions()}
                        onApplyDescription={applySkillDescriptionSuggestion}
                        onApplyEvidenceNote={applySkillEvidenceNoteSuggestion}
                        onAppendProofIdeas={appendSkillProofIdeas}
                      />
                    ) : null}
                  </div>
                  <EditorActions onSave={saveSkill} onCancel={() => setSkillEditor(null)} busy={busyKey === 'save-skill'} saveLabel={t.update} t={t} />
                </EditorCard>
              );
            }
            return (
              <EntityCard key={item.id ?? `skill-${item.display_order}`} icon={<Wrench className="size-5" />} title={item.skill_name} subtitle={[detail?.category ?? item.category, detail?.proficiency_hint ?? item.proficiency_hint, (detail?.years_hint ?? item.years_hint) ? `${detail?.years_hint ?? item.years_hint} yıl` : null].filter(Boolean).join(' · ') || t.previewEmpty} description={detail?.evidence_note ?? undefined} chips={detail?.evidence_file_name ? [detail.evidence_file_name] : []} onEdit={() => setSkillEditor({mode: 'edit', targetId: item.id, values: draftFromSkill(item, detail)})} onDelete={item.id ? () => void deleteSkill(item.id ?? '') : undefined} deleting={busyKey === `delete-skill-${item.id}`} t={t} />
            );
          })}
          {skillEditor?.mode === 'create' ? (
            <EditorCard>
              <SkillEditorForm values={skillEditor.values} setValues={(updater) => setSkillEditor((current) => current ? {...current, values: updater(current.values)} : current)} t={t} proficiencyMarker={buildMarkerNode(markerKeyFor('skill.proficiency_hint', skillEditor.values.skill_name || skillEditor.targetId))} evidenceMarker={buildMarkerNode(markerKeyFor('skill.evidence_note', skillEditor.values.skill_name || skillEditor.targetId))} />
              <div className="mt-4 rounded-2xl border border-violet-500/15 bg-violet-500/[0.06] p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-sm font-semibold text-foreground">AI desteği</div>
                    <div className="text-xs leading-6 text-muted-foreground">
                      {locale === 'en'
                        ? 'Generate stronger skill phrasing and evidence ideas without saving automatically.'
                        : locale === 'de'
                          ? 'Erzeuge stärkere Kompetenzformulierungen und Nachweisideen, ohne automatisch zu speichern.'
                          : 'Otomatik kaydetmeden daha güçlü beceri ifadesi ve kanıt fikirleri üret.'}
                    </div>
                  </div>
                  <SecondaryButton onClick={() => void loadSkillEvidenceSuggestions()} disabled={busyKey !== null || skillEvidenceLoading}>
                    <Sparkles className="mr-2 size-4" />
                    {locale === 'en' ? 'Suggest description & proof' : locale === 'de' ? 'Beschreibung & Nachweis vorschlagen' : 'Açıklama ve kanıt öner'}
                  </SecondaryButton>
                </div>
                {skillEvidenceOpen ? (
                  <AiSkillEvidencePanel
                    locale={locale}
                    isLoading={skillEvidenceLoading}
                    errorMessage={skillEvidenceError}
                    response={skillEvidenceResult}
                    onClose={() => confirmPanelClose([markerKeyFor('skill.proficiency_hint', skillEditor?.values.skill_name ?? skillEditor?.targetId), markerKeyFor('skill.evidence_note', skillEditor?.values.skill_name ?? skillEditor?.targetId)], () => setSkillEvidenceOpen(false))}
                    onRefresh={() => void loadSkillEvidenceSuggestions()}
                    onApplyDescription={applySkillDescriptionSuggestion}
                    onApplyEvidenceNote={applySkillEvidenceNoteSuggestion}
                    onAppendProofIdeas={appendSkillProofIdeas}
                  />
                ) : null}
              </div>
              <EditorActions onSave={saveSkill} onCancel={() => setSkillEditor(null)} busy={busyKey === 'save-skill'} saveLabel={t.save} t={t} />
            </EditorCard>
          ) : null}
        </div>
      </Surface>

      <ProfileHealthDrawer
        open={profileHealthOpen}
        onClose={() => setProfileHealthOpen(false)}
        completionScore={completionScore}
        sections={profile.completeness.sections}
        suggestions={[
          ...(suggestions?.critical_gaps ?? []),
          ...(suggestions?.quick_wins ?? []),
          ...(suggestions?.highlights ?? []),
        ]}
        copy={{
          title: t.healthDrawerTitle,
          subtitle: t.healthDrawerSubtitle,
          completionLabel: t.healthDrawerCompletionLabel,
          strongAreasTitle: t.healthDrawerStrongAreas,
          focusAreasTitle: t.healthDrawerFocusAreas,
          suggestionsTitle: t.healthDrawerSuggestions,
          emptyLabel: t.healthDrawerEmpty,
          close: t.cancel,
        }}
      />

      <AvatarCropDialog
        open={cropDialogOpen}
        imageUrl={avatarSourceUrl}
        filename={avatarSourceName}
        onClose={() => {
          setCropDialogOpen(false);
          if (avatarSourceUrl) {
            URL.revokeObjectURL(avatarSourceUrl);
          }
          setAvatarSourceUrl(null);
          setAvatarSourceName(null);
        }}
        onConfirm={submitCroppedAvatar}
        saving={busyKey === 'avatar'}
      />
    </div>
  );
}

function ExperienceEditorForm({values, setValues, t}: {values: ExperienceDraft; setValues: (updater: (current: ExperienceDraft) => ExperienceDraft) => void; t: Copy}) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label={t.experienceRole}><InputField value={values.title} onChange={(event) => setValues((current) => ({...current, title: event.target.value}))} /></Field>
        <Field label={t.experienceCompany}><InputField value={values.company_name} onChange={(event) => setValues((current) => ({...current, company_name: event.target.value}))} /></Field>
        <Field label={t.experienceStart}><InputField value={values.start_date} onChange={(event) => setValues((current) => ({...current, start_date: event.target.value}))} placeholder="2021" /></Field>
        <Field label={t.experienceEnd}><InputField value={values.end_date} onChange={(event) => setValues((current) => ({...current, end_date: event.target.value}))} placeholder="2024" /></Field>
      </div>
      <label className="mt-4 flex items-center gap-3 text-sm text-foreground"><input type="checkbox" checked={values.is_current} onChange={(event) => setValues((current) => ({...current, is_current: event.target.checked}))} />{t.experienceCurrent}</label>
      <div className="mt-4"><Field label={t.experienceDescription}><TextAreaField value={values.description} onChange={(event) => setValues((current) => ({...current, description: event.target.value}))} rows={4} /></Field></div>
    </>
  );
}

function EducationEditorForm({values, setValues, t, universityOptions, departmentOptions}: {values: EducationDraft; setValues: (updater: (current: EducationDraft) => EducationDraft) => void; t: Copy; universityOptions: ComboboxOption[]; departmentOptions: ComboboxOption[]}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Field label={t.educationInstitution} hint={t.educationInstitutionHint}>
        <ComboboxField value={values.institution} onChange={(value) => setValues((current) => ({...current, institution: value}))} options={universityOptions} placeholder={t.educationInstitutionFallback} emptyLabel={t.educationInstitutionHint} />
      </Field>
      <Field label={t.educationDegree}><InputField value={values.degree} onChange={(event) => setValues((current) => ({...current, degree: event.target.value}))} /></Field>
      <Field label={t.educationField} hint={t.educationFieldHint}>
        <ComboboxField value={values.field_of_study} onChange={(value) => setValues((current) => ({...current, field_of_study: value}))} options={departmentOptions} placeholder={t.educationFieldFallback} emptyLabel={t.educationFieldHint} />
      </Field>
      <Field label={t.educationStart}><InputField value={values.start_date} onChange={(event) => setValues((current) => ({...current, start_date: event.target.value}))} placeholder="2020" /></Field>
      <Field label={t.educationEnd}><InputField value={values.end_date} onChange={(event) => setValues((current) => ({...current, end_date: event.target.value}))} placeholder="2024" /></Field>
    </div>
  );
}

function LanguageEditorForm({values, setValues, t}: {values: LanguageDraft; setValues: (updater: (current: LanguageDraft) => LanguageDraft) => void; t: Copy}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Field label={t.languageName}><InputField value={values.language_name} onChange={(event) => setValues((current) => ({...current, language_name: event.target.value}))} /></Field>
      <Field label={t.languageLevel}>
        <SelectField value={values.proficiency_level} onChange={(event) => setValues((current) => ({...current, proficiency_level: event.target.value as LanguageDraft['proficiency_level']}))}>
          <option value="">—</option>
          {languageLevelOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </SelectField>
      </Field>
      <Field label={t.languageCertificate}><InputField value={values.certificate_name} onChange={(event) => setValues((current) => ({...current, certificate_name: event.target.value}))} /></Field>
      <Field label={t.languageIssuer}><InputField value={values.issuer_name} onChange={(event) => setValues((current) => ({...current, issuer_name: event.target.value}))} /></Field>
      <div className="md:col-span-2">
        <FileSelectButton
          label={t.languageDocument}
          accept=".pdf,.png,.jpg,.jpeg"
          file={values.certificate_file}
          buttonLabel="Belge yükle"
          emptyLabel="Henüz belge seçilmedi"
          onChange={(file) => setValues((current) => ({...current, certificate_file: file}))}
        />
      </div>
    </div>
  );
}

function SkillEditorForm({values, setValues, t, proficiencyMarker, evidenceMarker}: {values: SkillDraft; setValues: (updater: (current: SkillDraft) => SkillDraft) => void; t: Copy; proficiencyMarker?: ReactNode; evidenceMarker?: ReactNode}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Field label={t.skillName}><InputField value={values.skill_name} onChange={(event) => setValues((current) => ({...current, skill_name: event.target.value}))} /></Field>
      <Field label={t.skillCategory}>
        <SelectField value={values.category} onChange={(event) => setValues((current) => ({...current, category: event.target.value}))}>
          <option value="">{t.skillCategoriesTitle}</option>
          {DEFAULT_SKILL_CATEGORIES.map((category) => <option key={category} value={category}>{category}</option>)}
        </SelectField>
      </Field>
      <Field label={t.skillProficiency} marker={proficiencyMarker}><InputField value={values.proficiency_hint} onChange={(event) => setValues((current) => ({...current, proficiency_hint: event.target.value}))} /></Field>
      <Field label={t.skillYears}><InputField type="number" value={values.years_hint} onChange={(event) => setValues((current) => ({...current, years_hint: event.target.value}))} /></Field>
      <div className="md:col-span-2"><Field label={t.skillEvidenceNote} marker={evidenceMarker}><TextAreaField value={values.evidence_note} onChange={(event) => setValues((current) => ({...current, evidence_note: event.target.value}))} rows={4} /></Field></div>
      <div className="md:col-span-2">
        <FileSelectButton
          label={t.skillEvidenceFile}
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          file={values.evidence_file}
          buttonLabel="Belge yükle"
          emptyLabel="Henüz belge seçilmedi"
          onChange={(file) => setValues((current) => ({...current, evidence_file: file}))}
        />
      </div>
    </div>
  );
}
