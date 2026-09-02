'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type Theme = 'clarity' | 'obsidian' | 'platinum' | 'crimson' | 'aurum';

const THEMES: Theme[] = ['clarity', 'obsidian', 'platinum', 'crimson', 'aurum'];

function isTheme(value: string | null): value is Theme {
  return THEMES.includes(value as Theme);
}

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (theme: Theme) => void;
  cycleTheme: () => void;
};

const STORAGE_KEY = 'noytera-theme-v2';

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'clarity';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (isTheme(stored)) return stored;
  return 'clarity';
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  THEMES.forEach(t => root.classList.remove(t));
  root.classList.add(theme);
  root.setAttribute('data-theme', theme);
}

export function ThemeProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((nextTheme: Theme) => setThemeState(nextTheme), []);
  const cycleTheme = useCallback(() => {
    setThemeState(prev => THEMES[(THEMES.indexOf(prev) + 1) % THEMES.length]);
  }, []);

  const value = useMemo<ThemeContextValue>(() => ({ theme, resolvedTheme: theme, setTheme, cycleTheme }), [theme, setTheme, cycleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
