export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'kindynos:theme';
const DARK_QUERY = '(prefers-color-scheme: dark)';

/** The theme of the system, and its changes while the page is open. */
export function systemTheme(): Theme {
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light';
}

export function onSystemThemeChange(callback: () => void): () => void {
  const query = window.matchMedia(DARK_QUERY);
  query.addEventListener('change', callback);
  return () => query.removeEventListener('change', callback);
}

/**
 * The theme chosen on an earlier visit, or null to follow the system. The page reads the same key
 * before its first paint (web/index.html), so that a dark choice never flashes light.
 */
export function storedTheme(): Theme | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : null;
  } catch {
    return null;
  }
}

export function storeTheme(theme: Theme | null): void {
  try {
    if (theme) localStorage.setItem(STORAGE_KEY, theme);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Not kept for the next visit: the choice still holds for this one
  }
}
