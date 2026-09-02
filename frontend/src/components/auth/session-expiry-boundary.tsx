'use client';

import {useEffect, useState} from 'react';
import {useLocale} from 'next-intl';
import {usePathname, useRouter} from 'next/navigation';
import {useQueryClient} from '@tanstack/react-query';
import {AlertTriangle, LogIn} from 'lucide-react';

import {buildLoginRedirectHref} from '@/lib/auth-redirect';
import {onSessionExpired, type AuthSessionExpiredDetail} from '@/lib/auth-session-events';

const copy = {
  tr: {
    eyebrow: 'Oturum yenileme gerekli',
    title: 'Oturumun süresi doldu',
    body: 'Güvenliğin için çalışma alanı kilitlendi. Devam etmek için tekrar giriş yap.',
    action: 'Tekrar giriş yap',
    requestId: 'İstek ID',
  },
  en: {
    eyebrow: 'Session refresh required',
    title: 'Your session expired',
    body: 'For your security, the workspace has been locked. Sign in again to continue.',
    action: 'Sign in again',
    requestId: 'Request ID',
  },
  de: {
    eyebrow: 'Sitzung erneuern',
    title: 'Deine Sitzung ist abgelaufen',
    body: 'Zu deiner Sicherheit wurde der Arbeitsbereich gesperrt. Melde dich erneut an, um fortzufahren.',
    action: 'Erneut anmelden',
    requestId: 'Request-ID',
  },
} as const;

type SupportedCopyLocale = keyof typeof copy;

function getCopy(locale: string) {
  return copy[(locale as SupportedCopyLocale) in copy ? (locale as SupportedCopyLocale) : 'en'];
}

export function SessionExpiryBoundary() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [expired, setExpired] = useState<AuthSessionExpiredDetail | null>(null);
  const text = getCopy(locale);

  const search = typeof window === 'undefined' ? '' : window.location.search;

  useEffect(() => {
    return onSessionExpired((detail) => {
      if (pathname.endsWith('/login')) {
        return;
      }

      queryClient.clear();
      setExpired(detail);
    });
  }, [pathname, queryClient]);

  if (!expired) {
    return null;
  }

  const loginHref = buildLoginRedirectHref({
    locale,
    pathname,
    search,
    surface: expired.surface,
  });

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/70 px-4 backdrop-blur-xl">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="session-expired-title"
        className="w-full max-w-md rounded-[32px] border border-border bg-surface-elevated p-6 shadow-[0_30px_100px_-35px_rgba(15,23,42,0.65)]"
      >
        <div className="flex size-12 items-center justify-center rounded-2xl bg-danger/10 text-danger">
          <AlertTriangle className="size-5" />
        </div>
        <div className="mt-5 text-xs font-bold uppercase tracking-[0.24em] text-danger/80">
          {text.eyebrow}
        </div>
        <h2 id="session-expired-title" className="mt-2 text-2xl font-black tracking-tight text-foreground">
          {text.title}
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{text.body}</p>

        {expired.requestId ? (
          <div className="mt-4 rounded-2xl border border-border bg-muted/20 px-4 py-3 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">{text.requestId}:</span> {expired.requestId}
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => {
            router.replace(loginHref);
            router.refresh();
          }}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
        >
          <LogIn className="size-4" />
          {text.action}
        </button>
      </div>
    </div>
  );
}
