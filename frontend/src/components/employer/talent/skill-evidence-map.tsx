import {CheckCircle2, Code2, FileSearch, ShieldQuestion} from 'lucide-react';

import {StatusBadge, SurfaceCard} from '@/components/employer/ui';
import {cn} from '@/lib/utils';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity, EmployerCandidateSkill} from '@/types/employer';

function buildSkillEvidence(candidate: EmployerCandidateOpportunity, skill: EmployerCandidateSkill, index: number, locale: string) {
  const highlight = candidate.highlights[index % Math.max(candidate.highlights.length, 1)];
  if (highlight) return highlight;
  return locale.startsWith('tr')
    ? `${skill.name} becerisi CV ve profil sinyallerinden çıkarıldı; görüşmede kapsam ve derinlik doğrulanmalı.`
    : `${skill.name} was inferred from CV and profile signals; verify scope and depth in interview.`;
}

function levelLabel(level: EmployerCandidateSkill['level'] | undefined, locale: string) {
  const labels = locale.startsWith('tr')
    ? {beginner: 'Başlangıç', intermediate: 'Orta', advanced: 'İleri', expert: 'Uzman'}
    : {beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced', expert: 'Expert'};
  return level ? labels[level] : labels.intermediate;
}

export function SkillEvidenceMap({candidate, locale}: {candidate: EmployerCandidateOpportunity; locale: string}) {
  const copy = getTalentWorkflowCopy(locale);

  return (
    <SurfaceCard variant="elevated" padding="none" className="overflow-hidden">
      <div className="border-b border-border/70 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.skillEvidence.title}</p>
            <h3 className="mt-2 text-lg font-black tracking-[-0.03em] text-foreground">{copy.skillEvidence.title}</h3>
            <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">{copy.skillEvidence.description}</p>
          </div>
          <div className="hidden size-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary sm:flex">
            <FileSearch className="size-5" />
          </div>
        </div>
      </div>

      <div className="grid gap-3 p-4 sm:grid-cols-2 sm:p-5">
        {candidate.skills.map((skill, index) => (
          <div key={skill.name} className="rounded-[22px] border border-border bg-surface-muted/45 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <div className={cn('flex size-10 shrink-0 items-center justify-center rounded-2xl border', skill.matched ? 'border-emerald-500/20 bg-emerald-500/10 text-success' : 'border-border bg-surface text-muted-foreground')}>
                  {skill.matched ? <CheckCircle2 className="size-5" /> : <Code2 className="size-5" />}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-black text-foreground">{skill.name}</p>
                  <p className="mt-1 text-xs font-bold text-muted-foreground">{levelLabel(skill.level, locale)} · {skill.years ?? 1} {copy.skillEvidence.years}</p>
                </div>
              </div>
              <StatusBadge tone={skill.matched ? 'success' : 'neutral'} className="text-[10px]">
                {skill.matched ? copy.skillEvidence.matched : copy.skillEvidence.extra}
              </StatusBadge>
            </div>
            <p className="mt-3 text-sm font-semibold leading-6 text-muted-foreground">{buildSkillEvidence(candidate, skill, index, locale)}</p>
            <div className="mt-3 rounded-2xl border border-border bg-surface p-3">
              <div className="flex items-start gap-2">
                <ShieldQuestion className="mt-0.5 size-4 shrink-0 text-warning" />
                <p className="text-xs font-bold leading-5 text-muted-foreground">
                  {locale.startsWith('tr')
                    ? `Görüşmede ${skill.name} için gerçek proje kapsamı, sahiplenme seviyesi ve son 12 ay kullanımı doğrulansın.`
                    : `Verify real project scope, ownership level and last-12-month usage for ${skill.name} in the interview.`}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SurfaceCard>
  );
}
