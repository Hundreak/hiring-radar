'use client';

import {useSyncExternalStore} from 'react';
import {Palette} from 'lucide-react';

import {useTheme} from '@/components/theme/theme-provider';
import {IconButton} from '@/components/ui/icon-button';

function subscribe(): () => void {
  return () => {};
}

function useIsHydrated(): boolean {
  return useSyncExternalStore(subscribe, () => true, () => false);
}

const themeLabels: Record<string, string> = {
  onyx: 'Onyx (Premium)',
  nova: 'Nova (Corporate)',
  aura: 'Aura (Vibrant)'
};

export function ThemeToggle() {
  const {resolvedTheme, cycleTheme} = useTheme();
  const isHydrated = useIsHydrated();

  return (
    <IconButton
      aria-label="Toggle theme"
      title={isHydrated ? themeLabels[resolvedTheme] || 'Toggle theme' : 'Toggle theme'}
      type="button"
      onClick={() => {
        if (!isHydrated) return;
        cycleTheme();
      }}
    >
      <Palette className="size-4" />
    </IconButton>
  );
}
