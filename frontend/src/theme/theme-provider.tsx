'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';

/**
 * ── NoyTera Premium Theme System v3.0 ──
 *
 * Four meticulously crafted themes:
 *   obsidian — Ultra-premium dark (Linear.app inspired)
 *   platinum — Clean investor-grade light
 *   crimson  — Bold, energetic dark
 *   aurum    — Gold luxury flagship
 */
export type Theme = 'obsidian' | 'platinum' | 'crimson' | 'aurum';

const THEMES: Theme[] = ['obsidian', 'platinum', 'crimson', 'aurum'];

function isTheme(value: string | null): value is Theme {
  return THEMES.includes(value as Theme);
}

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (theme: Theme) => void;
  cycleTheme: () => void;
};

const STORAGE_KEY = 'hiring-radar-theme-v3';

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'obsidian';
  }

  const storedTheme = window.localStorage.getItem(STORAGE_KEY);
  if (isTheme(storedTheme)) {
    return storedTheme;
  }

  return 'obsidian';
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  THEMES.forEach((t) => root.classList.remove(t));
  root.classList.add(theme);
  root.setAttribute('data-theme', theme);
}

export function ThemeProvider({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((nextTheme: Theme) => {
    setThemeState(nextTheme);
  }, []);

  const cycleTheme = useCallback(() => {
    setThemeState((prev) => {
      const idx = THEMES.indexOf(prev);
      return THEMES[(idx + 1) % THEMES.length];
    });
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme: theme,
      setTheme,
      cycleTheme
    }),
    [theme, setTheme, cycleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }

  return context;
}
