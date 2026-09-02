import Link from 'next/link';
import {BriefcaseBusiness, Radar, Search, Sparkles, Upload} from 'lucide-react';

import {
  employerActivitiesMock,
  employerAnalyticsMock,
  employerDashboardCandidatesMock,
  employerDashboardMock,
  employerDashboardRiskyJobsMock,
  employerPipelineMock,
} from '@/data/employer-mock-data';
import {
  getEmployerCockpitCopy,
  localizeDashboardActivity,
  localizeDashboardCandidate,
  localizeDashboardJob,
  localizeDashboardMetric,
  localizeHiringHealth,
  localizePipelineStage,
} from '@/lib/employer-cockpit-copy';
import {cn} from '@/lib/utils';

import {ActivityFeed} from './activity-feed';
import {AiCopilotCard} from './ai-copilot-card';
import {CandidateOpportunityList} from './candidate-opportunity-list';
import {EmployerKpiGrid} from './employer-kpi-grid';
import {HiringHealthCard} from './hiring-health-card';
import {JobRiskList} from './job-risk-list';
import {PipelineMini} from './pipeline-mini';

const quickActionIcons = {
  plus: Sparkles,
  upload: Upload,
  search: Search,
} as const;

const quickActionToneClasses = {
  primary: 'border-primary/25 bg-primary/10 text-primary hover:bg-primary/15',
  accent: 'border-violet-500/25 bg-violet-500/10 text-accent hover:bg-violet-500/15',
  success: 'border-emerald-500/25 bg-emerald-500/10 text-success hover:bg-emerald-500/15',
  warning: 'border-amber-500/25 bg-amber-500/10 text-warning hover:bg-amber-500/15',
} as const;

export function EmployerCockpit({locale}: {locale: string}) {
  const copy = getEmployerCockpitCopy(locale);
  const baseHref = `/${locale}/employer`;
  const primaryInsight = employerDashboardMock.insights[0];
  const weeklyTotal = employerAnalyticsMock.weeklyApplications.reduce((sum, point) => sum + point.count, 0);
  const weeklyQualified = employerAnalyticsMock.weeklyApplications.reduce((sum, point) => sum + point.qualified, 0);
  const metrics = employerDashboardMock.metrics.map((metric) => localizeDashboardMetric(metric, locale));
  const hiringHealth = localizeHiringHealth(employerDashboardMock.hiringHealth, locale);
  const riskyJobs = employerDashboardRiskyJobsMock.map((job) => localizeDashboardJob(job, locale));
  const candidates = employerDashboardCandidatesMock.map((candidate) => localizeDashboardCandidate(candidate, locale));
  const pipeline = employerPipelineMock.map((stage) => localizePipelineStage(stage, locale));
  const activities = employerActivitiesMock.map((activity) => localizeDashboardActivity(activity, locale));

  return (
    <div className="space-y-5 sm:space-y-6">
      <section className="relative overflow-hidden rounded-[28px] border border-border sm:rounded-[32px] bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.18),transparent_34%),linear-gradient(135deg,var(--surface-elevated),var(--surface))] p-5 shadow-[0_30px_120px_rgba(0,0,0,0.24)] sm:p-6 lg:p-7">
        <div className="absolute right-10 top-6 hidden rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary lg:block">
          {copy.hero.versionBadge}
        </div>
        <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,420px)]">
          <div className="space-y-6">
            <div className="max-w-4xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 px-3 py-1 text-xs font-semibold text-muted-foreground">
                <Radar className="size-3.5 text-primary" />
                {copy.hero.eyebrow}
              </div>
              <div className="space-y-2">
                <h1 className="text-3xl font-black tracking-[-0.04em] text-foreground sm:text-4xl lg:text-5xl">
                  {copy.hero.titlePrefix} <span className="gradient-text">{copy.hero.titleHighlight}</span> {copy.hero.titleSuffix}
                </h1>
                <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{copy.hero.description}</p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {employerDashboardMock.quickActions.map((action) => {
                const Icon = quickActionIcons[action.icon as keyof typeof quickActionIcons] ?? BriefcaseBusiness;
                const actionCopy = copy.quickActions[action.id as keyof typeof copy.quickActions];
                return (
                  <Link
                    key={action.id}
                    href={localizeEmployerHref(action.href, locale)}
                    className={cn(
                      'group rounded-3xl border p-4 transition hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
                      quickActionToneClasses[action.tone]
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl border border-current/20 bg-current/10">
                        <Icon className="size-5" />
                      </span>
                      <span className="min-w-0 space-y-1">
                        <span className="block text-sm font-bold text-foreground">{actionCopy?.label ?? action.label}</span>
                        <span className="block text-xs leading-5 text-muted-foreground">{actionCopy?.description ?? action.description}</span>
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          <HiringHealthCard health={hiringHealth} copy={copy} />
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(360px,420px)]">
        <AiCopilotCard insight={primaryInsight} baseHref={baseHref} copy={copy} />
        <ApplicationPulse weeklyTotal={weeklyTotal} weeklyQualified={weeklyQualified} copy={copy} />
      </div>

      <EmployerKpiGrid metrics={metrics} copy={copy} />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <JobRiskList jobs={riskyJobs} baseHref={baseHref} copy={copy} />
        <CandidateOpportunityList candidates={candidates} baseHref={baseHref} copy={copy} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,420px)]">
        <PipelineMini stages={pipeline} baseHref={baseHref} copy={copy} />
        <ActivityFeed activities={activities} locale={locale} copy={copy} />
      </div>
    </div>
  );
}

function ApplicationPulse({weeklyTotal, weeklyQualified, copy}: {weeklyTotal: number; weeklyQualified: number; copy: ReturnType<typeof getEmployerCockpitCopy>}) {
  const qualificationRate = Math.round((weeklyQualified / weeklyTotal) * 100);

  return (
    <section className="rounded-[28px] border border-border bg-surface/80 p-5 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-primary">{copy.pulse.eyebrow}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground">
            {weeklyTotal} {copy.pulse.applications}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {weeklyQualified} {copy.pulse.qualified} · %{qualificationRate} {copy.pulse.qualityRate}
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-right">
          <p className="text-xs font-semibold text-success">+18%</p>
          <p className="text-[11px] text-muted-foreground">{copy.pulse.trend}</p>
        </div>
      </div>

      <div className="mt-6 flex h-28 items-end gap-2">
        {employerAnalyticsMock.weeklyApplications.map((point) => {
          const height = Math.max(18, Math.round((point.count / 52) * 100));
          const qualifiedHeight = Math.max(10, Math.round((point.qualified / point.count) * height));
          return (
            <div key={point.day} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <div className="relative flex h-24 w-full items-end overflow-hidden rounded-2xl border border-border bg-surface-muted">
                <div className="w-full rounded-t-2xl bg-primary/30" style={{height: `${height}%`}} />
                <div className="absolute bottom-0 left-0 right-0 rounded-t-2xl bg-primary" style={{height: `${qualifiedHeight}%`}} />
              </div>
              <span className="text-[11px] font-semibold text-muted-foreground">{point.day}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function localizeEmployerHref(href: string, locale: string): string {
  if (href.startsWith(`/${locale}/`)) return href;
  if (href.startsWith('/tr/')) return href.replace('/tr/', `/${locale}/`);
  return href;
}
