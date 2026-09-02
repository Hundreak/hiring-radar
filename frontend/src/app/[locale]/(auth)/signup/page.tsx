import {Suspense} from 'react';

import {PublicFooter} from '@/components/layout/public-footer';
import {PublicHeader} from '@/components/layout/public-header';
import {SignupView} from '@/components/auth/signup-view';

export default async function SignupPage({
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
            {locale === 'tr' ? 'Kayıt ekranı yükleniyor…' : 'Loading sign-up…'}
          </section>
        }
      >
        <SignupView locale={locale} />
      </Suspense>
      <PublicFooter locale={locale} />
    </div>
  );
}
