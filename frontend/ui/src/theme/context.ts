import { createContext } from 'react';
import type { Theme } from './system';

export interface ThemeState {
  /** The theme of the page: the one chosen, else the system's */
  theme: Theme;
  /** Switch to the other theme; switching back to the system's follows the system again */
  toggle: () => void;
}

export const ThemeContext = createContext<ThemeState | null>(null);
