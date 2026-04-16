'use client';

import {Bookmark, Clock3, MapPin} from 'lucide-react';
import {useTranslations} from 'next-intl';

import {Badge} from '@/components/ui/badge';

export type JobCardModel = {
  id: string;
  title: string;
  company: string;
  location: string;
  workModel: string;
  contractType: string;
  tags: string[];
  postedLabel: string;
  matched: boolean;
  matchScore?: number;
  matchedKeywords?: string[];
  href?: string;
  saved?: boolean;
  onToggleSave?: () => void;
};

export function JobCard({job}: {job: JobCardModel}) {
  const t = useTranslations('jobs');

  return (
    <div
      className={`flex cursor-pointer flex-col gap-2.5 rounded-xl border p-4 transition ${
        job.matched
          ? 'border-primary/30 bg-primary/[0.04] hover:border-primary/50'
          : 'border-border bg-surface hover:border-primary/30'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {job.matched && job.matchScore != null && (
            <div className="mb-1.5 inline-flex items-center gap-1 rounded bg-primary/15 px-2 py-0.5 text-[11px] font-medium text-secondary-foreground">
              <span className="size-1 rounded-full bg-primary" />
              {t('matchedForYou', {score: job.matchScore})}
            </div>
          )}
          <h3 className="text-sm font-medium leading-snug text-foreground">
            {job.title}
          </h3>
          <p className="text-xs text-muted-foreground">{job.company}</p>
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            job.onToggleSave?.();
          }}
          className={`flex size-7 shrink-0 items-center justify-center rounded-lg border transition ${
            job.saved
              ? 'border-primary/40 bg-primary/20 text-primary'
              : 'border-border bg-surface-muted text-muted-foreground hover:bg-surface-strong'
          }`}
        >
          <Bookmark className="size-3.5" />
        </button>
      </div>

      {job.matched && job.matchScore != null && (
        <div className="flex items-center gap-1.5">
          <div className="h-[3px] flex-1 rounded-full bg-border">
            <div
              className="h-[3px] rounded-full bg-primary"
              style={{width: `${job.matchScore}%`}}
            />
          </div>
          <span className="text-[11px] font-semibold text-primary">
            {job.matchScore}%
          </span>
        </div>
      )}

      <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <MapPin className="size-3" />
          {job.location}
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock3 className="size-3" />
          {job.postedLabel}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {job.tags.map((tag) => (
          <Badge key={tag} className="rounded px-1.5 py-0.5 text-[10px]">
            {tag}
          </Badge>
        ))}
        {job.contractType && (
          <Badge
            tone="success"
            className="rounded px-1.5 py-0.5 text-[10px]"
          >
            {job.contractType}
          </Badge>
        )}
        {job.workModel === 'Remote' && (
          <Badge
            tone="remote"
            className="rounded px-1.5 py-0.5 text-[10px]"
          >
            Remote
          </Badge>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-border/50 pt-2 text-[11px]">
        <span className="text-muted-foreground">{job.postedLabel}</span>
        {job.href ? (
          <a
            href={job.href}
            className="font-medium text-primary hover:text-secondary-foreground"
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            {t('viewDetails')} ↗
          </a>
        ) : (
          <span className="font-medium text-primary">
            {t('viewDetails')} ↗
          </span>
        )}
      </div>
    </div>
  );
}
