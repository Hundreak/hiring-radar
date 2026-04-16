import {type ClassValue, clsx} from 'clsx';
import {twMerge} from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function sluglessPathname(pathname: string): string {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return '';
  return `/${segments.slice(1).join('/')}`;
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}
