import { createContext } from 'react';
import type { Language, Params } from './translate';

export interface I18n {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, params?: Params) => string;
}

export const I18nContext = createContext<I18n | null>(null);
