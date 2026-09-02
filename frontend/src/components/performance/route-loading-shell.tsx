import {cn} from '@/lib/utils';

type RouteLoadingShellProps = Readonly<{
  variant?: 'candidate' | 'employer';
  title?: string;
  description?: string;
}>;

function SkeletonLine({className}: {className?: string}) {
  return <div className={cn('animate-pulse rounded-full bg-muted/80', className)} />;
}

function SkeletonCard({className}: {className?: string}) {
  return (
    <div className={cn('rounded-2xl border border-border bg-surface p-4 shadow-sm', className)}>
      <div className="space-y-3">
        <SkeletonLine className="h-3 w-20" />
        <SkeletonLine className="h-5 w-3/5" />
        <SkeletonLine className="h-3 w-full" />
        <SkeletonLine className="h-3 w-4/5" />
      </div>
    </div>
  );
}

function CandidateSkeleton() {
  return (
    <div className="container-shell py-8">
      <div className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <SkeletonLine className="h-4 w-32" />
            <SkeletonLine className="h-7 w-64" />
            <SkeletonLine className="h-3 w-80 max-w-full" />
          </div>
          <SkeletonLine className="h-10 w-36 rounded-2xl" />
        </div>

        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="hidden space-y-3 lg:block">
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard className="md:col-span-2" />
          </div>
        </div>
      </div>
    </div>
  );
}

function EmployerSkeleton() {
  return (
    <div className="theme-comfort-bg employer-main-shell min-h-dvh bg-background text-foreground">
      <div className="flex min-h-dvh">
        <aside className="hidden w-[280px] shrink-0 border-r border-border bg-surface/70 p-5 lg:block">
          <SkeletonLine className="h-9 w-32" />
          <div className="mt-8 space-y-3">
            {Array.from({length: 7}).map((_, index) => (
              <SkeletonLine key={index} className="h-9 w-full rounded-2xl" />
            ))}
          </div>
        </aside>
        <main className="min-w-0 flex-1 px-4 py-5 sm:px-6 xl:px-8">
          <div className="mb-5 flex items-center justify-between gap-4 rounded-3xl border border-border bg-surface/75 p-4 shadow-sm">
            <div className="space-y-2">
              <SkeletonLine className="h-4 w-28" />
              <SkeletonLine className="h-6 w-56" />
            </div>
            <SkeletonLine className="h-10 w-10 rounded-2xl" />
          </div>
          <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
            <div className="grid gap-3 md:grid-cols-2">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard className="md:col-span-2" />
            </div>
            <div className="space-y-3">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export function RouteLoadingShell({variant = 'candidate'}: RouteLoadingShellProps) {
  if (variant === 'employer') {
    return <EmployerSkeleton />;
  }

  return <CandidateSkeleton />;
}
