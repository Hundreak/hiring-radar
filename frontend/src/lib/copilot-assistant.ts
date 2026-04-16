import {ApiError, api, suggestProfileSkillEvidence} from '@/lib/api';
import type {
  AiHeadlineSummaryResponse,
  AiRoleFocusResponse,
  AiSkillEvidenceResponse,
  AiSkillGroupingResponse,
} from '@/types/ai';

import type {CopilotSection} from '@/lib/copilot-ui';

export type CopilotResolvedIntent =
  | 'headline_summary'
  | 'role_focus'
  | 'skill_grouping'
  | 'skill_evidence';

export type CopilotAssistantReply = {
  content: string;
  telemetryRef: string | null;
  intent: CopilotResolvedIntent;
};

const HEADLINE_KEYWORDS = ['başlık', 'headline', 'title', 'tagline'];
const SUMMARY_KEYWORDS = ['özet', 'summary', 'about me', 'bio', 'profil özeti'];
const ROLE_KEYWORDS = ['rol', 'role', 'pozisyon', 'position', 'uygun', 'fit', 'target role', 'hedef rol'];
const GROUPING_KEYWORDS = ['grupla', 'group', 'cluster', 'kategori', 'organize', 'organise', 'sınıfla'];
const EVIDENCE_KEYWORDS = ['kanıt', 'evidence', 'proof', 'ispat', 'portfolio', 'portföy', 'örnek', 'example'];
const SKILL_WORDS = ['beceri', 'skill', 'kompetenz'];

export async function generateCopilotReply({
  prompt,
  locale,
  section,
}: {
  prompt: string;
  locale: string;
  section: CopilotSection;
}): Promise<CopilotAssistantReply> {
  const intent = resolveCopilotIntent(prompt, section);

  switch (intent) {
    case 'headline_summary': {
      const response = await api.suggestProfileHeadlineSummary({
        locale,
        headline_option_count: 3,
        summary_option_count: 2,
      });
      return {
        content: formatHeadlineSummaryReply(response, locale),
        telemetryRef: response.telemetry_ref,
        intent,
      };
    }
    case 'role_focus': {
      const response = await api.suggestProfileRoleFocus({
        locale,
        suggestion_count: 4,
      });
      return {
        content: formatRoleFocusReply(response, locale),
        telemetryRef: response.telemetry_ref,
        intent,
      };
    }
    case 'skill_grouping': {
      const response = await api.suggestProfileSkillGrouping({
        locale,
        group_limit: 4,
        skill_limit_per_group: 6,
      });
      return {
        content: formatSkillGroupingReply(response, locale),
        telemetryRef: response.telemetry_ref,
        intent,
      };
    }
    case 'skill_evidence': {
      const skillName = extractSkillName(prompt) ?? defaultSkillLabel(locale);
      const response = await suggestProfileSkillEvidence({
        locale,
        skill_name: skillName,
      });
      return {
        content: formatSkillEvidenceReply(response, locale, skillName),
        telemetryRef: response.telemetry_ref,
        intent,
      };
    }
  }
}

export function buildCopilotErrorReply(locale: string, error: unknown): string {
  const detail =
    error instanceof ApiError
      ? error.detail || error.message
      : error instanceof Error
        ? error.message
        : null;

  if (locale === 'de') {
    return detail
      ? `Ich konnte gerade keine fundierte Antwort erstellen. Grund: ${detail}`
      : 'Ich konnte gerade keine fundierte Antwort erstellen. Bitte versuche es erneut.';
  }

  if (locale === 'en') {
    return detail
      ? `I could not build a grounded response right now. Reason: ${detail}`
      : 'I could not build a grounded response right now. Please try again.';
  }

  return detail
    ? `Şu anda grounded bir yanıt üretemedim. Neden: ${detail}`
    : 'Şu anda grounded bir yanıt üretemedim. Lütfen tekrar dene.';
}

function resolveCopilotIntent(prompt: string, section: CopilotSection): CopilotResolvedIntent {
  const lower = prompt.toLocaleLowerCase();

  if (containsAny(lower, EVIDENCE_KEYWORDS) && containsAny(lower, SKILL_WORDS)) {
    return 'skill_evidence';
  }
  if (containsAny(lower, GROUPING_KEYWORDS) && containsAny(lower, SKILL_WORDS)) {
    return 'skill_grouping';
  }
  if (containsAny(lower, HEADLINE_KEYWORDS) || containsAny(lower, SUMMARY_KEYWORDS)) {
    return 'headline_summary';
  }
  if (containsAny(lower, ROLE_KEYWORDS)) {
    return 'role_focus';
  }
  if (section === 'matches' || section === 'jobs') {
    return 'role_focus';
  }
  return 'headline_summary';
}

function containsAny(text: string, keywords: string[]): boolean {
  return keywords.some((keyword) => text.includes(keyword));
}

function extractSkillName(prompt: string): string | null {
  const quoted = prompt.match(/["""']([^"""']{2,80})["""']/);
  if (quoted?.[1]) return quoted[1].trim();

  const patterns = [
    /(?:beceri|skill|kompetenz)\s*[:\-]\s*([^.,\n]{2,80})/i,
    /(?:beceri|skill|kompetenz)\s+(?:için|for|für)\s+([^.,\n]{2,80})/i,
    /([^.,\n]{2,80})\s+(?:becerisi|skill|kompetenz)/i,
  ];

  for (const pattern of patterns) {
    const match = prompt.match(pattern);
    if (match?.[1]) return match[1].trim();
  }

  return null;
}

function defaultSkillLabel(locale: string): string {
  if (locale === 'de') return 'Technische Kompetenz';
  if (locale === 'en') return 'Technical Skill';
  return 'Teknik Beceri';
}

function formatHeadlineSummaryReply(response: AiHeadlineSummaryResponse, locale: string): string {
  const lines: string[] = [
    locale === 'de'
      ? 'Profil başlığı ve özet için en güçlü seçenekleri çıkardım:'
      : locale === 'en'
        ? 'I pulled the strongest options for your profile headline and summary:'
        : 'Profil başlığı ve özet için en güçlü seçenekleri çıkardım:',
  ];

  if (response.headline_options.length > 0) {
    lines.push('');
    lines.push(locale === 'en' ? 'Headline options:' : locale === 'de' ? 'Titeloptionen:' : 'Başlık seçenekleri:');
    response.headline_options.slice(0, 3).forEach((item, index) => {
      lines.push(`${index + 1}. ${item.title}`);
      if (item.rationale) lines.push(`   ${item.rationale}`);
    });
  }

  if (response.summary_options.length > 0) {
    lines.push('');
    lines.push(locale === 'en' ? 'Summary options:' : locale === 'de' ? 'Kurzprofil-Optionen:' : 'Özet seçenekleri:');
    response.summary_options.slice(0, 2).forEach((item, index) => {
      lines.push(`${index + 1}. ${item.text}`);
      if (item.rationale) lines.push(`   ${item.rationale}`);
    });
  }

  appendWarnings(lines, response.warnings, locale);
  return lines.join('\n');
}

function formatRoleFocusReply(response: AiRoleFocusResponse, locale: string): string {
  const lines: string[] = [
    locale === 'de'
      ? 'Profiline göre en mantıklı rol odaklarını özetledim:'
      : locale === 'en'
        ? 'I summarized the role directions that fit your profile best:'
        : 'Profiline göre en mantıklı rol odaklarını özetledim:',
    '',
  ];

  response.role_suggestions.slice(0, 4).forEach((item, index) => {
    lines.push(`${index + 1}. ${item.role_name}`);
    lines.push(`   ${item.fit_reason}`);
    if (item.missing_signals.length > 0) {
      lines.push(`   ${locale === 'en' ? 'Missing signals' : locale === 'de' ? 'Fehlende Signale' : 'Eksik sinyaller'}: ${item.missing_signals.join(', ')}`);
    }
  });

  appendWarnings(lines, response.warnings, locale);
  return lines.join('\n');
}

function formatSkillGroupingReply(response: AiSkillGroupingResponse, locale: string): string {
  const lines: string[] = [
    locale === 'de'
      ? 'Becerilerini daha okunur ve profesyonel kümelere ayırdım:'
      : locale === 'en'
        ? 'I grouped your skills into cleaner, more professional clusters:'
        : 'Becerilerini daha okunur ve profesyonel kümelere ayırdım:',
    '',
  ];

  response.groups.slice(0, 4).forEach((group, index) => {
    lines.push(`${index + 1}. ${group.group_name}: ${group.skills.join(', ')}`);
    if (group.notes) lines.push(`   ${group.notes}`);
  });

  if (response.normalization_suggestions.length > 0) {
    lines.push('');
    lines.push(
      `${locale === 'en' ? 'Normalization suggestions' : locale === 'de' ? 'Normalisierungsvorschläge' : 'Normalizasyon önerileri'}: ${response.normalization_suggestions.join(', ')}`,
    );
  }

  if (response.duplicates.length > 0) {
    lines.push(
      `${locale === 'en' ? 'Possible duplicates' : locale === 'de' ? 'Mögliche Duplikate' : 'Olası tekrarlar'}: ${response.duplicates.join(', ')}`,
    );
  }

  appendWarnings(lines, response.warnings, locale);
  return lines.join('\n');
}

function formatSkillEvidenceReply(response: AiSkillEvidenceResponse, locale: string, skillName: string): string {
  const lines: string[] = [
    locale === 'de'
      ? `${skillName} için daha güçlü anlatım ve kanıt yönlerini hazırladım:`
      : locale === 'en'
        ? `I prepared stronger explanation and proof directions for ${skillName}:`
        : `${skillName} için daha güçlü anlatım ve kanıt yönlerini hazırladım:`,
    '',
  ];

  if (response.description_suggestions.length > 0) {
    lines.push(locale === 'en' ? 'Description ideas:' : locale === 'de' ? 'Beschreibungsideen:' : 'Açıklama fikirleri:');
    response.description_suggestions.slice(0, 2).forEach((item, index) => lines.push(`${index + 1}. ${item}`));
    lines.push('');
  }

  if (response.evidence_note_suggestions.length > 0) {
    lines.push(locale === 'en' ? 'Evidence notes:' : locale === 'de' ? 'Nachweisnotizen:' : 'Kanıt notları:');
    response.evidence_note_suggestions.slice(0, 2).forEach((item, index) => lines.push(`${index + 1}. ${item}`));
    lines.push('');
  }

  if (response.proof_ideas.length > 0) {
    lines.push(locale === 'en' ? 'Proof ideas:' : locale === 'de' ? 'Nachweisideen:' : 'Kanıt fikirleri:');
    response.proof_ideas.slice(0, 4).forEach((item, index) => lines.push(`${index + 1}. ${item}`));
  }

  if (response.strengthening_note) {
    lines.push('');
    lines.push(`${locale === 'en' ? 'Strengthening note' : locale === 'de' ? 'Verstärkungshinweis' : 'Güçlendirme notu'}: ${response.strengthening_note}`);
  }

  if (response.missing_signals.length > 0) {
    lines.push('');
    lines.push(
      `${locale === 'en' ? 'Missing signals' : locale === 'de' ? 'Fehlende Signale' : 'Eksik sinyaller'}: ${response.missing_signals.join(', ')}`,
    );
  }

  appendWarnings(lines, response.warnings, locale);
  return lines.join('\n');
}

function appendWarnings(lines: string[], warnings: string[], locale: string) {
  if (warnings.length === 0) return;
  lines.push('');
  lines.push(locale === 'en' ? 'Notes:' : locale === 'de' ? 'Hinweise:' : 'Notlar:');
  warnings.slice(0, 3).forEach((warning) => lines.push(`- ${warning}`));
}
