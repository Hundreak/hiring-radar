import {Activity, ClipboardCheck, Clock3, Eye, MailCheck, Radar} from 'lucide-react';

import {SurfaceCard} from '@/components/employer/ui';
import {cn} from '@/lib/utils';
import {getTalentWorkflowCopy} from '@/lib/employer-talent-workflow-copy';
import type {EmployerCandidateOpportunity} from '@/types/employer';

type TimelineTone = 'primary' | 'success' | 'info' | 'warning';

export function CandidateTimeline({candidate, locale}: {candidate: EmployerCandidateOpportunity; locale: string}) {
  const copy = getTalentWorkflowCopy(locale);
  const events: Array<{id: string; title: string; description: string; time: string; icon: typeof Radar; tone: TimelineTone}> = [
    {
      id: 'source',
      title: copy.timeline.sourceTitle,
      description: candidate.source === 'talent_radar' ? copy.timeline.sourceRadar : copy.timeline.sourcePool,
      time: candidate.appliedAt,
      icon: Radar,
      tone: 'primary',
    },
    {
      id: 'activity',
      title: copy.timeline.activityTitle,
      description: candidate.lastActiveAt,
      time: candidate.lastActiveAt,
      icon: Activity,
      tone: 'success',
    },
    {
      id: 'review',
      title: copy.timeline.reviewTitle,
      description: candidate.recommendedAction,
      time: copy.common.now,
      icon: Eye,
      tone: 'info',
    },
    {
      id: 'next',
      title: copy.timeline.nextTitle,
      description: candidate.recommendedAction,
      time: copy.common.next,
      icon: ClipboardCheck,
      tone: 'warning',
    },
  ];

  return (
    <SurfaceCard variant="elevated" padding="md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-muted-foreground">{copy.timeline.eyebrow}</p>
          <h3 className="mt-2 text-lg font-black tracking-[-0.03em] text-foreground">{copy.timeline.title}</h3>
        </div>
        <div className="flex size-11 items-center justify-center rounded-2xl bg-surface-muted text-primary">
          <Clock3 className="size-5" />
        </div>
      </div>

      <div className="mt-5 space-y-4">
        {events.map((event, index) => {
          const Icon = event.icon;
          return (
            <div key={event.id} className="relative flex gap-3">
              {index < events.length - 1 && <span className="absolute left-5 top-10 h-[calc(100%+0.25rem)] w-px bg-border" />}
              <div className={cn('relative z-10 flex size-10 shrink-0 items-center justify-center rounded-2xl border bg-surface', event.tone === 'primary' && 'border-primary/20 text-primary', event.tone === 'success' && 'border-emerald-500/20 text-success', event.tone === 'info' && 'border-blue-500/20 text-blue-500', event.tone === 'warning' && 'border-amber-500/20 text-warning')}>
                <Icon className="size-4" />
              </div>
              <div className="min-w-0 flex-1 rounded-2xl border border-border bg-surface-muted/45 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-black text-foreground">{event.title}</p>
                  <span className="inline-flex items-center gap-1 rounded-full bg-surface px-2 py-0.5 text-[10px] font-black uppercase tracking-[0.12em] text-muted-foreground">
                    <MailCheck className="size-3" /> {event.time}
                  </span>
                </div>
                <p className="mt-1 text-sm font-semibold leading-6 text-muted-foreground">{event.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}
