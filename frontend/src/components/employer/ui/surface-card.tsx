import {cn} from '@/lib/utils';

type SurfaceCardProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: 'default' | 'muted' | 'elevated' | 'interactive' | 'accent';
  padding?: 'none' | 'sm' | 'md' | 'lg';
};

const variantClasses: Record<NonNullable<SurfaceCardProps['variant']>, string> = {
  default: 'border-border bg-surface/90 shadow-[0_24px_80px_rgba(15,23,42,0.08)]',
  muted: 'border-border/80 bg-surface-muted/70',
  elevated: 'border-primary/10 bg-surface shadow-[0_28px_100px_rgba(15,23,42,0.16)]',
  interactive:
    'border-border bg-surface/90 transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[0_24px_80px_rgba(15,23,42,0.14)]',
  accent:
    'border-primary/20 bg-[linear-gradient(135deg,var(--surface),rgba(99,102,241,0.08))] shadow-[0_28px_100px_rgba(15,23,42,0.16)]'
};

const paddingClasses: Record<NonNullable<SurfaceCardProps['padding']>, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6'
};

export function SurfaceCard({
  className,
  variant = 'default',
  padding = 'md',
  ...props
}: SurfaceCardProps) {
  return (
    <section
      className={cn(
        'rounded-[28px] border backdrop-blur-sm',
        variantClasses[variant],
        paddingClasses[padding],
        className
      )}
      {...props}
    />
  );
}
