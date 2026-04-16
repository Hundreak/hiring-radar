'use client';

import {Bookmark, Sparkles} from 'lucide-react';
import {useTranslations} from 'next-intl';

import {Badge} from '@/components/ui/badge';
import {dispatchCopilotPrompt} from '@/lib/copilot-ui';
import type {SavedJob, SavedJobStatus} from '@/types/saved';

function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / 86_400_000));
}

export function SavedJobCard({
  job,
  onStatusChange,
  onAddNote,
  onRemove,
}: {
  job: SavedJob;
  onStatusChange: (id: number, status: SavedJobStatus) => void;
  onAddNote: (id: number) => void;
  onRemove: (jobId: number) => void;
}) {
  const t = useTranslations('saved');

  // Status-dependent action buttons
  const actions: {label: string; status: SavedJobStatus}[] = [];
  if (job.status === 'reviewing') {
    actions.push({label: t('statusApplied'), status: 'applied'});
  } else if (job.status === 'applied') {
    actions.push({label: t('statusInterview'), status: 'interview'});
    actions.push({label: t('statusRejected'), status: 'archived'});
    actions.push({label: t('statusNoResponse'), status: 'archived'});
  } else if (job.status === 'interview') {
    actions.push({label: t('statusOffer'), status: 'archived'});
    actions.push({label: t('statusSecondInterview'), status: 'interview'});
    actions.push({label: t('statusRejected'), status: 'archived'});
  } else if (job.status === 'archived') {
    actions.push({label: t('restoreReviewing'), status: 'reviewing'});
    actions.push({label: t('restoreApplied'), status: 'applied'});
  }

  const statusLabel = job.status === 'reviewing' ? t('colReviewing')
    : job.status === 'applied' ? t('colApplied')
    : job.status === 'interview' ? t('colInterview')
    : t('tabArchive');

  return (
    <div className="rounded-xl border border-border bg-surface p-3.5 space-y-2.5">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="text-[13px] font-medium leading-snug text-foreground truncate">
            {job.title}
          </h4>
          <p className="text-[11px] text-muted-foreground">
            {job.company_name}
            {job.location ? ` · ${job.location}` : ''}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onRemove(job.job_id)}
          className="flex size-[26px] shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/20 text-primary transition hover:bg-primary/30"
        >
          <Bookmark className="size-3" />
        </button>
      </div>

      {/* Match score bar */}
      {job.match_score != null && (
        <div className="flex items-center gap-2">
          <div className="h-[3px] flex-1 rounded-full bg-border">
            <div
              className={`h-[3px] rounded-full ${
                job.match_score >= 80 ? 'bg-match-high'
                : job.match_score >= 60 ? 'bg-match-mid'
                : 'bg-match-low'
              }`}
              style={{width: `${job.match_score}%`}}
            />
          </div>
          <span className="text-[10px] text-muted-foreground">{job.match_score}%</span>
        </div>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-1">
        {job.matched_keywords.slice(0, 3).map((kw) => (
          <Badge key={kw} tone="matched" className="rounded px-1.5 py-0.5 text-[10px]">
            {kw}
          </Badge>
        ))}
        <Badge tone="info" className="rounded px-1.5 py-0.5 text-[10px]">
          {statusLabel}
        </Badge>
      </div>

      {/* Deadline */}
      {job.deadline_at && (
        <div className="text-[10px] text-warning">
          {t('daysLeft', {count: daysUntil(job.deadline_at)})}
        </div>
      )}

      {/* Notes preview */}
      {job.notes.length > 0 && (
        <button
          type="button"
          onClick={() => onAddNote(job.id)}
          className="w-full rounded-lg bg-surface-muted p-2 text-left hover:bg-surface-strong transition space-y-1"
        >
          <div className="text-[11px] text-muted-foreground line-clamp-2">
            {job.notes[0].content}
          </div>
          {job.notes.length > 1 && (
            <div className="text-[10px] text-primary">
              {t('openNotesCount', {count: job.notes.length})}
            </div>
          )}
        </button>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between border-t border-border/50 pt-2">
        <button
          type="button"
          onClick={() => onAddNote(job.id)}
          className="text-[10px] text-muted-foreground hover:text-foreground"
        >
          {job.notes.length === 0 ? t('addNote') : t('openNotes')}
        </button>
        <div className="flex items-center gap-1.5 flex-wrap justify-end">
          {job.status === 'interview' && (
            <button
              type="button"
              onClick={() => {
                const prompt = `${t('interviewPrepPrompt', {title: job.title, company: job.company_name})}`;
                dispatchCopilotPrompt(prompt);
              }}
              className="flex items-center gap-1 rounded-md bg-primary/15 border border-primary/30 px-2 py-1 text-[10px] font-medium text-secondary-foreground hover:bg-primary/25 transition"
            >
              <Sparkles className="size-3" />
              {t('interviewPrep')}
            </button>
          )}
          {job.status === 'reviewing' && job.canonical_url && (
            <a
              href={job.canonical_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90"
            >
              {t('applyAction')}
            </a>
          )}
          {actions.map((a, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onStatusChange(job.id, a.status)}
              className="rounded-md border border-border px-2 py-1 text-[10px] text-muted-foreground hover:bg-surface-muted"
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
