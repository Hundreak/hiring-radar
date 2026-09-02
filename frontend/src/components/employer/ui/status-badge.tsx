import {Circle, CircleAlert, CircleCheck, Clock3, Sparkles} from 'lucide-react';

import {cn} from '@/lib/utils';

type EmployerStatusTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'ai';

type StatusBadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: EmployerStatusTone;
  icon?: React.ReactNode;
};

const toneClasses: Record<EmployerStatusTone, string> = {
  neutral: 'border-border bg-surface-muted text-muted-foreground',
  success: 'border-emerald-500/20 bg-emerald-500/10 text-success',
  warning: 'border-amber-500/20 bg-amber-500/10 text-warning',
  danger: 'border-red-500/20 bg-red-500/10 text-danger',
  info: 'border-blue-500/20 bg-blue-500/10 text-blue-500',
  ai: 'border-primary/20 bg-primary/10 text-primary'
};

const defaultIcons: Record<EmployerStatusTone, React.ReactNode> = {
  neutral: <Circle className="size-3" />,
  success: <CircleCheck className="size-3.5" />,
  warning: <Clock3 className="size-3.5" />,
  danger: <CircleAlert className="size-3.5" />,
  info: <Circle className="size-3" />,
  ai: <Sparkles className="size-3.5" />
};

export function StatusBadge({tone = 'neutral', icon, className, children, ...props}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold',
        toneClasses[tone],
        className
      )}
      {...props}
    >
      {icon ?? defaultIcons[tone]}
      {children}
    </span>
  );
}
