'use client';

import {Bookmark, Sparkles} from 'lucide-react';
import {useLocale, useTranslations} from 'next-intl';

import {MatchExplainabilityPanel} from '@/components/matches/match-explainability-panel';
import {Badge} from '@/components/ui/badge';
import {dispatchCopilotPrompt} from '@/lib/copilot-ui';
import {
  buildLocalizedDeterministicReason,
  buildMatchAnalysisPrompt,
  buildMatchReason,
  getMeaningfulKeywords,
  getPrimaryGapTerms,
  getSkillAlignmentSnapshot,
  type SupportedLocale,
} from '@/lib/match-ui';
import type {JobMatchExplanation} from '@/types/job';

export type MatchCardModel = {
  id: string;
  title: string;
  company: string;
  location: string;
  matchScore: number;
  postedLabel: string;
  contractType: string;
  matchedKeywords: string[];
  targetRoles?: string[];
  isScorePreview?: boolean;
  href?: string;
  saved?: boolean;
  onToggleSave?: () => void;
  explanation?: JobMatchExplanation | null;
};

function scoreColor(score: number) {
  if (score >= 80) return {ring: 'border-match-high bg-match-high/10', text: 'text-match-high', fill: 'bg-match-high'};
  if (score >= 60) return {ring: 'border-match-mid bg-match-mid/10', text: 'text-match-mid', fill: 'bg-match-mid'};
  return {ring: 'border-match-low bg-match-low/10', text: 'text-match-low', fill: 'bg-match-low'};
}

function uniqueVisibleTerms(values: string[], limit = 4): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const value of values) {
    const trimmed = value.trim();
    if (!trimmed) continue;
    const normalized = trimmed.toLowerCase();
    if (seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(trimmed);
    if (result.length >= limit) break;
  }

  return result;
}

export function MatchCard({match}: {match: MatchCardModel}) {
  const t = useTranslations('matches');
  const locale = useLocale() as SupportedLocale;
  const colors = scoreColor(match.matchScore);
  const meaningfulKeywords = getMeaningfulKeywords(match.matchedKeywords);
  const fallbackReason = buildMatchReason({
    matchedKeywords: match.matchedKeywords,
    targetRoles: match.targetRoles,
    location: match.location,
    matchScore: match.matchScore,
  });
  const deterministicReason = buildLocalizedDeterministicReason(locale, match.explanation);
  const skillSnapshot = getSkillAlignmentSnapshot(match.explanation);
  const gapTerms = getPrimaryGapTerms(match.explanation);
  const reasonDetail = deterministicReason?.detail ?? (
    fallbackReason?.kind === 'keyword'
      ? t('whyKeyword', {keyword: fallbackReason.keyword})
      : fallbackReason?.kind === 'role'
        ? t('whyRole', {role: fallbackReason.role})
        : fallbackReason?.kind === 'location'
          ? t('whyLocation', {location: fallbackReason.location})
          : null
  );

  const reasonTerms = uniqueVisibleTerms(
    deterministicReason?.supportingTerms.length ? deterministicReason.supportingTerms : meaningfulKeywords,
    4
  );

  const scoreLabel = match.isScorePreview ? t('scorePreviewShort') : `${match.matchScore}%`;
  const scoreSubLabel = match.isScorePreview ? t('scoreNeedsContext') : t('matchingScoreLabel');

  return (
    <div
      className={`flex flex-col rounded-xl border transition cursor-pointer ${
        match.matchScore >= 80
          ? 'border-primary/30 bg-primary/[0.04] hover:border-primary/50'
          : 'border-border bg-surface hover:border-primary/30'
      }`}
    >
      <div className="flex flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div
              className={`flex size-11 shrink-0 items-center justify-center rounded-full border-2 ${colors.ring}`}
            >
              <span className={`text-[13px] font-bold ${colors.text}`}>{scoreLabel}</span>
            </div>
            <div className="min-w-0">
              <h3 className="text-[13px] font-medium leading-snug text-foreground">{match.title}</h3>
              <p className="text-[11px] text-muted-foreground">{match.company} · {match.location}</p>
              <p className="mt-0.5 text-[10px] text-muted-foreground/80">{scoreSubLabel}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              match.onToggleSave?.();
            }}
            className={`flex size-[26px] shrink-0 items-center justify-center rounded-md border transition ${
              match.saved
                ? 'border-primary/40 bg-primary/20 text-primary'
                : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
            }`}
          >
            <Bookmark className="size-3" />
          </button>
        </div>

        {reasonDetail ? (
          <div className="rounded-lg border border-primary/20 bg-primary/[0.04] px-3 py-2.5">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-primary">
              {t('whyHighlighted')}
            </div>
            <p className="text-[11px] leading-relaxed text-muted-foreground">{reasonDetail}</p>
            {reasonTerms.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {reasonTerms.map((term) => (
                  <Badge key={term} tone="matched" className="rounded px-1.5 py-0.5 text-[10px]">
                    {term}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        <MatchExplainabilityPanel
          title={match.title}
          company={match.company}
          location={match.location}
          matchScore={match.matchScore}
          isScorePreview={match.isScorePreview}
          explanation={match.explanation}
          fallbackTerms={reasonTerms.length ? reasonTerms : meaningfulKeywords}
        />

        <div className="flex items-center justify-between border-t border-border/50 pt-2">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              dispatchCopilotPrompt(
                buildMatchAnalysisPrompt({
                  title: match.title,
                  company: match.company,
                  location: match.location,
                  matchScore: match.matchScore,
                  matchedKeywords: match.matchedKeywords,
                  explanationSummary: match.explanation?.summary ?? null,
                  evidenceTerms: skillSnapshot.evidenceTerms,
                  gapTerms,
                })
              );
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-secondary-foreground hover:bg-primary/20"
          >
            <Sparkles className="size-3" />
            {t('analyzeWithAi')}
          </button>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-muted-foreground">{match.postedLabel}</span>
            {match.href ? (
              <a
                href={match.href}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="rounded-md bg-primary px-3 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90"
              >
                {t('apply')}
              </a>
            ) : (
              <button
                type="button"
                className="rounded-md bg-primary px-3 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90"
              >
                {t('apply')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
