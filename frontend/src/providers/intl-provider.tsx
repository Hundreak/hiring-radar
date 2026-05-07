'use client';

import {NextIntlClientProvider} from 'next-intl';
import type {AbstractIntlMessages} from 'next-intl';

export function IntlProvider({
  locale,
  messages,
  children,
}: {
  locale: string;
  messages: AbstractIntlMessages;
  children: React.ReactNode;
}) {
  return (
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
      onError={(error) => {
        if (process.env.NODE_ENV !== 'production') {
          console.warn('[next-intl missing key]', error.message);
        }
      }}
      getMessageFallback={({namespace, key}) =>
        [namespace, key].filter(Boolean).join('.')
      }
    >
      {children}
    </NextIntlClientProvider>
  );
}
