/** A matchMedia for jsdom, which has none: the system theme of the tests, light until one changes it. */

const DARK_QUERY = '(prefers-color-scheme: dark)';

let dark = false;
const listeners = new Set<() => void>();

export function installMatchMedia(): void {
  dark = false;
  listeners.clear();
  window.matchMedia = (query: string) =>
    ({
      media: query,
      get matches() {
        return query === DARK_QUERY && dark;
      },
      addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
      removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
    }) as unknown as MediaQueryList;
}

export function setSystemTheme(theme: 'light' | 'dark'): void {
  dark = theme === 'dark';
  listeners.forEach((listener) => listener());
}
