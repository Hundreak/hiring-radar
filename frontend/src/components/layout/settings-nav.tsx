'use client';

import Link from 'next/link';
import {useSelectedLayoutSegment} from 'next/navigation';
import {useTranslations} from 'next-intl';

const items = ['profile', 'security', 'preferences', 'notifications'] as const;

export function SettingsNav({locale}: {locale: string}) {
  const segment = useSelectedLayoutSegment();
  const t = useTranslations('settings');

  return (
    <aside className="card-surface rounded-[28px] border border-border bg-surface p-3">
      <div className="px-3 pb-3 pt-2 text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
        {t('navTitle')}
      </div>
      <nav className="flex flex-col gap-1">
        {items.map((item) => {
          const active = segment === item || (!segment && item === 'profile')
          return (
            <Link
              key={item}
              href={`/${locale}/settings/${item}`}
              className={
                active
                  ? 'rounded-2xl bg-surface-strong px-4 py-3 text-sm font-semibold text-foreground'
                  : 'rounded-2xl px-4 py-3 text-sm text-muted-foreground transition hover:bg-surface-muted hover:text-foreground'
              }
            >
              {t(`tabs.${item}`)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
