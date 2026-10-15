import { I18nProvider, ReportFooter, SkipLink, ThemeProvider } from '@kindynos/ui';
import { useEffect } from 'react';
import type { ReportData } from './data';
import { Explorer } from './explorer/Explorer';
import { yearOf } from './format';
import { messages, useReportI18n } from './messages';
import styles from './Report.module.css';
import { ReportHeader } from './ReportHeader';
import { CausalFlow } from './sections/CausalFlow';
import { DomainChart } from './sections/DomainChart';
import { KeyFindings } from './sections/KeyFindings';
import { Overview } from './sections/Overview';
import { Patterns } from './sections/Patterns';
import { Profile } from './sections/Profile';
import { SummarySection } from './sections/SummarySection';

/** The report of a run, in the language of the run */
export function ReportApp({ data }: { data: ReportData }) {
  return (
    <ThemeProvider>
      <I18nProvider messages={messages} language={data.language}>
        <Report data={data} />
      </I18nProvider>
    </ThemeProvider>
  );
}

/** The sections of the report, from the verdict of the rules to every risk */
export function Report({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const title = data.system_name ?? t('report.default_title');

  useEffect(() => {
    document.title = t('report.page_title', { name: title });
  }, [t, title]);

  return (
    <>
      <SkipLink />
      <ReportHeader data={data} />
      <main id="content" tabIndex={-1} className={styles.main}>
        <Overview data={data} title={title} />
        <KeyFindings data={data} />
        <SummarySection data={data} />
        <DomainChart data={data} />
        <CausalFlow data={data} />
        <Profile data={data} />
        <Patterns data={data} />
        <Explorer data={data} />
      </main>
      <div className={styles.footer}>
        <ReportFooter year={yearOf(data.created)} />
      </div>
    </>
  );
}

/** A built report that Python did not fill: it says so in both languages */
export function NoData() {
  return (
    <main className={styles.empty}>
      <p lang="en">This report has no data: Kindynos writes them in it when it makes the report.</p>
      <p lang="it">Questo report non ha dati: Kindynos li scrive quando compone il report.</p>
    </main>
  );
}
