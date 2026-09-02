'use client';

import {Bell, ChevronDown, LogOut, MoonStar, Settings, UserRound} from 'lucide-react';
import {useRouter} from 'next/navigation';
import {useMemo, useState} from 'react';

import {ThemeToggle} from '@/components/theme/theme-toggle';
import {useEmployerLogoutMutation} from '@/hooks/use-api-queries';
import {getEmployerCopy} from '@/lib/employer-copy';
import {cn} from '@/lib/utils';
import type {EmployerAuthSession} from '@/types/user';

export function EmployerUserMenu({locale, session}: {locale: string; session: EmployerAuthSession}) {
  const [isOpen, setIsOpen] = useState(false);
  const copy = useMemo(() => getEmployerCopy(locale), [locale]);
  const router = useRouter();
  const logoutMutation = useEmployerLogoutMutation();
  const displayName = session.name ?? session.full_name ?? session.email;
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'NT';

  async function handleLogout() {
    await logoutMutation.mutateAsync().catch(() => null);
    router.replace(`/${locale}/login?role=employer`);
    router.refresh();
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className={cn(
          'flex items-center gap-2 rounded-2xl border border-border bg-surface px-2 py-1.5 text-left transition',
          'hover:border-primary/35 hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]'
        )}
        aria-expanded={isOpen}
        aria-label={copy.userMenu.ariaLabel}
      >
        <span className="flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-xs font-black text-white">
          {initials}
        </span>
        <span className="hidden min-w-0 sm:block">
          <span className="block truncate text-xs font-bold text-foreground">{displayName}</span>
          <span className="block truncate text-[10px] text-muted-foreground">{session.role_key || copy.userMenu.owner}</span>
        </span>
        <ChevronDown className={cn('hidden size-3.5 text-muted-foreground transition sm:block', isOpen && 'rotate-180')} />
      </button>

      {isOpen ? (
        <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-64 overflow-hidden rounded-3xl border border-border bg-surface-elevated shadow-2xl shadow-black/30">
          <div className="border-b border-border p-4">
            <div className="text-sm font-bold text-foreground">{displayName}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">{session.email}</div>
            <div className="mt-1 text-[11px] font-semibold text-primary">{session.company_name}</div>
          </div>
          <div className="space-y-1 p-2">
            <button className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground transition hover:bg-surface-muted hover:text-foreground">
              <UserRound className="size-4" /> {copy.userMenu.profile}
            </button>
            <button className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground transition hover:bg-surface-muted hover:text-foreground">
              <Settings className="size-4" /> {copy.userMenu.workspaceSettings}
            </button>
            <div className="flex items-center justify-between rounded-2xl px-3 py-2.5 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-3"><MoonStar className="size-4" /> {copy.userMenu.theme}</span>
              <ThemeToggle />
            </div>
            <button className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-muted-foreground transition hover:bg-surface-muted hover:text-foreground">
              <Bell className="size-4" /> {copy.userMenu.notifications}
            </button>
          </div>
          <div className="border-t border-border p-2">
            <button
              type="button"
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm text-danger transition hover:bg-danger/10 disabled:cursor-wait disabled:opacity-60"
            >
              <LogOut className="size-4" /> {copy.userMenu.logout}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
