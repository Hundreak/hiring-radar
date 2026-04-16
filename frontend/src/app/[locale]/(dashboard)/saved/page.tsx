'use client';

import {useCallback, useEffect, useMemo, useState} from 'react';
import {useTranslations} from 'next-intl';

import {SavedJobCard} from '@/components/saved/saved-job-card';
import {SavedSidebar} from '@/components/saved/saved-sidebar';
import {ApiError, api} from '@/lib/api';
import {dispatchSavedJobsChanged} from '@/lib/saved-jobs-events';
import type {SavedJob, SavedJobNote, SavedJobStatus} from '@/types/saved';

type TabKey = 'all' | SavedJobStatus;

const TABS: TabKey[] = ['all', 'reviewing', 'applied', 'interview', 'archived'];

export default function SavedPage() {
  const t = useTranslations('saved');
  const [jobs, setJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>('all');

  // Note modal state
  const [noteModal, setNoteModal] = useState<SavedJob | null>(null);
  const [noteText, setNoteText] = useState('');
  const [editingNote, setEditingNote] = useState<SavedJobNote | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getSavedJobs()
      .then((res) => {
        if (active) setJobs(res.items);
      })
      .catch((reason: Error) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) return;
        setError(reason.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const filtered = useMemo(
    () => (tab === 'all' ? jobs : jobs.filter((j) => j.status === tab)),
    [jobs, tab]
  );

  const counts = useMemo(() => {
    const c = {reviewing: 0, applied: 0, interview: 0, archived: 0};
    for (const j of jobs) {
      if (j.status in c) c[j.status as keyof typeof c]++;
    }
    return c;
  }, [jobs]);

  const handleStatusChange = useCallback(
    async (savedJobId: number, newStatus: SavedJobStatus) => {
      try {
        const updated = await api.updateSavedJobStatus(savedJobId, newStatus);
        setJobs((prev) =>
          prev.map((j) => (j.id === savedJobId ? updated : j))
        );
      } catch { /* silent */ }
    },
    []
  );

  const handleOpenNotes = useCallback((savedJobId: number) => {
    const job = jobs.find((j) => j.id === savedJobId);
    if (!job) return;
    setNoteModal(job);
    setNoteText('');
    setEditingNote(null);
  }, [jobs]);

  const handleAddNote = useCallback(async () => {
    if (!noteModal || !noteText.trim()) return;
    try {
      const note = await api.addSavedJobNote(noteModal.id, noteText.trim());
      setJobs((prev) =>
        prev.map((j) =>
          j.id === noteModal.id ? {...j, notes: [note, ...j.notes]} : j
        )
      );
      setNoteModal((prev) => prev ? {...prev, notes: [note, ...prev.notes]} : null);
      setNoteText('');
    } catch { /* silent */ }
  }, [noteModal, noteText]);

  const handleStartEditNote = useCallback((note: SavedJobNote) => {
    setEditingNote(note);
    setNoteText(note.content);
  }, []);

  const handleSaveEditNote = useCallback(async () => {
    if (!noteModal || !editingNote || !noteText.trim()) return;
    try {
      await api.updateSavedJobNote(noteModal.id, editingNote.id, noteText.trim());
      const updatedNote = {...editingNote, content: noteText.trim()};
      const updateNotes = (notes: SavedJobNote[]) =>
        notes.map((n) => (n.id === editingNote.id ? updatedNote : n));
      setJobs((prev) =>
        prev.map((j) =>
          j.id === noteModal.id ? {...j, notes: updateNotes(j.notes)} : j
        )
      );
      setNoteModal((prev) => prev ? {...prev, notes: updateNotes(prev.notes)} : null);
      setEditingNote(null);
      setNoteText('');
    } catch { /* silent */ }
  }, [noteModal, editingNote, noteText]);

  const handleRemove = useCallback(async (jobId: number) => {
    // Optimistic: remove from list immediately
    setJobs((prev) => prev.filter((j) => j.job_id !== jobId));
    // Close note modal if it was open for this job
    setNoteModal((prev) => (prev && prev.job_id === jobId ? null : prev));
    try {
      await api.unsaveJob(jobId);
      dispatchSavedJobsChanged({jobId, action: 'unsaved'});
    } catch {
      // Rollback on failure: re-fetch the list
      api.getSavedJobs().then((res) => setJobs(res.items)).catch(() => {});
    }
  }, []);

  const tabLabels: Record<TabKey, string> = {
    all: t('tabAll'),
    reviewing: t('tabReviewing'),
    applied: t('tabApplied'),
    interview: t('tabInterview'),
    archived: t('tabArchive'),
  };

  const showKanban = tab === 'all';
  const reviewing = useMemo(() => jobs.filter((j) => j.status === 'reviewing'), [jobs]);
  const applied = useMemo(() => jobs.filter((j) => j.status === 'applied'), [jobs]);
  const interview = useMemo(() => jobs.filter((j) => j.status === 'interview'), [jobs]);
  const archived = useMemo(() => jobs.filter((j) => j.status === 'archived'), [jobs]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight">{t('title')}</h1>
          <p className="mt-1 max-w-lg text-xs leading-relaxed text-muted-foreground">
            {t('description')}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatPill value={String(jobs.length)} label={t('savedCount')} color="text-primary" />
          <StatPill value={String(counts.applied)} label={t('appliedCount')} />
          <StatPill value={String(counts.interview)} label={t('interviewCount')} color="text-success" />
        </div>
      </div>

      {/* How it works */}
      <div className="flex items-center gap-2.5 rounded-xl border border-primary/20 bg-primary/[0.06] px-4 py-3">
        <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary/20">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M7 2l1 3h3l-2.5 2 1 3L7 8.5 4.5 10l1-3L3 5h3z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" className="text-secondary-foreground" />
          </svg>
        </div>
        <p className="flex-1 text-xs text-muted-foreground">
          <strong className="font-medium text-foreground/70">{t('howTitle')}</strong>{' '}
          {t('howText')}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2">
        {TABS.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-lg border px-3 py-1.5 text-xs transition ${
              tab === key
                ? 'border-primary/40 bg-primary/15 text-secondary-foreground'
                : 'border-border bg-surface-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {tabLabels[key]}
            {key !== 'all' && (
              <span className="ml-1 text-[10px] text-muted-foreground">
                {counts[key as keyof typeof counts]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
          {t('loading')}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-danger/30 bg-danger/5 p-8 text-sm text-danger">
          {error}
        </div>
      ) : showKanban ? (
        <div className="grid saved-body gap-4">
          <div className="grid saved-cols gap-3">
            <KanbanColumn title={t('colReviewing')} count={reviewing.length}>
              {reviewing.length === 0 ? (
                <EmptyColumn message={t('emptyColumn')} />
              ) : (
                reviewing.map((j) => (
                  <SavedJobCard key={j.id} job={j} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
                ))
              )}
            </KanbanColumn>
            <KanbanColumn title={t('colApplied')} count={applied.length}>
              {applied.length === 0 ? (
                <EmptyColumn message={t('emptyColumn')} />
              ) : (
                applied.map((j) => (
                  <SavedJobCard key={j.id} job={j} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
                ))
              )}
            </KanbanColumn>
            <KanbanColumn title={t('colInterview')} count={interview.length}>
              {interview.length === 0 ? (
                <EmptyColumn message={t('emptyColumn')} />
              ) : (
                interview.map((j) => (
                  <SavedJobCard key={j.id} job={j} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
                ))
              )}
            </KanbanColumn>
            {archived.length > 0 && (
              <KanbanColumn title={t('tabArchive')} count={archived.length}>
                {archived.map((j) => (
                  <SavedJobCard key={j.id} job={j} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
                ))}
              </KanbanColumn>
            )}
          </div>
          <SavedSidebar jobs={jobs} />
        </div>
      ) : (
        <div className="grid saved-body gap-4">
          <div className="grid match-cards-grid gap-2.5 self-start">
            {filtered.length === 0 ? (
              <div className="col-span-full rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
                {t('emptyColumn')}
              </div>
            ) : (
              filtered.map((j) => (
                <SavedJobCard key={j.id} job={j} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
              ))
            )}
          </div>
          <SavedSidebar jobs={jobs} />
        </div>
      )}

      {/* ── Note Modal ── */}
      {noteModal && (
        <NoteModal
          job={noteModal}
          noteText={noteText}
          editingNote={editingNote}
          onNoteTextChange={setNoteText}
          onAdd={handleAddNote}
          onStartEdit={handleStartEditNote}
          onSaveEdit={handleSaveEditNote}
          onCancelEdit={() => { setEditingNote(null); setNoteText(''); }}
          onClose={() => setNoteModal(null)}
        />
      )}
    </div>
  );
}

function NoteModal({
  job,
  noteText,
  editingNote,
  onNoteTextChange,
  onAdd,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onClose,
}: {
  job: SavedJob;
  noteText: string;
  editingNote: SavedJobNote | null;
  onNoteTextChange: (v: string) => void;
  onAdd: () => void;
  onStartEdit: (note: SavedJobNote) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onClose: () => void;
}) {
  const t = useTranslations('saved');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>

        <h3 className="text-sm font-semibold text-foreground">{t('noteModalTitle')}</h3>
        <p className="mt-0.5 text-[11px] text-muted-foreground">{job.title} — {job.company_name}</p>

        {/* Existing notes */}
        <div className="mt-4 max-h-48 space-y-2 overflow-y-auto">
          {job.notes.length === 0 && (
            <p className="text-[11px] text-muted-foreground">{t('noNotes')}</p>
          )}
          {job.notes.map((note) => (
            <div key={note.id} className="rounded-lg bg-surface-muted p-2.5">
              {editingNote?.id === note.id ? (
                <div className="space-y-2">
                  <textarea
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    rows={2}
                    value={noteText}
                    onChange={(e) => onNoteTextChange(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <button type="button" onClick={onSaveEdit} className="rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90">
                      {t('saveNote')}
                    </button>
                    <button type="button" onClick={onCancelEdit} className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:bg-surface-strong">
                      {t('cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-[11px] text-foreground/80 whitespace-pre-wrap">{note.content}</div>
                    <div className="mt-1 text-[10px] text-muted-foreground/60">{note.created_at?.slice(0, 10)}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onStartEdit(note)}
                    className="shrink-0 text-[10px] text-primary hover:underline"
                  >
                    {t('editNote')}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Add new note */}
        {!editingNote && (
          <div className="mt-4 space-y-2">
            <textarea
              className="w-full rounded-lg border border-border bg-surface-muted px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              rows={3}
              placeholder={t('noteModalPlaceholder')}
              value={noteText}
              onChange={(e) => onNoteTextChange(e.target.value)}
            />
            <button
              type="button"
              onClick={onAdd}
              disabled={!noteText.trim()}
              className="rounded-md bg-primary px-3 py-1.5 text-[11px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
            >
              {t('addNote')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function KanbanColumn({title, count, children}: {title: string; count: number; children: React.ReactNode}) {
  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground/70">{title}</span>
        <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">{count}</span>
      </div>
      <div className="space-y-2.5">{children}</div>
    </div>
  );
}

function EmptyColumn({message}: {message: string}) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-surface/50 p-6 text-center text-[11px] text-muted-foreground">
      {message}
    </div>
  );
}

function StatPill({value, label, color}: {value: string; label: string; color?: string}) {
  return (
    <div className="flex min-w-[68px] flex-col items-center rounded-xl border border-border bg-surface px-4 py-2.5">
      <span className={`text-lg font-bold leading-none ${color ?? 'text-foreground'}`}>{value}</span>
      <span className="mt-1 text-[10px] text-muted-foreground">{label}</span>
    </div>
  );
}
