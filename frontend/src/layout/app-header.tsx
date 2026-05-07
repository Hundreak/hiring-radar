'use client';

import Link from 'next/link';
import {useRouter, useSearchParams} from 'next/navigation';
import {Bookmark, Radar, Search} from 'lucide-react';
import {useTranslations} from 'next-intl';
import {useState} from 'react';

import {LocaleSwitcher} from '@/components/layout/locale-switcher';
import {UserMenu} from '@/components/layout/user-menu';
import {ThemeToggle} from '@/components/theme/theme-toggle';
import {Input} from '@/components/ui/input';
import type {SupportedLocale} from '@/types/user';

export function AppHeader({locale}: {locale: string}) {
  const t = useTranslations('common');
  const jobsT = useTranslations('jobs');
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');

  function submitSearch(event: React.FormEvent) {
    event.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    if (query.trim()) params.set('q', query.trim());
    else params.delete('q');
    router.push(`/${locale}/jobs?${params.toString()}`);
  }

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/80 backdrop-blur-xl">
      <div className="container-shell flex flex-col gap-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/${locale}/jobs`} className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Radar className="size-5" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-tight">NoyTera</div>
              <div className="text-xs text-muted-foreground">{t('appNavigation.jobs')}</div>
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
          <form onSubmit={submitSearch} className="relative flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={jobsT('searchPlaceholder')}
              className="pl-11"
            />
          </form>
          <div className="hidden items-center gap-2 lg:flex">
            <LocaleSwitcher />
            <ThemeToggle />
            <Link
              href={`/${locale}/saved`}
              className="inline-flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              <Bookmark className="size-4" />
            </Link>
            <UserMenu locale={locale as SupportedLocale} />
          </div>
        </div>
      </div>
    </header>
  );
}
