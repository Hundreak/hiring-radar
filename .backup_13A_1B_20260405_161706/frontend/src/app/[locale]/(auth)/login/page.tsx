import Link from 'next/link';
import {getTranslations} from 'next-intl/server';

import {PublicHeader} from '@/components/layout/public-header';
import {Button} from '@/components/ui/button';
import {Card} from '@/components/ui/card';
import {Input} from '@/components/ui/input';

export default async function LoginPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'auth'});

  return (
    <>
      <PublicHeader locale={locale} />
      <section className="container-shell grid auth-grid items-start gap-8 pb-24 pt-10">
        <Card className="p-8">
          <div className="space-y-5">
            <div className="inline-flex rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent">
              {t('loginProductBadge')}
            </div>
            <h1 className="text-4xl font-bold tracking-tight">{t('loginHeadline')}</h1>
            <p className="max-w-xl text-base leading-8 text-muted-foreground">
              {t('loginDescription')}
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              {['signal', 'clarity', 'control', 'multilingual'].map((item) => (
                <div key={item} className="rounded-3xl border border-border bg-surface-muted p-5">
                  <h2 className="font-semibold">{t(`marketing.${item}.title`)}</h2>
                  <p className="mt-2 text-sm leading-7 text-muted-foreground">
                    {t(`marketing.${item}.description`)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card className="p-8">
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">{t('loginTitle')}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{t('loginSubtext')}</p>
            </div>
            <div className="grid gap-3">
              <Input placeholder={t('fields.email')} />
              <Input type="password" placeholder={t('fields.password')} />
              <Button>{t('passwordLogin')}</Button>
            </div>
            <div className="relative py-1 text-center text-xs uppercase tracking-[0.22em] text-muted-foreground">
              {t('or')}
            </div>
            <div className="grid gap-3">
              <Input placeholder={t('fields.magicLinkEmail')} />
              <Button variant="secondary">{t('magicLinkLogin')}</Button>
            </div>
            <div className="flex items-center justify-between text-sm">
              <Link href={`/${locale}/signup`} className="font-medium text-primary">
                {t('createAccount')}
              </Link>
              <Link href={`/${locale}/login`} className="text-muted-foreground">
                {t('forgotPassword')}
              </Link>
            </div>
          </div>
        </Card>
      </section>
    </>
  );
}
