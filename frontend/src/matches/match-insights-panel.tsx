'use client';

import {useTranslations} from 'next-intl';

import type {MatchInsightsData} from '@/lib/api';
import {getMeaningfulKeywords} from '@/lib/match-ui';

export function MatchInsightsPanel({
  insights,
}: {
  insights: MatchInsightsData | null;
}) {
  const t = useTranslations('matches');

  if (!insights) return null;

  const strengths = insights.strengths
    .map((item) => ({...item, keyword: getMeaningfulKeywords([item.keyword])[0] ?? ''}))
    .filter((item) => item.keyword);

  const gaps = insights.gaps
    .map((item) => ({...item, keyword: getMeaningfulKeywords([item.keyword])[0] ?? ''}))
    .filter((item) => item.keyword);

  return (
    <aside className="space-y-3">
      <div className="rounded-xl border border-border bg-surface p-3.5">
        <div className="mb-3 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          <span className="size-1.5 rounded-full bg-primary" />
          {t('insightsTitle')}
        </div>
        {strengths.length === 0 && insights.remote_count === 0 ? (
          <p className="text-[11px] leading-relaxed text-muted-foreground">{t('insightsEmpty')}</p>
        ) : (
          <div className="space-y-2.5">
            {strengths.slice(0, 3).map((s) => {
              const pct = s.total_jobs > 0 ? Math.round((s.match_count / s.total_jobs) * 100) : 0;
              return (
                <InsightRow
                  key={s.keyword}
                  color="bg-primary/15"
                  iconColor="text-primary"
                  icon="star"
                  title={t('strengthTitle', {keyword: s.keyword})}
                  sub={t('strengthSub', {count: s.match_count, pct})}
                />
              );
            })}
            {insights.remote_count > 0 ? (
              <InsightRow
                color="bg-success/10"
                iconColor="text-success"
                icon="check"
                title={t('remoteTitle')}
                sub={t('remoteSub', {remote: insights.remote_count, total: insights.total_matched})}
              />
            ) : null}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-border bg-surface p-3.5">
        <div className="mb-3 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          <span className="size-1.5 rounded-full bg-warning" />
          {t('gapsTitle')}
        </div>
        {gaps.length === 0 ? (
          <p className="text-[11px] leading-relaxed text-muted-foreground">{t('gapsEmpty')}</p>
        ) : (
          <div className="space-y-2">
            {gaps.slice(0, 3).map((g) => (
              <GapRow
                key={g.keyword}
                skill={g.keyword}
                jobsLabel={t('gapsJobs', {count: g.demand_count})}
                pct={g.demand_pct}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function InsightRow({
  color,
  iconColor,
  icon,
  title,
  sub,
}: {
  color: string;
  iconColor: string;
  icon: 'star' | 'check' | 'warning';
  title: string;
  sub: string;
}) {
  return (
    <div className="flex items-start gap-2.5 border-b border-border/50 pb-2.5 last:border-b-0 last:pb-0">
      <div className={`flex size-7 shrink-0 items-center justify-center rounded-lg ${color}`}>
        {icon === 'star' && (
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" className={iconColor}>
            <path d="M7 2l1.2 3.3H11.5L9 7.2l.7 3.3L7 8.8l-2.7 1.7.7-3.3L2.5 5.3l3.3-.7z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
          </svg>
        )}
        {icon === 'check' && (
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" className={iconColor}>
            <path d="M2 7l3.5 3.5L12 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
        {icon === 'warning' && (
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" className={iconColor}>
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.2" />
            <path d="M7 4.5v3M7 9v.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
          </svg>
        )}
      </div>
      <div>
        <div className="text-xs font-medium text-foreground/65">{title}</div>
        <div className="text-[11px] leading-relaxed text-muted-foreground">{sub}</div>
      </div>
    </div>
  );
}

function GapRow({skill, jobsLabel, pct}: {skill: string; jobsLabel: string; pct: number}) {
  return (
    <div className="flex items-center justify-between border-b border-border/50 py-1.5 last:border-b-0">
      <div>
        <div className="text-xs text-muted-foreground">{skill}</div>
        <div className="text-[10px] text-muted-foreground/60">{jobsLabel}</div>
      </div>
      <div className="w-14">
        <div className="h-[3px] rounded-full bg-border">
          <div className="h-[3px] rounded-full bg-warning" style={{width: `${pct}%`}} />
        </div>
      </div>
    </div>
  );
}
