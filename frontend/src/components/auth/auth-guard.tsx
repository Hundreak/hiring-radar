'use client';

import {useEffect, useState} from 'react';
import {usePathname, useRouter} from 'next/navigation';

import {ApiError, api} from '@/lib/api';
import {buildLoginRedirectHref} from '@/lib/auth-redirect';

export function AuthGuard({
  locale,
  children,
}: {
  locale: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    api
      .getSession()
      .then(() => {
        if (active) {
          setStatus('ready');
        }
      })
      .catch((reason: Error) => {
        if (!active) {
          return;
        }

        if (reason instanceof ApiError && reason.status === 401) {
          router.replace(
            buildLoginRedirectHref({
              locale,
              pathname: pathname || `/${locale}/jobs`,
              surface: 'candidate',
            })
          );
          return;
        }

        setError(reason.message);
        setStatus('error');
      });

    return () => {
      active = false;
    };
  }, [locale, pathname, router]);

  if (status === 'loading') {
    return (
      <main className="container-shell py-14">
        <div className="card-surface rounded-[28px] border border-border bg-surface p-8 text-sm text-muted-foreground">
          Loading your workspace…
        </div>
      </main>
    );
  }

  if (status === 'error') {
    return (
      <main className="container-shell py-14">
        <div className="card-surface rounded-[28px] border border-border bg-surface p-8">
          <div className="text-lg font-semibold tracking-tight">
            Workspace unavailable
          </div>
          <p className="mt-2 text-sm text-rose-600">
            {error || 'Unable to load your session.'}
          </p>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
