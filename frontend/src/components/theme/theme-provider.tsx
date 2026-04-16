'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';

type Theme = 'dark' | 'light';

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (theme: Theme) => void;
};

const STORAGE_KEY = 'hiring-radar-theme';

const ThemeContext = createContext<ThemeContextValue | null>(null);

function isTheme(value: string | null): value is Theme {
  return value === 'dark' || value === 'light';
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'dark';
  }

  const storedTheme = window.localStorage.getItem(STORAGE_KEY);
  if (isTheme(storedTheme)) {
    return storedTheme;
  }

  return 'dark';
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove('light', 'dark');
  root.classList.add(theme);
  root.style.colorScheme = theme;
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

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme: theme,
      setTheme
    }),
    [theme, setTheme]
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