'use client';

import {useMemo} from 'react';
import {useLocale, useTranslations} from 'next-intl';

import {calculateOfferRate, countActivePipeline, countSavedJobsByStatus} from '@/lib/saved-pipeline';
import type {SavedJob} from '@/types/saved';

export function SavedPipelineSummary({jobs}: {jobs: SavedJob[]}) {
  const t = useTranslations('saved');
  const locale = useLocale();

  const metrics = useMemo(() => {
    const counts = countSavedJobsByStatus(jobs);
    const offerRate = calculateOfferRate(jobs);
    // Yuzde isaretinin yeri dile gore degisir (TR "%42", EN "42%").
    const offerRateLabel =
      offerRate === null
        ? '—'
        : new Intl.NumberFormat(locale, {style: 'percent', maximumFractionDigits: 0}).format(offerRate / 100);

    return [
      {
        key: 'active',
        value: String(countActivePipeline(counts)),
        label: t('pipelineActive'),
        hint: t('pipelineActiveHint'),
        accent: 'text-primary',
      },
      {
        key: 'interviews',
        value: String(counts.interview),
        label: t('pipelineInterviews'),
        hint: t('pipelineInterviewsHint'),
        accent: 'text-foreground',
      },
      {
        key: 'offers',
        value: String(counts.offer),
        label: t('pipelineOffers'),
        hint: t('pipelineOffersHint'),
        accent: 'text-success',
      },
      {
        key: 'offerRate',
        value: offerRateLabel,
        label: t('pipelineOfferRate'),
        hint: t('pipelineOfferRateHint'),
        accent: 'text-foreground',
      },
    ];
  }, [jobs, locale, t]);

  return (
    <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <div key={metric.key} className="rounded-xl border border-border bg-surface p-3.5">
          <div className={`text-2xl font-bold leading-none ${metric.accent}`}>{metric.value}</div>
          <div className="mt-2 text-xs font-medium text-foreground/70">{metric.label}</div>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{metric.hint}</p>
        </div>
      ))}
    </div>
  );
}
