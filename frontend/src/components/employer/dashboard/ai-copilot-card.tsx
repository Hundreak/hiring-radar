import Link from 'next/link';
import {ArrowRight, CheckCircle2, ShieldCheck, Sparkles} from 'lucide-react';

import {InsightCard, StatusBadge} from '@/components/employer/ui';
import type {EmployerInsight} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';

export function AiCopilotCard({insight, baseHref, copy}: {insight: EmployerInsight; baseHref: string; copy: EmployerCockpitCopy}) {
  const localizedInsight = copy.ai.insights[insight.id] ?? {
    title: insight.title,
    description: insight.description,
    actionLabel: insight.actionLabel ?? '',
    evidence: insight.evidence ?? [],
  };

  return (
    <InsightCard
      eyebrow={copy.ai.eyebrow}
      confidence={91}
      title={localizedInsight.title}
      description={localizedInsight.description}
      bullets={localizedInsight.evidence}
      secondaryAction={
        <>
          {insight.actionHref && localizedInsight.actionLabel ? (
            <Link
              href={localizeHref(insight.actionHref, baseHref)}
              className="inline-flex h-9 items-center justify-center rounded-2xl bg-primary px-3.5 text-xs font-semibold text-primary-foreground shadow-sm transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
            >
              {localizedInsight.actionLabel}
              <ArrowRight className="ml-2 size-4" />
            </Link>
          ) : null}
          <Link
            href={`${baseHref}/analytics`}
            className="inline-flex h-9 items-center gap-2 rounded-2xl border border-border bg-surface px-3.5 text-xs font-semibold text-foreground transition hover:border-primary/35 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
          >
            {copy.ai.seeRisks}
          </Link>
          <StatusBadge tone="success" icon={<ShieldCheck className="size-3.5" />}>
            {copy.ai.humanApprovalRequired}
          </StatusBadge>
        </>
      }
      className="min-h-full"
    />
  );
}

export function AiEvidencePill({children}: {children: React.ReactNode}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-primary/15 bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
      <Sparkles className="size-3" />
      {children}
    </span>
  );
}

export function ConfirmedPill({children}: {children: React.ReactNode}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/15 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-success">
      <CheckCircle2 className="size-3" />
      {children}
    </span>
  );
}

function localizeHref(href: string, baseHref: string): string {
  if (href.startsWith('/tr/employer')) return href.replace('/tr/employer', baseHref);
  return href;
}
