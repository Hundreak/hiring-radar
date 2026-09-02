"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  Filter,
  Plus,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PaginationControls } from "@/components/ui/pagination-controls";
import {
  EmptyState,
  MetricCard,
  SectionHeader,
  StatusBadge,
  SurfaceCard,
} from "@/components/employer/ui";
import { employerJobsMock } from "@/data/employer-jobs.mock";
import { getEmployerJobsCopy } from "@/lib/employer-jobs-talent-copy";
import type { EmployerJobStatus, EmployerRiskLevel } from "@/types/employer";
import {
  DEFAULT_EMPLOYER_PAGE_SIZE,
  DEFAULT_PAGE_SIZE_OPTIONS,
  createPaginationMeta,
  paginateClientItems,
} from "@/lib/pagination";
import { cn } from "@/lib/utils";

import { JobQualityScore } from "./job-quality-score";
import { JobRiskBadge } from "./job-risk-badge";
import { JobSummaryCard } from "./job-summary-card";

export function EmployerJobsPage({ locale }: { locale: string }) {
  const copy = getEmployerJobsCopy(locale);
  const statusFilters = copy.filters.status as Array<{
    label: string;
    value: EmployerJobStatus | "all";
  }>;
  const riskFilters = copy.filters.risks as Array<{
    label: string;
    value: EmployerRiskLevel | "all";
  }>;
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<EmployerJobStatus | "all">("all");
  const [risk, setRisk] = useState<EmployerRiskLevel | "all">("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_EMPLOYER_PAGE_SIZE);
  const [selectedJobId, setSelectedJobId] = useState(
    employerJobsMock[0]?.id ?? 0,
  );

  const selectedJob =
    employerJobsMock.find((job) => job.id === selectedJobId) ??
    employerJobsMock[0];

  const filteredJobs = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase("tr-TR");
    return employerJobsMock.filter((job) => {
      const matchesSearch =
        !normalizedSearch ||
        [job.title, job.department, job.location, ...job.tags]
          .join(" ")
          .toLocaleLowerCase("tr-TR")
          .includes(normalizedSearch);
      const matchesStatus = status === "all" || job.status === status;
      const matchesRisk = risk === "all" || job.riskLevel === risk;
      return matchesSearch && matchesStatus && matchesRisk;
    });
  }, [search, status, risk]);

  const paginationMeta = useMemo(
    () => createPaginationMeta({
      page,
      pageSize,
      totalItems: filteredJobs.length,
      totalPages: filteredJobs.length === 0 ? 0 : Math.ceil(filteredJobs.length / pageSize),
    }),
    [filteredJobs.length, page, pageSize],
  );

  const pagedJobs = useMemo(
    () => paginateClientItems(filteredJobs, paginationMeta.page, paginationMeta.pageSize),
    [filteredJobs, paginationMeta.page, paginationMeta.pageSize],
  );

  useEffect(() => {
    setPage(1);
  }, [search, status, risk, pageSize]);

  const activeJobs = employerJobsMock.filter((job) => job.status === "active");
  const riskyJobs = employerJobsMock.filter(
    (job) => job.riskLevel === "risk" || job.riskLevel === "critical",
  );
  const averageQuality = Math.round(
    employerJobsMock.reduce((total, job) => total + job.qualityScore, 0) /
      employerJobsMock.length,
  );
  const qualifiedApplicants = employerJobsMock.reduce(
    (total, job) => total + job.qualifiedApplicants,
    0,
  );
  const totalApplicants = employerJobsMock.reduce(
    (total, job) => total + job.applicants,
    0,
  );
  const bestOpportunity = [...employerJobsMock].sort(
    (a, b) => b.qualityScore + b.matchAvg - (a.qualityScore + a.matchAvg),
  )[0];

  return (
    <div className="space-y-6 sm:space-y-8">
      <section className="relative overflow-hidden rounded-[28px] border border-border sm:rounded-[34px] bg-[linear-gradient(135deg,color-mix(in_srgb,var(--surface-elevated)_95%,transparent),color-mix(in_srgb,var(--primary)_10%,transparent))] p-5 shadow-[var(--shadow-card)] sm:p-7">
        <div
          className="absolute right-0 top-0 size-72 rounded-full bg-primary/10 blur-3xl"
          aria-hidden="true"
        />
        <div
          className="absolute bottom-0 left-1/3 size-56 rounded-full bg-accent/10 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,420px)] xl:items-end">
          <div className="max-w-4xl space-y-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>
                {copy.page.aiReady}
              </StatusBadge>
              <StatusBadge
                tone="success"
                icon={<CheckCircle2 className="size-3.5" />}
              >
                {copy.page.themeActive}
              </StatusBadge>
              <StatusBadge tone="info">{copy.page.releaseBadge}</StatusBadge>
            </div>
            <div className="space-y-3">
              <h1 className="max-w-3xl text-3xl font-black tracking-[-0.055em] text-foreground sm:text-5xl">
                {copy.page.title}
              </h1>
              <p className="max-w-3xl text-base leading-7 text-muted-foreground sm:text-lg">
                {copy.page.description}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" type="button">
                <Plus className="size-4" />
                {copy.page.newJob}
              </Button>
              <Button size="lg" variant="secondary" type="button">
                <ShieldCheck className="size-4" />
                {copy.page.optimizeAll}
              </Button>
            </div>
          </div>

          {bestOpportunity ? (
            <SurfaceCard variant="elevated" className="bg-surface/65">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">
                    {copy.page.opportunity}
                  </p>
                  <h2 className="mt-2 text-xl font-black tracking-[-0.03em] text-foreground">
                    {bestOpportunity.title}
                  </h2>
                </div>
                <JobRiskBadge level={bestOpportunity.riskLevel} locale={locale} />
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {copy.page.opportunityText(
                  bestOpportunity.qualityScore,
                  bestOpportunity.matchAvg,
                )}
              </p>
              <Button className="mt-5 w-full" variant="soft" type="button">
                {copy.page.openOpportunity}
                <ArrowRight className="size-4" />
              </Button>
            </SurfaceCard>
          ) : null}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <MetricCard
          label={copy.page.activeJobs}
          value={activeJobs.length}
          description={copy.page.activeJobsDesc}
          icon={BriefcaseBusiness}
          trend={{ value: 12, label: copy.metricTrends.week }}
        />
        <MetricCard
          label={copy.page.qualifiedCandidates}
          value={qualifiedApplicants}
          description={copy.page.totalApplicants(totalApplicants)}
          icon={CheckCircle2}
          trend={{ value: 18, label: copy.metricTrends.quality }}
        />
        <MetricCard
          label={copy.page.averageQuality}
          value={`${averageQuality}/100`}
          description={copy.page.averageQualityDesc}
          icon={ShieldCheck}
          trend={{ value: 7, label: copy.metricTrends.improved }}
        />
        <MetricCard
          label={copy.page.riskyJobs}
          value={riskyJobs.length}
          description={copy.page.riskyJobsDesc}
          icon={TrendingUp}
          trend={{
            value: -9,
            label: copy.metricTrends.risk,
            positiveDirection: "down",
          }}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,420px)]">
        <div className="space-y-5">
          <SectionHeader
            eyebrow={copy.page.portfolioEyebrow}
            title={copy.page.portfolioTitle}
            description={copy.page.portfolioDesc}
            action={
              <Button variant="secondary" type="button">
                <SlidersHorizontal className="size-4" />
                {copy.page.customizeView}
              </Button>
            }
          />

          <SurfaceCard className="space-y-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="relative min-w-0 flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={copy.page.searchPlaceholder}
                  className="comfort-input h-12 w-full rounded-2xl pl-11 pr-4 text-sm"
                  type="search"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {statusFilters.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setStatus(item.value)}
                    className={cn(
                      "rounded-2xl border px-3.5 py-2 text-xs font-black transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]",
                      status === item.value
                        ? "border-primary/35 bg-secondary text-secondary-foreground"
                        : "border-border bg-surface text-muted-foreground hover:border-border-strong hover:text-foreground",
                    )}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-border/70 pt-4">
              <span className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">
                <Filter className="size-3.5" />
                {copy.page.riskFilter}
              </span>
              {riskFilters.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => setRisk(item.value)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-bold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]",
                    risk === item.value
                      ? "border-accent/35 bg-accent-soft text-accent"
                      : "border-border bg-surface/50 text-muted-foreground hover:border-border-strong hover:text-foreground",
                  )}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </SurfaceCard>

          <PaginationControls
            meta={paginationMeta}
            labels={{
              previous: copy.pagination.previous,
              next: copy.pagination.next,
              pageSize: copy.pagination.pageSize,
              summary: ({ start, end, total }) => copy.pagination.summary(start, end, total),
            }}
            pageSizeOptions={DEFAULT_PAGE_SIZE_OPTIONS}
            onPageChange={setPage}
            onPageSizeChange={(nextPageSize) => {
              setPageSize(nextPageSize);
              setPage(1);
            }}
          />

          {filteredJobs.length ? (
            <div className="space-y-4">
              {pagedJobs.map((job) => (
                <div
                  key={job.id}
                  onMouseEnter={() => setSelectedJobId(job.id)}
                  onFocus={() => setSelectedJobId(job.id)}
                >
                  <JobSummaryCard job={job} locale={locale} />
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title={copy.page.noResultsTitle}
              description={copy.page.noResultsDesc}
              action={{
                label: copy.page.clearFilters,
                onClick: () => {
                  setSearch("");
                  setStatus("all");
                  setRisk("all");
                },
              }}
            />
          )}

          {filteredJobs.length > pageSize ? (
            <PaginationControls
              meta={paginationMeta}
              labels={{
                previous: copy.pagination.previous,
                next: copy.pagination.next,
                pageSize: copy.pagination.pageSize,
                summary: ({ start, end, total }) => copy.pagination.summary(start, end, total),
              }}
              onPageChange={setPage}
            />
          ) : null}
        </div>

        <aside className="space-y-5 xl:sticky xl:top-28 xl:self-start">
          {selectedJob ? (
            <JobQualityScore job={selectedJob} locale={locale} />
          ) : null}

          <SurfaceCard>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-muted-foreground">
                  {copy.page.quickActionsEyebrow}
                </p>
                <h3 className="mt-1 text-lg font-black tracking-[-0.03em] text-foreground">
                  {copy.page.quickActionsTitle}
                </h3>
              </div>
              <Sparkles className="size-5 text-primary" />
            </div>
            <div className="mt-4 space-y-3">
              {copy.page.quickActions.map((action) => (
                <button
                  key={action}
                  type="button"
                  className="flex w-full items-center justify-between gap-3 rounded-2xl border border-border bg-surface/50 p-3 text-left text-sm font-semibold text-foreground transition hover:border-primary/30 hover:bg-surface-strong focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
                >
                  <span>{action}</span>
                  <ArrowRight className="size-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          </SurfaceCard>
        </aside>
      </section>
    </div>
  );
}
