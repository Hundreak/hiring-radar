'use client';

import {ShieldCheck} from 'lucide-react';
import {usePathname, useRouter} from 'next/navigation';
import {useEffect, type ReactNode} from 'react';

import {ApiError} from '@/lib/api';
import {buildLoginRedirectHref} from '@/lib/auth-redirect';
import {useEmployerSessionQuery} from '@/hooks/use-api-queries';
import type {EmployerAuthSession} from '@/types/user';

type EmployerAuthGateProps = Readonly<{
  locale: string;
  children: (session: EmployerAuthSession) => ReactNode;
}>;

export function EmployerAuthGate({locale, children}: EmployerAuthGateProps) {
  const router = useRouter();
  const pathname = usePathname();
  const {data, error, isLoading, isError} = useEmployerSessionQuery();

  useEffect(() => {
    if (!isError) return;

    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      router.replace(
        buildLoginRedirectHref({
          locale,
          pathname: pathname || `/${locale}/employer/dashboard`,
          surface: 'employer',
        })
      );
    }
  }, [error, isError, locale, pathname, router]);

  if (data) {
    return <>{children(data)}</>;
  }

  const message = isError
    ? 'İşveren oturumu doğrulanıyor. Giriş sayfasına yönlendiriliyorsunuz.'
    : 'İşveren çalışma alanı hazırlanıyor.';

  return (
    <div className="flex min-h-dvh items-center justify-center px-6">
      <div className="w-full max-w-md rounded-3xl border border-border bg-surface-elevated p-6 text-center shadow-2xl shadow-black/20">
        <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <ShieldCheck className="size-5" />
        </div>
        <h1 className="mt-4 text-lg font-black text-foreground">Güvenli işveren alanı</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{message}</p>
        {isLoading ? (
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-surface-muted">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-primary/60" />
          </div>
        ) : null}
      </div>
    </div>
  );
}
