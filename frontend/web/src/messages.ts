import { common, useI18n } from '@kindynos/ui';
import galleryEn from '../../../locales/en/gallery.json';
import galleryIt from '../../../locales/it/gallery.json';

/** The strings of the web interface (locales/<language>/): the components', the gallery's */
export const messages = {
  en: { common: common.en, gallery: galleryEn },
  it: { common: common.it, gallery: galleryIt satisfies typeof galleryEn },
};

export type WebMessages = (typeof messages)['en'];

export const useWebI18n = () => useI18n<WebMessages>();
