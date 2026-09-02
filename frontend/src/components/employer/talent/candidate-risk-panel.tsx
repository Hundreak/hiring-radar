import {AlertTriangle, HelpCircle, ShieldCheck} from 'lucide-react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity} from '@/types/employer';

export function CandidateRiskPanel({candidate, locale}: {candidate: EmployerCandidateOpportunity; locale: string}) {
  const copy = getTalentWorkflowCopy(locale);
  const questions: string[] = candidate.risks.length > 0
    ? candidate.risks.map((risk) => locale.startsWith('tr') ? `${risk} konusu görüşmede nasıl doğrulanmalı?` : `How should we verify ${risk} in interview?`)
    : [copy.risk.noClearRiskLong];
  const hasRisk = candidate.risks.length > 1;

  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
      <div className="border-b border-border/70 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge tone={hasRisk ? 'warning' : 'success'} icon={hasRisk ? <AlertTriangle className="size-3.5" /> : <ShieldCheck className="size-3.5" />}>
                {hasRisk ? copy.risk.needsVerification : copy.risk.lowRisk}
              </StatusBadge>
            </div>
            <h3 className="mt-3 text-lg font-black tracking-[-0.03em] text-foreground">{copy.risk.title}</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">{copy.risk.description}</p>
          </div>
        </div>
      </div>
      <div className="grid gap-3 p-4 sm:grid-cols-2 sm:p-5">
        <div className="space-y-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.risk.riskSignals}</p>
          {(candidate.risks.length > 0 ? candidate.risks : [copy.risk.noClearRisk]).map((risk) => (
            <div key={risk} className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm font-bold leading-6 text-foreground">
              {risk}
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.risk.questions}</p>
          {questions.map((question) => (
            <div key={question} className="flex items-start gap-3 rounded-2xl border border-border bg-surface-muted/55 p-3">
              <HelpCircle className="mt-0.5 size-4 shrink-0 text-primary" />
              <p className="text-sm font-semibold leading-6 text-muted-foreground">{question}</p>
            </div>
          ))}
        </div>
      </div>
    </SurfaceCard>
  );
}
