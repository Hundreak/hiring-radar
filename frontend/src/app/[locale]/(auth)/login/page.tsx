import {Suspense} from 'react';

import {LoginView} from '@/components/auth/login-view';
import {PublicFooter} from '@/components/layout/public-footer';
import {PublicHeader} from '@/components/layout/public-header';

export default async function LoginPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <PublicHeader locale={locale} />
      <Suspense
        fallback={
          <section className="container-shell py-16 text-sm text-muted-foreground">
            Loading sign-in…
          </section>
        }
      >
        <LoginView locale={locale} />
      </Suspense>
      <PublicFooter locale={locale} />
    </div>
  );
}
