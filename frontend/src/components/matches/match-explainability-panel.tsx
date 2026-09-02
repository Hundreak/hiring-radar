'use client';

import {Sparkles} from 'lucide-react';
import {useLocale, useTranslations} from 'next-intl';

import {Badge} from '@/components/ui/badge';
import {dispatchCopilotPrompt} from '@/lib/copilot-ui';
import {
  buildMatchActionPlanPrompt,
  buildMatchExplainabilityModel,
  type MatchActionPlanItem,
  type MatchConfidenceLevel,
  type MatchReadinessLevel,
} from '@/lib/match-explainability';
import type {SupportedLocale} from '@/lib/match-ui';
import type {JobMatchExplanation} from '@/types/job';

export function MatchExplainabilityPanel({
  title,
  company,
  location,
  matchScore,
  isScorePreview,
  explanation,
  fallbackTerms,
}: {
  title: string;
  company: string;
  location: string;
  matchScore: number;
  isScorePreview?: boolean;
  explanation?: JobMatchExplanation | null;
  fallbackTerms?: string[];
}) {
  const t = useTranslations('matches');
  const locale = useLocale() as SupportedLocale;
  const model = buildMatchExplainabilityModel({
    matchScore,
    isScorePreview,
    explanation: explanation ?? null,
    fallbackTerms,
  });

  const hasScoreDrivers = model.topDrivers.length > 0;
  const hasActions = model.actionPlan.length > 0;
  const hasTerms = model.strongestTerms.length > 0 || model.missingTerms.length > 0;

  if (!hasScoreDrivers && !hasActions && !hasTerms && !explanation) {
    return null;
  }

  return (
    <div className="rounded-lg border border-border/70 bg-surface-muted/60 p-3">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {t('explainabilityTitle')}
          </div>
          <p className="mt-0.5 text-[11px] leading-relaxed text-foreground/80">
            {t(readinessSummaryKey(model.readiness.level))}
          </p>
        </div>
        <div className="shrink-0 rounded-full border border-primary/30 bg-primary/10 px-2 py-1 text-[10px] font-semibold text-secondary-foreground">
          {t(readinessLabelKey(model.readiness.level))}
        </div>
      </div>

      <div className="mb-2 grid grid-cols-2 gap-2 text-[10px]">
        <MetricPill label={t('explainabilityReadiness')} value={t(readinessLabelKey(model.readiness.level))} />
        <MetricPill label={t('explainabilityConfidence')} value={t(confidenceLabelKey(model.confidence))} />
      </div>

      {hasScoreDrivers ? (
        <div className="mb-2 space-y-1.5">
          <div className="text-[10px] font-medium text-muted-foreground">{t('explainabilityDrivers')}</div>
          {model.topDrivers.map((driver) => (
            <div key={driver.component_key}>
              <div className="mb-1 flex items-center justify-between gap-2 text-[10px]">
                <span className="truncate text-foreground/75">{driver.label}</span>
                <span className="font-medium text-foreground/60">{Math.round(driver.raw_score * 100)}%</span>
              </div>
              <div className="h-[4px] rounded-full bg-border">
                <div
                  className="h-[4px] rounded-full bg-primary/70"
                  style={{width: `${Math.max(4, Math.min(100, Math.round(driver.raw_score * 100)))}%`}}
                />
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {model.strongestTerms.length > 0 ? (
        <TermGroup title={t('explainabilityStrongSignals')} terms={model.strongestTerms} tone="matched" />
      ) : null}

      {model.missingTerms.length > 0 ? (
        <TermGroup title={t('explainabilityRiskSignals')} terms={model.missingTerms} tone="warning" />
      ) : null}

      {hasActions ? (
        <div className="mt-2 rounded-md border border-border/70 bg-surface/70 px-2.5 py-2">
          <div className="mb-1.5 text-[10px] font-medium text-muted-foreground">{t('explainabilityActionPlan')}</div>
          <div className="space-y-1">
            {model.actionPlan.map((action, index) => (
              <p key={`${action.kind}-${index}`} className="text-[11px] leading-relaxed text-foreground/75">
                {formatAction(t, action)}
              </p>
            ))}
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          dispatchCopilotPrompt(
            buildMatchActionPlanPrompt({
              locale,
              title,
              company,
              location,
              matchScore,
              explanation: explanation ?? null,
              model,
            })
          );
        }}
        className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-secondary-foreground hover:bg-primary/20"
      >
        <Sparkles className="size-3" />
        {t('explainabilityAiPlan')}
      </button>
    </div>
  );
}

function MetricPill({label, value}: {label: string; value: string}) {
  return (
    <div className="rounded-md border border-border/70 bg-surface px-2 py-1.5">
      <div className="text-[9px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5 truncate font-medium text-foreground/75">{value}</div>
    </div>
  );
}

function TermGroup({title, terms, tone}: {title: string; terms: string[]; tone: 'matched' | 'warning'}) {
  return (
    <div className="mb-2">
      <div className="mb-1 text-[10px] font-medium text-muted-foreground">{title}</div>
      <div className="flex flex-wrap gap-1">
        {terms.slice(0, 5).map((term) => (
          <Badge key={`${title}-${term}`} tone={tone} className="rounded px-1.5 py-0.5 text-[10px]">
            {term}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function readinessLabelKey(level: MatchReadinessLevel): string {
  return level === 'ready'
    ? 'explainabilityReady'
    : level === 'review'
      ? 'explainabilityReview'
      : 'explainabilityStretch';
}

function readinessSummaryKey(level: MatchReadinessLevel): string {
  return level === 'ready'
    ? 'explainabilityReadySummary'
    : level === 'review'
      ? 'explainabilityReviewSummary'
      : 'explainabilityStretchSummary';
}

function confidenceLabelKey(level: MatchConfidenceLevel): string {
  return level === 'strong'
    ? 'analysisStrongShort'
    : level === 'moderate'
      ? 'analysisModerateShort'
      : 'analysisLimitedShort';
}

function formatAction(t: ReturnType<typeof useTranslations>, action: MatchActionPlanItem): string {
  const terms = action.terms.join(', ');
  if (action.kind === 'apply_now') return t('explainabilityActionApply');
  if (action.kind === 'prepare_story') return t('explainabilityActionStory', {terms: terms || '—'});
  if (action.kind === 'strengthen_gap') return t('explainabilityActionGap', {terms: terms || '—'});
  return t('explainabilityActionVerify');
}
