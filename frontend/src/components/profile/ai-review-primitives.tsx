'use client';

import type {ReactNode} from 'react';
import {CheckCircle2, Loader2, RefreshCw, Sparkles, X} from 'lucide-react';

import {Button} from '@/components/ui/button';

function renderMultiline(text: string) {
  if (!text.trim()) {
    return <span className="text-muted-foreground">Henüz içerik yok.</span>;
  }

  return text.split('\n').map((line, index) => (
    <span key={`${line}-${index}`} className="block">
      {line || ' '}
    </span>
  ));
}

export function AiPanelShell({
  badgeLabel,
  title,
  body,
  isLoading,
  loadingTitle,
  loadingSteps,
  retryDisabled,
  onRetry,
  retryLabel,
  onClose,
  closeLabel,
  children,
  headerActions,
  errorTitle,
  errorMessage,
}: {
  badgeLabel: string;
  title: string;
  body: string;
  isLoading: boolean;
  loadingTitle: string;
  loadingSteps: string[];
  retryDisabled?: boolean;
  onRetry: () => void;
  retryLabel: string;
  onClose: () => void;
  closeLabel: string;
  children: ReactNode;
  headerActions?: ReactNode;
  errorTitle?: string;
  errorMessage?: string | null;
}) {
  return (
    <div className="mt-5 overflow-hidden rounded-[28px] border border-border bg-gradient-to-br from-background via-background to-muted/30 shadow-[0_20px_60px_-36px_rgba(94,92,230,0.35)]">
      <div className="border-b border-border/80 bg-gradient-to-r from-violet-500/10 via-fuchsia-500/8 to-cyan-500/10 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700 dark:text-violet-200">
              <Sparkles className="size-3.5" />
              {badgeLabel}
            </div>
            <h3 className="mt-3 text-lg font-semibold tracking-tight text-foreground">{title}</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{body}</p>
          </div>
          <div className="flex items-center gap-2">
            {headerActions}
            <Button type="button" variant="secondary" onClick={onRetry} disabled={isLoading || retryDisabled}>
              {isLoading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <RefreshCw className="mr-2 size-4" />}
              {retryLabel}
            </Button>
            <Button type="button" variant="ghost" onClick={onClose} aria-label={closeLabel}>
              <X className="size-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5">
        {errorMessage ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100">
            {errorTitle ? <div className="font-semibold">{errorTitle}</div> : null}
            <div className={errorTitle ? 'mt-1' : ''}>{errorMessage}</div>
          </div>
        ) : null}

        {isLoading ? (
          <div className="rounded-2xl border border-border bg-muted/20 px-4 py-5">
            <div className="flex items-center gap-3 text-sm font-medium text-foreground">
              <Loader2 className="size-4 animate-spin" />
              {loadingTitle}
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {loadingSteps.map((step) => (
                <div key={step} className="rounded-2xl border border-border bg-background/80 px-4 py-4 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    <span className="inline-flex size-2.5 rounded-full bg-violet-500 animate-pulse" />
                    {step}
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-muted">
                    <div className="h-2 w-2/3 animate-pulse rounded-full bg-violet-500/50" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {!isLoading ? children : null}
      </div>
    </div>
  );
}

export function AiPreviewBox({
  label,
  value,
  emphasized = false,
}: {
  label: string;
  value: string;
  emphasized?: boolean;
}) {
  return (
    <div className={`rounded-2xl border px-4 py-3 ${emphasized ? 'border-violet-300 bg-violet-50/60 dark:border-violet-400/30 dark:bg-violet-500/10' : 'border-border bg-background/80'}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-sm leading-6 text-foreground whitespace-pre-wrap break-words">{renderMultiline(value)}</div>
    </div>
  );
}

export function AiSuggestionAppliedBadge({
  visible,
  label,
}: {
  visible: boolean;
  label: string;
}) {
  if (!visible) return null;

  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700 dark:border-emerald-400/30 dark:bg-emerald-500/10 dark:text-emerald-200">
      <CheckCircle2 className="size-3.5" />
      {label}
    </div>
  );
}
