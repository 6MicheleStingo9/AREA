import { useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from 'react';
import { ThemeContext, type ThemeState } from './context';
import { onSystemThemeChange, storedTheme, storeTheme, systemTheme, type Theme } from './system';

/**
 * The light or dark theme. A choice sets data-theme on <html>, which fixes the color-scheme of the
 * design tokens (tokens.css); without one the page follows the system.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [choice, setChoice] = useState<Theme | null>(storedTheme);
  const system = useSyncExternalStore(onSystemThemeChange, systemTheme, () => 'light' as const);
  const theme = choice ?? system;

  useEffect(() => {
    const root = document.documentElement;
    if (choice) root.dataset.theme = choice;
    else delete root.dataset.theme;
  }, [choice]);

  const state = useMemo<ThemeState>(
    () => ({
      theme,
      toggle: () => {
        const next: Theme = theme === 'dark' ? 'light' : 'dark';
        const nextChoice = next === system ? null : next;
        storeTheme(nextChoice);
        setChoice(nextChoice);
      },
    }),
    [theme, system],
  );

  return <ThemeContext value={state}>{children}</ThemeContext>;
}
