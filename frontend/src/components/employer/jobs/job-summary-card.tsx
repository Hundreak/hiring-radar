import {
  BarChart3,
  BriefcaseBusiness,
  Clock3,
  Eye,
  MapPin,
  MoreHorizontal,
  Pencil,
  Pause,
  Play,
  Sparkles,
  Users,
} from "lucide-react";

import type { EmployerJobStatus, EmployerJobSummary } from "@/types/employer";
import { getEmployerJobsCopy } from "@/lib/employer-jobs-talent-copy";
import { Button } from "@/components/ui/button";
import { ScoreBadge, StatusBadge, SurfaceCard } from "@/components/employer/ui";
import { cn } from "@/lib/utils";

import { JobQualityScore } from "./job-quality-score";
import { JobRiskBadge } from "./job-risk-badge";

const statusTone: Record<
  EmployerJobStatus,
  "success" | "warning" | "neutral" | "info"
> = {
  active: "success",
  paused: "warning",
  closed: "neutral",
  draft: "info",
};

function formatSalary(
  job: EmployerJobSummary,
  copy: ReturnType<typeof getEmployerJobsCopy>,
  locale: string,
) {
  if (!job.salaryRange) return copy.card.salaryRangeMissing;
  const { min, max, currency, visible } = job.salaryRange;
  const formatter = new Intl.NumberFormat(locale === "tr" ? "tr-TR" : "en-US", {
    maximumFractionDigits: 0,
  });
  const suffix = currency === "TRY" ? "₺" : currency;
  return `${visible ? copy.card.salaryVisiblePrefix : copy.card.salaryHiddenPrefix} · ${formatter.format(min)}-${formatter.format(max)} ${suffix}`;
}

export function JobSummaryCard({
  job,
  locale,
}: {
  job: EmployerJobSummary;
  locale: string;
}) {
  const copy = getEmployerJobsCopy(locale);
  const status = {
    label: copy.card.statuses[job.status],
    tone: statusTone[job.status],
  };
  const qualifiedRate =
    job.applicants > 0
      ? Math.round((job.qualifiedApplicants / job.applicants) * 100)
      : 0;

  return (
    <SurfaceCard
      variant="interactive"
      className="group overflow-hidden"
      padding="none"
    >
      <div className="grid gap-0 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="p-5 sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                <JobRiskBadge level={job.riskLevel} locale={locale} />
                <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>
                  {copy.card.aiWatching}
                </StatusBadge>
              </div>

              <div className="flex gap-4">
                <div className="hidden size-12 shrink-0 items-center justify-center rounded-2xl border border-border bg-surface-muted text-primary shadow-sm sm:flex">
                  <BriefcaseBusiness className="size-5" />
                </div>
                <div className="min-w-0">
                  <h3 className="truncate text-xl font-black tracking-[-0.03em] text-foreground">
                    {job.title}
                  </h3>
                  <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
                    <span className="font-semibold text-foreground/85">
                      {job.department}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <MapPin className="size-4" />
                      {job.location}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <Clock3 className="size-4" />
                      {job.postedAt}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex shrink-0 flex-wrap items-center gap-2">
              <Button variant="secondary" size="sm" type="button">
                <Pencil className="size-4" />
                {copy.card.edit}
              </Button>
              <Button variant="soft" size="sm" type="button">
                {job.status === "paused" ? (
                  <Play className="size-4" />
                ) : (
                  <Pause className="size-4" />
                )}
                {job.status === "paused" ? copy.card.publish : copy.card.pause}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                type="button"
                aria-label={copy.card.more}
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-border bg-surface/50 p-4">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                <Users className="size-4" />
                {copy.card.applications}
              </div>
              <div className="mt-2 text-2xl font-black text-foreground">
                {job.applicants}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {job.qualifiedApplicants} {copy.card.qualified} · %
                {qualifiedRate}
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-surface/50 p-4">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                <BarChart3 className="size-4" />
                {copy.card.match}
              </div>
              <div className="mt-2">
                <ScoreBadge score={job.matchAvg} label={copy.card.average} />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {copy.card.strongSignal}
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-surface/50 p-4">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                <Eye className="size-4" />
                {copy.card.views}
              </div>
              <div className="mt-2 text-2xl font-black text-foreground">
                {job.views}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {copy.card.conversion} %{Math.round(job.conversionRate)}
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-surface/50 p-4">
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                {copy.card.salary}
              </div>
              <div
                className={cn(
                  "mt-2 text-sm font-black",
                  job.salaryRange?.visible ? "text-success" : "text-warning",
                )}
              >
                {job.salaryRange?.visible
                  ? copy.card.salaryVisible
                  : copy.card.salaryHidden}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatSalary(job, copy, locale)}
              </p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {job.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-surface-muted px-3 py-1 text-xs font-bold text-muted-foreground"
              >
                {tag}
              </span>
            ))}
          </div>

          {job.riskReasons.length ? (
            <div className="mt-5 rounded-2xl border border-border bg-surface/45 p-4">
              <div className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
                {copy.card.riskSignals}
              </div>
              <ul className="mt-3 grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
                {job.riskReasons.slice(0, 4).map((reason) => (
                  <li key={reason} className="flex gap-2 leading-5">
                    <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <div className="border-t border-border bg-surface/35 p-4 xl:border-l xl:border-t-0">
          <JobQualityScore job={job} compact locale={locale} />
        </div>
      </div>
    </SurfaceCard>
  );
}
