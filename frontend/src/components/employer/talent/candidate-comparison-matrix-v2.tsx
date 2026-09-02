'use client';

import {AlertTriangle, Award, BarChart3, CheckCircle2, Clock3, DollarSign, Eye, MapPin, ShieldCheck, Sparkles, Target, TrendingUp} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {EmptyState, ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {cn} from '@/lib/utils';
import {formatWorkflowSalary, getTalentWorkflowCopy, getTalentWorkflowLanguage, workflowAvailabilityLabels, workflowCandidateStatusLabels, workflowWorkModelLabels} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity, EmployerWorkModel} from '@/types/employer';

type CandidateComparisonMatrixV2Props = {
  candidates: EmployerCandidateOpportunity[];
  onSelect: (id: number) => void;
  onOpenProfile?: (id: number) => void;
  locale: string;
};

type EnrichedCandidate = {
  candidate: EmployerCandidateOpportunity;
  skillCoverage: number;
  decisionScore: number;
  salaryFit: number;
  availabilityScore: number;
  workFitScore: number;
};

const AVAILABILITY_SCORE: Record<EmployerCandidateOpportunity['availability'], number> = {immediate: 100, two_weeks: 88, one_month: 68, passive: 42};
const WORK_FIT_SCORE: Record<EmployerWorkModel | 'flexible', number> = {office: 72, hybrid: 88, remote: 90, flexible: 96};

function getSalaryFitScore(candidate: EmployerCandidateOpportunity) {
  const max = candidate.salaryExpectation?.max;
  if (!max) return 62;
  if (max <= 105000) return 94;
  if (max <= 125000) return 84;
  if (max <= 145000) return 68;
  return 54;
}

function buildSkillUniverse(candidates: EmployerCandidateOpportunity[]) {
  const counts = new Map<string, number>();
  candidates.forEach((candidate) => {
    candidate.skills.forEach((skill) => {
      counts.set(skill.name, (counts.get(skill.name) ?? 0) + (skill.matched ? 2 : 1));
    });
  });
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 8).map(([skill]) => skill);
}

function getSkillCoverage(candidate: EmployerCandidateOpportunity, skillUniverse: string[]) {
  if (skillUniverse.length === 0) return 0;
  const candidateSkills = new Set(candidate.skills.map((skill) => skill.name.toLocaleLowerCase('tr-TR')));
  const covered = skillUniverse.filter((skill) => candidateSkills.has(skill.toLocaleLowerCase('tr-TR'))).length;
  return Math.round((covered / skillUniverse.length) * 100);
}

function getDecisionScore(candidate: EmployerCandidateOpportunity, skillCoverage: number) {
  const salaryFit = getSalaryFitScore(candidate);
  const riskPenalty = candidate.risks.length * 4;
  return Math.max(42, Math.min(98, Math.round(candidate.matchScore * 0.28 + candidate.intentScore * 0.18 + skillCoverage * 0.22 + salaryFit * 0.14 + AVAILABILITY_SCORE[candidate.availability] * 0.1 + WORK_FIT_SCORE[candidate.workPreference] * 0.08 - riskPenalty)));
}

function getTone(score: number): 'success' | 'warning' | 'danger' | 'info' | 'ai' | 'neutral' {
  if (score >= 86) return 'success';
  if (score >= 76) return 'ai';
  if (score >= 64) return 'warning';
  return 'danger';
}

function getRiskTone(count: number): 'success' | 'warning' | 'danger' {
  if (count <= 1) return 'success';
  if (count === 2) return 'warning';
  return 'danger';
}

function getCandidateSkillLevel(candidate: EmployerCandidateOpportunity, skillName: string) {
  return candidate.skills.find((skill) => skill.name.toLocaleLowerCase('tr-TR') === skillName.toLocaleLowerCase('tr-TR'));
}

function SignalMeter({score, label, compact}: {score: number; label: string; compact?: boolean}) {
  return (
    <div className={compact ? 'space-y-1' : 'space-y-2'}>
      <div className="flex items-center justify-between gap-2 text-xs font-black text-muted-foreground">
        <span>{label}</span>
        <span>{score}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--primary),var(--accent))]" style={{width: `${Math.max(4, Math.min(100, score))}%`}} />
      </div>
    </div>
  );
}

function DecisionSummaryCard({icon: Icon, label, candidate, helper, tone}: {icon: typeof Award; label: string; candidate?: EmployerCandidateOpportunity; helper: string; tone: 'success' | 'warning' | 'info' | 'ai'}) {
  return (
    <SurfaceCard variant="elevated" padding="md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
          <p className="mt-2 truncate text-lg font-black tracking-[-0.03em] text-foreground">{candidate?.name ?? '—'}</p>
          <p className="mt-1 line-clamp-2 text-xs font-semibold text-muted-foreground">{helper}</p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" /></div>
      </div>
      <div className="mt-3"><StatusBadge tone={tone}>{candidate?.headline ?? '—'}</StatusBadge></div>
    </SurfaceCard>
  );
}

function ComparisonRow({label, helper, enriched, render}: {label: string; helper: string; enriched: EnrichedCandidate[]; render: (item: EnrichedCandidate) => React.ReactNode}) {
  return (
    <div className="grid border-b border-border/80" style={{gridTemplateColumns: `220px repeat(${enriched.length}, minmax(220px, 1fr))`}}>
      <div className="border-r border-border bg-surface-muted p-4">
        <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
        <p className="mt-2 text-sm font-semibold leading-5 text-muted-foreground">{helper}</p>
      </div>
      {enriched.map((item) => (
        <div key={`${label}-${item.candidate.id}`} className="border-r border-border p-4">{render(item)}</div>
      ))}
    </div>
  );
}

export function CandidateComparisonMatrixV2({candidates, onSelect, onOpenProfile, locale}: CandidateComparisonMatrixV2Props) {
  const copy = getTalentWorkflowCopy(locale);
  const lang = getTalentWorkflowLanguage(locale);
  const availabilityLabels = workflowAvailabilityLabels[lang];
  const workModelLabels = workflowWorkModelLabels[lang];
  const statusLabels = workflowCandidateStatusLabels[lang];

  if (candidates.length === 0) {
    return <EmptyState icon={BarChart3} title={copy.compare.emptyTitle} description={copy.compare.emptyDescription} />;
  }

  const skillUniverse = buildSkillUniverse(candidates);
  const enriched = candidates.map((candidate) => {
    const skillCoverage = getSkillCoverage(candidate, skillUniverse);
    return {candidate, skillCoverage, decisionScore: getDecisionScore(candidate, skillCoverage), salaryFit: getSalaryFitScore(candidate), availabilityScore: AVAILABILITY_SCORE[candidate.availability], workFitScore: WORK_FIT_SCORE[candidate.workPreference]};
  });

  const best = [...enriched].sort((a, b) => b.decisionScore - a.decisionScore)[0];
  const fastest = [...enriched].sort((a, b) => b.availabilityScore + b.candidate.intentScore - (a.availabilityScore + a.candidate.intentScore))[0];
  const safest = [...enriched].sort((a, b) => a.candidate.risks.length - b.candidate.risks.length || b.decisionScore - a.decisionScore)[0];
  const bestSalary = [...enriched].sort((a, b) => b.salaryFit - a.salaryFit || b.decisionScore - a.decisionScore)[0];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 xl:grid-cols-4">
        <DecisionSummaryCard icon={Award} label={copy.compare.strongestDecision} candidate={best?.candidate} helper={`${best?.decisionScore ?? 0}/100`} tone="success" />
        <DecisionSummaryCard icon={Clock3} label={copy.compare.fastestClose} candidate={fastest?.candidate} helper={`${availabilityLabels[fastest?.candidate.availability ?? 'passive']} · ${copy.common.intent} ${fastest?.candidate.intentScore ?? 0}`} tone="info" />
        <DecisionSummaryCard icon={ShieldCheck} label={copy.compare.lowestRisk} candidate={safest?.candidate} helper={`${safest?.candidate.risks.length ?? 0} ${locale.startsWith('tr') ? 'risk' : 'risks'}`} tone="ai" />
        <DecisionSummaryCard icon={DollarSign} label={copy.compare.bestBudgetFit} candidate={bestSalary?.candidate} helper={`${bestSalary?.salaryFit ?? 0}/100`} tone="warning" />
      </div>

      <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
        <div className="border-b border-border/80 bg-surface-muted/35 p-4 sm:p-5">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>{copy.compare.decisionIntelligence}</StatusBadge>
                <StatusBadge tone="info" icon={<Target className="size-3.5" />}>{copy.compare.criticalSkills(skillUniverse.length)}</StatusBadge>
              </div>
              <h3 className="mt-3 text-xl font-black tracking-[-0.035em] text-foreground">{copy.compare.title}</h3>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{copy.compare.description}</p>
            </div>
            <div className="rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-bold text-primary">
              {copy.compare.aiRecommendation(best?.candidate.name ?? copy.common.candidate, fastest?.candidate.name ?? copy.common.candidate)}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[980px]">
            <div className="grid border-b border-border/80" style={{gridTemplateColumns: `220px repeat(${enriched.length}, minmax(220px, 1fr))`}}>
              <div className="border-r border-border bg-surface-muted p-4"><p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.compare.decisionSummary}</p><p className="mt-2 text-sm font-bold text-foreground">{copy.compare.calibration}</p></div>
              {enriched.map((item, index) => (
                <button key={item.candidate.id} type="button" onClick={() => onSelect(item.candidate.id)} className={cn('border-r border-border p-4 text-left transition hover:bg-surface-muted/65 focus:outline-none focus:ring-4 focus:ring-[var(--ring)]', item.candidate.id === best?.candidate.id && 'bg-success/5')}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2"><span className="flex size-9 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-xs font-black text-primary">{item.candidate.initials}</span><div className="min-w-0"><p className="truncate text-sm font-black text-foreground">{item.candidate.name}</p><p className="truncate text-xs font-semibold text-muted-foreground">{item.candidate.headline}</p></div></div>
                      <div className="mt-3 flex flex-wrap gap-1.5"><StatusBadge tone={index === 0 ? 'success' : getTone(item.decisionScore)}>{index === 0 ? (locale.startsWith('tr') ? 'Öncelikli' : 'Priority') : statusLabels[item.candidate.status]}</StatusBadge><StatusBadge tone={getRiskTone(item.candidate.risks.length)}>{item.candidate.risks.length} {locale.startsWith('tr') ? 'risk' : 'risks'}</StatusBadge></div>
                    </div>
                    <ScoreBadge score={item.decisionScore} size="md" />
                  </div>
                </button>
              ))}
            </div>

            <ComparisonRow label={locale.startsWith('tr') ? 'İşe alım güveni' : 'Hire confidence'} helper={locale.startsWith('tr') ? 'Karar skoru' : 'Decision score'} enriched={enriched} render={(item) => <SignalMeter score={item.decisionScore} label={item.decisionScore >= 86 ? (locale.startsWith('tr') ? 'Güçlü aday' : 'Strong hire') : item.decisionScore >= 76 ? (locale.startsWith('tr') ? 'İyi aday' : 'Good candidate') : (locale.startsWith('tr') ? 'Doğrula' : 'Verify')} />} />
            <ComparisonRow label={`${copy.common.match} / ${copy.common.intent}`} helper={locale.startsWith('tr') ? 'Uygunluk + sıcaklık' : 'Fit + warmth'} enriched={enriched} render={(item) => <div className="space-y-2"><SignalMeter score={item.candidate.matchScore} label={`${copy.common.match} ${item.candidate.matchScore}`} compact /><SignalMeter score={item.candidate.intentScore} label={`${copy.common.intent} ${item.candidate.intentScore}`} compact /></div>} />
            <ComparisonRow label={copy.compare.skillCoverage} helper={locale.startsWith('tr') ? 'Kritik beceriler' : 'Critical skills'} enriched={enriched} render={(item) => <div className="space-y-2"><SignalMeter score={item.skillCoverage} label={`${item.skillCoverage}%`} /><div className="flex flex-wrap gap-1.5">{skillUniverse.slice(0, 5).map((skill) => { const candidateSkill = getCandidateSkillLevel(item.candidate, skill); return <span key={`${item.candidate.id}-${skill}`} className={cn('rounded-full border px-2 py-1 text-[10px] font-black', candidateSkill ? 'border-success/25 bg-success/10 text-success' : 'border-border bg-surface-muted text-muted-foreground')}>{candidateSkill ? '✓' : '−'} {skill}</span>; })}</div></div>} />
            <ComparisonRow label={`${copy.common.salary} / ${copy.compare.closeSpeed}`} helper={locale.startsWith('tr') ? 'Bütçe ve hız' : 'Budget and speed'} enriched={enriched} render={(item) => <div className="space-y-2 text-sm font-bold text-foreground"><div className="flex items-center justify-between gap-2"><span className="text-muted-foreground">{copy.common.salary}</span><span>{formatWorkflowSalary(item.candidate, locale)}</span></div><SignalMeter score={item.salaryFit} label={`${copy.compare.salaryFit} ${item.salaryFit}`} compact /><div className="flex items-center justify-between gap-2"><span className="text-muted-foreground">{copy.common.availability}</span><StatusBadge tone={getTone(item.availabilityScore)}>{availabilityLabels[item.candidate.availability]}</StatusBadge></div></div>} />
            <ComparisonRow label={locale.startsWith('tr') ? 'Lokasyon / model' : 'Location / model'} helper={locale.startsWith('tr') ? 'Operasyon uyumu' : 'Operational fit'} enriched={enriched} render={(item) => <div className="space-y-2"><div className="flex items-center gap-2 text-sm font-bold text-foreground"><MapPin className="size-4 text-muted-foreground" />{item.candidate.location}</div><SignalMeter score={item.workFitScore} label={workModelLabels[item.candidate.workPreference]} compact /></div>} />
            <ComparisonRow label={copy.compare.riskMatrix} helper={locale.startsWith('tr') ? 'Görüşmede açılacak konular' : 'Topics to verify in interview'} enriched={enriched} render={(item) => <div className="space-y-2">{item.candidate.risks.length > 0 ? item.candidate.risks.slice(0, 3).map((risk) => <div key={risk} className="flex gap-2 rounded-2xl border border-warning/20 bg-warning/10 p-2 text-xs font-semibold leading-5 text-foreground"><AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-warning" /><span>{risk}</span></div>) : <div className="flex gap-2 rounded-2xl border border-success/20 bg-success/10 p-2 text-xs font-bold text-success"><CheckCircle2 className="size-3.5" />{locale.startsWith('tr') ? 'Kritik risk yok' : 'No critical risk'}</div>}</div>} />
            <ComparisonRow label={copy.compare.nextAction} helper={locale.startsWith('tr') ? 'Sonraki en iyi adım' : 'Next best step'} enriched={enriched} render={(item) => <div className="space-y-3"><p className="text-sm font-bold leading-6 text-foreground">{item.candidate.recommendedAction}</p><div className="flex flex-wrap gap-2"><Button size="sm" className="gap-2" onClick={() => onOpenProfile?.(item.candidate.id)}><Eye className="size-3.5" />{copy.compare.open360}</Button><Button size="sm" variant="secondary" className="gap-2" onClick={() => onSelect(item.candidate.id)}><ArrowRightIcon />{copy.compare.select}</Button></div></div>} />
          </div>
        </div>
      </SurfaceCard>
    </div>
  );
}

function ArrowRightIcon() {
  return <TrendingUp className="size-3.5" />;
}
