import Link from 'next/link';
import {ArrowRight, Clock3, MapPin, WalletCards} from 'lucide-react';

import {ScoreBadge, SectionHeader, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import type {EmployerCandidateOpportunity} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';

export function CandidateOpportunityList({candidates, baseHref, copy}: {candidates: EmployerCandidateOpportunity[]; baseHref: string; copy: EmployerCockpitCopy}) {
  return (
    <SurfaceCard className="space-y-5">
      <SectionHeader
        eyebrow={copy.candidates.eyebrow}
        title={copy.candidates.title}
        description={copy.candidates.description}
        action={
          <Link href={`${baseHref}/candidates`} className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
            {copy.candidates.viewAll} <ArrowRight className="size-4" />
          </Link>
        }
      />

      <div className="grid gap-3">
        {candidates.map((candidate) => (
          <Link
            key={candidate.id}
            href={`${baseHref}/candidates/${candidate.id}`}
            className="group rounded-[24px] border border-border bg-surface/70 p-4 transition hover:-translate-y-0.5 hover:border-primary/25 hover:bg-surface-muted/70 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
          >
            <div className="flex gap-4">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-sm font-black text-white shadow-lg shadow-primary/10">
                {candidate.initials}
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-bold text-foreground">{candidate.name}</h3>
                    <p className="truncate text-xs text-muted-foreground">
                      {candidate.headline} · {candidate.experience} {copy.candidates.years}
                    </p>
                  </div>
                  <ScoreBadge score={candidate.matchScore} label={copy.candidates.match} size="sm" />
                </div>

                <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1 rounded-full bg-surface px-2 py-1">
                    <MapPin className="size-3" /> {candidate.location}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-surface px-2 py-1">
                    <Clock3 className="size-3" /> {copy.candidates.availability[candidate.availability]}
                  </span>
                  {candidate.salaryExpectation ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-surface px-2 py-1">
                      <WalletCards className="size-3" /> {Math.round(candidate.salaryExpectation.min / 1000)}-{Math.round(candidate.salaryExpectation.max / 1000)}K {candidate.salaryExpectation.currency}
                    </span>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {candidate.skills.slice(0, 4).map((skill) => (
                    <span
                      key={skill.name}
                      className="rounded-full border border-primary/15 bg-primary/10 px-2 py-1 text-[11px] font-semibold text-primary"
                    >
                      {skill.name}
                    </span>
                  ))}
                </div>

                <div className="rounded-2xl border border-border bg-surface/70 p-3">
                  <p className="text-xs font-semibold text-foreground">{copy.candidates.recommendedAction}</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{candidate.recommendedAction}</p>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="rounded-[22px] border border-emerald-500/20 bg-emerald-500/10 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold text-foreground">{copy.candidates.signal}</p>
          <StatusBadge tone="success">{copy.candidates.signalBadge}</StatusBadge>
        </div>
      </div>
    </SurfaceCard>
  );
}
