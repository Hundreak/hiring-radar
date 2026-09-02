import {type LucideIcon} from 'lucide-react';

import {formatCompactNumber} from '@/lib/employer-format';
import {cn} from '@/lib/utils';

import {SurfaceCard} from './surface-card';
import {TrendIndicator} from './trend-indicator';

type MetricCardProps = {
  label: string;
  value: number | string;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label?: string;
    positiveDirection?: 'up' | 'down';
  };
  action?: React.ReactNode;
  className?: string;
};

export function MetricCard({label, value, description, icon: Icon, trend, action, className}: MetricCardProps) {
  const displayValue = typeof value === 'number' ? formatCompactNumber(value) : value;

  return (
    <SurfaceCard variant="interactive" className={cn('group relative overflow-hidden', className)}>
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 transition group-hover:opacity-100" />
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-3xl font-semibold tracking-[-0.04em] text-foreground">{displayValue}</p>
            {trend ? (
              <TrendIndicator
                value={trend.value}
                label={trend.label}
                positiveDirection={trend.positiveDirection}
              />
            ) : null}
          </div>
          {description ? <p className="text-sm leading-5 text-muted-foreground">{description}</p> : null}
        </div>
        {Icon ? (
          <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl border border-border bg-surface-muted text-primary shadow-sm">
            <Icon className="size-5" />
          </div>
        ) : null}
      </div>
      {action ? <div className="mt-5 border-t border-border/70 pt-4">{action}</div> : null}
    </SurfaceCard>
  );
}
