'use client';

import type {ReactNode} from 'react';
import {AlertCircle, CheckCircle2, Info, TriangleAlert, X} from 'lucide-react';

export type FeedbackTone = 'success' | 'error' | 'warning' | 'info';

const toneMap: Record<FeedbackTone, {container: string; icon: string; Icon: typeof CheckCircle2}> = {
  success: {
    container: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    icon: 'text-emerald-600',
    Icon: CheckCircle2,
  },
  error: {
    container: 'border-rose-200 bg-rose-50 text-rose-800',
    icon: 'text-rose-600',
    Icon: AlertCircle,
  },
  warning: {
    container: 'border-amber-200 bg-amber-50 text-amber-800',
    icon: 'text-amber-600',
    Icon: TriangleAlert,
  },
  info: {
    container: 'border-sky-200 bg-sky-50 text-sky-800',
    icon: 'text-sky-600',
    Icon: Info,
  },
};

export function FeedbackBanner({
  tone,
  title,
  children,
  onDismiss,
  className = '',
}: {
  tone: FeedbackTone;
  title?: string | null;
  children: ReactNode;
  onDismiss?: (() => void) | null;
  className?: string;
}) {
  const {container, icon, Icon} = toneMap[tone];

  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${container} ${className}`.trim()} role="status" aria-live="polite">
      <div className="flex items-start gap-3">
        <Icon className={`mt-0.5 size-4 shrink-0 ${icon}`} />
        <div className="min-w-0 flex-1">
          {title ? <div className="font-semibold">{title}</div> : null}
          <div className={title ? 'mt-1 leading-6' : 'leading-6'}>{children}</div>
        </div>
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="inline-flex size-7 shrink-0 items-center justify-center rounded-full border border-current/15 bg-white/50 text-current transition hover:bg-white/80"
            aria-label="Kapat"
          >
            <X className="size-4" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
