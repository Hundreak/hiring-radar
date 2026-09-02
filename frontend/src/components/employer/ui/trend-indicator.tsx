import {ArrowDownRight, ArrowRight, ArrowUpRight} from 'lucide-react';

import {cn} from '@/lib/utils';
import {formatEmployerPercent, getTrendDirection, type EmployerTrendDirection} from '@/lib/employer-format';

type TrendIndicatorProps = {
  value: number;
  label?: string;
  direction?: EmployerTrendDirection;
  positiveDirection?: 'up' | 'down';
  className?: string;
};

export function TrendIndicator({
  value,
  label,
  direction = getTrendDirection(value),
  positiveDirection = 'up',
  className
}: TrendIndicatorProps) {
  const isPositive = direction === 'flat' ? null : direction === positiveDirection;
  const Icon = direction === 'up' ? ArrowUpRight : direction === 'down' ? ArrowDownRight : ArrowRight;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold',
        isPositive === true && 'bg-emerald-500/10 text-success',
        isPositive === false && 'bg-red-500/10 text-danger',
        isPositive === null && 'bg-surface-muted text-muted-foreground',
        className
      )}
    >
      <Icon className="size-3.5" />
      <span>{formatEmployerPercent(value, {signed: true})}</span>
      {label ? <span className="font-medium opacity-80">{label}</span> : null}
    </span>
  );
}
