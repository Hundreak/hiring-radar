'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Command, PanelLeftClose, X} from 'lucide-react';
import {useMemo} from 'react';

import {getEmployerCopy} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';

import {CompanySwitcher} from './company-switcher';
import {getEmployerNavSections} from './employer-nav';

type EmployerSidebarProps = {
  locale: string;
  isOpen: boolean;
  onClose: () => void;
};

function isNavItemActive(pathname: string, href: string): boolean {
  if (pathname === href) return true;
  return href.endsWith('/employer') ? false : pathname.startsWith(`${href}/`);
}

export function EmployerSidebar({locale, isOpen, onClose}: EmployerSidebarProps) {
  const pathname = usePathname();
  const copy = useMemo(() => getEmployerCopy(locale), [locale]);
  const navSections = getEmployerNavSections(locale);

  return (
    <>
      <button
        type="button"
        aria-label={copy.shell.sidebarClose}
        onClick={onClose}
        className={cn(
          'fixed inset-0 z-40 bg-black/50 opacity-0 backdrop-blur-sm transition lg:hidden',
          isOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none'
        )}
      />

      <aside
        aria-label={copy.shell.sidebarNavigation}
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-[min(320px,calc(100vw-24px))] flex-col border-r border-border bg-background/96 px-4 py-4 shadow-2xl shadow-black/30 backdrop-blur-2xl transition-transform duration-300 lg:sticky lg:top-0 lg:z-auto lg:h-dvh lg:w-[300px] lg:translate-x-0 lg:shadow-none',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="mb-5 flex items-center justify-between gap-3">
          <Link href={`/${locale}/employer`} onClick={onClose} className="group flex min-w-0 items-center gap-3 rounded-2xl focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]">
            <span className="relative flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
              <Command className="size-5" />
              <span className="absolute -right-1 -top-1 size-3 rounded-full border-2 border-background bg-success" />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-black tracking-tight text-foreground">{copy.shell.productName}</span>
              <span className="block truncate text-[11px] font-medium text-muted-foreground">{copy.shell.productLabel}</span>
            </span>
          </Link>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onClose}
              className="hidden size-9 items-center justify-center rounded-xl text-muted-foreground transition hover:bg-surface-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] lg:flex"
              aria-label={copy.shell.sidebarCollapseSoon}
              title={copy.shell.sidebarCollapseSoon}
            >
              <PanelLeftClose className="size-4" />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex size-9 items-center justify-center rounded-xl text-muted-foreground transition hover:bg-surface-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] lg:hidden"
              aria-label={copy.shell.sidebarClose}
            >
              <X className="size-4" />
            </button>
          </div>
        </div>

        <CompanySwitcher locale={locale} />

        <nav className="employer-scrollbar mt-6 flex-1 space-y-6 overflow-y-auto pr-1" aria-label={copy.shell.moduleNavigation}>
          {navSections.map((section) => (
            <div key={section.title}>
              <div className="mb-2 px-2 text-[10px] font-black uppercase tracking-[0.22em] text-muted-foreground/80">
                {section.title}
              </div>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const isActive = isNavItemActive(pathname, item.href);
                  const Icon = item.icon;

                  if (item.disabled) {
                    return (
                      <div
                        key={item.href}
                        className="group flex cursor-not-allowed items-center gap-3 rounded-2xl px-3 py-2.5 text-muted-foreground/55"
                        title={`${item.label} · ${copy.badges.soon}`}
                        aria-disabled="true"
                      >
                        <Icon className="size-4 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate text-sm font-semibold">{item.label}</span>
                            {item.badge ? (
                              <span className="rounded-full border border-border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-muted-foreground">
                                {item.badge}
                              </span>
                            ) : null}
                          </div>
                          <p className="truncate text-[11px] leading-4 text-muted-foreground/55">{item.description}</p>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      aria-current={isActive ? 'page' : undefined}
                      className={cn(
                        'interactive-surface group relative flex items-center gap-3 rounded-2xl px-3 py-2.5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]',
                        isActive
                          ? 'bg-secondary text-secondary-foreground shadow-sm shadow-primary/5'
                          : 'text-muted-foreground hover:bg-surface-muted hover:text-foreground'
                      )}
                    >
                      {isActive ? <span className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-full bg-primary" /> : null}
                      <Icon className={cn('size-4 shrink-0 transition', isActive && 'text-primary')} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold">{item.label}</span>
                          {item.badge ? (
                            <span className="rounded-full bg-accent-soft px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wide text-accent">
                              {item.badge}
                            </span>
                          ) : null}
                        </div>
                        <p className={cn('truncate text-[11px] leading-4', isActive ? 'text-secondary-foreground/75' : 'text-muted-foreground')}>
                          {item.description}
                        </p>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="mt-5 rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/15 via-accent-soft to-transparent p-4">
          <div className="text-xs font-black uppercase tracking-[0.16em] text-primary">{copy.shell.qualityBadge}</div>
          <p className="mt-2 text-sm font-bold text-foreground">{copy.shell.qualityTitle}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">{copy.shell.qualityDescription}</p>
        </div>
      </aside>
    </>
  );
}
