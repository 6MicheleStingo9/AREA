import { act, render, renderHook, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { I18nProvider } from './I18nProvider';
import { richText } from './richText';
import { useI18n } from './useI18n';

const messages = {
  en: { app: { hello: 'Hello', saved: 'Saved in {path}.' } },
  it: { app: { hello: 'Ciao', saved: 'Salvato in {path}.' } },
};

const wrapper = ({ children }: { children: ReactNode }) => (
  <I18nProvider messages={messages}>{children}</I18nProvider>
);

describe('I18nProvider', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('speaks the first language of the browser that Kindynos knows', () => {
    vi.spyOn(navigator, 'languages', 'get').mockReturnValue(['fr-FR', 'it-IT', 'en']);
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(result.current.lang).toBe('it');
    expect(result.current.t('app.hello')).toBe('Ciao');
    expect(document.documentElement.lang).toBe('it');
  });

  it('falls back to English for a browser in another language', () => {
    vi.spyOn(navigator, 'languages', 'get').mockReturnValue(['de-DE']);
    const { result } = renderHook(() => useI18n(), { wrapper });
    expect(result.current.lang).toBe('en');
  });

  it('keeps the chosen language for the next visit', () => {
    const { result, unmount } = renderHook(() => useI18n(), { wrapper });
    act(() => result.current.setLang('it'));
    expect(result.current.t('app.hello')).toBe('Ciao');
    expect(document.documentElement.lang).toBe('it');
    unmount();
    const { result: next } = renderHook(() => useI18n(), { wrapper });
    expect(next.current.lang).toBe('it');
  });

  it('still switches language when the browser blocks the storage', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError');
    });
    const { result } = renderHook(() => useI18n(), { wrapper });
    act(() => result.current.setLang('it'));
    expect(result.current.lang).toBe('it');
  });

  it('needs a provider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useI18n())).toThrow(/I18nProvider/);
  });
});

describe('richText', () => {
  it('puts elements in the placeholders of a string', () => {
    function Saved() {
      const { t } = useI18n();
      return <p>{richText(t('app.saved'), { path: <code>files/reports/</code> })}</p>;
    }
    render(<Saved />, { wrapper });
    expect(screen.getByText('files/reports/').tagName).toBe('CODE');
    expect(screen.getByText(/Saved in/)).toHaveTextContent('Saved in files/reports/.');
  });
});
