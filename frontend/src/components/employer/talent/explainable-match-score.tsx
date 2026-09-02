import {BadgeCheck, BriefcaseBusiness, CircleDollarSign, Clock3, MapPin, Puzzle, Radar, ShieldCheck} from 'lucide-react';

import {ScoreBadge, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {cn} from '@/lib/utils';
import {formatWorkflowSalary, getTalentWorkflowCopy, workflowAvailabilityLabels, getTalentWorkflowLanguage, workflowWorkModelLabels} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity} from '@/types/employer';

type MatchFactor = {
  id: string;
  label: string;
  score: number;
  weight: number;
  evidence: string;
  icon: typeof ShieldCheck;
  tone: 'success' | 'info' | 'warning' | 'ai';
};

function clampScore(value: number) {
  return Math.max(42, Math.min(99, Math.round(value)));
}

export function buildExplainableMatchFactors(candidate: EmployerCandidateOpportunity, locale = 'tr'): MatchFactor[] {
  const copy = getTalentWorkflowCopy(locale);
  const lang = getTalentWorkflowLanguage(locale);
  const availability = workflowAvailabilityLabels[lang];
  const workModels = workflowWorkModelLabels[lang];
  const matchedSkills = candidate.skills.filter((skill) => skill.matched).length;
  const matchedSkillNames = candidate.skills.filter((skill) => skill.matched).slice(0, 4).map((skill) => skill.name).join(', ');
  const skillScore = clampScore((matchedSkills / Math.max(candidate.skills.length, 1)) * 100 + candidate.matchScore * 0.15);
  const experienceScore = clampScore(62 + candidate.experience * 5 + (candidate.targetRole ? 6 : 0));
  const workModelScore = candidate.workPreference === 'flexible' ? 94 : candidate.workPreference === 'hybrid' ? 88 : candidate.workPreference === 'remote' ? 84 : 78;
  const salaryScore = candidate.salaryExpectation ? clampScore(100 - Math.max(candidate.salaryExpectation.max - 130000, 0) / 1600) : 68;
  const intentScore = clampScore(candidate.intentScore + (candidate.availability === 'immediate' ? 12 : candidate.availability === 'two_weeks' ? 7 : 0));
  const verificationScore = clampScore(92 - candidate.risks.length * 8 + candidate.highlights.length * 3);

  return [
    {
      id: 'skills',
      label: copy.explainable.requiredSkills,
      score: skillScore,
      weight: 32,
      evidence: copy.explainable.skillsEvidence(matchedSkills, candidate.skills.length, matchedSkillNames),
      icon: Puzzle,
      tone: 'success',
    },
    {
      id: 'experience',
      label: copy.explainable.roleExperience,
      score: experienceScore,
      weight: 20,
      evidence: locale.startsWith('tr')
        ? `${candidate.experience} yıllık deneyim ve ${candidate.targetRole ?? candidate.headline} odağı rol beklentisine yakın.`
        : `${candidate.experience} years of experience and focus on ${candidate.targetRole ?? candidate.headline} are close to the role expectation.`,
      icon: BriefcaseBusiness,
      tone: 'info',
    },
    {
      id: 'work-model',
      label: copy.explainable.workModel,
      score: workModelScore,
      weight: 14,
      evidence: locale.startsWith('tr')
        ? `${candidate.location} lokasyonu ve ${workModels[candidate.workPreference]} çalışma tercihi ilan esnekliğiyle değerlendirildi.`
        : `${candidate.location} and ${workModels[candidate.workPreference]} preference were evaluated against job flexibility.`,
      icon: MapPin,
      tone: workModelScore >= 85 ? 'success' : 'warning',
    },
    {
      id: 'salary',
      label: copy.explainable.salaryFit,
      score: salaryScore,
      weight: 12,
      evidence: candidate.salaryExpectation ? copy.explainable.salaryEvidence(formatWorkflowSalary(candidate, locale)) : copy.explainable.salaryMissing,
      icon: CircleDollarSign,
      tone: salaryScore >= 78 ? 'success' : 'warning',
    },
    {
      id: 'intent',
      label: copy.explainable.intentAccess,
      score: intentScore,
      weight: 14,
      evidence: locale.startsWith('tr')
        ? `${candidate.lastActiveAt} aktifti; müsaitlik sinyali: ${availability[candidate.availability]}.`
        : `Active ${candidate.lastActiveAt}; availability signal: ${availability[candidate.availability]}.`,
      icon: Radar,
      tone: intentScore >= 82 ? 'ai' : 'info',
    },
    {
      id: 'verification',
      label: copy.explainable.verificationRisk,
      score: verificationScore,
      weight: 8,
      evidence: copy.explainable.verificationEvidence(candidate.risks.length),
      icon: ShieldCheck,
      tone: verificationScore >= 78 ? 'success' : 'warning',
    },
  ];
}

export function ExplainableMatchScore({candidate, locale}: {candidate: EmployerCandidateOpportunity; locale: string}) {
  const copy = getTalentWorkflowCopy(locale);
  const factors = buildExplainableMatchFactors(candidate, locale);
  const weightedScore = Math.round(factors.reduce((total, factor) => total + factor.score * factor.weight, 0) / factors.reduce((total, factor) => total + factor.weight, 0));

  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
      <div className="border-b border-border/70 bg-surface-muted/35 p-4 sm:p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge tone="ai" icon={<BadgeCheck className="size-3.5" />}>{copy.explainable.badge}</StatusBadge>
              <StatusBadge tone="info" icon={<Clock3 className="size-3.5" />}>{copy.explainable.humanApproval}</StatusBadge>
            </div>
            <h3 className="mt-3 text-lg font-black tracking-[-0.03em] text-foreground">{copy.explainable.title}</h3>
            <p className="mt-1 max-w-2xl text-sm font-semibold leading-6 text-muted-foreground">{copy.explainable.description}</p>
          </div>
          <ScoreBadge score={weightedScore} label={copy.common.weighted} size="lg" />
        </div>
      </div>

      <div className="divide-y divide-border/70">
        {factors.map((factor) => {
          const Icon = factor.icon;
          return (
            <div key={factor.id} className="grid gap-3 p-4 sm:grid-cols-[minmax(0,1fr)_160px] sm:items-center sm:p-5">
              <div className="flex min-w-0 gap-3">
                <div className={cn('flex size-11 shrink-0 items-center justify-center rounded-2xl border', factor.tone === 'success' && 'border-emerald-500/20 bg-emerald-500/10 text-success', factor.tone === 'warning' && 'border-amber-500/20 bg-amber-500/10 text-warning', factor.tone === 'info' && 'border-blue-500/20 bg-blue-500/10 text-blue-500', factor.tone === 'ai' && 'border-primary/20 bg-primary/10 text-primary')}>
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-black text-foreground">{factor.label}</p>
                    <span className="rounded-full bg-surface-muted px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.12em] text-muted-foreground">%{factor.weight}</span>
                  </div>
                  <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">{factor.evidence}</p>
                </div>
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between text-xs font-black text-muted-foreground">
                  <span>{copy.common.status}</span>
                  <span>{factor.score}/100</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-surface-muted">
                  <div className="h-full rounded-full bg-[linear-gradient(90deg,var(--primary),var(--accent))]" style={{width: `${factor.score}%`}} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}
