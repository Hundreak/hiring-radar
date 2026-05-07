'use client';

import {Bookmark, Clock3, MapPin, Sparkles} from 'lucide-react';
import {useLocale, useTranslations} from 'next-intl';

import {Badge} from '@/components/ui/badge';
import {dispatchCopilotPrompt} from '@/lib/copilot-ui';
import {
  buildJobAnalysisPrompt,
  buildRecommendationSummary,
  shouldShowRecommendationSummary,
} from '@/lib/job-recommendation-ui';
import {
  buildLocalizedDeterministicReason,
  getMeaningfulKeywords,
  getPrimaryGapTerms,
  getSkillAlignmentSnapshot,
  type SupportedLocale,
} from '@/lib/match-ui';
import type {JobMatchExplanation} from '@/types/job';

export type JobCardModel = {
  id: string;
  title: string;
  company: string;
  location: string;
  workModel: string;
  contractType: string;
  tags: string[];
  postedLabel: string;
  matched: boolean;
  matchScore?: number;
  matchedKeywords?: string[];
  href?: string;
  saved?: boolean;
  onToggleSave?: () => void;
  explanation?: JobMatchExplanation | null;
};

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

export function JobCard({job}: {job: JobCardModel}) {
  const t = useTranslations('jobs');
  const locale = useLocale() as SupportedLocale;
  const matchedKeywords = Array.isArray(job.matchedKeywords) ? job.matchedKeywords : [];
  const deterministicReason = buildLocalizedDeterministicReason(locale, job.explanation);
  const skillSnapshot = getSkillAlignmentSnapshot(job.explanation);
  const gapTerms = getPrimaryGapTerms(job.explanation);
  const analysisCoverage = job.explanation?.analysis_coverage ?? null;
  const analysisCoverageLabel = analysisCoverage
    ? analysisCoverage.level === 'strong'
      ? t('analysisStrong')
      : analysisCoverage.level === 'moderate'
        ? t('analysisModerate')
        : t('analysisLimited')
    : null;
  const recommendationSummary = deterministicReason?.detail ?? (
    shouldShowRecommendationSummary({
      matched: job.matched,
      matchScore: job.matchScore,
      matchedKeywords,
    })
      ? buildRecommendationSummary({
          locale,
          matchedKeywords,
          title: job.title,
          company: job.company,
        })
      : null
  );
  const evidenceTerms = uniqueVisibleTerms(
    [...skillSnapshot.evidenceTerms, ...(deterministicReason?.supportingTerms ?? [])],
    4
  );
  const visibleTags = uniqueVisibleTerms([...getMeaningfulKeywords(job.tags), ...evidenceTerms], 4);

  return (
    <div
      className={`flex cursor-pointer flex-col gap-2.5 rounded-xl border p-4 transition ${
        job.matched && (job.matchScore ?? 0) >= 80
          ? 'border-primary/30 bg-primary/[0.04] hover:border-primary/50'
          : 'border-border bg-surface hover:border-primary/30'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {job.matched && job.matchScore != null && (
            <div className="mb-1.5 inline-flex items-center gap-1 rounded bg-primary/15 px-2 py-0.5 text-[11px] font-medium text-secondary-foreground">
              <span className="size-1 rounded-full bg-primary" />
              {t('matchedForYou', {score: job.matchScore})}
            </div>
          )}
          <h3 className="text-sm font-medium leading-snug text-foreground">
            {job.title}
          </h3>
          <p className="text-xs text-muted-foreground">{job.company}</p>
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            job.onToggleSave?.();
          }}
          className={`flex size-7 shrink-0 items-center justify-center rounded-lg border transition ${
            job.saved
              ? 'border-primary/40 bg-primary/20 text-primary'
              : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
          }`}
        >
          <Bookmark className="size-3.5" />
        </button>
      </div>

      {recommendationSummary && (
        <div className="rounded-lg border border-primary/20 bg-primary/[0.04] px-3 py-2">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-primary">
            {t('whyThisMayFit')}
          </div>
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            {recommendationSummary}
          </p>
          {evidenceTerms.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {evidenceTerms.map((term) => (
                <Badge key={term} tone="matched" className="rounded px-1.5 py-0.5 text-[10px]">
                  {term}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>
      )}

      {analysisCoverage && analysisCoverageLabel ? (
        <div className="rounded-lg border border-border/70 bg-surface-muted/70 px-3 py-2">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {t('analysisCoverage')}
          </div>
          <p className="text-[11px] leading-relaxed text-foreground/80">{analysisCoverageLabel}</p>
        </div>
      ) : null}

      {job.matched && job.matchScore != null && (
        <div className="flex items-center gap-1.5">
          <div className="h-[3px] flex-1 rounded-full bg-border">
            <div
              className="h-[3px] rounded-full bg-primary"
              style={{width: `${job.matchScore}%`}}
            />
          </div>
          <span className="text-[11px] font-semibold text-primary">
            {job.matchScore}%
          </span>
        </div>
      )}

      <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <MapPin className="size-3" />
          {job.location}
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock3 className="size-3" />
          {job.postedLabel}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {visibleTags.map((tag) => (
          <Badge key={tag} className="rounded px-1.5 py-0.5 text-[10px]">
            {tag}
          </Badge>
        ))}
        {job.contractType && (
          <Badge tone="success" className="rounded px-1.5 py-0.5 text-[10px]">
            {job.contractType}
          </Badge>
        )}
        {job.workModel === 'Remote' && (
          <Badge tone="remote" className="rounded px-1.5 py-0.5 text-[10px]">
            Remote
          </Badge>
        )}
      </div>

      {gapTerms.length > 0 ? (
        <div className="flex flex-wrap gap-1 border-t border-border/50 pt-2">
          {gapTerms.map((term) => (
            <Badge key={term} tone="warning" className="rounded px-1.5 py-0.5 text-[10px]">
              {term}
            </Badge>
          ))}
        </div>
      ) : null}

      <div className="flex items-center justify-between border-t border-border/50 pt-2 text-[11px]">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            dispatchCopilotPrompt(
              buildJobAnalysisPrompt({
                locale,
                title: job.title,
                company: job.company,
                location: job.location,
                matchScore: job.matchScore ?? null,
                matchedKeywords,
                href: job.href,
                explanationSummary: job.explanation?.summary ?? null,
                evidenceTerms,
                gapTerms,
              })
            );
          }}
          className="inline-flex items-center gap-1.5 rounded-md border border-primary/25 bg-primary/[0.08] px-2.5 py-1 text-[11px] font-medium text-secondary-foreground hover:bg-primary/[0.14]"
        >
          <Sparkles className="size-3" />
          {t('analyzeWithAi')}
        </button>
        {job.href ? (
          <a
            href={job.href}
            className="font-medium text-primary hover:text-secondary-foreground"
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            {t('viewDetails')} ↗
          </a>
        ) : (
          <span className="font-medium text-primary">
            {t('viewDetails')} ↗
          </span>
        )}
      </div>
    </div>
  );
}
