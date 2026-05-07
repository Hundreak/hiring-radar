import type {JobMatchExplanation, JobMatchScoreBreakdownItem} from '@/types/job';

export type SupportedLocale = 'tr' | 'en' | 'de';

export type MatchReason =
  | {kind: 'keyword'; keyword: string}
  | {kind: 'role'; role: string}
  | {kind: 'location'; location: string}
  | null;

export type LocalizedDeterministicReason = {
  title: string | null;
  detail: string;
  supportingTerms: string[];
  gapTerms: string[];
};

export type DeterministicReason = LocalizedDeterministicReason;

export type SkillAlignmentSnapshot = {
  score: number | null;
  evidenceTerms: string[];
};

const GENERIC_TERMS = new Set([
  'engineer',
  'engineering',
  'developer',
  'manager',
  'specialist',
  'analyst',
  'lead',
  'senior',
  'junior',
  'intern',
  'staff',
  'associate',
  'executive',
  'officer',
  'consultant',
  'architect',
  'role',
  'position',
  'team',
  'general',
  'cloud',
  'platform',
  'system',
  'systems',
  'operations',
  'sales',
  'support',
]);

function normalizeToken(raw: string): string {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[()]/g, ' ')
    .replace(/[–—]/g, '-')
    .replace(/[^\p{L}\p{N}\s+#./-]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function toTitleCase(value: string): string {
  return value
    .split(' ')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function isMeaningfulDisplayTerm(normalized: string): boolean {
  if (!normalized || normalized.length < 3) return false;

  const parts = normalized.split(' ').filter(Boolean);
  if (parts.length === 0) return false;
  if (parts.length === 1 && GENERIC_TERMS.has(parts[0])) return false;
  if (parts.length <= 2 && parts.every((part) => GENERIC_TERMS.has(part))) return false;

  return true;
}

function uniqueTerms(values: Array<string | null | undefined>, limit = 6): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const rawValue of values) {
    if (typeof rawValue !== 'string') continue;
    const normalized = normalizeToken(rawValue);
    if (!isMeaningfulDisplayTerm(normalized) || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(toTitleCase(normalized));
    if (result.length >= limit) break;
  }

  return result;
}

function ensureSentence(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return '';
  return /[.!?]$/.test(trimmed) ? trimmed : `${trimmed}.`;
}

function humanJoin(values: string[]): string {
  if (values.length <= 1) return values[0] ?? '';
  if (values.length === 2) return `${values[0]} and ${values[1]}`;
  return `${values.slice(0, -1).join(', ')}, and ${values.at(-1)}`;
}

function humanJoinLocalized(locale: SupportedLocale, values: string[]): string {
  if (values.length <= 1) return values[0] ?? '';
  if (locale === 'tr') {
    if (values.length === 2) return `${values[0]} ve ${values[1]}`;
    return `${values.slice(0, -1).join(', ')} ve ${values.at(-1)}`;
  }
  if (locale === 'de') {
    if (values.length === 2) return `${values[0]} und ${values[1]}`;
    return `${values.slice(0, -1).join(', ')} und ${values.at(-1)}`;
  }
  return humanJoin(values);
}

function asArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function getBreakdownItems(
  explanation: JobMatchExplanation | null | undefined,
): JobMatchScoreBreakdownItem[] {
  return asArray(explanation?.matching_score_breakdown);
}

function getEvidencePoints(explanation: JobMatchExplanation | null | undefined) {
  return asArray(explanation?.key_evidence_points);
}

function getGapAnalysis(explanation: JobMatchExplanation | null | undefined) {
  return asArray(explanation?.gap_analysis);
}

function getMatchedSkillTerms(explanation: JobMatchExplanation | null | undefined): string[] {
  return asArray(explanation?.matched_skill_terms);
}

function getMissingSkillTerms(explanation: JobMatchExplanation | null | undefined): string[] {
  return asArray(explanation?.missing_skill_terms);
}

export function getBreakdownItem(
  explanation: JobMatchExplanation | null | undefined,
  componentKey: string,
): JobMatchScoreBreakdownItem | null {
  return getBreakdownItems(explanation).find((item) => item.component_key === componentKey) ?? null;
}

function fallbackReasonDetail(params: {
  locale: SupportedLocale;
  explanation: JobMatchExplanation;
  evidenceTerms: string[];
  gapTerms: string[];
}): string | null {
  const strongest = getBreakdownItems(params.explanation)[0] ?? null;
  const evidenceText = humanJoinLocalized(params.locale, params.evidenceTerms.slice(0, 3));
  const gapText = humanJoinLocalized(params.locale, params.gapTerms.slice(0, 3));

  if (params.locale === 'tr') {
    if (strongest && evidenceText) {
      return `${strongest.label} tarafında ${evidenceText} sinyalleri bu ilanla güçlü bir örtüşme gösteriyor.`;
    }
    if (gapText) {
      return `Bu ilanda özellikle ${gapText} tarafı daha dikkatli incelenmeli.`;
    }
    return 'Deterministik eşleşme motoru bu ilanı profilindeki güçlü sinyaller nedeniyle öne çıkarıyor.';
  }

  if (params.locale === 'de') {
    if (strongest && evidenceText) {
      return `Im Bereich ${strongest.label} zeigen Signale wie ${evidenceText} eine starke Überschneidung mit dieser Stelle.`;
    }
    if (gapText) {
      return `Bei dieser Stelle sollte besonders ${gapText} genauer geprüft werden.`;
    }
    return 'Die deterministische Matching-Engine hebt diese Stelle wegen starker Profilsignale hervor.';
  }

  if (strongest && evidenceText) {
    return `${strongest.label} looks strong here because signals like ${evidenceText} overlap with the role.`;
  }
  if (gapText) {
    return `This role still needs a closer review around ${gapText}.`;
  }
  return 'The deterministic matching engine is prioritizing this job because several profile signals align well.';
}

function externalContextSuffix(locale: SupportedLocale, explanation: JobMatchExplanation): string {
  const insights = explanation.external_source_insights;
  if (!insights || !['cached', 'live'].includes(insights.enrichment_status)) return '';

  const externalTerms = uniqueTerms(
    [
      ...asArray(insights.technology_stack_terms),
      ...asArray(insights.site_specific_requirements),
      ...asArray(insights.responsibility_clues),
    ],
    2,
  );

  if (externalTerms.length === 0) return '';

  const joined = humanJoinLocalized(locale, externalTerms);
  if (locale === 'tr') return ` Orijinal ilan kaynağında ${joined} beklentileri de görülüyor.`;
  if (locale === 'de') return ` In der Originalquelle sind zusätzlich Erwartungen wie ${joined} sichtbar.`;
  return ` The original source page also highlights expectations such as ${joined}.`;
}

export function getMeaningfulKeywords(keywords: string[] | null | undefined): string[] {
  if (!Array.isArray(keywords)) return [];
  return uniqueTerms(keywords, 8);
}

export function buildLocalizedDeterministicReason(
  locale: SupportedLocale,
  explanation: JobMatchExplanation | null | undefined,
): LocalizedDeterministicReason | null {
  if (!explanation) return null;

  const firstEvidence = getEvidencePoints(explanation)[0] ?? null;
  const firstGap = getGapAnalysis(explanation)[0] ?? null;
  const supportingTerms = uniqueTerms(
    [
      ...asArray(firstEvidence?.supporting_terms),
      ...getMatchedSkillTerms(explanation),
      ...asArray(getBreakdownItem(explanation, 'skill_alignment')?.evidence_terms),
      ...asArray(getBreakdownItem(explanation, 'domain_alignment')?.evidence_terms),
    ],
    4,
  );
  const gapTerms = uniqueTerms(
    [
      ...asArray(firstGap?.missing_terms),
      ...getMissingSkillTerms(explanation),
      ...asArray(getBreakdownItem(explanation, 'skill_alignment')?.missing_terms),
    ],
    4,
  );

  const termsText = humanJoinLocalized(locale, supportingTerms.slice(0, 3));

  let detail: string | null = null;

  switch (firstEvidence?.code) {
    case 'skill_overlap_high':
      detail =
        locale === 'tr'
          ? `Profilindeki ${termsText || 'temel teknik'} sinyalleri bu ilanın ana gereksinimleriyle güçlü biçimde örtüşüyor.`
          : locale === 'de'
            ? `Deine Profilsignale rund um ${termsText || 'zentrale technische Themen'} überschneiden sich stark mit den Kernanforderungen dieser Stelle.`
            : `Your profile signals around ${termsText || 'core technical topics'} overlap strongly with this job's main requirements.`;
      break;
    case 'role_family_match':
      detail =
        locale === 'tr'
          ? `Hedeflediğin rol yönü bu ilanla uyumlu görünüyor${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Deine aktuelle Zielrolle passt gut zu dieser Stelle${termsText ? `: ${termsText}` : ''}.`
            : `Your current role direction aligns well with this position${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'title_similarity_strong':
      detail =
        locale === 'tr'
          ? `İlan başlığı, profilindeki rol diliyle anlamlı biçimde örtüşüyor${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Der Stellentitel überschneidet sich sinnvoll mit der Rollensprache in deinem Profil${termsText ? `: ${termsText}` : ''}.`
            : `The job title meaningfully overlaps with the role language already present in your profile${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'discipline_preference_match':
      detail =
        locale === 'tr'
          ? `Bu rol, profilinde zaten güçlü görünen disiplin alanına oturuyor${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Diese Stelle liegt in einem Fachbereich, der in deinem Profil bereits stark erscheint${termsText ? `: ${termsText}` : ''}.`
            : `This role sits in a discipline that is already clearly represented in your profile${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'location_preference_match':
    case 'remote_preference_match':
    case 'workplace_mode_match':
      detail =
        locale === 'tr'
          ? `Çalışma biçimi ve konum tarafı tercihlerinle uyumlu görünüyor${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Arbeitsmodell und Standort passen zu deinen Präferenzen${termsText ? `: ${termsText}` : ''}.`
            : `The workplace setup and location look compatible with your stated preferences${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'experience_requirement_covered':
      detail =
        locale === 'tr'
          ? 'Deneyim seviyen bu rolün beklediği tabanla uyumlu görünüyor.'
          : locale === 'de'
            ? 'Dein Erfahrungsniveau wirkt passend zur erwarteten Basis dieser Rolle.'
            : 'Your experience level appears to cover the baseline this role is asking for.';
      break;
    case 'seniority_match':
      detail =
        locale === 'tr'
          ? 'Kıdem seviyesi bu rolün beklediği düzeyle uyumlu görünüyor.'
          : locale === 'de'
            ? 'Dein Senioritätsniveau passt gut zum erwarteten Level dieser Rolle.'
            : 'Your seniority level looks aligned with what this role expects.';
      break;
    case 'domain_experience_match':
      detail =
        locale === 'tr'
          ? `Deneyim geçmişin işin alan bağlamıyla örtüşüyor${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Dein Erfahrungshintergrund passt zum fachlichen Kontext der Stelle${termsText ? `: ${termsText}` : ''}.`
            : `Your experience background overlaps with the job's domain context${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'scope_alignment':
      detail =
        locale === 'tr'
          ? 'Sorumluluk ve sahiplik beklentileri profilindeki sinyallerle uyumlu görünüyor.'
          : locale === 'de'
            ? 'Verantwortungsumfang und Ownership-Erwartungen passen zu deinen Profilsignalen.'
            : 'The ownership and responsibility expectations look aligned with your profile signals.';
      break;
    case 'language_requirement_covered':
      detail =
        locale === 'tr'
          ? `Dil gereksinimi tarafında da görünür bir örtüşme var${termsText ? `: ${termsText}` : ''}.`
          : locale === 'de'
            ? `Auch bei den Sprachanforderungen ist eine erkennbare Überschneidung vorhanden${termsText ? `: ${termsText}` : ''}.`
            : `There is visible overlap on the language requirement side as well${termsText ? `: ${termsText}` : ''}.`;
      break;
    case 'education_requirement_covered':
      detail =
        locale === 'tr'
          ? 'Eğitim sinyalleri de bu rol için zayıf değil; profilin bu tarafta boş görünmüyor.'
          : locale === 'de'
            ? 'Auch die Bildungssignale wirken für diese Rolle nicht schwach; dein Profil ist hier nicht leer.'
            : 'Education signals are not weak for this role either; your profile does not look empty on that side.';
      break;
    default:
      detail = fallbackReasonDetail({locale, explanation, evidenceTerms: supportingTerms, gapTerms});
      break;
  }

  const finalDetail = ensureSentence(`${detail ?? ''}${externalContextSuffix(locale, explanation)}`);
  if (!finalDetail) return null;

  return {
    title: firstEvidence?.title ?? null,
    detail: finalDetail,
    supportingTerms,
    gapTerms,
  };
}

export function buildLocalizedReasonSummary(
  locale: SupportedLocale,
  explanation: JobMatchExplanation | null | undefined,
): string | null {
  return buildLocalizedDeterministicReason(locale, explanation)?.detail ?? null;
}

export function buildDeterministicReason(
  explanation: JobMatchExplanation | null | undefined,
): DeterministicReason | null {
  return buildLocalizedDeterministicReason('en', explanation);
}

export function getSkillAlignmentSnapshot(
  explanation: JobMatchExplanation | null | undefined,
): SkillAlignmentSnapshot {
  const skillBreakdown = getBreakdownItem(explanation, 'skill_alignment');
  const score =
    typeof skillBreakdown?.raw_score === 'number'
      ? Math.max(0, Math.min(100, Math.round(skillBreakdown.raw_score * 100)))
      : null;

  const firstEvidence = getEvidencePoints(explanation)[0] ?? null;
  const evidenceTerms = uniqueTerms(
    [
      ...asArray(skillBreakdown?.evidence_terms),
      ...getMatchedSkillTerms(explanation),
      ...asArray(firstEvidence?.supporting_terms),
    ],
    5,
  );

  return {score, evidenceTerms};
}

export function getSkillAlignmentScore(
  explanation: JobMatchExplanation | null | undefined,
): number | null {
  return getSkillAlignmentSnapshot(explanation).score;
}

export function getPrimaryGapTerms(
  explanation: JobMatchExplanation | null | undefined,
  limit = 4,
): string[] {
  if (!explanation) return [];

  const firstGap = getGapAnalysis(explanation)[0] ?? null;
  return uniqueTerms(
    [
      ...asArray(firstGap?.missing_terms),
      ...getMissingSkillTerms(explanation),
      ...asArray(getBreakdownItem(explanation, 'skill_alignment')?.missing_terms),
    ],
    limit,
  );
}

export function getPrimarySkillTerms(
  source:
    | JobMatchExplanation
    | {explanation?: JobMatchExplanation | null; matched_keywords?: string[] | null}
    | null
    | undefined,
  limit = 4,
): string[] {
  const explanation =
    source && typeof source === 'object' && 'matching_score_breakdown' in source
      ? source
      : source?.explanation;
  const fallbackKeywords =
    source && typeof source === 'object' && 'matched_keywords' in source
      ? source.matched_keywords
      : null;

  return uniqueTerms(
    [
      ...getSkillAlignmentSnapshot(explanation).evidenceTerms,
      ...getMatchedSkillTerms(explanation),
      ...asArray(fallbackKeywords),
    ],
    limit,
  );
}

export function getComponentScore(
  explanation: JobMatchExplanation | null | undefined,
  componentKey: string,
): number | null {
  const item = getBreakdownItem(explanation, componentKey);
  if (typeof item?.raw_score !== 'number') return null;
  return Math.max(0, Math.min(100, Math.round(item.raw_score * 100)));
}

export function buildMatchReason(args: {
  matchedKeywords?: string[] | null;
  targetRoles?: string[] | null;
  location?: string | null;
  matchScore?: number | null;
}): MatchReason {
  const meaningfulKeywords = getMeaningfulKeywords(args.matchedKeywords);
  if (meaningfulKeywords.length > 0 && (args.matchScore ?? 0) >= 65) {
    return {kind: 'keyword', keyword: meaningfulKeywords[0]};
  }

  const normalizedRoles = Array.isArray(args.targetRoles)
    ? args.targetRoles
        .map((role) => (typeof role === 'string' ? normalizeToken(role) : ''))
        .filter(Boolean)
    : [];

  for (const role of normalizedRoles) {
    const parts = role.split(' ').filter(Boolean);
    if (parts.length === 1 && GENERIC_TERMS.has(parts[0])) continue;
    if (parts.length <= 2 && parts.every((part) => GENERIC_TERMS.has(part))) continue;
    if (role.length >= 4) return {kind: 'role', role: toTitleCase(role)};
  }

  if (typeof args.location === 'string') {
    const normalizedLocation = normalizeToken(args.location);
    if (normalizedLocation.includes('remote') || normalizedLocation.includes('hybrid')) {
      return {kind: 'location', location: toTitleCase(normalizedLocation)};
    }
  }

  return null;
}

export function isScorePreview(
  scores: number[],
  rankingMode?: 'legacy_keyword' | 'deterministic_matching' | null,
): boolean {
  if (rankingMode === 'deterministic_matching') return false;

  const finite = scores.filter((score) => Number.isFinite(score));
  if (finite.length < 4) return false;

  const min = Math.min(...finite);
  const max = Math.max(...finite);
  return max - min <= 6;
}

export function buildMatchAnalysisPrompt(args: {
  title: string;
  company: string;
  location?: string | null;
  matchScore?: number | null;
  matchedKeywords?: string[] | null;
  explanationSummary?: string | null;
  evidenceTerms?: string[] | null;
  gapTerms?: string[] | null;
}): string {
  const meaningfulKeywords = getMeaningfulKeywords(args.matchedKeywords);
  const evidenceTerms = uniqueTerms(asArray(args.evidenceTerms));
  const gapTerms = uniqueTerms(asArray(args.gapTerms), 4);

  const lines = [
    `Bu ilanı profilime göre profesyonel şekilde analiz et: ${args.title}`,
    `Şirket: ${args.company}`,
    `Konum: ${args.location || 'Belirtilmemiş'}`,
  ];

  if (typeof args.matchScore === 'number') {
    lines.push(`Mevcut eşleşme skoru: ${args.matchScore}%`);
  }

  if (args.explanationSummary) {
    lines.push(`Deterministik özet: ${args.explanationSummary}`);
  }

  if (evidenceTerms.length > 0) {
    lines.push(`Şu an görünen güçlü sinyaller: ${evidenceTerms.join(', ')}`);
  } else if (meaningfulKeywords.length > 0) {
    lines.push(`Şu an eşleşen güçlü sinyaller: ${meaningfulKeywords.join(', ')}`);
  }

  if (gapTerms.length > 0) {
    lines.push(`Dikkat edilmesi gereken gap sinyalleri: ${gapTerms.join(', ')}`);
  }

  lines.push(
    'Lütfen şunları açıkla: neden uygun olabilirim, hangi eksiklerim kritik olabilir, başvurmadan önce neleri güçlendirmeliyim ve CV içinde hangi noktaları öne çıkarmalıyım.',
  );

  return lines.join('\n');
}
