import {ArrowRight, type LucideIcon} from 'lucide-react';

import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

import {SurfaceCard} from './surface-card';

type EmptyStateProps = {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick?: () => void;
  };
  secondaryAction?: React.ReactNode;
  className?: string;
};

export function EmptyState({icon: Icon, title, description, action, secondaryAction, className}: EmptyStateProps) {
  return (
    <SurfaceCard
      variant="muted"
      className={cn('flex min-h-[260px] items-center justify-center border-dashed text-center', className)}
    >
      <div className="mx-auto flex max-w-md flex-col items-center gap-4">
        {Icon ? (
          <div className="flex size-14 items-center justify-center rounded-3xl border border-border bg-surface text-primary shadow-sm">
            <Icon className="size-6" />
          </div>
        ) : null}
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
        {(action || secondaryAction) ? (
          <div className="flex flex-wrap items-center justify-center gap-3">
            {action ? (
              <Button type="button" size="sm" onClick={action.onClick}>
                {action.label}
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
