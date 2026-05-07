'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {
  BarChart3,
  Bell,
  Briefcase,
  Building2,
  ChevronLeft,
  ChevronRight,
  FileText,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import {useState} from 'react';

import {IconButton} from '@/components/ui/icon-button';
import {ThemeToggle} from '@/components/theme/theme-toggle';
import {cn} from '@/lib/utils';

function EmployerSidebar({
  locale,
  isOpen,
  onClose,
}: {
  locale: string;
  isOpen: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();

  const navItems = [
    {href: `/${locale}/employer`, icon: LayoutDashboard, label: 'Dashboard'},
    {href: `/${locale}/employer/jobs`, icon: Briefcase, label: 'İlanlarım'},
    {href: `/${locale}/employer/candidates`, icon: Users, label: 'Adaylar'},
    {href: `/${locale}/employer/matches`, icon: UserCheck, label: 'Eşleşmeler'},
    {href: `/${locale}/employer/analytics`, icon: BarChart3, label: 'Analiz'},
    {href: `/${locale}/employer/settings`, icon: Settings, label: 'Ayarlar'},
  ];

  const slugless = pathname.replace(`/${locale}/employer`, '') || '/';

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={cn('sidebar-overlay', isOpen && 'open')}
        onClick={onClose}
      />
      {/* Sidebar */}
      <aside className={cn('employer-sidebar', isOpen && 'open')}>
        <div className="employer-sidebar-header">
          <div className="flex items-center justify-between">
            <Link
              href={`/${locale}/employer`}
              className="flex items-center gap-3"
              onClick={onClose}
            >
              <div className="flex size-10 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
                <Building2 className="size-5" />
              </div>
              <div>
                <div className="text-sm font-bold tracking-tight">NoyTera</div>
                <div className="text-[11px] text-muted-foreground">İşveren Paneli</div>
              </div>
            </Link>
            <button
              onClick={onClose}
              className="flex size-8 items-center justify-center rounded-xl text-muted-foreground hover:bg-surface-muted lg:hidden"
            >
              <X className="size-4" />
            </button>
          </div>
        </div>

        <nav className="employer-sidebar-nav">
          {navItems.map((item) => {
            const isActive =
              item.href === `/${locale}/employer`
                ? slugless === '/'
                : slugless.startsWith(item.href.replace(`/${locale}/employer`, ''));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn('employer-nav-link', isActive && 'active')}
                onClick={onClose}
              >
                <item.icon />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="employer-sidebar-footer">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-xl bg-accent-soft text-accent font-bold text-sm">
              NT
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold truncate">NoyTera A.Ş.</div>
              <div className="text-[10px] text-muted-foreground">Premium Plan</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default function EmployerLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: {locale: string};
}>) {
  const {locale} = params;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifCount] = useState(4);

  return (
    <div className="employer-layout">
      <EmployerSidebar
        locale={locale}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="employer-main">
        {/* Top bar */}
        <div className="employer-topbar">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex size-10 items-center justify-center rounded-2xl border border-border bg-surface text-muted-foreground hover:text-foreground lg:hidden"
            >
              <Menu className="size-5" />
            </button>
            <div>
              <h1 className="employer-page-title">İşveren Paneli</h1>
              <p className="employer-page-desc">Adaylarınızı yönetin ve en iyi eşleşmeleri bulun</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Ara..."
                  className="h-10 w-56 rounded-2xl border border-border bg-surface pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
                />
              </div>
            </div>

            <ThemeToggle />

            <IconButton className="relative">
              <Bell className="size-4" />
              {notifCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-bold text-white">
                  {notifCount}
                </span>
              )}
            </IconButton>

            <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-sm font-bold text-white cursor-pointer">
              NT
            </div>
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}
