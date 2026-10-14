import { use } from 'react';
import { I18nContext, type I18n } from './context';
import type { MessageKey, Messages, Params } from './translate';

export interface TypedI18n<M> extends Omit<I18n, 't'> {
  t: (key: MessageKey<M>, params?: Params) => string;
}

/** The language and the strings of the interface; M, the catalog of the caller, types the keys. */
export function useI18n<M extends Messages = Messages>(): TypedI18n<M> {
  const i18n = use(I18nContext);
  if (!i18n) throw new Error('useI18n() needs an <I18nProvider> around the app');
  return i18n;
}
