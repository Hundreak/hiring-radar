'use client';

import {useTranslations} from 'next-intl';

import type {SavedJob} from '@/types/saved';

const STATUS_LABEL_KEY: Record<string, string> = {
  reviewing: 'colReviewing',
  applied: 'colApplied',
  interview: 'colInterview',
  archived: 'tabArchive',
};

export function SavedSidebar({jobs}: {jobs: SavedJob[]}) {
  const t = useTranslations('saved');

  const withDeadline = jobs
    .filter((j) => j.deadline_at)
    .sort((a, b) => (a.deadline_at ?? '').localeCompare(b.deadline_at ?? ''))
    .slice(0, 5);

  const recentActivity = jobs
    .filter((j) => j.status !== 'reviewing')
    .sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? ''))
    .slice(0, 5);

  return (
    <aside className="space-y-3">
      {/* Deadlines */}
      <div className="rounded-xl border border-border bg-surface p-3.5">
        <div className="mb-3 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          <span className="size-1.5 rounded-full bg-warning" />
          {t('deadlinesTitle')}
        </div>
        {withDeadline.length === 0 ? (
          <p className="text-[11px] text-muted-foreground">—</p>
        ) : (
          <div className="space-y-2">
            {withDeadline.map((j) => (
              <div
                key={j.id}
                className="flex items-center justify-between border-b border-border/50 pb-2 last:border-b-0 last:pb-0"
              >
                <div>
                  <div className="text-xs text-muted-foreground truncate max-w-[170px]">
                    {j.title}
                  </div>
                  <div className="text-[10px] text-muted-foreground/60">
                    {j.company_name}
                  </div>
                </div>
                <span className="text-[10px] text-warning">
                  {j.deadline_at?.slice(0, 10)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Activity */}
      <div className="rounded-xl border border-border bg-surface p-3.5">
        <div className="mb-3 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          <span className="size-1.5 rounded-full bg-primary" />
          {t('activityTitle')}
        </div>
        {recentActivity.length === 0 ? (
          <p className="text-[11px] text-muted-foreground">—</p>
        ) : (
          <div className="space-y-2">
            {recentActivity.map((j) => (
              <div
                key={j.id}
                className="flex items-center justify-between border-b border-border/50 pb-2 last:border-b-0 last:pb-0"
              >
                <div>
                  <div className="text-xs text-muted-foreground truncate max-w-[170px]">
                    {j.title}
                  </div>
                  <div className="text-[10px] text-muted-foreground/60">
                    {j.updated_at?.slice(0, 10)}
                  </div>
                </div>
                <span className="rounded px-1.5 py-0.5 text-[10px] bg-surface-muted text-muted-foreground">
                  {t(STATUS_LABEL_KEY[j.status] ?? 'colReviewing')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

    </aside>
  );
}
