'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Bell, ChevronRight, Command, Menu, Plus, Search, Sparkles} from 'lucide-react';
import {useMemo} from 'react';

import {IconButton} from '@/components/ui/icon-button';
import {getEmployerCopy} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';
import type {EmployerAuthSession} from '@/types/user';

import {EmployerUserMenu} from './employer-user-menu';
import {getEmployerNavSections, getEmployerQuickActions} from './employer-nav';

type EmployerTopbarProps = {
  locale: string;
  session: EmployerAuthSession;
  onMenuClick: () => void;
};

function getCurrentPage(locale: string, pathname: string) {
  const sections = getEmployerNavSections(locale);
  const items = sections.flatMap((section) => section.items).filter((item) => !item.disabled);
  const exactMatch = items.find((item) => pathname === item.href);
  if (exactMatch) return exactMatch;

  return items
    .filter((item) => pathname.startsWith(`${item.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0] ?? items[0];
}

export function EmployerTopbar({locale, session, onMenuClick}: EmployerTopbarProps) {
  const pathname = usePathname();
  const copy = useMemo(() => getEmployerCopy(locale), [locale]);
  const currentPage = getCurrentPage(locale, pathname);
  const quickActions = getEmployerQuickActions(locale);
  const CurrentIcon = currentPage.icon;

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/88 backdrop-blur-2xl supports-[backdrop-filter]:bg-background/72">
      <div className="flex min-h-[76px] items-center justify-between gap-3 px-4 py-3 sm:px-6 xl:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="touch-target flex shrink-0 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground transition hover:border-primary/35 hover:bg-surface-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] lg:hidden"
            aria-label={copy.topbar.mobileMenu}
          >
            <Menu className="size-5" />
          </button>

          <div className="hidden size-11 shrink-0 items-center justify-center rounded-2xl border border-border bg-surface-muted text-primary shadow-sm sm:flex">
            <CurrentIcon className="size-5" />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground sm:text-[11px]">
              {copy.topbar.breadcrumbRoot}
              <ChevronRight className="size-3" />
              <span className="truncate text-primary">{currentPage.label}</span>
            </div>
            <h1 className="truncate text-base font-black tracking-tight text-foreground sm:text-xl">{currentPage.label}</h1>
            <p className="hidden truncate text-xs leading-5 text-muted-foreground md:block">{currentPage.description}</p>
          </div>
        </div>

        <div className="flex min-w-0 flex-1 items-center justify-end gap-2 lg:gap-3">
          <label className="relative hidden w-full max-w-md xl:block">
            <span className="sr-only">{copy.topbar.searchLabel}</span>
            <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              placeholder={copy.topbar.searchPlaceholder}
              className={cn(
                'comfort-input h-11 w-full rounded-2xl pl-10 pr-20 text-sm shadow-sm',
                'placeholder:text-muted-foreground'
              )}
            />
            <span className="pointer-events-none absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1 rounded-lg border border-border bg-surface-muted px-2 py-1 text-[10px] font-black text-muted-foreground">
              <Command className="size-3" />K
            </span>
          </label>

          <div className="hidden items-center gap-1 rounded-2xl border border-border bg-surface p-1 md:flex">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className="interactive-surface group flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold text-muted-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]"
                  title={action.description}
                >
                  <Icon className="size-3.5 text-primary transition group-hover:scale-110" />
                  <span className="hidden xl:inline">{action.label}</span>
                </Link>
              );
            })}
          </div>

          <Link
            href={`/${locale}/employer/jobs?new=1`}
            className="touch-target inline-flex items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 hover:opacity-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] sm:w-auto sm:px-4 sm:text-sm sm:font-black"
            aria-label={copy.topbar.newJobAria}
          >
            <Plus className="size-4" />
            <span className="hidden sm:ml-2 sm:inline">{copy.topbar.newJob}</span>
          </Link>

          <IconButton className="relative hidden sm:inline-flex" aria-label={copy.topbar.aiSuggestions}>
            <Sparkles className="size-4" />
            <span className="absolute -right-0.5 -top-0.5 size-2.5 rounded-full border-2 border-background bg-accent" />
          </IconButton>

          <IconButton className="relative" aria-label={copy.topbar.notifications}>
            <Bell className="size-4" />
            <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-black text-white">
              4
            </span>
          </IconButton>

          <EmployerUserMenu locale={locale} session={session} />
        </div>
      </div>

      <div className="border-t border-border/70 px-4 py-3 sm:px-6 xl:hidden">
        <label className="relative block">
          <span className="sr-only">{copy.topbar.mobileSearchLabel}</span>
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder={copy.topbar.mobileSearchPlaceholder}
            className="comfort-input h-11 w-full rounded-2xl pl-10 pr-4 text-sm"
          />
        </label>
      </div>
    </header>
  );
}
