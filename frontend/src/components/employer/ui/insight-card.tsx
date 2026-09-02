import {ArrowRight, Sparkles} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

import {StatusBadge} from './status-badge';
import {SurfaceCard} from './surface-card';

type InsightCardProps = {
  title: string;
  description: string;
  eyebrow?: string;
  confidence?: number;
  bullets?: string[];
  primaryAction?: {
    label: string;
    onClick?: () => void;
  };
  secondaryAction?: React.ReactNode;
  className?: string;
};

export function InsightCard({
  title,
  description,
  eyebrow = 'AI Insight',
  confidence,
  bullets,
  primaryAction,
  secondaryAction,
  className
}: InsightCardProps) {
  return (
    <SurfaceCard variant="accent" className={cn('relative overflow-hidden', className)}>
      <div className="absolute right-0 top-0 size-40 rounded-full bg-primary/10 blur-3xl" aria-hidden="true" />
      <div className="relative space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge tone="ai" icon={<Sparkles className="size-3.5" />}>
            {eyebrow}
          </StatusBadge>
          {typeof confidence === 'number' ? (
            <StatusBadge tone="info">Güven: %{Math.round(confidence)}</StatusBadge>
          ) : null}
        </div>
        <div className="max-w-3xl space-y-2">
          <h3 className="text-2xl font-semibold tracking-[-0.03em] text-foreground">{title}</h3>
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
        {bullets?.length ? (
          <ul className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
            {bullets.map((bullet) => (
              <li key={bullet} className="flex gap-2 rounded-2xl border border-border/70 bg-surface/60 p-3">
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {(primaryAction || secondaryAction) ? (
          <div className="flex flex-wrap items-center gap-3">
            {primaryAction ? (
              <Button type="button" size="sm" onClick={primaryAction.onClick}>
                {primaryAction.label}
                <ArrowRight className="ml-2 size-4" />
              </Button>
            ) : null}
            {secondaryAction}
          </div>
        ) : null}
      </div>
    </SurfaceCard>
  );
}
