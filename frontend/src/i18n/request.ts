import {getRequestConfig} from 'next-intl/server';

import {routing} from '@/i18n/routing';

export default getRequestConfig(async ({requestLocale}) => {
  const requested = await requestLocale;
  const locale = routing.locales.includes((requested || '') as never)
    ? requested!
    : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
    // Prevent missing-key errors from hard-crashing the page.
    // The key path is rendered verbatim so developers can spot the gap.
    onError(error) {
      if (process.env.NODE_ENV !== 'production') {
        console.warn('[next-intl]', error.message);
      }
    },
    getMessageFallback({namespace, key}) {
      return [namespace, key].filter(Boolean).join('.');
    },
  };
});
