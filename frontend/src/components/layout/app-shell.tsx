import {Suspense} from 'react';

import {AuthGuard} from '@/components/auth/auth-guard';
import {CopilotWidget} from '@/components/ai/copilot-widget';
import {AppHeader} from '@/components/layout/app-header';

export function AppShell({locale, children}: {locale: string; children: React.ReactNode}) {
  return (
    <AuthGuard locale={locale}>
      <Suspense fallback={<div className="container-shell py-4 text-sm text-muted-foreground">Loading navigation…</div>}>
        <AppHeader locale={locale} />
      </Suspense>
      <main className="container-shell py-8">{children}</main>
      <CopilotWidget locale={locale} />
    </AuthGuard>
  );
}
