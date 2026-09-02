'use client';

import {Suspense, useCallback, useEffect, useMemo, useState} from 'react';
import {useSearchParams} from 'next/navigation';
import {useTranslations} from 'next-intl';

import {
  JobFilterSidebar,
  createEmptyJobFilters,
  normalizeJobFilters,
  type FilterState,
} from '@/components/jobs/job-filter-sidebar';
import {JobCard} from '@/components/jobs/job-card';
import {PaginationControls} from '@/components/ui/pagination-controls';
import {Badge} from '@/components/ui/badge';
import {
  getQueryErrorMessage,
  useJobsQuery,
  useSaveJobMutation,
  useSavedJobsEventBridge,
  useSavedJobsQuery,
  useUnsaveJobMutation,
} from '@/hooks/use-api-queries';
import {DEFAULT_LIST_PAGE_SIZE, DEFAULT_PAGE_SIZE_OPTIONS, createPaginationMeta} from '@/lib/pagination';
import type {JobListItem} from '@/types/job';

function formatPostedLabel(job: JobListItem) {
  return job.first_seen_at || job.last_seen_at || '—';
}

function includesIgnoreCase(value: string | null | undefined, query: string): boolean {
  return typeof value === 'string' && value.toLowerCase().includes(query);
}

function JobsPageContent() {
  const t = useTranslations('jobs');
  const searchParams = useSearchParams();

  const [filters, setFilters] = useState<FilterState>(() => createEmptyJobFilters());
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_LIST_PAGE_SIZE);

  const query = useMemo(() => searchParams.get('q') || '', [searchParams]);
  const jobsQuery = useJobsQuery(query, {page, pageSize});
  const savedJobsQuery = useSavedJobsQuery();
  const saveJobMutation = useSaveJobMutation();
  const unsaveJobMutation = useUnsaveJobMutation();

  useSavedJobsEventBridge();

  const jobs = jobsQuery.data?.items ?? [];
  const paginationMeta = useMemo(
    () => createPaginationMeta({
      page: jobsQuery.data?.page ?? page,
      pageSize: jobsQuery.data?.page_size ?? pageSize,
      totalItems: jobsQuery.data?.total_items ?? jobs.length,
      totalPages: jobsQuery.data?.total_pages ?? null,
    }),
    [jobs.length, jobsQuery.data?.page, jobsQuery.data?.page_size, jobsQuery.data?.total_items, jobsQuery.data?.total_pages, page, pageSize]
  );
  const savedJobIds = useMemo(
    () => new Set((savedJobsQuery.data?.items ?? []).map((savedJob) => savedJob.job_id)),
    [savedJobsQuery.data?.items]
  );
  const loading = jobsQuery.isLoading || savedJobsQuery.isLoading;
  const error = getQueryErrorMessage(jobsQuery.error) ?? getQueryErrorMessage(savedJobsQuery.error);

  const normalizedFilters = useMemo(() => normalizeJobFilters(filters), [filters]);

  // Filtre degisince sayfayi basa al (render sirasinda ayarlama).
  const filterSignature = `${query}|${pageSize}|${JSON.stringify(normalizedFilters)}`;
  const [lastFilterSignature, setLastFilterSignature] = useState(filterSignature);
  if (lastFilterSignature !== filterSignature) {
    setLastFilterSignature(filterSignature);
    setPage(1);
  }

  // "Yeni" filtresi icin referans an. Render sirasinda saat okumak saf
  // degildir ve ayni render icinde farkli sonuc verebilir; oturum basinda
  // bir kez sabitlenir.
  const [sessionNowMs] = useState(() => Date.now());

  const filteredJobs = useMemo(() => {
    let result = jobs;

    if (normalizedFilters.quick.has('matched')) {
      result = result.filter((job) => job.matched);
    }
    if (normalizedFilters.quick.has('remote')) {
      result = result.filter(
        (job) =>
          includesIgnoreCase(job.location, 'remote') ||
          includesIgnoreCase(job.title, 'remote') ||
          includesIgnoreCase(job.workplace_type, 'remote')
      );
    }
    if (normalizedFilters.quick.has('new')) {
      result = result.filter((job) => {
        if (!job.first_seen_at) return false;
        const firstSeen = new Date(job.first_seen_at);
        return sessionNowMs - firstSeen.getTime() < 3 * 24 * 60 * 60 * 1000;
      });
    }
    if (normalizedFilters.quick.has('fulltime')) {
      result = result.filter(
        (job) =>
          includesIgnoreCase(job.employment_type, 'full') ||
          includesIgnoreCase(job.source_name, 'full') ||
          includesIgnoreCase(job.title, 'full-time') ||
          includesIgnoreCase(job.title, 'fulltime')
      );
    }
    if (normalizedFilters.quick.has('parttime')) {
      result = result.filter(
        (job) =>
          includesIgnoreCase(job.employment_type, 'part') ||
          includesIgnoreCase(job.title, 'part-time') ||
          includesIgnoreCase(job.title, 'parttime') ||
          includesIgnoreCase(job.title, 'part time')
      );
    }
    if (normalizedFilters.quick.has('internship')) {
      result = result.filter(
        (job) =>
          includesIgnoreCase(job.seniority, 'intern') ||
          includesIgnoreCase(job.title, 'intern') ||
          includesIgnoreCase(job.title, 'staj') ||
          includesIgnoreCase(job.title, 'praktikum')
      );
    }

    if (normalizedFilters.companies.size > 0) {
      result = result.filter((job) => {
        const company = job.company_name?.trim();
        return Boolean(company && normalizedFilters.companies.has(company));
      });
    }

    if (normalizedFilters.locations.size > 0) {
      result = result.filter((job) => {
        const location = job.location?.trim();
        if (!location) return false;
        const normalizedLocation = location.split(',')[0].trim();
        return normalizedFilters.locations.has(normalizedLocation);
      });
    }

    if (normalizedFilters.workplaceTypes.size > 0) {
      result = result.filter((job) => {
        const workplaceType = job.workplace_type?.trim();
        return Boolean(workplaceType && normalizedFilters.workplaceTypes.has(workplaceType));
      });
    }

    if (normalizedFilters.employmentTypes.size > 0) {
      result = result.filter((job) => {
        const employmentType = job.employment_type?.trim();
        return Boolean(employmentType && normalizedFilters.employmentTypes.has(employmentType));
      });
    }

    if (normalizedFilters.seniorities.size > 0) {
      result = result.filter((job) => {
        const seniority = job.seniority?.trim();
        return Boolean(seniority && normalizedFilters.seniorities.has(seniority));
      });
    }

    if (normalizedFilters.keywords.length > 0) {
      const keywordQueries = normalizedFilters.keywords.map((keyword) => keyword.toLowerCase());
      result = result.filter((job) => {
        const haystack = [
          job.title,
          job.company_name,
          job.location,
          job.source_name,
          job.workplace_type,
          job.employment_type,
          job.seniority,
          ...(Array.isArray(job.matched_keywords) ? job.matched_keywords : []),
        ]
          .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
          .join(' ')
          .toLowerCase();

        return keywordQueries.every((keyword) => haystack.includes(keyword));
      });
    }

    return result;
  }, [jobs, normalizedFilters, sessionNowMs]);

  const handleToggleSave = useCallback(
    async (jobId: number, matchScore?: number) => {
      const isSaved = savedJobIds.has(jobId);
      try {
        if (isSaved) {
          await unsaveJobMutation.mutateAsync(jobId);
        } else {
          await saveJobMutation.mutateAsync({jobId, matchScore});
        }
      } catch {
        // silent
      }
    },
    [saveJobMutation, savedJobIds, unsaveJobMutation]
  );

  const activeFilterLabels = useMemo(() => {
    const labels: {key: string; label: string; clear: () => void}[] = [];
    const labelMap: Record<string, string> = {
      matched: t('matchedOnly'),
      remote: t('remote'),
      new: t('newListings'),
      fulltime: t('fullTime'),
      parttime: t('partTime'),
      internship: t('internship'),
    };

    for (const key of normalizedFilters.quick) {
      labels.push({
        key: `quick:${key}`,
        label: labelMap[key] ?? key,
        clear: () => {
          const next = new Set(normalizedFilters.quick);
          next.delete(key);
          setFilters({...normalizedFilters, quick: next});
        },
      });
    }
    for (const value of normalizedFilters.companies) {
      labels.push({
        key: `company:${value}`,
        label: value,
        clear: () => {
          const next = new Set(normalizedFilters.companies);
          next.delete(value);
          setFilters({...normalizedFilters, companies: next});
        },
      });
    }
    for (const value of normalizedFilters.locations) {
      labels.push({
        key: `location:${value}`,
        label: value,
        clear: () => {
          const next = new Set(normalizedFilters.locations);
          next.delete(value);
          setFilters({...normalizedFilters, locations: next});
        },
      });
    }
    for (const value of normalizedFilters.workplaceTypes) {
      labels.push({
        key: `workplace:${value}`,
        label: value,
        clear: () => {
          const next = new Set(normalizedFilters.workplaceTypes);
          next.delete(value);
          setFilters({...normalizedFilters, workplaceTypes: next});
        },
      });
    }
    for (const value of normalizedFilters.employmentTypes) {
      labels.push({
        key: `employment:${value}`,
        label: value,
        clear: () => {
          const next = new Set(normalizedFilters.employmentTypes);
          next.delete(value);
          setFilters({...normalizedFilters, employmentTypes: next});
        },
      });
    }
    for (const value of normalizedFilters.seniorities) {
      labels.push({
        key: `seniority:${value}`,
        label: value,
        clear: () => {
          const next = new Set(normalizedFilters.seniorities);
          next.delete(value);
          setFilters({...normalizedFilters, seniorities: next});
        },
      });
    }
    for (const value of normalizedFilters.keywords) {
      labels.push({
        key: `keyword:${value}`,
        label: value,
        clear: () => {
          setFilters({
            ...normalizedFilters,
            keywords: normalizedFilters.keywords.filter((keyword) => keyword !== value),
          });
        },
      });
    }
    return labels;
  }, [normalizedFilters, t]);

  return (
    <div className="grid jobs-grid gap-6">
      <JobFilterSidebar
        jobs={jobs}
        filters={normalizedFilters}
        onFilterChange={setFilters}
      />

      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold tracking-tight">{t('title')}</h1>
            <p className="text-xs text-muted-foreground">{t('description')}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="success" className="gap-1">
              <span className="size-1.5 rounded-full bg-success animate-pulse-dot" />
              {t('liveFeed')}
            </Badge>
            <Badge>{t('resultCount', {count: filteredJobs.length})}</Badge>
          </div>
        </div>

        {activeFilterLabels.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-muted-foreground">{t('activeFilters')}:</span>
            {activeFilterLabels.map((filter) => (
              <button
                key={filter.key}
                type="button"
                onClick={filter.clear}
                className="inline-flex items-center gap-1 rounded bg-primary/10 border border-primary/25 px-2 py-0.5 text-[11px] text-secondary-foreground hover:bg-primary/20"
              >
                {filter.label}
                <span className="opacity-60">×</span>
              </button>
            ))}
          </div>
        )}

        <PaginationControls
          meta={paginationMeta}
          labels={{
            previous: t('paginationPrevious'),
            next: t('paginationNext'),
            pageSize: t('paginationPageSize'),
            summary: ({start, end, total}) => t('paginationSummary', {start, end, total}),
          }}
          pageSizeOptions={DEFAULT_PAGE_SIZE_OPTIONS}
          onPageChange={setPage}
          onPageSizeChange={(nextPageSize) => {
            setPageSize(nextPageSize);
            setPage(1);
          }}
        />

        {loading ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
            {t('loadingJobs')}
          </div>
        ) : error ? (
          <div className="rounded-xl border border-danger/30 bg-danger/5 p-8 text-sm text-danger">
            {error}
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
            {t('noJobs')}
          </div>
        ) : (
          <div className="grid gap-2.5 xl:grid-cols-2">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={{
                  id: String(job.id),
                  title: job.title,
                  company: job.company_name,
                  location: job.location || '—',
                  workModel: job.workplace_type
                    ? job.workplace_type.replaceAll('_', ' ')
                    : job.location?.toLowerCase().includes('remote')
                      ? 'Remote'
                      : 'Onsite',
                  contractType: job.employment_type || job.source_name,
                  tags: Array.isArray(job.matched_keywords) && job.matched_keywords.length > 0
                    ? job.matched_keywords
                    : [job.source_name],
                  postedLabel: formatPostedLabel(job),
                  matched: job.matched,
                  matchScore: job.match_score ?? undefined,
                  matchedKeywords: Array.isArray(job.matched_keywords) ? job.matched_keywords : [],
                  explanation: job.explanation ?? null,
                  href: job.canonical_url,
                  saved: savedJobIds.has(job.id),
                  onToggleSave: () => handleToggleSave(job.id, job.match_score ?? undefined),
                }}
              />
            ))}
          </div>
        )}

        {!loading && !error && paginationMeta.totalPages > 1 ? (
          <PaginationControls
            meta={paginationMeta}
            labels={{
              previous: t('paginationPrevious'),
              next: t('paginationNext'),
              pageSize: t('paginationPageSize'),
              summary: ({start, end, total}) => t('paginationSummary', {start, end, total}),
            }}
            onPageChange={setPage}
          />
        ) : null}
      </div>
    </div>
  );
}


export default function JobsPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-3xl border border-border bg-surface p-6 text-sm text-muted-foreground">
          Loading jobs…
        </div>
      }
    >
      <JobsPageContent />
    </Suspense>
  );
}
