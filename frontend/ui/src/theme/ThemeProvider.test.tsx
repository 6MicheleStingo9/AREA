import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { setSystemTheme } from '../test/system-theme';
import { ThemeProvider } from './ThemeProvider';
import { useTheme } from './useTheme';

const render = () => renderHook(() => useTheme(), { wrapper: ThemeProvider });
const attribute = () => document.documentElement.dataset.theme;

describe('ThemeProvider', () => {
  it('follows the system until a choice', () => {
    const { result } = render();
    expect(result.current.theme).toBe('light');
    act(() => setSystemTheme('dark'));
    expect(result.current.theme).toBe('dark');
    expect(attribute()).toBeUndefined();
  });

  it('fixes the chosen theme on <html> and keeps it for the next visit', () => {
    const { result, unmount } = render();
    act(() => result.current.toggle());
    expect(result.current.theme).toBe('dark');
    expect(attribute()).toBe('dark');
    // The system changing does not override a choice
    act(() => setSystemTheme('light'));
    expect(result.current.theme).toBe('dark');
    unmount();
    expect(render().result.current.theme).toBe('dark');
  });

  it('follows the system again when switched back to its theme', () => {
    const { result } = render();
    act(() => result.current.toggle());
    act(() => result.current.toggle());
    expect(result.current.theme).toBe('light');
    expect(attribute()).toBeUndefined();
    expect(localStorage.getItem('kindynos:theme')).toBeNull();
    act(() => setSystemTheme('dark'));
    expect(result.current.theme).toBe('dark');
  });
});
