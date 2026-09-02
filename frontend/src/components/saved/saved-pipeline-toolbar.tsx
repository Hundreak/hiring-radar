'use client';

import {useTranslations} from 'next-intl';

import type {SavedJobSortKey, SavedJobTabKey, SavedPipelineCounts} from '@/lib/saved-pipeline';

const TABS: readonly {key: SavedJobTabKey; labelKey: string}[] = [
  {key: 'all', labelKey: 'tabAll'},
  {key: 'reviewing', labelKey: 'tabReviewing'},
  {key: 'applied', labelKey: 'tabApplied'},
  {key: 'interview', labelKey: 'tabInterview'},
  {key: 'offer', labelKey: 'tabOffer'},
  {key: 'rejected', labelKey: 'tabRejected'},
  {key: 'archived', labelKey: 'tabArchive'},
];

const SORT_OPTIONS: readonly {key: SavedJobSortKey; labelKey: string}[] = [
  {key: 'activity', labelKey: 'sortActivity'},
  {key: 'deadline', labelKey: 'sortDeadline'},
  {key: 'score', labelKey: 'sortScore'},
];

export function SavedPipelineToolbar({
  tab,
  onTabChange,
  counts,
  query,
  onQueryChange,
  sortKey,
  onSortChange,
}: {
  tab: SavedJobTabKey;
  onTabChange: (tab: SavedJobTabKey) => void;
  counts: SavedPipelineCounts;
  query: string;
  onQueryChange: (query: string) => void;
  sortKey: SavedJobSortKey;
  onSortChange: (sortKey: SavedJobSortKey) => void;
}) {
  const t = useTranslations('saved');

  return (
    <div className="rounded-xl border border-border bg-surface p-3.5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-xs font-medium text-foreground/70">{t('pipelineToolbarTitle')}</h2>
          <p className="mt-1 max-w-xl text-[11px] leading-relaxed text-muted-foreground">
            {t('pipelineToolbarSubtitle')}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="relative">
            <span className="sr-only">{t('searchPlaceholder')}</span>
            <input
              type="search"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder={t('searchPlaceholder')}
              className="h-8 w-56 rounded-lg border border-border bg-surface-muted px-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </label>

          <label className="relative">
            <span className="sr-only">{t('sortActivity')}</span>
            <select
              value={sortKey}
              onChange={(event) => onSortChange(event.target.value as SavedJobSortKey)}
              className="h-8 rounded-lg border border-border bg-surface-muted px-2.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {t(option.labelKey)}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5" role="tablist" aria-label={t('pipelineToolbarTitle')}>
        {TABS.map((item) => {
          const active = item.key === tab;

          return (
            <button
              key={item.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onTabChange(item.key)}
              className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[11px] transition ${
                active
                  ? 'border-primary/30 bg-primary/10 text-foreground'
                  : 'border-border bg-surface text-muted-foreground hover:bg-surface-muted hover:text-foreground'
              }`}
            >
              <span className="font-medium">{t(item.labelKey)}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] ${
                  active ? 'bg-primary/20 text-foreground' : 'bg-surface-muted text-muted-foreground'
                }`}
              >
                {counts[item.key]}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
