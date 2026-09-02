import {cn} from '@/lib/utils';
import {clampEmployerScore} from '@/lib/employer-format';

type ScoreBadgeProps = {
  score: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

function getScoreTone(score: number): string {
  if (score >= 85) return 'border-emerald-500/30 bg-emerald-500/10 text-success';
  if (score >= 70) return 'border-blue-500/30 bg-blue-500/10 text-blue-500';
  if (score >= 55) return 'border-amber-500/30 bg-amber-500/10 text-warning';
  return 'border-red-500/30 bg-red-500/10 text-danger';
}

const sizeClasses = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base'
};

export function ScoreBadge({score, label = 'Skor', size = 'md', className}: ScoreBadgeProps) {
  const normalizedScore = clampEmployerScore(score);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border font-semibold tabular-nums',
        getScoreTone(normalizedScore),
        sizeClasses[size],
        className
      )}
      aria-label={`${label}: ${normalizedScore} / 100`}
    >
      <span className="opacity-80">{label}</span>
      <span>{normalizedScore}</span>
    </span>
  );
}
