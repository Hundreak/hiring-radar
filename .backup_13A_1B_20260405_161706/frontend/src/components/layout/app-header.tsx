import Link from 'next/link';
import {BellDot, Bookmark, Radar, Search, UserCircle2} from 'lucide-react';
import {getTranslations} from 'next-intl/server';

import {LocaleSwitcher} from '@/components/layout/locale-switcher';
import {ThemeToggle} from '@/components/theme/theme-toggle';
import {Input} from '@/components/ui/input';

export async function AppHeader({locale}: {locale: string}) {
  const t = await getTranslations({locale, namespace: 'common'});

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/80 backdrop-blur-xl">
      <div className="container-shell flex flex-col gap-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/${locale}/jobs`} className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Radar className="size-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-tight">Hiring Radar</div>
              <div className="text-xs text-muted-foreground">
                {t('appNavigation.jobs')}
              </div>
            </div>
          </Link>

          <nav className="hidden items-center gap-2 lg:flex">
            <Link className="rounded-full px-3 py-2 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground" href={`/${locale}/jobs`}>
              {t('appNavigation.jobs')}
            </Link>
            <Link className="rounded-full px-3 py-2 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground" href={`/${locale}/matches`}>
              {t('appNavigation.matches')}
            </Link>
            <Link className="rounded-full px-3 py-2 text-sm text-muted-foreground hover:bg-surface-muted hover:text-foreground" href={`/${locale}/saved`}>
              {t('appNavigation.saved')}
            </Link>
          </nav>
        </div>

        <div className="flex flex-1 items-center gap-3 lg:max-w-xl">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder={t('jobs.searchPlaceholder')} className="pl-11" />
          </div>
          <div className="hidden items-center gap-2 lg:flex">
            <LocaleSwitcher />
            <ThemeToggle />
            <Link
              href={`/${locale}/saved`}
              className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <Bookmark className="size-4" />
            </Link>
            <Link
              href={`/${locale}/settings/notifications`}
              className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <BellDot className="size-4" />
            </Link>
            <Link
              href={`/${locale}/settings/profile`}
              className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <UserCircle2 className="size-4" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
