import en from '../../../../locales/en/common.json';
import it from '../../../../locales/it/common.json';
import type { Language } from './translate';

/** The strings of the components (locales/<language>/common.json): every app includes them. */
export const common = { en, it: it satisfies typeof en } satisfies Record<Language, unknown>;

export type CommonMessages = { common: typeof en };
