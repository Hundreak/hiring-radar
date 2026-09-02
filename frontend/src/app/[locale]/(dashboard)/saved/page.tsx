'use client';

import {useCallback, useMemo, useState} from 'react';
import {useTranslations} from 'next-intl';

import {SavedJobCard} from '@/components/saved/saved-job-card';
import {SavedPipelineSummary} from '@/components/saved/saved-pipeline-summary';
import {SavedPipelineToolbar} from '@/components/saved/saved-pipeline-toolbar';
import {SavedSidebar} from '@/components/saved/saved-sidebar';
import {PaginationControls} from '@/components/ui/pagination-controls';
import {
  getQueryErrorMessage,
  useAddSavedJobNoteMutation,
  useSavedJobsQuery,
  useUnsaveJobMutation,
  useUpdateSavedJobNoteMutation,
  useUpdateSavedJobStatusMutation,
} from '@/hooks/use-api-queries';
import {
  countSavedJobsByStatus,
  filterAndSortSavedJobs,
  groupSavedJobsByStatus,
  SAVED_PIPELINE_STATUSES,
  type SavedJobSortKey,
  type SavedJobTabKey,
} from '@/lib/saved-pipeline';
import {DEFAULT_SAVED_PAGE_SIZE, SAVED_PAGE_SIZE_OPTIONS, createPaginationMeta} from '@/lib/pagination';
import type {SavedJob, SavedJobNote, SavedJobStatus} from '@/types/saved';

export default function SavedPage() {
  const t = useTranslations('saved');
  const [tab, setTab] = useState<SavedJobTabKey>('all');
  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState<SavedJobSortKey>('activity');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_SAVED_PAGE_SIZE);

  const statusFilter: SavedJobStatus | null = tab === 'all' ? null : tab;
  const savedJobsQuery = useSavedJobsQuery({page, pageSize, status: statusFilter});
  const updateStatusMutation = useUpdateSavedJobStatusMutation();
  const addNoteMutation = useAddSavedJobNoteMutation();
  const updateNoteMutation = useUpdateSavedJobNoteMutation();
  const unsaveJobMutation = useUnsaveJobMutation();

  const [noteModal, setNoteModal] = useState<SavedJob | null>(null);
  const [noteText, setNoteText] = useState('');
  const [editingNote, setEditingNote] = useState<SavedJobNote | null>(null);

  const jobs = savedJobsQuery.data?.items ?? [];
  const paginationMeta = useMemo(
    () => createPaginationMeta({
      page: savedJobsQuery.data?.page ?? page,
      pageSize: savedJobsQuery.data?.page_size ?? pageSize,
      totalItems: savedJobsQuery.data?.total_items ?? jobs.length,
      totalPages: savedJobsQuery.data?.total_pages ?? null,
    }),
    [jobs.length, savedJobsQuery.data?.page, savedJobsQuery.data?.page_size, savedJobsQuery.data?.total_items, savedJobsQuery.data?.total_pages, page, pageSize]
  );
  const loading = savedJobsQuery.isLoading;
  const error = getQueryErrorMessage(savedJobsQuery.error);
  const activeNoteModal = useMemo(
    () => (noteModal ? jobs.find((job) => job.id === noteModal.id) ?? noteModal : null),
    [jobs, noteModal]
  );

  const counts = useMemo(() => countSavedJobsByStatus(jobs), [jobs]);
  const visibleJobs = useMemo(
    () => filterAndSortSavedJobs({jobs, tab, query, sortKey}),
    [jobs, query, sortKey, tab]
  );
  const visibleGroups = useMemo(() => groupSavedJobsByStatus(visibleJobs), [visibleJobs]);

  // Filtre degisince sayfayi basa al. Effect yerine render sirasinda
  // ayarlanir: effect'te setState cagirmak basamakli render tetikler.
  const filterSignature = `${tab}|${query}|${sortKey}|${pageSize}`;
  const [lastFilterSignature, setLastFilterSignature] = useState(filterSignature);
  if (lastFilterSignature !== filterSignature) {
    setLastFilterSignature(filterSignature);
    setPage(1);
  }

  const handleStatusChange = useCallback(
    async (savedJobId: number, newStatus: SavedJobStatus) => {
      try {
        await updateStatusMutation.mutateAsync({savedJobId, status: newStatus});
      } catch { /* silent */ }
    },
    [updateStatusMutation]
  );

  const handleOpenNotes = useCallback((savedJobId: number) => {
    const job = jobs.find((j) => j.id === savedJobId);
    if (!job) return;
    setNoteModal(job);
    setNoteText('');
    setEditingNote(null);
  }, [jobs]);

  const handleAddNote = useCallback(async () => {
    if (!activeNoteModal || !noteText.trim()) return;
    try {
      await addNoteMutation.mutateAsync({
        savedJobId: activeNoteModal.id,
        content: noteText.trim(),
      });
      setNoteText('');
    } catch { /* silent */ }
  }, [activeNoteModal, addNoteMutation, noteText]);

  const handleStartEditNote = useCallback((note: SavedJobNote) => {
    setEditingNote(note);
    setNoteText(note.content);
  }, []);

  const handleSaveEditNote = useCallback(async () => {
    if (!activeNoteModal || !editingNote || !noteText.trim()) return;
    try {
      await updateNoteMutation.mutateAsync({
        savedJobId: activeNoteModal.id,
        noteId: editingNote.id,
        content: noteText.trim(),
      });
      setEditingNote(null);
      setNoteText('');
    } catch { /* silent */ }
  }, [activeNoteModal, editingNote, noteText, updateNoteMutation]);

  const handleRemove = useCallback(async (jobId: number) => {
    setNoteModal((prev) => (prev && prev.job_id === jobId ? null : prev));
    try {
      await unsaveJobMutation.mutateAsync(jobId);
    } catch { /* silent */ }
  }, [unsaveJobMutation]);

  const showPipeline = tab === 'all';

  return (
    <div className="space-y-4">
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

      <div className="rounded-xl border border-primary/20 bg-primary/[0.06] px-4 py-3">
        <div className="flex items-center gap-2.5">
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
      </div>

      <SavedPipelineSummary jobs={jobs} />
      <SavedPipelineToolbar
        tab={tab}
        onTabChange={setTab}
        counts={counts}
        query={query}
        onQueryChange={setQuery}
        sortKey={sortKey}
        onSortChange={setSortKey}
      />

      <PaginationControls
        meta={paginationMeta}
        labels={{
          previous: t('paginationPrevious'),
          next: t('paginationNext'),
          pageSize: t('paginationPageSize'),
          summary: ({start, end, total}) => t('paginationSummary', {start, end, total}),
        }}
        pageSizeOptions={SAVED_PAGE_SIZE_OPTIONS}
        onPageChange={setPage}
        onPageSizeChange={(nextPageSize) => {
          setPageSize(nextPageSize);
          setPage(1);
        }}
      />

      {loading ? (
        <div className="rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
          {t('loading')}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-danger/30 bg-danger/5 p-8 text-sm text-danger">
          {error}
        </div>
      ) : showPipeline ? (
        <div className="grid saved-body gap-4">
          <div className="grid saved-cols gap-3">
            {SAVED_PIPELINE_STATUSES.map((status) => (
              <KanbanColumn
                key={status}
                title={t(status === 'offer' ? 'colOffer' : status === 'rejected' ? 'colRejected' : status === 'interview' ? 'colInterview' : status === 'applied' ? 'colApplied' : 'colReviewing')}
                count={visibleGroups[status].length}
              >
                {visibleGroups[status].length === 0 ? (
                  <EmptyColumn message={t(status === 'rejected' ? 'emptyRejectedColumn' : status === 'offer' ? 'emptyOfferColumn' : 'emptyColumn')} />
                ) : (
                  visibleGroups[status].map((job) => (
                    <SavedJobCard key={job.id} job={job} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
                  ))
                )}
              </KanbanColumn>
            ))}
          </div>
          <SavedSidebar jobs={jobs} />
        </div>
      ) : (
        <div className="grid saved-body gap-4">
          <div className="grid match-cards-grid gap-2.5 self-start">
            {visibleJobs.length === 0 ? (
              <div className="col-span-full rounded-xl border border-border bg-surface p-8 text-sm text-muted-foreground">
                {t('emptySearch')}
              </div>
            ) : (
              visibleJobs.map((job) => (
                <SavedJobCard key={job.id} job={job} onStatusChange={handleStatusChange} onAddNote={handleOpenNotes} onRemove={handleRemove} />
              ))
            )}
          </div>
          <SavedSidebar jobs={jobs} />
        </div>
      )}

      {!loading && !error && paginationMeta.totalPages > 1 ? (
        <PaginationControls
          meta={paginationMeta}
          labels={{
            previous: t('paginationPrevious'),
            next: t('paginationNext'),
            pageSize: t('paginationPageSize'),
            summary: ({start, end, total}) => t('paginationSummary', {start, end, total}),
          }}
          onPageChange={setPage}
        />
      ) : null}

      {activeNoteModal && (
        <NoteModal
          job={activeNoteModal}
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
