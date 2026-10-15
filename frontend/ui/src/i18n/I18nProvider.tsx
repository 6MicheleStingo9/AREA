import { startTransition, useEffect, useMemo, useState, type ReactNode } from 'react';
import { I18nContext, type I18n } from './context';
import { detectLanguage, storeLanguage } from './language';
import { translate, type Language, type Messages } from './translate';

interface I18nProviderProps {
  /** The strings of the app in every language, one group per file of locales/<language>/ */
  messages: Record<Language, Messages>;
  /** The language of a document written in one, as a report: without it, the reader's is detected */
  language?: Language;
  children: ReactNode;
}

/** The language of the interface: detected, kept for the next visit, set on <html lang>. */
export function I18nProvider({ messages, language, children }: I18nProviderProps) {
  const [lang, setLang] = useState<Language>(() => language ?? detectLanguage());

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const i18n = useMemo<I18n>(
    () => ({
      lang,
      setLang: (next) => {
        storeLanguage(next);
        // A transition: what loads for the new language (the questions) keeps the page on screen
        startTransition(() => setLang(next));
      },
      t: (key, params) => translate(messages, lang, key, params),
    }),
    [lang, messages],
  );

  return <I18nContext value={i18n}>{children}</I18nContext>;
}
