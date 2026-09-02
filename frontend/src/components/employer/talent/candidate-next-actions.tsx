import Link from 'next/link';
import {Archive, CalendarClock, MailPlus, MessageSquareText, Send, Star, UserCheck} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {SurfaceCard} from '@/components/employer/ui';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity} from '@/types/employer';

export function CandidateNextActions({candidate, locale}: {candidate: EmployerCandidateOpportunity; locale: string}) {
  const copy = getTalentWorkflowCopy(locale);
  const messagePreview = candidate.recommendedAction;
  return (
    <SurfaceCard variant="accent" padding="md" className="overflow-hidden">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-primary">{copy.nextActions.eyebrow}</p>
          <h3 className="mt-2 text-lg font-black tracking-[-0.03em] text-foreground">{candidate.recommendedAction}</h3>
          <p className="mt-2 text-sm font-semibold leading-6 text-muted-foreground">{messagePreview}</p>
        </div>
        <div className="hidden size-12 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg sm:flex">
          <Send className="size-5" />
        </div>
      </div>

      <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <Button className="gap-2"><MessageSquareText className="size-4" /> {copy.nextActions.writeMessage}</Button>
        <Button variant="secondary" className="gap-2"><CalendarClock className="size-4" /> {copy.nextActions.scheduleInterview}</Button>
        <Button variant="soft" className="gap-2"><Star className="size-4" /> {copy.nextActions.shortlist}</Button>
        <Link href={`/${locale}/employer/candidates/${candidate.id}`} className="inline-flex min-h-10 items-center justify-center gap-2 rounded-2xl border border-border bg-surface-elevated px-4 py-2.5 text-sm font-bold text-foreground shadow-sm transition hover:border-primary/35 hover:bg-surface-strong focus:outline-none focus:ring-4 focus:ring-[var(--ring)]">
          <UserCheck className="size-4" /> {copy.common.fullProfile}
        </Link>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border/70 pt-4">
        <button type="button" className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-black text-muted-foreground transition hover:border-primary/35 hover:text-foreground">
          <MailPlus className="size-3.5" /> {copy.nextActions.addToCampaign}
        </button>
        <button type="button" className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-black text-muted-foreground transition hover:border-primary/35 hover:text-foreground">
          <Archive className="size-3.5" /> {copy.nextActions.archive}
        </button>
      </div>
    </SurfaceCard>
  );
}
