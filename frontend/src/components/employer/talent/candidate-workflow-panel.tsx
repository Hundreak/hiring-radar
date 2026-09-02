'use client';

import {Archive, BellRing, CheckCircle2, Clock3, MessageSquareText, NotebookPen, Plus, Send, Tag, X} from 'lucide-react';
import {useMemo, useState} from 'react';

import {Button} from '@/components/ui/button';
import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {cn} from '@/lib/utils';
import {formatWorkflowDateTime, getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {CandidateWorkflowNote} from '@/types/employer-outreach';

function noteToneClass(tone: CandidateWorkflowNote['tone']) {
  if (tone === 'success') return 'border-emerald-500/20 bg-emerald-500/10';
  if (tone === 'warning') return 'border-amber-500/20 bg-amber-500/10';
  if (tone === 'ai') return 'border-primary/20 bg-primary/10';
  return 'border-border bg-surface-muted/50';
}

export function CandidateWorkflowPanel({
  candidate,
  locale,
  tags,
  notes,
  onAddTag,
  onRemoveTag,
  onAddNote,
  onArchive,
  onShortlist,
}: {
  candidate: EmployerCandidateOpportunity;
  locale: string;
  tags: string[];
  notes: CandidateWorkflowNote[];
  onAddTag: (tag: string) => void;
  onRemoveTag: (tag: string) => void;
  onAddNote: (note: string) => void;
  onArchive?: () => void;
  onShortlist?: () => void;
}) {
  const copy = getTalentWorkflowCopy(locale);
  const [tagDraft, setTagDraft] = useState('');
  const [noteDraft, setNoteDraft] = useState('');

  const suggestedTags = useMemo(() => {
    return copy.workflow.quickTags.filter((tag) => !tags.includes(tag)).slice(0, 4);
  }, [copy.workflow.quickTags, tags]);

  const submitTag = (value = tagDraft) => {
    const normalized = value.trim();
    if (!normalized) return;
    onAddTag(normalized);
    setTagDraft('');
  };

  const submitNote = () => {
    const normalized = noteDraft.trim();
    if (!normalized) return;
    onAddNote(normalized);
    setNoteDraft('');
  };

  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
      <div className="border-b border-border/75 bg-surface-muted/35 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<NotebookPen className="size-3.5" />}>{copy.workflow.badge}</StatusBadge>
              <StatusBadge tone={notes.length > 0 ? 'success' : 'neutral'}>{notes.length} {copy.common.notes ?? 'notes'}</StatusBadge>
            </div>
            <h3 className="mt-3 text-lg font-black tracking-[-0.03em] text-foreground">{copy.workflow.title}</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">{copy.workflow.description(candidate.name)}</p>
          </div>
          <div className="hidden size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary sm:flex">
            <MessageSquareText className="size-5" />
          </div>
        </div>
      </div>

      <div className="space-y-5 p-4">
        <section>
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.15em] text-muted-foreground"><Tag className="size-3.5" /> {copy.workflow.tags}</p>
            <span className="text-[11px] font-bold text-muted-foreground">{tags.length} {copy.workflow.active}</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {tags.length > 0 ? tags.map((tag) => (
              <button key={tag} type="button" onClick={() => onRemoveTag(tag)} className="group inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-black text-primary transition hover:bg-primary/15 focus:outline-none focus:ring-4 focus:ring-[var(--ring)]" title={copy.workflow.removeTag}>
                {tag}<X className="size-3 opacity-60 transition group-hover:opacity-100" />
              </button>
            )) : (
              <span className="rounded-full border border-dashed border-border px-3 py-1.5 text-xs font-bold text-muted-foreground">{copy.workflow.noTags}</span>
            )}
          </div>

          <div className="mt-3 flex gap-2">
            <input value={tagDraft} onChange={(event) => setTagDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') submitTag(); }} placeholder={copy.workflow.tagPlaceholder} className="min-h-10 flex-1 rounded-2xl border border-border bg-surface px-3 text-sm font-semibold text-foreground outline-none transition placeholder:text-muted-foreground focus:ring-4 focus:ring-[var(--ring)]" />
            <Button size="sm" variant="secondary" onClick={() => submitTag()} className="gap-2"><Plus className="size-4" /> {copy.workflow.add}</Button>
          </div>

          {suggestedTags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestedTags.map((tag) => (
                <button key={tag} type="button" onClick={() => submitTag(tag)} className="rounded-full border border-border bg-surface-muted px-2.5 py-1 text-[11px] font-black text-muted-foreground transition hover:border-primary/30 hover:text-primary">+ {tag}</button>
              ))}
            </div>
          )}
        </section>

        <section>
          <p className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.15em] text-muted-foreground"><NotebookPen className="size-3.5" /> {copy.workflow.quickNote}</p>
          <textarea value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} placeholder={copy.workflow.notePlaceholder} rows={4} className="w-full resize-none rounded-2xl border border-border bg-surface p-3 text-sm font-semibold leading-6 text-foreground outline-none transition placeholder:text-muted-foreground focus:ring-4 focus:ring-[var(--ring)]" />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-semibold text-muted-foreground">{copy.workflow.notePersistence}</p>
            <Button size="sm" onClick={submitNote} disabled={!noteDraft.trim()} className="gap-2"><Send className="size-4" /> {copy.workflow.saveNote}</Button>
          </div>
        </section>

        <section>
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.15em] text-muted-foreground"><Clock3 className="size-3.5" /> {copy.workflow.activity}</p>
            <span className="text-[11px] font-bold text-muted-foreground">{copy.workflow.lastUpdate} {formatWorkflowDateTime(locale)}</span>
          </div>

          <div className="space-y-2">
            {notes.length > 0 ? notes.map((note) => (
              <article key={note.id} className={cn('rounded-2xl border p-3', noteToneClass(note.tone))}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0"><p className="text-xs font-black text-foreground">{note.author}</p><p className="mt-1 text-sm font-semibold leading-6 text-foreground">{note.body}</p></div>
                  <span className="shrink-0 text-[11px] font-bold text-muted-foreground">{note.createdAt}</span>
                </div>
              </article>
            )) : (
              <div className="rounded-2xl border border-dashed border-border bg-surface-muted/40 p-4 text-sm font-semibold leading-6 text-muted-foreground">{copy.workflow.noNotes}</div>
            )}
          </div>
        </section>

        <section className="grid gap-2 sm:grid-cols-2">
          <Button variant="soft" onClick={onShortlist} className="gap-2"><CheckCircle2 className="size-4" /> {copy.workflow.moveToShortlist}</Button>
          <Button variant="secondary" className="gap-2"><BellRing className="size-4" /> {copy.workflow.setFollowUp}</Button>
          <Button variant="outline" className="gap-2"><MessageSquareText className="size-4" /> {copy.workflow.askHm}</Button>
          <Button variant="ghost" onClick={onArchive} className="gap-2 text-muted-foreground hover:text-destructive"><Archive className="size-4" /> {copy.workflow.archive}</Button>
        </section>
      </div>
    </SurfaceCard>
  );
}
