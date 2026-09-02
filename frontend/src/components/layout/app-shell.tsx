import {Suspense} from 'react';

import {AuthGuard} from '@/components/auth/auth-guard';
import {CopilotWidgetLoader} from '@/components/ai/copilot-widget-loader';
import {AppHeader} from '@/components/layout/app-header';
import {CandidateOnboardingPanel} from '@/components/onboarding/candidate-onboarding-panel';

export function AppShell({locale, children}: {locale: string; children: React.ReactNode}) {
  return (
    <AuthGuard locale={locale}>
      <Suspense fallback={<div className="container-shell py-4 text-sm text-muted-foreground">Loading navigation…</div>}>
        <AppHeader locale={locale} />
      </Suspense>
      <CandidateOnboardingPanel locale={locale} />
      <main className="container-shell py-8">{children}</main>
      <CopilotWidgetLoader locale={locale} />
    </AuthGuard>
  );
}
