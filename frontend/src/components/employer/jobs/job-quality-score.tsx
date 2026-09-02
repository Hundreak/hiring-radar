import {
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  Info,
  Lightbulb,
  ShieldCheck,
} from "lucide-react";

import type { EmployerJobSummary, EmployerRiskLevel } from "@/types/employer";
import { getEmployerJobsCopy } from "@/lib/employer-jobs-talent-copy";
import { Button } from "@/components/ui/button";
import { ScoreBadge, StatusBadge, SurfaceCard } from "@/components/employer/ui";
import { cn } from "@/lib/utils";

function factorTone(status: EmployerRiskLevel) {
  if (status === "healthy")
    return "text-success bg-emerald-500/10 border-emerald-500/20";
  if (status === "watch")
    return "text-blue-300 bg-blue-500/10 border-blue-500/20";
  if (status === "risk")
    return "text-warning bg-amber-500/10 border-amber-500/25";
  return "text-danger bg-red-500/10 border-red-500/25";
}

function factorIcon(status: EmployerRiskLevel) {
  if (status === "healthy") return CheckCircle2;
  if (status === "watch") return Info;
  return CircleAlert;
}

export function JobQualityScore({
  job,
  compact = false,
  locale,
}: {
  job: EmployerJobSummary;
  compact?: boolean;
  locale: string;
}) {
  const copy = getEmployerJobsCopy(locale);
  const riskCount = job.qualityFactors.filter(
    (factor) => factor.status === "risk" || factor.status === "critical",
  ).length;
  const watchCount = job.qualityFactors.filter(
    (factor) => factor.status === "watch",
  ).length;

  return (
    <SurfaceCard
      variant="accent"
      padding={compact ? "sm" : "md"}
      className="relative overflow-hidden"
    >
      <div
        className="absolute right-0 top-0 size-36 rounded-full bg-accent/10 blur-3xl"
        aria-hidden="true"
      />
      <div className="relative space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <StatusBadge tone="ai" icon={<ShieldCheck className="size-3.5" />}>
              {copy.quality.badge}
            </StatusBadge>
            <div>
              <h3 className="text-base font-black tracking-[-0.02em] text-foreground">
                {job.title}
              </h3>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {copy.quality.description}
              </p>
            </div>
          </div>
          <ScoreBadge
            score={job.qualityScore}
            label={copy.quality.scoreLabel}
            size={compact ? "md" : "lg"}
          />
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface/60 p-3">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
              {copy.quality.risk}
            </div>
            <div className="mt-1 text-lg font-black text-foreground">
              {riskCount}
            </div>
          </div>
          <div className="rounded-2xl border border-border bg-surface/60 p-3">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
              {copy.quality.watch}
            </div>
            <div className="mt-1 text-lg font-black text-foreground">
              {watchCount}
            </div>
          </div>
          <div className="rounded-2xl border border-border bg-surface/60 p-3">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted-foreground">
              {copy.quality.conversion}
            </div>
            <div className="mt-1 text-lg font-black text-foreground">
              %{Math.round(job.conversionRate)}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          {job.qualityFactors.slice(0, compact ? 2 : 3).map((factor) => {
            const Icon = factorIcon(factor.status);
            return (
              <div
                key={factor.id}
                className="rounded-2xl border border-border bg-surface/55 p-3"
              >
                <div className="flex items-start gap-3">
                  <span
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center rounded-xl border",
                      factorTone(factor.status),
                    )}
                  >
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-bold text-foreground">
                        {factor.label}
                      </p>
                      <span className="text-xs font-black tabular-nums text-muted-foreground">
                        {factor.score}/100
                      </span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">
                      {factor.description}
                    </p>
                    {!compact && factor.recommendation ? (
                      <p className="mt-2 inline-flex items-start gap-1.5 rounded-xl bg-accent-soft px-2.5 py-1.5 text-xs font-semibold leading-5 text-accent">
                        <Lightbulb className="mt-0.5 size-3.5 shrink-0" />
                        {factor.recommendation}
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {!compact ? (
          <div className="flex flex-wrap gap-2 border-t border-border/70 pt-4">
            <Button size="sm" type="button">
              {copy.quality.optimize}
              <ArrowRight className="size-4" />
            </Button>
            <Button size="sm" variant="secondary" type="button">
              {copy.quality.preview}
            </Button>
          </div>
        ) : null}
      </div>
    </SurfaceCard>
  );
}
