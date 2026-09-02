export type EmployerTrendDirection = 'up' | 'down' | 'flat';

export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat('tr-TR', {
    notation: Math.abs(value) >= 10_000 ? 'compact' : 'standard',
    maximumFractionDigits: 1
  }).format(value);
}

export function formatEmployerPercent(value: number, options?: {signed?: boolean}): string {
  const rounded = Math.round(value);
  const sign = options?.signed && rounded > 0 ? '+' : '';
  return `${sign}${rounded}%`;
}

export function formatEmployerDuration(days: number): string {
  if (days < 1) return 'Bugün';
  if (days === 1) return '1 gün';
  if (days < 7) return `${days} gün`;
  const weeks = Math.round(days / 7);
  return weeks === 1 ? '1 hafta' : `${weeks} hafta`;
}

export function getTrendDirection(value: number): EmployerTrendDirection {
  if (value > 0) return 'up';
  if (value < 0) return 'down';
  return 'flat';
}

export function clampEmployerScore(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}
