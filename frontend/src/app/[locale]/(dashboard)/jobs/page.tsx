'use client';

import {useCallback, useEffect, useMemo, useState} from 'react';
import {useSearchParams} from 'next/navigation';
import {useTranslations} from 'next-intl';

import {JobCard} from '@/components/jobs/job-card';
import {JobFilterSidebar} from '@/components/jobs/job-filter-sidebar';
import type {FilterState} from '@/components/jobs/job-filter-sidebar';
import {Badge} from '@/components/ui/badge';
import {ApiError, api} from '@/lib/api';
import {dispatchSavedJobsChanged, onSavedJobsChanged} from '@/lib/saved-jobs-events';
import type {JobListItem} from '@/types/job';

function formatPostedLabel(job: JobListItem) {
  return job.first_seen_at || job.last_seen_at || '—';
}

const EMPTY_FILTERS: FilterState = {
  quick: new Set(),
  companies: new Set(),
  locations: new Set(),
};

export default function JobsPage() {
  const t = useTranslations('jobs');
  const searchParams = useSearchParams();

  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);

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
    return () => { active = false; };
  }, [query]);

  // Sync saved state from other pages (saved page, matches page)
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

  const filteredJobs = useMemo(() => {
    let result = jobs;

    // Quick filters
    if (filters.quick.has('matched')) {
      result = result.filter((j) => j.matched);
    }
    if (filters.quick.has('remote')) {
      result = result.filter(
        (j) =>
          j.location?.toLowerCase().includes('remote') ||
          j.title.toLowerCase().includes('remote')
      );
    }
    if (filters.quick.has('new')) {
      result = result.filter((j) => {
        if (!j.first_seen_at) return false;
        const d = new Date(j.first_seen_at);
        return Date.now() - d.getTime() < 3 * 24 * 60 * 60 * 1000;
      });
    }
    if (filters.quick.has('fulltime')) {
      result = result.filter(
        (j) =>
          j.source_name?.toLowerCase().includes('full') ||
          j.title.toLowerCase().includes('full-time') ||
          j.title.toLowerCase().includes('fulltime')
      );
    }
    if (filters.quick.has('parttime')) {
      result = result.filter(
        (j) =>
          j.title.toLowerCase().includes('part-time') ||
          j.title.toLowerCase().includes('parttime') ||
          j.title.toLowerCase().includes('part time')
      );
    }
    if (filters.quick.has('internship')) {
      result = result.filter(
        (j) =>
          j.title.toLowerCase().includes('intern') ||
          j.title.toLowerCase().includes('staj') ||
          j.title.toLowerCase().includes('praktikum')
      );
    }

    // Company filter
    if (filters.companies.size > 0) {
      result = result.filter((j) => {
        const company = j.company_name?.trim();
        return company && filters.companies.has(company);
      });
    }

    // Location filter
    if (filters.locations.size > 0) {
      result = result.filter((j) => {
        const loc = j.location?.trim();
        if (!loc) return false;
        const normalized = loc.split(',')[0].trim();
        return filters.locations.has(normalized);
      });
    }

    return result;
  }, [jobs, filters]);

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

  const totalActive = filters.quick.size + filters.companies.size + filters.locations.size;

  const activeFilterLabels = useMemo(() => {
    const labels: {key: string; label: string; clear: () => void}[] = [];
    for (const key of filters.quick) {
      const labelMap: Record<string, string> = {
        matched: t('matchedOnly'),
        remote: t('remote'),
        new: t('newListings'),
        fulltime: t('fullTime'),
        parttime: t('partTime'),
        internship: t('internship'),
      };
      labels.push({
        key: `quick:${key}`,
        label: labelMap[key] ?? key,
        clear: () => {
          const next = new Set(filters.quick);
          next.delete(key);
          setFilters({...filters, quick: next});
        },
      });
    }
    for (const value of filters.companies) {
      labels.push({
        key: `company:${value}`,
        label: value,
        clear: () => {
          const next = new Set(filters.companies);
          next.delete(value);
          setFilters({...filters, companies: next});
        },
      });
    }
    for (const value of filters.locations) {
      labels.push({
        key: `location:${value}`,
        label: value,
        clear: () => {
          const next = new Set(filters.locations);
          next.delete(value);
          setFilters({...filters, locations: next});
        },
      });
    }
    return labels;
  }, [filters, t]);

  return (
    <div className="grid jobs-grid gap-6">
      <JobFilterSidebar
        jobs={jobs}
        filters={filters}
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
            {activeFilterLabels.map((f) => (
              <button
                key={f.key}
                type="button"
                onClick={f.clear}
                className="inline-flex items-center gap-1 rounded bg-primary/10 border border-primary/25 px-2 py-0.5 text-[11px] text-secondary-foreground hover:bg-primary/20"
              >
                {f.label}
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
                  workModel: job.location?.toLowerCase().includes('remote')
                    ? 'Remote'
                    : 'Onsite',
                  contractType: job.source_name,
                  tags: job.matched_keywords.length > 0
                    ? job.matched_keywords
                    : [job.source_name],
                  postedLabel: formatPostedLabel(job),
                  matched: job.matched,
                  matchScore: job.match_score ?? undefined,
                  matchedKeywords: job.matched_keywords,
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
