'use client';

import {useSyncExternalStore} from 'react';
import {MoonStar, SunMedium} from 'lucide-react';

import {useTheme} from '@/components/theme/theme-provider';
import {IconButton} from '@/components/ui/icon-button';

function subscribe(): () => void {
  return () => {};
}

function useIsHydrated(): boolean {
  return useSyncExternalStore(subscribe, () => true, () => false);
}

export function ThemeToggle() {
  const {resolvedTheme, setTheme} = useTheme();
  const isHydrated = useIsHydrated();

  const isDark = resolvedTheme === 'dark';

  return (
    <IconButton
      aria-label="Toggle theme"
      title={
        isHydrated
          ? isDark
            ? 'Switch to light mode'
            : 'Switch to dark mode'
          : 'Toggle theme'
      }
      type="button"
      onClick={() => {
        if (!isHydrated) return;
        setTheme(isDark ? 'light' : 'dark');
      }}
    >
      {isHydrated ? (
        isDark ? (
          <SunMedium className="size-4" />
        ) : (
          <MoonStar className="size-4" />
        )
      ) : (
        <span className="size-4" aria-hidden="true" />
      )}
    </IconButton>
  );
}