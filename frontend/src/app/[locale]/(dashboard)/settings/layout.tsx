import {getTranslations} from 'next-intl/server';

import {SettingsNav} from '@/components/layout/settings-nav';

export default async function SettingsLayout({
  children,
  params
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{locale: string}>;
}>) {
  const {locale} = await params;
  const t = await getTranslations({locale, namespace: 'settings'});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('pageTitle')}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{t('pageDescription')}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        <SettingsNav locale={locale} />
        <div>{children}</div>
      </div>
    </div>
  );
}
