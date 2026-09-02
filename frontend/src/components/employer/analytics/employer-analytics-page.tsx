'use client';

import Link from 'next/link';
import {
  AlertTriangle,
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  Download,
  Gauge,
  RefreshCw,
  Search,
  Target,
  TrendingDown,
  TrendingUp,
  UsersRound,
} from 'lucide-react';
import {useMemo, useState} from 'react';

import {MetricCard, ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {employerAnalyticsMock} from '@/data/employer-analytics.mock';
import {employerCandidatesMock} from '@/data/employer-candidates.mock';
import {employerPipelineMock} from '@/data/employer-dashboard.mock';
import {employerJobsMock} from '@/data/employer-jobs.mock';
import {formatCompactNumber} from '@/lib/employer-format';
import {getEmployerAnalyticsCopy} from '@/lib/employer-page-copy';
import {cn} from '@/lib/utils';
import type {EmployerInsightTone, EmployerJobSummary, EmployerRiskLevel, EmployerSourceKey} from '@/types/employer';

type AnalyticsPeriod = '7d' | '30d' | '90d';
type AnalyticsLens = 'executive' | 'pipeline' | 'sourcing' | 'quality';

type FunnelStage = {
  id: keyof ReturnType<typeof getEmployerAnalyticsCopy>['funnel']['stages'];
  count: number;
  conversion: number;
  target: number;
  overdue?: number;
};

type SourceIntelligence = {
  key: EmployerSourceKey;
  count: number;
  qualityScore: number;
  responseScore: number;
  costIndex: number;
  conversion: number;
};

const lensOrder: AnalyticsLens[] = ['executive', 'pipeline', 'sourcing', 'quality'];
const periodOrder: AnalyticsPeriod[] = ['7d', '30d', '90d'];

const funnelStages: FunnelStage[] = [
  {id: 'views', count: 1489, conversion: 100, target: 100},
  {id: 'applications', count: 248, conversion: 16.7, target: 18},
  {id: 'qualified', count: 74, conversion: 29.8, target: 32},
  {id: 'shortlist', count: 31, conversion: 41.9, target: 45, overdue: 8},
  {id: 'interview', count: 14, conversion: 45.1, target: 50, overdue: 3},
  {id: 'offer', count: 4, conversion: 28.5, target: 35},
  {id: 'hired', count: 2, conversion: 50, target: 55},
];

const campaignHealthSignals = [
  {id: 'ready', value: 4},
  {id: 'review', value: 11},
  {id: 'blocked', value: 3},
  {id: 'response', value: '%38'},
] as const;

function routeHref(locale: string, target: string) {
  if (target === 'analytics') return `/${locale}/employer/analytics`;
  return `/${locale}/employer/${target}`;
}

function getPeriodMultiplier(period: AnalyticsPeriod) {
  if (period === '7d') return 0.34;
  if (period === '90d') return 2.7;
  return 1;
}

function scaleNumber(value: number, period: AnalyticsPeriod) {
  return Math.round(value * getPeriodMultiplier(period));
}

function getExecutiveScore() {
  const avgMatch = Math.round(employerCandidatesMock.reduce((sum, candidate) => sum + candidate.matchScore, 0) / employerCandidatesMock.length);
  const avgJobQuality = Math.round(employerJobsMock.reduce((sum, job) => sum + job.qualityScore, 0) / employerJobsMock.length);
  const pipelineHealth = Math.round(100 - employerPipelineMock.reduce((sum, stage) => sum + stage.overdueCount, 0) * 4.2);
  return Math.round(avgMatch * 0.38 + avgJobQuality * 0.32 + pipelineHealth * 0.3);
}

function getSourceIntelligence(): SourceIntelligence[] {
  return employerAnalyticsMock.sourceBreakdown.map((source) => {
    const responseScore = source.key === 'referral' ? 49 : source.key === 'talent_radar' ? 44 : source.key === 'linkedin' ? 36 : source.key === 'direct' ? 32 : 27;
    const costIndex = source.key === 'referral' ? 34 : source.key === 'talent_radar' ? 42 : source.key === 'direct' ? 54 : source.key === 'linkedin' ? 68 : 79;
    const conversion = Math.round((source.qualityScore / Math.max(1, costIndex)) * 18);
    return {key: source.key, count: source.count, qualityScore: source.qualityScore, responseScore, costIndex, conversion};
  });
}

function sourceTone(source: EmployerSourceKey): EmployerInsightTone {
  if (source === 'referral') return 'success';
  if (source === 'talent_radar') return 'ai';
  if (source === 'job_board') return 'warning';
  return 'info';
}

function riskTone(risk: EmployerRiskLevel): 'success' | 'warning' | 'danger' | 'info' {
  if (risk === 'healthy') return 'success';
  if (risk === 'watch') return 'info';
  if (risk === 'critical') return 'danger';
  return 'warning';
}

function insightClass(tone: EmployerInsightTone) {
  if (tone === 'success') return 'border-emerald-500/20 bg-emerald-500/10';
  if (tone === 'warning') return 'border-amber-500/20 bg-amber-500/10';
  if (tone === 'danger') return 'border-red-500/20 bg-red-500/10';
  if (tone === 'ai') return 'border-primary/20 bg-primary/10';
  return 'border-blue-500/20 bg-blue-500/10';
}

function miniBar(width: number, tone: 'primary' | 'success' | 'warning' | 'danger' = 'primary') {
  const toneClass = {
    primary: 'bg-primary',
    success: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
  }[tone];

  return (
    <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
      <div className={cn('h-full rounded-full transition-all', toneClass)} style={{width: `${Math.max(4, Math.min(width, 100))}%`}} />
    </div>
  );
}

function TrendText({positive, children}: {positive: boolean; children: React.ReactNode}) {
  return (
    <span className={cn('inline-flex items-center gap-1 text-xs font-bold', positive ? 'text-success' : 'text-warning')}>
      {positive ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />}
      {children}
    </span>
  );
}

function FunnelChart({locale, period}: {locale: string; period: AnalyticsPeriod}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const maxCount = Math.max(...funnelStages.map((stage) => scaleNumber(stage.count, period)));

  return (
    <SurfaceCard className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone="ai">{copy.funnel.badge}</StatusBadge>
            <StatusBadge tone="info">{copy.periods[period]}</StatusBadge>
          </div>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.funnel.title}</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.funnel.description}</p>
        </div>
        <Button type="button" variant="outline" size="sm">
          <Download className="size-4" />
          {copy.funnel.report}
        </Button>
      </div>

      <div className="space-y-4">
        {funnelStages.map((stage, index) => {
          const scaledCount = scaleNumber(stage.count, period);
          const width = (scaledCount / maxCount) * 100;
          const isAtRisk = Boolean(stage.overdue && stage.overdue > 0);

          return (
            <div key={stage.id} className="grid gap-3 rounded-2xl border border-border/70 bg-surface-muted/40 p-3 md:grid-cols-[150px_1fr_170px] md:items-center">
              <div>
                <p className="text-sm font-semibold text-foreground">{copy.funnel.stages[stage.id]}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{copy.funnel.stagePrefix} {index + 1}</p>
              </div>
              <div className="space-y-2">
                <div className="h-9 overflow-hidden rounded-2xl bg-surface shadow-inner">
                  <div
                    className={cn('flex h-full items-center justify-end rounded-2xl px-3 text-xs font-bold text-white transition-all', isAtRisk ? 'bg-warning' : index >= 4 ? 'bg-success' : 'bg-primary')}
                    style={{width: `${Math.max(8, width)}%`}}
                  >
                    {formatCompactNumber(scaledCount)}
                  </div>
                </div>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>{copy.funnel.target} %{stage.target}</span>
                  <span>{copy.funnel.actual} %{Math.round(stage.conversion)}</span>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 md:justify-end">
                {isAtRisk ? <StatusBadge tone="warning">{stage.overdue} {copy.funnel.overdue}</StatusBadge> : <StatusBadge tone="success">{copy.funnel.clear}</StatusBadge>}
                <ScoreBadge score={Math.round(stage.conversion * 2)} label={copy.funnel.momentum} size="sm" />
              </div>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}

function SourceQualityMatrix({locale}: {locale: string}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const sources = getSourceIntelligence();

  return (
    <SurfaceCard className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <StatusBadge tone="info">{copy.sources.badge}</StatusBadge>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.sources.title}</h2>
          <p className="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">{copy.sources.description}</p>
        </div>
        <Link href={`/${locale}/employer/campaigns`}>
          <Button type="button" variant="soft" size="sm">
            {copy.sources.action}
            <ArrowRight className="size-4" />
          </Button>
        </Link>
      </div>

      <div className="grid gap-3">
        {sources.map((source) => (
          <div key={source.key} className="rounded-3xl border border-border bg-surface/70 p-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={sourceTone(source.key)}>{copy.sources.labels[source.key]}</StatusBadge>
                  <span className="text-xs font-medium text-muted-foreground">{source.count} {copy.sources.candidate}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.sources.recommendations[source.key]}</p>
              </div>
              <div className="grid min-w-0 gap-3 sm:grid-cols-4 lg:w-[560px]">
                <MiniMetric label={copy.sources.quality} value={`${source.qualityScore}`} bar={source.qualityScore} tone={source.qualityScore >= 85 ? 'success' : 'primary'} />
                <MiniMetric label={copy.sources.response} value={`%${source.responseScore}`} bar={source.responseScore * 2} tone={source.responseScore >= 42 ? 'success' : 'warning'} />
                <MiniMetric label={copy.sources.cost} value={`${source.costIndex}`} bar={source.costIndex} tone={source.costIndex <= 45 ? 'success' : source.costIndex <= 65 ? 'warning' : 'danger'} />
                <MiniMetric label={copy.sources.roi} value={`${source.conversion}x`} bar={source.conversion * 8} tone={source.conversion >= 18 ? 'success' : 'primary'} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

function MiniMetric({label, value, bar, tone}: {label: string; value: string; bar: number; tone: 'primary' | 'success' | 'warning' | 'danger'}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-bold text-foreground">{value}</span>
      </div>
      {miniBar(bar, tone)}
    </div>
  );
}

function JobQualityPanel({locale, jobs}: {locale: string; jobs: EmployerJobSummary[]}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const sortedJobs = [...jobs].sort((a, b) => a.qualityScore - b.qualityScore).slice(0, 5);

  return (
    <SurfaceCard className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <StatusBadge tone="warning">{copy.jobQuality.badge}</StatusBadge>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.jobQuality.title}</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.jobQuality.description}</p>
        </div>
        <Link href={`/${locale}/employer/jobs`}>
          <Button type="button" variant="outline" size="sm">{copy.jobQuality.action}</Button>
        </Link>
      </div>

      <div className="space-y-3">
        {sortedJobs.map((job) => (
          <div key={job.id} className="rounded-2xl border border-border bg-surface-muted/50 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={riskTone(job.riskLevel)}>{copy.jobQuality.quality} {job.qualityScore}</StatusBadge>
                  <span className="text-xs font-semibold text-muted-foreground">{job.applicants} {copy.jobQuality.applicants} · {job.qualifiedApplicants} {copy.jobQuality.qualified}</span>
                </div>
                <h3 className="mt-2 truncate text-base font-black text-foreground">{job.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{copy.jobQuality.firstRisk}: {job.riskReasons[0] ?? copy.jobQuality.noRisk}</p>
              </div>
              <ScoreBadge score={job.qualityScore} label={copy.jobQuality.quality} size="sm" />
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <MiniMetric label={copy.jobQuality.conversion} value={`%${job.conversionRate}`} bar={job.conversionRate * 4} tone="primary" />
              <MiniMetric label={copy.jobQuality.match} value={`${job.matchAvg}`} bar={job.matchAvg} tone={job.matchAvg >= 85 ? 'success' : 'warning'} />
              <MiniMetric label={copy.jobQuality.quality} value={`${job.qualityScore}`} bar={job.qualityScore} tone={job.qualityScore >= 80 ? 'success' : job.qualityScore >= 70 ? 'warning' : 'danger'} />
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

function PipelinePanel({locale}: {locale: string}) {
  const copy = getEmployerAnalyticsCopy(locale);

  return (
    <SurfaceCard className="space-y-5">
      <div>
        <StatusBadge tone="ai">{copy.pipeline.badge}</StatusBadge>
        <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.pipeline.title}</h2>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.pipeline.description}</p>
      </div>
      <div className="space-y-3">
        {employerPipelineMock.map((stage) => (
          <div key={stage.id} className="rounded-2xl border border-border bg-surface-muted/50 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-black text-foreground">{stage.label}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{stage.count} {copy.pipeline.candidates} · {stage.targetDays} {copy.pipeline.targetDays}</p>
              </div>
              <StatusBadge tone={stage.overdueCount > 0 ? 'warning' : 'success'}>{stage.overdueCount} {copy.pipeline.overdue}</StatusBadge>
            </div>
            <div className="mt-4">
              <MiniMetric label={copy.pipeline.conversion} value={`%${stage.conversionRate ?? 0}`} bar={stage.conversionRate ?? 0} tone={(stage.conversionRate ?? 0) >= 50 ? 'success' : 'primary'} />
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

function CampaignHealthPanel({locale}: {locale: string}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const labels = {
    ready: copy.campaign.ready,
    review: copy.campaign.review,
    blocked: copy.campaign.blocked,
    response: copy.campaign.response,
  };

  return (
    <SurfaceCard className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <StatusBadge tone="info">{copy.campaign.badge}</StatusBadge>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.campaign.title}</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.campaign.description}</p>
        </div>
        <Link href={`/${locale}/employer/campaigns`}>
          <Button type="button" variant="soft" size="sm">{copy.campaign.action}</Button>
        </Link>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {campaignHealthSignals.map((signal) => (
          <div key={signal.id} className="rounded-2xl border border-border bg-surface-muted/50 p-4">
            <p className="text-xs font-bold text-muted-foreground">{labels[signal.id]}</p>
            <p className="mt-2 text-3xl font-black tracking-[-0.04em] text-foreground">{signal.value}</p>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}

function WeeklyQualityChart({locale}: {locale: string}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const max = Math.max(...employerAnalyticsMock.weeklyApplications.map((point) => point.count));
  const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;

  return (
    <SurfaceCard className="space-y-5">
      <div>
        <StatusBadge tone="success">{copy.chart.badge}</StatusBadge>
        <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{copy.chart.title}</h2>
      </div>
      <div className="grid grid-cols-7 items-end gap-2 rounded-3xl border border-border bg-surface-muted/40 p-4 sm:gap-4">
        {employerAnalyticsMock.weeklyApplications.map((point, index) => (
          <div key={point.day} className="flex min-h-[180px] flex-col justify-end gap-2 text-center">
            <div className="flex flex-1 items-end justify-center gap-1">
              <div className="w-3 rounded-t-xl bg-primary" style={{height: `${Math.max(12, (point.count / max) * 150)}px`}} title={`${copy.chart.applications}: ${point.count}`} />
              <div className="w-3 rounded-t-xl bg-success" style={{height: `${Math.max(10, (point.qualified / max) * 150)}px`}} title={`${copy.chart.qualified}: ${point.qualified}`} />
            </div>
            <p className="text-[11px] font-bold text-muted-foreground">{copy.chart.days[dayKeys[index]]}</p>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 text-xs font-semibold text-muted-foreground">
        <span className="inline-flex items-center gap-2"><span className="size-2 rounded-full bg-primary" />{copy.chart.applications}</span>
        <span className="inline-flex items-center gap-2"><span className="size-2 rounded-full bg-success" />{copy.chart.qualified}</span>
      </div>
    </SurfaceCard>
  );
}

function SidePanels({locale}: {locale: string}) {
  const copy = getEmployerAnalyticsCopy(locale);

  return (
    <div className="space-y-4">
      <SurfaceCard className="space-y-4">
        <StatusBadge tone="ai">{copy.insights.badge}</StatusBadge>
        <h2 className="text-lg font-black text-foreground">{copy.insights.title}</h2>
        <div className="space-y-3">
          {copy.insights.items.map((insight) => (
            <div key={insight.id} className={cn('rounded-2xl border p-4', insightClass(insight.severity))}>
              <p className="text-sm font-black text-foreground">{insight.title}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{insight.description}</p>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] font-bold text-muted-foreground">{insight.impact}</span>
                <Link href={routeHref(locale, insight.href)} className="text-xs font-black text-primary hover:underline">
                  {insight.action}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </SurfaceCard>

      <SurfaceCard className="space-y-4">
        <StatusBadge tone="info">{copy.benchmarks.badge}</StatusBadge>
        <h2 className="text-lg font-black text-foreground">{copy.benchmarks.title}</h2>
        <div className="space-y-3">
          {copy.benchmarks.items.map((item) => (
            <div key={item.label} className="rounded-2xl border border-border bg-surface-muted/50 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-foreground">{item.label}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{copy.benchmarks.benchmark}: {item.benchmark}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-black text-foreground">{item.value}</p>
                  <TrendText positive={item.positive}>{copy.benchmarks.current}</TrendText>
                </div>
              </div>
            </div>
          ))}
        </div>
      </SurfaceCard>

      <SurfaceCard className="space-y-4">
        <StatusBadge tone="success">{copy.boardPack.badge}</StatusBadge>
        <h2 className="text-lg font-black text-foreground">{copy.boardPack.title}</h2>
        <ul className="space-y-3">
          {copy.boardPack.items.map((item) => (
            <li key={item} className="flex gap-3 text-sm leading-6 text-muted-foreground">
              <CheckCircle2 className="mt-1 size-4 shrink-0 text-success" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </SurfaceCard>
    </div>
  );
}

export function EmployerAnalyticsPage({locale = 'tr'}: {locale?: string}) {
  const copy = getEmployerAnalyticsCopy(locale);
  const [period, setPeriod] = useState<AnalyticsPeriod>('30d');
  const [lens, setLens] = useState<AnalyticsLens>('executive');
  const [query, setQuery] = useState('');

  const activeJobs = useMemo(() => employerJobsMock.filter((job) => job.status === 'active'), []);
  const filteredJobs = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return employerJobsMock;
    return employerJobsMock.filter((job) => [job.title, job.department, job.location, ...job.tags].join(' ').toLowerCase().includes(normalized));
  }, [query]);
  const avgMatch = Math.round(employerCandidatesMock.reduce((sum, candidate) => sum + candidate.matchScore, 0) / employerCandidatesMock.length);
  const qualifiedCandidates = employerCandidatesMock.filter((candidate) => candidate.matchScore >= 82).length;
  const overdue = employerPipelineMock.reduce((sum, stage) => sum + stage.overdueCount, 0);
  const executiveScore = getExecutiveScore();

  return (
    <div className="space-y-6 pb-10">
      <SurfaceCard variant="accent" className="relative overflow-hidden p-6 sm:p-7">
        <div className="absolute -right-24 -top-24 size-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px] xl:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai">{copy.page.eyebrow}</StatusBadge>
              <StatusBadge tone="success">{copy.page.operatingScore}: {executiveScore}/100</StatusBadge>
            </div>
            <div className="space-y-3">
              <h1 className="max-w-4xl text-3xl font-black tracking-[-0.06em] text-foreground sm:text-4xl lg:text-5xl">{copy.page.title}</h1>
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{copy.page.description}</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" size="lg"><Download className="size-4" />{copy.page.export}</Button>
              <Button type="button" variant="secondary" size="lg"><RefreshCw className="size-4" />{copy.page.refresh}</Button>
            </div>
          </div>

          <div className="rounded-[28px] border border-border bg-surface/85 p-5 shadow-2xl backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">{copy.page.operatingScore}</p>
                <p className="mt-2 text-5xl font-black tracking-[-0.06em] text-foreground">{executiveScore}</p>
              </div>
              <div className="flex size-16 items-center justify-center rounded-[24px] border border-primary/20 bg-primary/10 text-primary"><Gauge className="size-8" /></div>
            </div>
            <p className="mt-4 text-sm leading-6 text-muted-foreground">{copy.page.operatingScoreHelper}</p>
            <div className="mt-5 grid gap-3">
              <MiniMetric label={copy.metrics.avgMatch.label} value={`${avgMatch}`} bar={avgMatch} tone="success" />
              <MiniMetric label={copy.metrics.activeJobs.label} value={`${activeJobs.length}`} bar={activeJobs.length * 12} tone="primary" />
              <MiniMetric label={copy.metrics.overdue.label} value={`${overdue}`} bar={overdue * 8} tone={overdue > 8 ? 'warning' : 'primary'} />
            </div>
          </div>
        </div>
      </SurfaceCard>

      <SurfaceCard className="p-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-2" aria-label={copy.page.lensLabel}>
            {lensOrder.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setLens(item)}
                className={cn('rounded-2xl border px-4 py-3 text-left transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]', lens === item ? 'border-primary bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'border-border bg-surface-muted text-muted-foreground hover:text-foreground')}
              >
                <span className="block text-sm font-black">{copy.lenses[item].label}</span>
                <span className={cn('mt-1 block text-xs', lens === item ? 'text-primary-foreground/75' : 'text-muted-foreground')}>{copy.lenses[item].description}</span>
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label className="relative min-w-[240px]">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <span className="sr-only">{copy.page.searchLabel}</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={copy.page.searchPlaceholder}
                className="h-12 w-full rounded-2xl border border-border bg-surface-elevated pl-10 pr-4 text-sm font-semibold text-foreground outline-none transition placeholder:text-muted-foreground/60 focus:border-primary/40 focus:ring-4 focus:ring-[var(--ring)]"
              />
            </label>
            <div className="flex rounded-2xl border border-border bg-surface-muted p-1" aria-label={copy.page.periodLabel}>
              {periodOrder.map((item) => (
                <button key={item} type="button" onClick={() => setPeriod(item)} className={cn('rounded-xl px-3 py-2 text-xs font-black transition', period === item ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground')}>
                  {copy.periods[item]}
                </button>
              ))}
            </div>
          </div>
        </div>
      </SurfaceCard>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label={copy.metrics.activeJobs.label} value={activeJobs.length} description={copy.metrics.activeJobs.description} icon={BriefcaseBusiness} trend={{value: 8, positiveDirection: 'up'}} />
        <MetricCard label={copy.metrics.qualifiedCandidates.label} value={qualifiedCandidates} description={copy.metrics.qualifiedCandidates.description} icon={UsersRound} trend={{value: 14, positiveDirection: 'up'}} />
        <MetricCard label={copy.metrics.avgMatch.label} value={avgMatch} description={copy.metrics.avgMatch.description} icon={Target} trend={{value: 4, positiveDirection: 'up'}} />
        <MetricCard label={copy.metrics.overdue.label} value={overdue} description={copy.metrics.overdue.description} icon={AlertTriangle} trend={{value: 7, positiveDirection: 'down'}} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <main className="space-y-6">
          {(lens === 'executive' || lens === 'pipeline') ? <FunnelChart locale={locale} period={period} /> : null}
          {(lens === 'executive' || lens === 'sourcing') ? <SourceQualityMatrix locale={locale} /> : null}
          {(lens === 'executive' || lens === 'quality') ? <JobQualityPanel locale={locale} jobs={filteredJobs} /> : null}
          {lens === 'pipeline' ? <PipelinePanel locale={locale} /> : null}
          {lens === 'sourcing' ? <CampaignHealthPanel locale={locale} /> : null}
          <WeeklyQualityChart locale={locale} />
        </main>
        <aside className="space-y-6 xl:sticky xl:top-24 xl:self-start">
          <SidePanels locale={locale} />
        </aside>
      </div>
    </div>
  );
}
