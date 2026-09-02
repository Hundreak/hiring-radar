'use client';

import {useEffect} from 'react';
import {BadgeCheck, Briefcase, CalendarClock, CircleDollarSign, MapPin, ShieldCheck, X} from 'lucide-react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';
import type {EmployerCandidateOpportunity, EmployerCandidateStatus} from '@/types/employer';
import {formatWorkflowSalary, getTalentWorkflowCopy, getTalentWorkflowLanguage, workflowAvailabilityLabels, workflowCandidateStatusLabels, workflowWorkModelLabels} from '@/lib/employer-talent-workflow-copy';
import {CandidateNextActions} from './candidate-next-actions';
import {CandidateRiskPanel} from './candidate-risk-panel';
import {CandidateTimeline} from './candidate-timeline';
import {ExplainableMatchScore} from './explainable-match-score';
import {SkillEvidenceMap} from './skill-evidence-map';

function getStatusTone(status: EmployerCandidateStatus): 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'ai' {
  if (status === 'hired' || status === 'shortlisted' || status === 'offer') return 'success';
  if (status === 'interview') return 'info';
  if (status === 'rejected') return 'danger';
  if (status === 'new') return 'ai';
  return 'neutral';
}

function FitMetric({icon, label, value, helper}: {icon: React.ReactNode; label: string; value: string; helper?: string}) {
  return (
    <div className="rounded-2xl border border-border bg-surface-muted/60 p-3">
      <p className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.14em] text-muted-foreground">{icon}{label}</p>
      <p className="mt-1 truncate text-sm font-black text-foreground">{value}</p>
      {helper && <p className="mt-1 line-clamp-1 text-xs font-semibold text-muted-foreground">{helper}</p>}
    </div>
  );
}

export function Candidate360Drawer({
  candidate,
  locale,
  open,
  onClose,
}: {
  candidate?: EmployerCandidateOpportunity;
  locale: string;
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose, open]);

  if (!candidate) return null;

  const lang = getTalentWorkflowLanguage(locale);
  const copy = getTalentWorkflowCopy(locale);
  const statusLabels = workflowCandidateStatusLabels[lang];
  const availability = workflowAvailabilityLabels[lang];
  const workModels = workflowWorkModelLabels[lang];

  return (
    <div className={cn('fixed inset-0 z-[80] transition', open ? 'pointer-events-auto' : 'pointer-events-none')} aria-hidden={!open}>
      <button
        type="button"
        className={cn('absolute inset-0 bg-slate-950/55 backdrop-blur-sm transition-opacity', open ? 'opacity-100' : 'opacity-0')}
        aria-label={copy.drawer.closeCandidate360}
        onClick={onClose}
      />
      <aside
        className={cn(
          'absolute right-0 top-0 flex h-full w-full max-w-[1180px] flex-col overflow-hidden border-l border-border bg-background shadow-[0_30px_120px_rgba(15,23,42,0.35)] transition-transform duration-300 ease-out',
          open ? 'translate-x-0' : 'translate-x-full'
        )}
        role="dialog"
        aria-modal="true"
        aria-label={`${candidate.name} ${copy.common.profile360}`}
      >
        <div className="flex items-center justify-between gap-3 border-b border-border bg-surface/90 px-4 py-3 backdrop-blur-xl sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--primary),var(--accent))] text-sm font-black text-primary-foreground shadow-lg">
              {candidate.initials}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="truncate text-lg font-black tracking-[-0.03em] text-foreground sm:text-xl">{candidate.name}</h2>
                <StatusBadge tone={getStatusTone(candidate.status)}>{statusLabels[candidate.status]}</StatusBadge>
              </div>
              <p className="line-clamp-1 text-sm font-semibold text-muted-foreground">{candidate.headline}</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button variant="soft" size="sm" className="hidden gap-2 sm:inline-flex">
              <ShieldCheck className="size-4" /> {copy.common.humanReviewMode}
            </Button>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/35 hover:text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
              aria-label={copy.drawer.closePanel}
            >
              <X className="size-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_15%_0%,rgba(56,189,248,0.10),transparent_28%),radial-gradient(circle_at_85%_4%,rgba(99,102,241,0.10),transparent_24%)] p-4 sm:p-6">
          <div className="mx-auto max-w-6xl space-y-5">
            <SurfaceCard variant="accent" padding="none" className="overflow-hidden">
              <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_260px] lg:p-6">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge tone="ai" icon={<BadgeCheck className="size-3.5" />}>{copy.common.profile360}</StatusBadge>
                    <StatusBadge tone="success">{copy.common.explainableAi}</StatusBadge>
                    <StatusBadge tone="info">{candidate.lastActiveAt} {copy.drawer.activeSuffix}</StatusBadge>
                  </div>
                  <h1 className="mt-4 text-3xl font-black tracking-[-0.045em] text-foreground sm:text-4xl">{candidate.name}</h1>
                  <p className="mt-2 max-w-3xl text-sm font-semibold leading-7 text-muted-foreground sm:text-base">{candidate.headline} · {candidate.education}</p>
                  <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <FitMetric icon={<MapPin className="size-4" />} label={copy.common.location} value={candidate.location} helper={workModels[candidate.workPreference]} />
                    <FitMetric icon={<Briefcase className="size-4" />} label={copy.common.experience} value={`${candidate.experience} ${copy.common.years}`} helper={candidate.targetRole ?? candidate.headline} />
                    <FitMetric icon={<CalendarClock className="size-4" />} label={copy.common.availability} value={availability[candidate.availability]} helper={candidate.lastActiveAt} />
                    <FitMetric icon={<CircleDollarSign className="size-4" />} label={copy.common.salary} value={formatWorkflowSalary(candidate, locale)} helper={copy.drawer.salaryHelper} />
                  </div>
                </div>
                <div className="grid content-start gap-3 rounded-[26px] border border-border bg-surface/80 p-4">
                  <ScoreBadge score={candidate.matchScore} label={copy.common.match} size="lg" />
                  <ScoreBadge score={candidate.intentScore} label={copy.common.intent} size="lg" />
                  <p className="text-xs font-semibold leading-5 text-muted-foreground">
                    {copy.drawer.matchDescription}
                  </p>
                </div>
              </div>
            </SurfaceCard>

            <CandidateNextActions candidate={candidate} locale={locale} />

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.8fr)]">
              <div className="space-y-5">
                <ExplainableMatchScore candidate={candidate} locale={locale} />
                <SkillEvidenceMap candidate={candidate} locale={locale} />
              </div>
              <div className="space-y-5">
                <CandidateRiskPanel candidate={candidate} locale={locale} />
                <CandidateTimeline candidate={candidate} locale={locale} />
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
