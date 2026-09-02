'use client';

import {useEffect, useMemo, useState} from 'react';

import {getEmployerCopy} from '@/lib/employer-copy';

import {EmployerAuthGate} from './employer-auth-gate';
import {EmployerSidebar} from './employer-sidebar';
import {EmployerTopbar} from './employer-topbar';

type EmployerShellProps = Readonly<{
  children: React.ReactNode;
  locale: string;
}>;

export function EmployerShell({children, locale}: EmployerShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const copy = useMemo(() => getEmployerCopy(locale), [locale]);

  useEffect(() => {
    if (!isSidebarOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsSidebarOpen(false);
    };

    document.addEventListener('keydown', onKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = '';
    };
  }, [isSidebarOpen]);

  return (
    <div className="theme-comfort-bg employer-main-shell min-h-dvh bg-background text-foreground selection:bg-primary/20">
      <a href="#employer-main" className="skip-link">{copy.shell.skipToContent}</a>
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[320px] top-[-180px] size-[420px] rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute bottom-[-220px] right-[-160px] size-[520px] rounded-full bg-accent/10 blur-3xl" />
      </div>

      <EmployerAuthGate locale={locale}>
        {(session) => (
          <div className="flex min-h-dvh">
            <EmployerSidebar locale={locale} isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

            <div className="flex min-w-0 flex-1 flex-col">
              <EmployerTopbar locale={locale} session={session} onMenuClick={() => setIsSidebarOpen(true)} />
              <main id="employer-main" tabIndex={-1} className="flex-1 scroll-mt-24 px-4 py-4 outline-none sm:px-6 sm:py-6 xl:px-8">
                <div className="employer-content-frame">{children}</div>
              </main>
            </div>
          </div>
        )}
      </EmployerAuthGate>
    </div>
  );
}
