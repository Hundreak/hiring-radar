import Link from 'next/link';
import {ArrowRight, BriefcaseBusiness, Eye, UsersRound} from 'lucide-react';

import {ScoreBadge, SectionHeader, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import type {EmployerJobSummary, EmployerRiskLevel} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';

const riskTone: Record<EmployerRiskLevel, 'neutral' | 'success' | 'warning' | 'danger' | 'info'> = {
  healthy: 'success',
  watch: 'warning',
  risk: 'danger',
  critical: 'danger',
};

export function JobRiskList({jobs, baseHref, copy}: {jobs: EmployerJobSummary[]; baseHref: string; copy: EmployerCockpitCopy}) {
  return (
    <SurfaceCard className="space-y-5">
      <SectionHeader
        eyebrow={copy.jobs.eyebrow}
        title={copy.jobs.title}
        description={copy.jobs.description}
        action={
          <Link href={`${baseHref}/jobs`} className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
            {copy.jobs.viewAll} <ArrowRight className="size-4" />
          </Link>
        }
      />

      <div className="grid gap-3">
        {jobs.slice(0, 4).map((job) => {
          return (
            <Link
              key={job.id}
              href={`${baseHref}/jobs?job=${job.slug}`}
              className="group rounded-[24px] border border-border bg-surface/70 p-4 transition hover:-translate-y-0.5 hover:border-primary/25 hover:bg-surface-muted/70 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl border border-border bg-surface-muted text-primary">
                      <BriefcaseBusiness className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-sm font-bold text-foreground">{job.title}</h3>
                      <p className="text-xs text-muted-foreground">{job.department} · {job.location} · {job.postedAt}</p>
                    </div>
                    <StatusBadge tone={riskTone[job.riskLevel]}>{copy.jobs.risks[job.riskLevel]}</StatusBadge>
                  </div>

                  <div className="grid gap-2 sm:grid-cols-3">
                    <MiniMetric icon={<UsersRound className="size-3.5" />} label={copy.jobs.applicants} value={`${job.applicants}`} />
                    <MiniMetric icon={<UsersRound className="size-3.5" />} label={copy.jobs.qualified} value={`${job.qualifiedApplicants}`} />
                    <MiniMetric icon={<Eye className="size-3.5" />} label={copy.jobs.conversion} value={`%${job.conversionRate}`} />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {job.riskReasons.slice(0, 3).map((reason) => (
                      <span key={reason} className="rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {reason}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 lg:w-40 lg:flex-col lg:items-end">
                  <ScoreBadge score={job.qualityScore} label={copy.jobs.quality} />
                  <div className="text-right">
                    <p className="text-sm font-bold text-foreground">%{job.matchAvg}</p>
                    <p className="text-[11px] text-muted-foreground">{copy.jobs.avgMatch}</p>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </SurfaceCard>
  );
}

function MiniMetric({icon, label, value}: {icon: React.ReactNode; label: string; value: string}) {
  return (
    <div className="rounded-2xl border border-border bg-surface/80 px-3 py-2">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-sm font-bold text-foreground">{value}</p>
    </div>
  );
}
