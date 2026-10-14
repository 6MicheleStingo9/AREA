import { use } from 'react';
import { ThemeContext, type ThemeState } from './context';

export function useTheme(): ThemeState {
  const state = use(ThemeContext);
  if (!state) throw new Error('useTheme() needs a <ThemeProvider> around the app');
  return state;
}
