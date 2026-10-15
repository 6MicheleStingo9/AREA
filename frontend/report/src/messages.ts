import { common, useI18n } from '@kindynos/ui';
import reportEn from '../../../locales/en/report.json';
import taxonomyEn from '../../../locales/en/taxonomy.json';
import reportIt from '../../../locales/it/report.json';
import taxonomyIt from '../../../locales/it/taxonomy.json';

/** The strings of the report (locales/<language>/): the components', the report's, the taxonomy */
export const messages = {
  en: { common: common.en, report: reportEn, taxonomy: taxonomyEn },
  it: {
    common: common.it,
    report: reportIt satisfies typeof reportEn,
    taxonomy: taxonomyIt satisfies typeof taxonomyEn,
  },
};

export type ReportMessages = (typeof messages)['en'];
export type ReportKey = Parameters<ReturnType<typeof useReportI18n>['t']>[0];

export const useReportI18n = () => useI18n<ReportMessages>();

interface Taxonomy {
  domains: Record<string, string>;
  subdomains: Record<string, { name: string; short: string }>;
}

/** The names of the MIT domains and subdomains in the language of the report, by id */
export function useTaxonomy(): Taxonomy {
  const { lang } = useReportI18n();
  return messages[lang].taxonomy;
}
