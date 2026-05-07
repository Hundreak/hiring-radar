'use client';

import {Filter, RotateCcw, Search, X} from 'lucide-react';
import {useMessages, useTranslations} from 'next-intl';
import {useMemo, useState} from 'react';

import {ProfileCompletionCard} from '@/components/profile/profile-completion-card';
import type {JobListItem} from '@/types/job';

export type FilterState = {
  quick: Set<string>;
  companies: Set<string>;
  locations: Set<string>;
  workplaceTypes: Set<string>;
  employmentTypes: Set<string>;
  seniorities: Set<string>;
  keywords: string[];
};

interface Facet {
  value: string;
  count: number;
}

type FacetCollection = {
  companies: Facet[];
  locations: Facet[];
  workplaceTypes: Facet[];
  employmentTypes: Facet[];
  seniorities: Facet[];
};

type JobCopyKey =
  | 'filtersPanelTitle'
  | 'filtersPanelDescription'
  | 'resetFilters'
  | 'keywordFilterTitle'
  | 'keywordInputPlaceholder'
  | 'keywordInputHelp'
  | 'quickFilters'
  | 'matchedOnly'
  | 'remote'
  | 'newListings'
  | 'fullTime'
  | 'partTime'
  | 'internship'
  | 'locationFilter'
  | 'companyFilter'
  | 'workplaceFilter'
  | 'employmentTypeFilter'
  | 'seniorityFilter'
  | 'facetSearchPlaceholder'
  | 'noFacetMatches';

const JOB_COPY_FALLBACKS: Record<JobCopyKey, string> = {
  filtersPanelTitle: 'Akıllı filtreler',
  filtersPanelDescription: 'İlanları çalışma modeli, kıdem, şirket ve kendi yazdığın anahtar kelimelerle daralt.',
  resetFilters: 'Sıfırla',
  keywordFilterTitle: 'Kendi filtreni yaz',
  keywordInputPlaceholder: 'Örn. python, embedded, cloud, istanbul',
  keywordInputHelp: 'Kelime eklemek için Enter tuşuna bas. Birden fazla kelime ekleyerek sonucu daraltabilirsin.',
  quickFilters: 'Hızlı filtreler',
  matchedOnly: 'Sadece eşleşenler',
  remote: 'Remote',
  newListings: 'Yeni ilanlar',
  fullTime: 'Tam zamanlı',
  partTime: 'Yarı zamanlı',
  internship: 'Staj',
  locationFilter: 'Konum',
  companyFilter: 'Şirket',
  workplaceFilter: 'Çalışma modeli',
  employmentTypeFilter: 'Çalışma tipi',
  seniorityFilter: 'Kıdem seviyesi',
  facetSearchPlaceholder: '{label} içinde ara',
  noFacetMatches: 'Bu aramada eşleşen seçenek yok.',
};

export function createEmptyJobFilters(): FilterState {
  return {
    quick: new Set(),
    companies: new Set(),
    locations: new Set(),
    workplaceTypes: new Set(),
    employmentTypes: new Set(),
    seniorities: new Set(),
    keywords: [],
  };
}

export function normalizeJobFilters(filters: Partial<FilterState> | FilterState | null | undefined): FilterState {
  const base = createEmptyJobFilters();
  if (!filters) {
    return base;
  }
  return {
    quick: filters.quick instanceof Set ? filters.quick : base.quick,
    companies: filters.companies instanceof Set ? filters.companies : base.companies,
    locations: filters.locations instanceof Set ? filters.locations : base.locations,
    workplaceTypes: filters.workplaceTypes instanceof Set ? filters.workplaceTypes : base.workplaceTypes,
    employmentTypes: filters.employmentTypes instanceof Set ? filters.employmentTypes : base.employmentTypes,
    seniorities: filters.seniorities instanceof Set ? filters.seniorities : base.seniorities,
    keywords: Array.isArray(filters.keywords) ? filters.keywords : base.keywords,
  };
}

function extractJobsMessages(messages: unknown): Partial<Record<JobCopyKey, string>> {
  if (!messages || typeof messages !== 'object') {
    return {};
  }
  const root = messages as Record<string, unknown>;
  const jobs = root.jobs;
  if (!jobs || typeof jobs !== 'object') {
    return {};
  }

  const result: Partial<Record<JobCopyKey, string>> = {};
  for (const key of Object.keys(JOB_COPY_FALLBACKS) as JobCopyKey[]) {
    const value = (jobs as Record<string, unknown>)[key];
    if (typeof value === 'string' && value.trim()) {
      result[key] = value;
    }
  }
  return result;
}

function resolveCopy(
  t: ReturnType<typeof useTranslations<'jobs'>>,
  availableMessages: Partial<Record<JobCopyKey, string>>,
  key: JobCopyKey,
  values?: Record<string, string>,
): string {
  if (availableMessages[key]) {
    try {
      return values ? t(key, values) : t(key);
    } catch {
      // Fall back to static copy below when translation resolution fails.
    }
  }

  let fallback = JOB_COPY_FALLBACKS[key];
  if (values) {
    for (const [token, value] of Object.entries(values)) {
      fallback = fallback.replace(`{${token}}`, value);
    }
  }
  return fallback;
}

function normalizeFacetValue(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function buildFacets(jobs: JobListItem[]): FacetCollection {
  const companyMap = new Map<string, number>();
  const locationMap = new Map<string, number>();
  const workplaceMap = new Map<string, number>();
  const employmentMap = new Map<string, number>();
  const seniorityMap = new Map<string, number>();

  for (const job of jobs) {
    const company = normalizeFacetValue(job.company_name);
    if (company) companyMap.set(company, (companyMap.get(company) ?? 0) + 1);

    const location = normalizeFacetValue(job.location?.split(',')[0]);
    if (location) locationMap.set(location, (locationMap.get(location) ?? 0) + 1);

    const workplace = normalizeFacetValue(job.workplace_type);
    if (workplace) workplaceMap.set(workplace, (workplaceMap.get(workplace) ?? 0) + 1);

    const employment = normalizeFacetValue(job.employment_type);
    if (employment) employmentMap.set(employment, (employmentMap.get(employment) ?? 0) + 1);

    const seniority = normalizeFacetValue(job.seniority);
    if (seniority) seniorityMap.set(seniority, (seniorityMap.get(seniority) ?? 0) + 1);
  }

  const toSorted = (map: Map<string, number>): Facet[] =>
    Array.from(map.entries())
      .map(([value, count]) => ({value, count}))
      .sort((a, b) => (b.count - a.count) || a.value.localeCompare(b.value));

  return {
    companies: toSorted(companyMap),
    locations: toSorted(locationMap),
    workplaceTypes: toSorted(workplaceMap),
    employmentTypes: toSorted(employmentMap),
    seniorities: toSorted(seniorityMap),
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

function humanizeFacet(value: string): string {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

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
  const messages = useMessages();
  const availableMessages = useMemo(() => extractJobsMessages(messages), [messages]);
  const copy = (key: JobCopyKey, values?: Record<string, string>) =>
    resolveCopy(t, availableMessages, key, values);

  const normalizedFilters = useMemo(() => normalizeJobFilters(filters), [filters]);
  const facets = useMemo(() => buildFacets(jobs), [jobs]);
  const [keywordInput, setKeywordInput] = useState('');
  const [facetSearch, setFacetSearch] = useState<Record<string, string>>({});

  const totalActive =
    normalizedFilters.quick.size +
    normalizedFilters.companies.size +
    normalizedFilters.locations.size +
    normalizedFilters.workplaceTypes.size +
    normalizedFilters.employmentTypes.size +
    normalizedFilters.seniorities.size +
    normalizedFilters.keywords.length;

  function updateSet<K extends keyof FilterState>(key: K, value: string) {
    const currentValue = normalizedFilters[key];
    if (!(currentValue instanceof Set)) {
      return;
    }
    const next = new Set(currentValue);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onFilterChange({...normalizedFilters, [key]: next} as FilterState);
  }

  function toggleQuick(key: string) {
    updateSet('quick', key);
  }

  function addKeyword(value: string) {
    const normalized = value.trim();
    if (!normalized) return;
    if (normalizedFilters.keywords.some((keyword) => keyword.toLowerCase() === normalized.toLowerCase())) {
      setKeywordInput('');
      return;
    }
    onFilterChange({...normalizedFilters, keywords: [...normalizedFilters.keywords, normalized]});
    setKeywordInput('');
  }

  function removeKeyword(value: string) {
    onFilterChange({
      ...normalizedFilters,
      keywords: normalizedFilters.keywords.filter((keyword) => keyword !== value),
    });
  }

  function clearAll() {
    onFilterChange(createEmptyJobFilters());
    setKeywordInput('');
  }

  return (
    <aside className="space-y-4 overflow-y-auto">
      <ProfileCompletionCard />

      <div className="rounded-2xl border border-border bg-surface p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/70">
              <Filter className="size-3.5" />
              {copy('filtersPanelTitle')}
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              {copy('filtersPanelDescription')}
            </p>
          </div>
          {totalActive > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface-muted px-2.5 py-1 text-[11px] text-muted-foreground transition hover:border-primary/25 hover:text-foreground"
            >
              <RotateCcw className="size-3" />
              {copy('resetFilters')}
            </button>
          )}
        </div>

        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-border/70 bg-surface-muted/40 p-3">
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground/70">
              {copy('keywordFilterTitle')}
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3 py-2">
              <Search className="size-3.5 text-muted-foreground" />
              <input
                value={keywordInput}
                onChange={(event) => setKeywordInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ',') {
                    event.preventDefault();
                    addKeyword(keywordInput);
                  }
                }}
                placeholder={copy('keywordInputPlaceholder')}
                className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground/50"
              />
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground/70">{copy('keywordInputHelp')}</p>
            {normalizedFilters.keywords.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {normalizedFilters.keywords.map((keyword) => (
                  <button
                    key={keyword}
                    type="button"
                    onClick={() => removeKeyword(keyword)}
                    className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-secondary-foreground"
                  >
                    {keyword}
                    <X className="size-3" />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground/70">
              {copy('quickFilters')}
            </div>
            <div className="flex flex-wrap gap-2">
              {QUICK_FILTERS.map((filter) => {
                const active = normalizedFilters.quick.has(filter.key);
                return (
                  <button
                    key={filter.key}
                    type="button"
                    onClick={() => toggleQuick(filter.key)}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition ${
                      active
                        ? 'border-primary/35 bg-primary/12 text-secondary-foreground shadow-sm'
                        : 'border-border bg-surface-muted/40 text-muted-foreground hover:border-primary/25 hover:text-foreground'
                    }`}
                  >
                    {copy(filter.labelKey)}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-3 border-t border-border/60 pt-4">
            <FacetGroup
              label={copy('locationFilter')}
              facets={facets.locations}
              selected={normalizedFilters.locations}
              searchValue={facetSearch.locations ?? ''}
              onSearchChange={(value) => setFacetSearch((current) => ({...current, locations: value}))}
              onToggle={(value) => updateSet('locations', value)}
            />
            <FacetGroup
              label={copy('companyFilter')}
              facets={facets.companies}
              selected={normalizedFilters.companies}
              searchValue={facetSearch.companies ?? ''}
              onSearchChange={(value) => setFacetSearch((current) => ({...current, companies: value}))}
              onToggle={(value) => updateSet('companies', value)}
            />
            <FacetGroup
              label={copy('workplaceFilter')}
              facets={facets.workplaceTypes}
              selected={normalizedFilters.workplaceTypes}
              searchValue={facetSearch.workplaceTypes ?? ''}
              onSearchChange={(value) => setFacetSearch((current) => ({...current, workplaceTypes: value}))}
              onToggle={(value) => updateSet('workplaceTypes', value)}
              humanize
            />
            <FacetGroup
              label={copy('employmentTypeFilter')}
              facets={facets.employmentTypes}
              selected={normalizedFilters.employmentTypes}
              searchValue={facetSearch.employmentTypes ?? ''}
              onSearchChange={(value) => setFacetSearch((current) => ({...current, employmentTypes: value}))}
              onToggle={(value) => updateSet('employmentTypes', value)}
              humanize
            />
            <FacetGroup
              label={copy('seniorityFilter')}
              facets={facets.seniorities}
              selected={normalizedFilters.seniorities}
              searchValue={facetSearch.seniorities ?? ''}
              onSearchChange={(value) => setFacetSearch((current) => ({...current, seniorities: value}))}
              onToggle={(value) => updateSet('seniorities', value)}
              humanize
            />
          </div>
        </div>
      </div>
    </aside>
  );
}

function FacetGroup({
  label,
  facets,
  selected,
  searchValue,
  onSearchChange,
  onToggle,
  humanize = false,
}: {
  label: string;
  facets: Facet[];
  selected: Set<string>;
  searchValue: string;
  onSearchChange: (value: string) => void;
  onToggle: (value: string) => void;
  humanize?: boolean;
}) {
  const t = useTranslations('jobs');
  const messages = useMessages();
  const availableMessages = useMemo(() => extractJobsMessages(messages), [messages]);
  const copy = (key: JobCopyKey, values?: Record<string, string>) =>
    resolveCopy(t, availableMessages, key, values);
  const visibleFacets = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    const filtered = !query
      ? facets
      : facets.filter((facet) => facet.value.toLowerCase().includes(query));
    return filtered.slice(0, 8);
  }, [facets, searchValue]);

  if (facets.length === 0) {
    return null;
  }

  return (
    <section className="space-y-2 rounded-xl border border-border/60 bg-surface-muted/25 p-3">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground/70">
        {label}
      </div>
      <div className="flex items-center gap-2 rounded-lg border border-border/70 bg-background px-2.5 py-2">
        <Search className="size-3 text-muted-foreground" />
        <input
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={copy('facetSearchPlaceholder', {label})}
          className="w-full bg-transparent text-xs outline-none placeholder:text-muted-foreground/45"
        />
      </div>
      <div className="space-y-1">
        {visibleFacets.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/60 px-3 py-2 text-[11px] text-muted-foreground/70">
            {copy('noFacetMatches')}
          </div>
        ) : (
          visibleFacets.map((facet) => {
            const active = selected.has(facet.value);
            const labelValue = humanize ? humanizeFacet(facet.value) : facet.value;
            return (
              <button
                key={facet.value}
                type="button"
                onClick={() => onToggle(facet.value)}
                className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition ${
                  active ? 'bg-primary/12 text-foreground' : 'hover:bg-background text-muted-foreground'
                }`}
              >
                <span
                  className={`flex size-4 shrink-0 items-center justify-center rounded border transition ${
                    active ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-background'
                  }`}
                >
                  {active && (
                    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                      <path d="M1.5 4L3 5.5L6.5 2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </span>
                <span className="flex-1">{labelValue}</span>
                <span className="text-[10px] text-muted-foreground/60">{facet.count}</span>
              </button>
            );
          })
        )}
      </div>
    </section>
  );
}
