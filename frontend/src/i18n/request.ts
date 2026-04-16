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
  };
});
