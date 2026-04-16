'use client';

import {Loader2, Sparkles, Wand2} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {FeedbackBanner} from '@/components/ui/feedback-banner';
import type {AiSkillGroupingResponse} from '@/types/ai';

type Props = {
  locale: string;
  isLoading: boolean;
  errorMessage: string | null;
  response: AiSkillGroupingResponse | null;
  onClose: () => void;
  onRefresh: () => void;
  onApplyGroup: (skills: string[]) => void;
  onApplyAll: (skills: string[]) => void;
};

function flattenUniqueSkills(response: AiSkillGroupingResponse | null): string[] {
  if (!response) return [];

  const seen = new Set<string>();
  const merged: string[] = [];

  for (const group of response.groups ?? []) {
    for (const skill of group.skills ?? []) {
      const normalized = skill.trim();
      if (!normalized) continue;

      const key = normalized.toLocaleLowerCase('tr-TR');
      if (seen.has(key)) continue;

      seen.add(key);
      merged.push(normalized);
    }
  }

  return merged;
}

export function AiSkillGroupingPanel({
  locale,
  isLoading,
  errorMessage,
  response,
  onClose,
  onRefresh,
  onApplyGroup,
  onApplyAll,
}: Props) {
  const allSkills = flattenUniqueSkills(response);

  return (
    <div className="mt-4 rounded-3xl border border-violet-200/70 bg-white/95 p-5 shadow-[0_20px_70px_rgba(91,33,182,0.12)] backdrop-blur dark:border-violet-500/20 dark:bg-slate-950/85">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700 dark:border-violet-500/20 dark:bg-violet-500/10 dark:text-violet-200">
            <Sparkles className="size-3.5" />
            {locale === 'en'
              ? 'AI Skill Grouping'
              : locale === 'de'
                ? 'KI-Kompetenzgruppierung'
                : 'AI Beceri Gruplama'}
          </div>
          <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {locale === 'en'
              ? 'Make your skills cleaner and easier to match'
              : locale === 'de'
                ? 'Mache deine Kompetenzen klarer und leichter matchbar'
                : 'Becerilerini daha düzenli ve daha eşleşebilir hale getir'}
          </h3>
          <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {locale === 'en'
              ? 'These suggestions reorganize your skills into clearer groups and surface duplicate or weak naming patterns.'
              : locale === 'de'
                ? 'Diese Vorschläge ordnen deine Kompetenzen in klarere Gruppen und heben Duplikate oder schwache Benennungen hervor.'
                : 'Bu öneriler becerilerini daha net kümelere ayırır, tekrarları ve zayıf isimlendirmeleri görünür hale getirir.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={onRefresh} disabled={isLoading}>
            {isLoading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Wand2 className="mr-2 size-4" />}
            {locale === 'en' ? 'Refresh' : locale === 'de' ? 'Neu laden' : 'Yeniden öner'}
          </Button>
          <Button type="button" variant="ghost" onClick={onClose}>
            {locale === 'en' ? 'Close' : locale === 'de' ? 'Schließen' : 'Kapat'}
          </Button>
        </div>
      </div>

      {errorMessage ? (
        <div className="mt-4">
          <FeedbackBanner tone="error" title={locale === 'en' ? 'Could not fetch suggestions' : locale === 'de' ? 'Vorschläge konnten nicht geladen werden' : 'Öneriler alınamadı'}>
            {errorMessage}
          </FeedbackBanner>
        </div>
      ) : null}

      {isLoading ? (
        <div className="mt-6 flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-400">
          <Loader2 className="mr-2 size-4 animate-spin" />
          {locale === 'en'
            ? 'Preparing skill groups...'
            : locale === 'de'
              ? 'Kompetenzgruppen werden vorbereitet...'
              : 'Beceri kümeleri hazırlanıyor...'}
        </div>
      ) : null}

      {!isLoading && response ? (
        <div className="mt-6 space-y-5">
          {response.groups.length > 0 ? (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-violet-100 bg-violet-50/70 px-4 py-3 dark:border-violet-500/15 dark:bg-violet-500/5">
              <div>
                <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {locale === 'en'
                    ? 'Apply the full suggested skill set'
                    : locale === 'de'
                      ? 'Den vollständigen vorgeschlagenen Kompetenzsatz anwenden'
                      : 'Tüm önerilen beceri setini uygula'}
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400">
                  {locale === 'en'
                    ? 'This merges the suggested skill groups into your current skill draft.'
                    : locale === 'de'
                      ? 'Dies führt die vorgeschlagenen Kompetenzgruppen in deinen aktuellen Entwurf zusammen.'
                      : 'Bu işlem önerilen beceri gruplarını mevcut beceri taslağınla birleştirir.'}
                </div>
              </div>
              <Button type="button" onClick={() => onApplyAll(allSkills)} disabled={allSkills.length === 0}>
                {locale === 'en' ? 'Apply all' : locale === 'de' ? 'Alle anwenden' : 'Tümünü uygula'}
              </Button>
            </div>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            {response.groups.map((group, index) => (
              <div
                key={`${group.group_name}-${index}`}
                className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/60"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{group.group_name}</h4>
                    {group.notes ? (
                      <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-400">{group.notes}</p>
                    ) : null}
                  </div>
                  <Button type="button" size="sm" variant="outline" onClick={() => onApplyGroup(group.skills)}>
                    {locale === 'en' ? 'Apply group' : locale === 'de' ? 'Gruppe anwenden' : 'Grubu uygula'}
                  </Button>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {group.skills.map((skill) => (
                    <span
                      key={`${group.group_name}-${skill}`}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {response.duplicates.length > 0 ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 dark:border-amber-500/20 dark:bg-amber-500/5">
              <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">
                {locale === 'en' ? 'Possible duplicates' : locale === 'de' ? 'Mögliche Duplikate' : 'Muhtemel tekrarlar'}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {response.duplicates.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-full border border-amber-200 bg-white px-3 py-1 text-xs font-medium text-amber-800 dark:border-amber-500/20 dark:bg-slate-950 dark:text-amber-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {response.normalization_suggestions.length > 0 ? (
            <div className="rounded-2xl border border-sky-200 bg-sky-50/80 p-4 dark:border-sky-500/20 dark:bg-sky-500/5">
              <div className="text-sm font-semibold text-sky-900 dark:text-sky-100">
                {locale === 'en' ? 'Normalization suggestions' : locale === 'de' ? 'Normalisierungsvorschläge' : 'Düzenleme önerileri'}
              </div>
              <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
                {response.normalization_suggestions.map((item, index) => (
                  <li key={`${item}-${index}`}>• {item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {response.warnings.length > 0 ? (
            <FeedbackBanner tone="warning" title={locale === 'en' ? 'Points to review' : locale === 'de' ? 'Zu prüfende Punkte' : 'Dikkat edilmesi gerekenler'}>
              <ul className="space-y-1">
                {response.warnings.map((warning, index) => (
                  <li key={`${warning}-${index}`}>• {warning}</li>
                ))}
              </ul>
            </FeedbackBanner>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
