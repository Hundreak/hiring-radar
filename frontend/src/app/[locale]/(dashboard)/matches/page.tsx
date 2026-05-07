'use client';

import {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouter} from 'next/navigation';
import {useLocale, useTranslations} from 'next-intl';

import {MatchCard} from '@/components/matches/match-card';
import {MatchInsightsPanel} from '@/components/matches/match-insights-panel';
import {ApiError, api} from '@/lib/api';
import type {MatchInsightsData} from '@/lib/api';
import {getSkillAlignmentScore, isScorePreview} from '@/lib/match-ui';
import {dispatchSavedJobsChanged, onSavedJobsChanged} from '@/lib/saved-jobs-events';
import type {UserProfileAggregateResponse} from '@/types/profile';
import type {JobListItem, JobRankingMode} from '@/types/job';

type SortMode = 'score' | 'newest' | 'skill';

function formatPostedLabel(job: JobListItem) {
  return job.first_seen_at || job.last_seen_at || '—';
}

export default function MatchesPage() {
  const t = useTranslations('matches');
  const locale = useLocale();
  const router = useRouter();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [insights, setInsights] = useState<MatchInsightsData | null>(null);
  const [profileAggregate, setProfileAggregate] = useState<UserProfileAggregateResponse | null>(null);
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState<SortMode>('score');
  const [rankingMode, setRankingMode] = useState<JobRankingMode>('legacy_keyword');

  useEffect(() => {
    let active = true;
    Promise.all([
      api.getMatches(),
      api.getMatchInsights(),
      api.getSavedJobs(),
      api.getUserProfileAggregate(),
    ])
      .then(([res, ins, savedRes, profileRes]) => {
        if (!active) return;
        setJobs(res.items);
        setRankingMode(res.ranking_mode ?? 'legacy_keyword');
        setInsights(ins);
        setProfileAggregate(profileRes);
        setSavedJobIds(new Set(savedRes.items.map((s) => s.job_id)));
      })
      .catch((reason: Error) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) return;
        setError(reason.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    return onSavedJobsChanged(({jobId, action}) => {
      setSavedJobIds((prev) => {
        const next = new Set(prev);
        if (action === 'unsaved') next.delete(jobId);
        else next.add(jobId);
        return next;
      });
    });
  }, []);

  const handleToggleSave = useCallback(
    async (jobId: number, matchScore?: number) => {
      const isSaved = savedJobIds.has(jobId);
      try {
        if (isSaved) {
          await api.unsaveJob(jobId);
          setSavedJobIds((prev) => {
            const next = new Set(prev);
            next.delete(jobId);
            return next;
          });
          dispatchSavedJobsChanged({jobId, action: 'unsaved'});
        } else {
          await api.saveJob(jobId, matchScore);
          setSavedJobIds((prev) => new Set(prev).add(jobId));
          dispatchSavedJobsChanged({jobId, action: 'saved'});
        }
      } catch {
        // keep silent for now
      }
    },
    [savedJobIds]
  );

  const sorted = useMemo(() => {
    const arr = [...jobs];
    if (sort === 'score') {
      arr.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0));
    } else if (sort === 'newest') {
      arr.sort((a, b) => (b.first_seen_at ?? '').localeCompare(a.first_seen_at ?? ''));
    } else if (sort === 'skill') {
      arr.sort((a, b) => (getSkillAlignmentScore(b.explanation) ?? 0) - (getSkillAlignmentScore(a.explanation) ?? 0));
    }
    return arr;
  }, [jobs, sort]);

  const allScores = useMemo(
    () => jobs.map((job) => job.match_score ?? 0).filter((score) => Number.isFinite(score)),
    [jobs]
  );

  const scorePreview = useMemo(() => isScorePreview(allScores, rankingMode), [allScores, rankingMode]);

  const highestScore = useMemo(() => Math.max(...allScores, 0), [allScores]);

  const newToday = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return jobs.filter((j) => j.first_seen_at?.startsWith(today)).length;
  }, [jobs]);

  const profileCompleteness = profileAggregate?.profile.completeness.score ?? 0;

  const profileBanner = useMemo(() => {
    if (profileCompleteness >= 85) {
      return {
        tone: 'success' as const,
        text: t('profileStrong'),
        cta: t('profileStrongCta'),
      };
    }

    const remaining = Math.max(0, 100 - profileCompleteness);
    return {
      tone: 'info' as const,
      text: t('profileNeedsMoreDetail', {percent: remaining}),
      cta: t('completeProfile'),
    };
  }, [profileCompleteness, t]);

  const sortButtons: {key: SortMode; label: string}[] = [
    {key: 'score', label: t('sortHighest')},
    {key: 'newest', label: t('sortNewest')},
    {key: 'skill', label: t('sortSkill')},
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-primary">
            <span className="size-1.5 rounded-full bg-primary animate-pulse-dot" />
            {t('liveEngine')}
          </div>
          <h1 className="text-xl font-bold tracking-tight">{t('heroTitle', {count: jobs.length})}</h1>
          <p className="mt-1 max-w-lg text-xs leading-relaxed text-muted-foreground">{t('description')}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatPill value={String(jobs.length)} label={t('matched')} color="text-primary" />
          <StatPill
            value={scorePreview ? t('scorePreviewBadge') : `${highestScore}%`}
            label={t('highest')}
          />
          <StatPill value={String(newToday)} label={t('newToday')} color="text-success" />
        </div>
      </div>

      <div
        className={`flex items-center gap-2.5 rounded-xl border px-4 py-3 ${
          profileBanner.tone === 'success'
            ? 'border-success/20 bg-success/8'
            : 'border-primary/20 bg-primary/[0.06]'
        }`}
      >
        <div
          className={`flex size-7 shrink-0 items-center justify-center rounded-lg ${
            profileBanner.tone === 'success' ? 'bg-success/15' : 'bg-primary/20'
          }`}
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M7 2l1 3h3l-2.5 2 1 3L7 8.5 4.5 10l1-3L3 5h3z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" className="text-secondary-foreground" />
          </svg>
        </div>
        <p className="flex-1 text-xs text-muted-foreground">
          <strong className="font-medium text-foreground/70">{profileBanner.text}</strong>
        </p>
        <button
          type="button"
          onClick={() => router.push(`/${locale}/settings/profile`)}
          className="shrink-0 rounded-lg border border-primary/30 bg-primary/15 px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          {profileBanner.cta}
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{t('sortLabel')}:</span>
          {sortButtons.map((s) => (
            <button
              key={s.key}
              type="button"
              onClick={() => setSort(s.key)}
              className={`rounded-lg border px-3 py-1.5 text-xs transition ${
                sort === s.key
                  ? 'border-primary/40 bg-primary/15 text-secondary-foreground'
                  : 'border-border bg-surface-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground">
          <strong className="font-medium text-foreground/60">{sorted.length}</strong>{' '}
          {t('matchedCount', {count: sorted.length})}
        </span>
      </div>

      {loading ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">{t('loading')}</div>
      ) : error ? (
        <div className="rounded-xl border border-danger/30 bg-danger/5 p-8 text-sm text-danger">{error}</div>
      ) : sorted.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">{t('noMatches')}</div>
      ) : (
        <div className="grid matches-grid gap-4">
          <div className="grid match-cards-grid gap-2.5 self-start">
            {sorted.map((job) => (
              <MatchCard
                key={job.id}
                match={{
                  id: String(job.id),
                  title: job.title,
                  company: job.company_name,
                  location: job.location || '—',
                  matchScore: job.match_score ?? 0,
                  postedLabel: formatPostedLabel(job),
                  contractType: job.source_name,
                  matchedKeywords: job.matched_keywords,
                  explanation: job.explanation,
                  isScorePreview: scorePreview,
                  href: job.canonical_url,
                  saved: savedJobIds.has(job.id),
                  onToggleSave: () => handleToggleSave(job.id, job.match_score ?? undefined),
                }}
              />
            ))}
          </div>
          <MatchInsightsPanel insights={insights} />
        </div>
      )}
    </div>
  );
}

function StatPill({
  value,
  label,
  color,
}: {
  value: string;
  label: string;
  color?: string;
}) {
  return (
    <div className="flex min-w-[68px] flex-col items-center rounded-xl border border-border bg-surface px-4 py-2.5">
      <span className={`text-lg font-bold leading-none ${color ?? 'text-foreground'}`}>{value}</span>
      <span className="mt-1 text-[10px] text-muted-foreground">{label}</span>
    </div>
  );
}
