'use client';

import {getPageRange, type PageSizeOption, type PaginationMeta} from '@/lib/pagination';

type PaginationLabels = {
  previous: string;
  next: string;
  pageSize: string;
  summary: (range: {start: number; end: number; total: number}) => string;
};

type PaginationControlsProps = {
  meta: PaginationMeta;
  labels: PaginationLabels;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: PageSizeOption[];
  className?: string;
};

export function PaginationControls({
  meta,
  labels,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions,
  className,
}: PaginationControlsProps) {
  const range = getPageRange(meta);
  const canGoPrevious = meta.page > 1;
  const canGoNext = meta.totalPages > 0 && meta.page < meta.totalPages;

  if (meta.totalItems === 0 && !onPageSizeChange) {
    return null;
  }

  return (
    <div
      className={`flex flex-col gap-3 rounded-xl border border-border bg-surface px-4 py-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between ${className ?? ''}`}
    >
      <div className="font-medium text-foreground/70">
        {labels.summary({start: range.start, end: range.end, total: meta.totalItems})}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {onPageSizeChange && pageSizeOptions?.length ? (
          <label className="flex items-center gap-2">
            <span>{labels.pageSize}</span>
            <select
              value={meta.pageSize}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
              className="h-8 rounded-lg border border-border bg-surface-muted px-2 text-xs font-medium text-foreground outline-none focus:ring-2 focus:ring-primary/30"
            >
              {pageSizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onPageChange(Math.max(1, meta.page - 1))}
            disabled={!canGoPrevious}
            className="rounded-lg border border-border bg-surface-muted px-3 py-1.5 font-medium text-foreground transition hover:border-primary/30 hover:bg-surface-strong disabled:cursor-not-allowed disabled:opacity-40"
          >
            {labels.previous}
          </button>
          <span className="min-w-16 text-center font-medium text-foreground/65">
            {meta.totalPages === 0 ? '0 / 0' : `${meta.page} / ${meta.totalPages}`}
          </span>
          <button
            type="button"
            onClick={() => onPageChange(meta.page + 1)}
            disabled={!canGoNext}
            className="rounded-lg border border-border bg-surface-muted px-3 py-1.5 font-medium text-foreground transition hover:border-primary/30 hover:bg-surface-strong disabled:cursor-not-allowed disabled:opacity-40"
          >
            {labels.next}
          </button>
        </div>
      </div>
    </div>
  );
}
