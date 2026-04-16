'use client';

import Link from 'next/link';
import {Languages} from 'lucide-react';
import {useLocale} from 'next-intl';
import {usePathname} from 'next/navigation';

import {routing} from '@/i18n/routing';
import {cn, sluglessPathname} from '@/lib/utils';

const localeLabels: Record<string, string> = {
  tr: 'TR',
  en: 'EN',
  de: 'DE'
};

export function LocaleSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();

  const suffix = sluglessPathname(pathname);

  return (
    <div className="flex items-center gap-1 rounded-2xl border border-border bg-surface-muted p-1">
      <div className="flex size-9 items-center justify-center text-muted-foreground">
        <Languages className="size-4" />
      </div>

      {routing.locales.map((item) => (
        <Link
          key={item}
          href={`/${item}${suffix || ''}`}
          className={cn(
            'rounded-xl px-3 py-2 text-xs font-semibold transition',
            item === locale
              ? 'bg-primary/15 text-secondary-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-surface-strong hover:text-foreground'
          )}
        >
          {localeLabels[item]}
        </Link>
      ))}
    </div>
  );
}
