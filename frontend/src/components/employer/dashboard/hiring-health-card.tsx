import {ArrowUpRight, CheckCircle2, Clock3, Gauge, Info} from 'lucide-react';

import type {EmployerInsightTone, HiringHealthScore} from '@/types/employer';
import type {EmployerCockpitCopy} from '@/lib/employer-cockpit-copy';
import {cn} from '@/lib/utils';

const driverToneClasses: Record<EmployerInsightTone, string> = {
  ai: 'bg-primary/10 text-primary border-primary/20',
  info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  success: 'bg-emerald-500/10 text-success border-emerald-500/20',
  warning: 'bg-amber-500/10 text-warning border-amber-500/20',
  danger: 'bg-red-500/10 text-danger border-red-500/20',
};

const driverIcons: Record<EmployerInsightTone, typeof CheckCircle2> = {
  ai: Gauge,
  info: Info,
  success: CheckCircle2,
  warning: Clock3,
  danger: Clock3,
};

type HiringHealthCardProps = {
  health: HiringHealthScore;
  copy: EmployerCockpitCopy;
};

export function HiringHealthCard({health, copy}: HiringHealthCardProps) {
  const stroke = `${health.score}, 100`;

  return (
    <aside className="rounded-[28px] border border-border bg-surface-elevated/80 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-primary">{copy.hiringHealth.eyebrow}</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-foreground">{health.label}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{health.summary}</p>
        </div>
        <div className="relative size-28 shrink-0">
          <svg viewBox="0 0 36 36" className="size-full -rotate-90" aria-hidden="true">
            <path
              d="M18 2.0845a15.9155 15.9155 0 1 1 0 31.831a15.9155 15.9155 0 1 1 0-31.831"
              fill="none"
              stroke="var(--surface-strong)"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845a15.9155 15.9155 0 1 1 0 31.831a15.9155 15.9155 0 1 1 0-31.831"
              fill="none"
              stroke="var(--primary)"
              strokeDasharray={stroke}
              strokeLinecap="round"
              strokeWidth="3"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-black tracking-[-0.06em] text-foreground">{health.score}</span>
            <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">/100</span>
          </div>
        </div>
      </div>

      <div className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-success">
        <ArrowUpRight className="size-3.5" />
        {health.change} {copy.hiringHealth.thisWeek}
      </div>

      <div className="mt-5 grid gap-3">
        {health.drivers.map((driver) => {
          const Icon = driverIcons[driver.tone];
          return (
            <div key={driver.id} className="rounded-2xl border border-border bg-surface/70 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  <span className={cn('flex size-8 shrink-0 items-center justify-center rounded-xl border', driverToneClasses[driver.tone])}>
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">{driver.label}</p>
                    <p className="truncate text-xs text-muted-foreground">{driver.description}</p>
                  </div>
                </div>
                <span className="text-sm font-bold tabular-nums text-foreground">{driver.value}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-muted">
                <div className="h-full rounded-full bg-primary" style={{width: `${driver.value}%`}} />
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
