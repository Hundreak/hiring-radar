import Link from 'next/link';

import {BrandLogo} from '@/components/brand/brand-logo';
import {LocaleSwitcher} from '@/components/layout/locale-switcher';
import {ThemeToggle} from '@/components/theme/theme-toggle';
import type {SupportedLocale} from '@/types/user';

type PublicHeaderProps = {
  locale: string;
};

const copy = {
  tr: {
    login: 'Giriş yap',
    signup: 'Ücretsiz başla',
    subtitle: 'AI destekli kariyer platformu'
  },
  en: {
    login: 'Log in',
    signup: 'Get started free',
    subtitle: 'AI-powered job discovery'
  },
  de: {
    login: 'Einloggen',
    signup: 'Kostenlos starten',
    subtitle: 'KI-gestützte Jobsuche'
  }
} as const;

function resolveLocale(locale: string): SupportedLocale {
  if (locale === 'tr' || locale === 'en' || locale === 'de') return locale;
  return 'tr';
}

export function PublicHeader({locale}: PublicHeaderProps) {
  const safeLocale = resolveLocale(locale);
  const t = copy[safeLocale];

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur-xl">
      <div className="container-shell flex min-h-[76px] items-center justify-between gap-4 py-3">
        <Link
          href={`/${safeLocale}`}
          aria-label="NoyTera home"
          className="inline-flex min-w-0 items-center gap-3"
        >
          <BrandLogo size="lg" showSubtitle={false} asLink={false} className="shrink-0" />

          <div className="min-w-0">
            <div className="truncate text-[1.85rem] font-semibold leading-none tracking-tight text-foreground sm:text-[2rem]">
              NoyTera
            </div>
            <div className="mt-1 truncate text-sm leading-none text-muted-foreground">
              {t.subtitle}
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          <ThemeToggle />

          <Link
            href={`/${safeLocale}/login`}
            className="inline-flex h-11 items-center justify-center rounded-2xl border border-border px-5 text-sm font-medium text-foreground transition hover:border-border-strong hover:bg-surface-muted"
          >
            {t.login}
          </Link>

          <Link
            href={`/${safeLocale}/signup`}
            className="inline-flex h-11 items-center justify-center rounded-2xl bg-primary px-5 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
          >
            {t.signup}
          </Link>
        </div>
      </div>
    </header>
  );
}

export default PublicHeader;