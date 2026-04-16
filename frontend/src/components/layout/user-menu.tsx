'use client';

import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import Image from 'next/image';
import Link from 'next/link';
import {usePathname, useRouter} from 'next/navigation';
import {Bell, ChevronDown, LogOut, LockKeyhole, Settings2, UserCircle2} from 'lucide-react';

import {FeedbackBanner} from '@/components/ui/feedback-banner';
import {api} from '@/lib/api';
import type {SupportedLocale} from '@/types/user';

function buildInitials(name: string | null | undefined) {
  if (!name) return 'HR';
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return 'HR';
  return words.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('') || 'HR';
}

const menuCopy: Record<SupportedLocale, {
  profile: string;
  security: string;
  preferences: string;
  notifications: string;
  logout: string;
  menuLabel: string;
  loadingLabel: string;
  logoutError: string;
}> = {
  tr: {
    profile: 'Profil',
    security: 'Güvenlik',
    preferences: 'Tercihler',
    notifications: 'Bildirimler',
    logout: 'Çıkış Yap',
    menuLabel: 'Hesap menüsü',
    loadingLabel: 'Hesap bilgileri yükleniyor',
    logoutError: 'Çıkış işlemi tamamlanamadı. Lütfen tekrar dene.',
  },
  en: {
    profile: 'Profile',
    security: 'Security',
    preferences: 'Preferences',
    notifications: 'Notifications',
    logout: 'Log out',
    menuLabel: 'Account menu',
    loadingLabel: 'Loading account info',
    logoutError: 'We could not sign you out right now. Please try again.',
  },
  de: {
    profile: 'Profil',
    security: 'Sicherheit',
    preferences: 'Präferenzen',
    notifications: 'Benachrichtigungen',
    logout: 'Abmelden',
    menuLabel: 'Kontomenü',
    loadingLabel: 'Kontoinformationen werden geladen',
    logoutError: 'Die Abmeldung konnte gerade nicht abgeschlossen werden. Bitte versuche es erneut.',
  },
};

export function UserMenu({locale}: {locale: SupportedLocale}) {
  const router = useRouter();
  const pathname = usePathname();
  const copy = menuCopy[locale];
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [open, setOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [fullName, setFullName] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [menuError, setMenuError] = useState<string | null>(null);

  const loadProfileSurface = useCallback(async () => {
    setLoadingProfile(true);
    try {
      const response = await api.getUserProfileAggregate();
      setAvatarUrl(response.profile.avatar.url);
      setFullName(response.profile.full_name.value);
      setMenuError(null);
    } catch {
      setAvatarUrl(null);
    } finally {
      setLoadingProfile(false);
    }
  }, []);

  useEffect(() => {
    void loadProfileSurface();
  }, [loadProfileSurface, pathname]);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, []);

  useEffect(() => {
    function handleSurfaceUpdate(event: Event) {
      const detail = (event as CustomEvent<{fullName?: string | null; avatarUrl?: string | null}>).detail;
      if (!detail) return;
      if ('avatarUrl' in detail) {
        setAvatarUrl(detail.avatarUrl ?? null);
      }
      if ('fullName' in detail) {
        setFullName(detail.fullName ?? null);
      }
    }

    function handleFocus() {
      void loadProfileSurface();
    }

    window.addEventListener('coresift:profile-surface-updated', handleSurfaceUpdate as EventListener);
    window.addEventListener('focus', handleFocus);
    return () => {
      window.removeEventListener('coresift:profile-surface-updated', handleSurfaceUpdate as EventListener);
      window.removeEventListener('focus', handleFocus);
    };
  }, [loadProfileSurface]);

  const initials = useMemo(() => buildInitials(fullName), [fullName]);

  async function onLogout() {
    try {
      setLoggingOut(true);
      setMenuError(null);
      await api.logout();
      setOpen(false);
      router.push(`/${locale}/login`);
      router.refresh();
    } catch {
      setMenuError(copy.logoutError);
    } finally {
      setLoggingOut(false);
    }
  }

  const items = [
    {href: `/${locale}/settings/profile`, label: copy.profile, icon: UserCircle2},
    {href: `/${locale}/settings/security`, label: copy.security, icon: LockKeyhole},
    {href: `/${locale}/settings/preferences`, label: copy.preferences, icon: Settings2},
    {href: `/${locale}/settings/notifications`, label: copy.notifications, icon: Bell},
  ];

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex h-11 items-center gap-2 rounded-full border border-border bg-surface px-2 pr-3 text-sm text-foreground transition hover:border-primary/40 hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-70"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={copy.menuLabel}
        disabled={loggingOut}
      >
        {avatarUrl ? (
          <span className="inline-flex size-9 items-center justify-center rounded-full border border-border/70 bg-muted/30 p-[2px] shadow-inner">
            <Image
              src={avatarUrl}
              alt={fullName ?? copy.profile}
              width={30}
              height={30}
              className="size-[30px] rounded-full object-cover object-center"
              unoptimized
            />
          </span>
        ) : (
          <span className="inline-flex size-9 items-center justify-center rounded-full bg-foreground text-xs font-semibold text-background">
            {initials}
          </span>
        )}
        <ChevronDown className={`size-4 text-muted-foreground transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open ? (
        <div className="absolute right-0 z-40 mt-3 w-64 rounded-[28px] border border-border bg-background p-2 shadow-[0_24px_80px_-35px_rgba(15,23,42,0.45)]">
          <div className="rounded-[22px] border border-border bg-muted/20 px-4 py-3">
            <div className="text-sm font-semibold text-foreground">{fullName || copy.profile}</div>
            <div className="mt-1 text-xs text-muted-foreground">{loadingProfile ? copy.loadingLabel : copy.menuLabel}</div>
          </div>

          {menuError ? (
            <FeedbackBanner tone="error" className="mt-2 text-xs" onDismiss={() => setMenuError(null)}>
              {menuError}
            </FeedbackBanner>
          ) : null}

          <div className="mt-2 space-y-1">
            {items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-foreground transition hover:bg-muted/50"
                >
                  <Icon className="size-4 text-muted-foreground" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="mt-2 border-t border-border pt-2">
            <button
              type="button"
              onClick={() => void onLogout()}
              disabled={loggingOut}
              className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium text-danger transition hover:bg-danger/10 disabled:opacity-60"
            >
              <LogOut className="size-4" />
              <span>{loggingOut ? `${copy.logout}...` : copy.logout}</span>
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
