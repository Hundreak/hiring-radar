import Link from 'next/link';
import {ArrowRight, AlertTriangle} from 'lucide-react';

import {SectionHeader, StatusBadge, SurfaceCard} from '@/components/employer/ui';
import type {EmployerPipelineStage} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';

const stageTone: Record<EmployerPipelineStage['tone'], 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'ai'> = {
  ai: 'ai',
  info: 'info',
  success: 'success',
  warning: 'warning',
  danger: 'danger',
};

export function PipelineMini({stages, baseHref, copy}: {stages: EmployerPipelineStage[]; baseHref: string; copy: EmployerCockpitCopy}) {
  const maxCount = Math.max(...stages.map((stage) => stage.count), 1);
  const totalOverdue = stages.reduce((sum, stage) => sum + stage.overdueCount, 0);

  return (
    <SurfaceCard className="space-y-5">
      <SectionHeader
        eyebrow={copy.pipeline.eyebrow}
        title={copy.pipeline.title}
        description={copy.pipeline.description}
        action={
          <Link href={`${baseHref}/candidates`} className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
            {copy.pipeline.openPipeline} <ArrowRight className="size-4" />
          </Link>
        }
      />

      {totalOverdue > 0 ? (
        <div className="flex flex-wrap items-center gap-3 rounded-[22px] border border-amber-500/20 bg-amber-500/10 p-4">
          <span className="flex size-10 items-center justify-center rounded-2xl bg-amber-500/10 text-warning">
            <AlertTriangle className="size-5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-foreground">{copy.pipeline.overdueTitle(totalOverdue)}</p>
            <p className="text-xs text-muted-foreground">{copy.pipeline.overdueDescription}</p>
          </div>
          <StatusBadge tone="warning">{copy.pipeline.slaRisk}</StatusBadge>
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-5">
        {stages.map((stage) => {
          const height = Math.max(16, Math.round((stage.count / maxCount) * 100));
          return (
            <div key={stage.id} className="rounded-[22px] border border-border bg-surface/70 p-3">
              <div className="flex h-28 items-end rounded-2xl bg-surface-muted p-2">
                <div className="w-full rounded-2xl bg-primary/80" style={{height: `${height}%`}} />
              </div>
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-bold text-foreground">{stage.label}</p>
                  <span className="text-sm font-black tabular-nums text-foreground">{stage.count}</span>
                </div>
                <p className="min-h-8 text-xs leading-4 text-muted-foreground">{stage.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  <StatusBadge tone={stageTone[stage.tone]} className="px-2 py-0.5 text-[10px]">
                    %{Math.round(stage.conversionRate ?? 0)} {copy.pipeline.conversion}
                  </StatusBadge>
                  {stage.overdueCount > 0 ? (
                    <StatusBadge tone="warning" className="px-2 py-0.5 text-[10px]">
                      {stage.overdueCount} {copy.pipeline.delayed}
                    </StatusBadge>
                  ) : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}
