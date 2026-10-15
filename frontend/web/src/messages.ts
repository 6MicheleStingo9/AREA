import { common, useI18n } from '@kindynos/ui';
import appEn from '../../../locales/en/app.json';
import galleryEn from '../../../locales/en/gallery.json';
import taxonomyEn from '../../../locales/en/taxonomy.json';
import appIt from '../../../locales/it/app.json';
import galleryIt from '../../../locales/it/gallery.json';
import taxonomyIt from '../../../locales/it/taxonomy.json';

/** The strings of the web interface (locales/<language>/): every app's, the pages', the taxonomy */
export const messages = {
  en: { common: common.en, app: appEn, taxonomy: taxonomyEn, gallery: galleryEn },
  it: {
    common: common.it,
    app: appIt satisfies typeof appEn,
    taxonomy: taxonomyIt satisfies typeof taxonomyEn,
    gallery: galleryIt satisfies typeof galleryEn,
  },
};

export type WebMessages = (typeof messages)['en'];

export const useWebI18n = () => useI18n<WebMessages>();

interface Taxonomy {
  domains: Record<string, string>;
  subdomains: Record<string, { name: string; short: string }>;
}

/** The names of the MIT domains and subdomains in the language of the interface, by id */
export function useTaxonomy(): Taxonomy {
  const { lang } = useWebI18n();
  return messages[lang].taxonomy;
}
