'use client';

import {RotateCcw} from 'lucide-react';
import {useTranslations} from 'next-intl';
import {useMemo} from 'react';

import {ProfileCompletionCard} from '@/components/profile/profile-completion-card';
import type {JobListItem} from '@/types/job';

type FilterState = {
  quick: Set<string>;
  companies: Set<string>;
  locations: Set<string>;
};

interface Facet {
  value: string;
  count: number;
}

function buildFacets(jobs: JobListItem[]) {
  const companyMap = new Map<string, number>();
  const locationMap = new Map<string, number>();

  for (const job of jobs) {
    const company = job.company_name?.trim();
    if (company) companyMap.set(company, (companyMap.get(company) ?? 0) + 1);

    const loc = job.location?.trim();
    if (loc) {
      const normalized = loc.split(',')[0].trim();
      if (normalized) locationMap.set(normalized, (locationMap.get(normalized) ?? 0) + 1);
    }
  }

  const toSorted = (map: Map<string, number>): Facet[] =>
    Array.from(map.entries())
      .map(([value, count]) => ({value, count}))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);

  return {
    companies: toSorted(companyMap),
    locations: toSorted(locationMap),
  };
}

const QUICK_FILTERS = [
  {key: 'matched', labelKey: 'matchedOnly'},
  {key: 'remote', labelKey: 'remote'},
  {key: 'new', labelKey: 'newListings'},
  {key: 'fulltime', labelKey: 'fullTime'},
  {key: 'parttime', labelKey: 'partTime'},
  {key: 'internship', labelKey: 'internship'},
] as const;

export function JobFilterSidebar({
  jobs,
  filters,
  onFilterChange,
}: {
  jobs: JobListItem[];
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
}) {
  const t = useTranslations('jobs');
  const facets = useMemo(() => buildFacets(jobs), [jobs]);

  function toggleQuick(key: string) {
    const next = new Set(filters.quick);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onFilterChange({...filters, quick: next});
  }

  function toggleCompany(value: string) {
    const next = new Set(filters.companies);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onFilterChange({...filters, companies: next});
  }

  function toggleLocation(value: string) {
    const next = new Set(filters.locations);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onFilterChange({...filters, locations: next});
  }

  function clearAll() {
    onFilterChange({quick: new Set(), companies: new Set(), locations: new Set()});
  }

  const totalActive = filters.quick.size + filters.companies.size + filters.locations.size;

  return (
    <aside className="space-y-4 overflow-y-auto">
      <ProfileCompletionCard />

      <div className="rounded-xl border border-border bg-surface p-4 space-y-3.5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
            {t('quickFilters')}
          </span>
          {totalActive > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="flex items-center gap-1 text-[11px] text-primary hover:text-primary/80 transition"
            >
              <RotateCcw className="size-2.5" />
              {t('resetFilters')}
            </button>
          )}
        </div>

        {/* Quick filter chips */}
        <div className="flex flex-wrap gap-1.5">
          {QUICK_FILTERS.map((f) => {
            const active = filters.quick.has(f.key);
            return (
              <button
                key={f.key}
                type="button"
                onClick={() => toggleQuick(f.key)}
                className={`inline-flex items-center gap-1.5 rounded-[7px] border px-2.5 py-[5px] text-xs transition ${
                  active
                    ? 'border-primary/40 bg-primary/15 text-primary'
                    : 'border-border/60 bg-surface-muted/30 text-muted-foreground hover:border-primary/25 hover:text-foreground/70'
                }`}
              >
                {t(f.labelKey)}
              </button>
            );
          })}
        </div>

        {/* Location filter */}
        {facets.locations.length > 0 && (
          <>
            <div className="h-px bg-border/40" />
            <FacetGroup
              label={t('locationFilter')}
              facets={facets.locations}
              selected={filters.locations}
              onToggle={toggleLocation}
            />
          </>
        )}

        {/* Company filter */}
        {facets.companies.length > 0 && (
          <>
            <div className="h-px bg-border/40" />
            <FacetGroup
              label={t('companyFilter')}
              facets={facets.companies}
              selected={filters.companies}
              onToggle={toggleCompany}
            />
          </>
        )}
      </div>
    </aside>
  );
}

function FacetGroup({
  label,
  facets,
  selected,
  onToggle,
}: {
  label: string;
  facets: Facet[];
  selected: Set<string>;
  onToggle: (value: string) => void;
}) {
  return (
    <div>
      <div className="mb-1.5 text-[11px] font-medium text-muted-foreground/60">
        {label}
      </div>
      <div className="flex flex-col gap-0.5">
        {facets.map((f) => {
          const active = selected.has(f.value);
          return (
            <button
              key={f.value}
              type="button"
              onClick={() => onToggle(f.value)}
              className={`flex items-center gap-2 rounded-[7px] px-2 py-[6px] text-left text-xs transition ${
                active ? 'bg-primary/10' : 'hover:bg-surface-muted/50'
              }`}
            >
              <span
                className={`flex size-[14px] shrink-0 items-center justify-center rounded-[3px] border transition ${
                  active
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-muted-foreground/25 bg-surface-muted/30'
                }`}
              >
                {active && (
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                    <path d="M1.5 4L3 5.5L6.5 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </span>
              <span className={`flex-1 ${active ? 'text-foreground/70' : 'text-muted-foreground'}`}>
                {f.value}
              </span>
              <span className="text-[11px] text-muted-foreground/30">
                {f.count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export type {FilterState};
