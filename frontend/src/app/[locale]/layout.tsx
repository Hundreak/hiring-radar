import {notFound} from 'next/navigation';
import {hasLocale} from 'next-intl';
import {getMessages, setRequestLocale} from 'next-intl/server';

import {IntlProvider} from '@/components/providers/intl-provider';
import {ThemeProvider} from '@/components/theme/theme-provider';
import {routing} from '@/i18n/routing';

export function generateStaticParams() {
  return routing.locales.map((locale) => ({locale}));
}

export default async function LocaleLayout({
  children,
  params
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{locale: string}>;
}>) {
  const {locale} = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);

  const messages = await getMessages();

  return (
    <IntlProvider locale={locale} messages={messages}>
      <ThemeProvider>{children}</ThemeProvider>
    </IntlProvider>
  );
}
