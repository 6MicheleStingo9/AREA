import { render, type RenderResult } from '@testing-library/react';
import type { ReactElement } from 'react';
import { common } from '../i18n/common';
import { I18nProvider } from '../i18n/I18nProvider';
import type { Language } from '../i18n/translate';
import { ThemeProvider } from '../theme/ThemeProvider';

const messages = { en: { common: common.en }, it: { common: common.it } };

/** Render inside the providers of an app, in a language (the one an earlier visit chose) */
export function renderInApp(ui: ReactElement, language: Language = 'en'): RenderResult {
  localStorage.setItem('kindynos:language', language);
  return render(
    <ThemeProvider>
      <I18nProvider messages={messages}>{ui}</I18nProvider>
    </ThemeProvider>,
  );
}
