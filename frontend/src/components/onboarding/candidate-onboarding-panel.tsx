'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ArrowRight, CheckCircle2, CircleDashed, Sparkles, X} from 'lucide-react';
import {useMemo, useSyncExternalStore} from 'react';

import {
  buildCandidateOnboardingModel,
  getCandidateOnboardingCopy,
  type CandidateOnboardingStepStatus,
} from '@/lib/candidate-onboarding';
import {cn} from '@/lib/utils';
import {
  getQueryErrorMessage,
  useSavedJobsQuery,
  useUserProfileAggregateQuery,
} from '@/hooks/use-api-queries';

const DISMISS_STORAGE_KEY = 'noytera:candidate-onboarding:dismissed-until';
const DISMISS_DURATION_MS = 24 * 60 * 60 * 1000;

function readDismissedUntil(): number {
  if (typeof window === 'undefined') return 0;
  const raw = window.localStorage.getItem(DISMISS_STORAGE_KEY);
  const parsed = raw ? Number.parseInt(raw, 10) : 0;
  return Number.isFinite(parsed) ? parsed : 0;
}

// useSyncExternalStore icin kucuk bir abonelik katmani. localStorage kendi
// basina degisim bildirmedigi icin kapatma islemi dinleyicileri elle uyarir;
// baska sekmelerden gelen degisimler `storage` olayindan gelir.
const dismissalListeners = new Set<() => void>();

function subscribeToDismissal(onStoreChange: () => void): () => void {
  dismissalListeners.add(onStoreChange);
  if (typeof window !== 'undefined') {
    window.addEventListener('storage', onStoreChange);
  }
  return () => {
    dismissalListeners.delete(onStoreChange);
    if (typeof window !== 'undefined') {
      window.removeEventListener('storage', onStoreChange);
    }
  };
}

function notifyDismissalChanged(): void {
  for (const listener of dismissalListeners) listener();
}

function StepIcon({status}: {status: CandidateOnboardingStepStatus}) {
  if (status === 'done') {
    return <CheckCircle2 className="size-3.5 text-success" />;
  }

  if (status === 'current') {
    return <Sparkles className="size-3.5 text-secondary-foreground" />;
  }

  return <CircleDashed className="size-3.5 text-muted-foreground/70" />;
}

function LoadingSkeleton() {
  return (
    <section className="container-shell pt-6">
      <div className="overflow-hidden rounded-[24px] border border-border bg-surface/70 p-4 shadow-sm">
        <div className="flex animate-pulse flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="h-3 w-36 rounded-full bg-muted" />
            <div className="h-4 w-72 max-w-full rounded-full bg-muted" />
          </div>
          <div className="h-9 w-32 rounded-2xl bg-muted" />
        </div>
      </div>
    </section>
  );
}

export function CandidateOnboardingPanel({locale}: {locale: string}) {
  const pathname = usePathname();
  const profileQuery = useUserProfileAggregateQuery();
  const savedJobsQuery = useSavedJobsQuery();

  // Kapatilma bilgisi yalnizca istemcide okunabilir. Effect + setState yerine
  // useSyncExternalStore: sunucu anlik goruntusu false, istemci gercek deger.
  // Boylece hidrasyon uyumsuzlugu da olusmaz.
  const dismissed = useSyncExternalStore(
    subscribeToDismissal,
    () => readDismissedUntil() > Date.now(),
    () => false,
  );

  const copy = useMemo(() => getCandidateOnboardingCopy(locale), [locale]);
  const savedJobCount = savedJobsQuery.data?.items.length ?? 0;
  const model = useMemo(
    () => buildCandidateOnboardingModel({
      aggregate: profileQuery.data ?? null,
      savedJobCount,
      locale,
    }),
    [locale, profileQuery.data, savedJobCount]
  );

  const error =
    getQueryErrorMessage(profileQuery.error) ??
    getQueryErrorMessage(savedJobsQuery.error);

  if (pathname?.includes('/settings/profile')) {
    return null;
  }

  if (dismissed || error) {
    return null;
  }

  if (profileQuery.isLoading) {
    return <LoadingSkeleton />;
  }

  if (!model) {
    return null;
  }

  function dismissForToday() {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(
        DISMISS_STORAGE_KEY,
        String(Date.now() + DISMISS_DURATION_MS)
      );
    }
    notifyDismissalChanged();
  }

  return (
    <section className="container-shell pt-6">
      <div className="relative overflow-hidden rounded-[28px] border border-primary/15 bg-gradient-to-br from-primary/[0.12] via-surface to-background p-4 shadow-[0_18px_60px_-44px_rgba(15,23,42,0.65)] sm:p-5">
        <div className="pointer-events-none absolute -right-16 -top-20 size-44 rounded-full bg-primary/15 blur-3xl" />
        <div className="relative flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0 space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-secondary-foreground backdrop-blur">
              <span className="size-1.5 rounded-full bg-primary animate-pulse-dot" />
              {copy.eyebrow}
            </div>
            <div>
              <h2 className="text-base font-semibold tracking-tight text-foreground sm:text-lg">
                {model.title}
              </h2>
              <p className="mt-1 max-w-3xl text-xs leading-6 text-muted-foreground sm:text-sm">
                {model.description}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {model.steps.map((step) => (
                <div
                  key={step.key}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition',
                    step.status === 'done' && 'border-success/20 bg-success/8 text-foreground/75',
                    step.status === 'current' && 'border-primary/30 bg-primary/15 text-secondary-foreground',
                    step.status === 'todo' && 'border-border bg-background/60 text-muted-foreground'
                  )}
                  title={step.description}
                >
                  <StepIcon status={step.status} />
                  {step.title}
                </div>
              ))}
            </div>
          </div>

          <div className="flex min-w-[260px] flex-col gap-3 rounded-[22px] border border-border/80 bg-background/80 p-4 shadow-sm backdrop-blur">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                  {copy.progressLabel}
                </div>
                <div className="mt-1 text-sm font-semibold text-foreground">
                  {model.progressLabel}
                </div>
              </div>
              <div className="rounded-2xl bg-primary/15 px-3 py-1.5 text-sm font-bold text-secondary-foreground">
                {model.progressPercent}%
              </div>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{width: `${model.progressPercent}%`}}
              />
            </div>
            <div className="rounded-2xl border border-border bg-surface-muted/80 p-3">
              <div className="text-xs font-semibold text-foreground">{model.nextAction.title}</div>
              <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                {model.nextAction.description}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href={`/${locale}${model.nextAction.href}`}
                className="inline-flex min-h-9 flex-1 items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary px-3 py-2 text-xs font-bold text-primary-foreground shadow-[0_12px_28px_color-mix(in_srgb,var(--primary)_20%,transparent)] transition hover:-translate-y-0.5"
              >
                {model.nextAction.cta}
                <ArrowRight className="size-3.5" />
              </Link>
              <button
                type="button"
                onClick={dismissForToday}
                className="inline-flex size-9 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/30 hover:text-foreground"
                aria-label={copy.dismissLabel}
                title={copy.dismissLabel}
              >
                <X className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
