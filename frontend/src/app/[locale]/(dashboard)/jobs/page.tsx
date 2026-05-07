'use client';

import {useCallback, useEffect, useMemo, useState} from 'react';
import {useSearchParams} from 'next/navigation';
import {useTranslations} from 'next-intl';

import {
  JobFilterSidebar,
  createEmptyJobFilters,
  normalizeJobFilters,
  type FilterState,
} from '@/components/jobs/job-filter-sidebar';
import {JobCard} from '@/components/jobs/job-card';
import {Badge} from '@/components/ui/badge';
import {ApiError, api} from '@/lib/api';
import {dispatchSavedJobsChanged, onSavedJobsChanged} from '@/lib/saved-jobs-events';
import type {JobListItem} from '@/types/job';

function formatPostedLabel(job: JobListItem) {
  return job.first_seen_at || job.last_seen_at || '—';
}

function includesIgnoreCase(value: string | null | undefined, query: string): boolean {
  return typeof value === 'string' && value.toLowerCase().includes(query);
}

function buildActiveFilterTotal(filters: FilterState): number {
  return (
    filters.quick.size +
    filters.companies.size +
    filters.locations.size +
    filters.workplaceTypes.size +
    filters.employmentTypes.size +
    filters.seniorities.size +
    filters.keywords.length
  );
}

export default function JobsPage() {
  const t = useTranslations('jobs');
  const searchParams = useSearchParams();

  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(() => createEmptyJobFilters());

  const query = useMemo(() => searchParams.get('q') || '', [searchParams]);

  useEffect(() => {
    let active = true;

    async function loadPageData() {
      setLoading(true);
      setError(null);
      try {
        const [jobsResponse, savedResponse] = await Promise.all([
          api.getJobs(query ? `?q=${encodeURIComponent(query)}` : ''),
          api.getSavedJobs(),
        ]);
        if (!active) return;
        setJobs(jobsResponse.items);
        setSavedJobIds(new Set(savedResponse.items.map((s) => s.job_id)));
      } catch (reason) {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) return;
        setError(reason instanceof Error ? reason.message : 'Request failed.');
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadPageData();
    return () => {
      active = false;
    };
  }, [query]);

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

  const normalizedFilters = useMemo(() => normalizeJobFilters(filters), [filters]);

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
        return Date.now() - firstSeen.getTime() < 3 * 24 * 60 * 60 * 1000;
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
  }, [jobs, normalizedFilters]);

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
        // silent
      }
    },
    [savedJobIds]
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
      </div>
    </div>
  );
}
