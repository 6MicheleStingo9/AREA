import { Eyebrow, Heading } from '@kindynos/ui';
import type { ReportData } from '../data';
import { longDate } from '../format';
import { useReportI18n } from '../messages';
import styles from './Overview.module.css';

/** The title of the report, the name of the system, and when and how it was made */
export function Overview({ data, title }: { data: ReportData; title: string }) {
  const { t, lang } = useReportI18n();
  const { answered, total } = data.questions;
  return (
    <div className={styles.overview}>
      <Eyebrow>{t('report.eyebrow')}</Eyebrow>
      <Heading level={1} className={styles.title}>
        {title}
      </Heading>
      <ul aria-label={t('report.meta.label')} className={styles.meta}>
        <li>
          <time dateTime={data.created}>{longDate(data.created, lang)}</time>
        </li>
        <li>{t(`common.language.${lang}`)}</li>
        {answered !== null && total !== null && (
          <li>{t('report.meta.questions', { answered, total })}</li>
        )}
        <li>
          <a
            href="https://airisk.mit.edu/"
            target="_blank"
            rel="noreferrer"
            className={styles.link}
          >
            {t('report.meta.taxonomy')}
          </a>
        </li>
      </ul>
    </div>
  );
}
