import mark from '../../../../../files/img/brand/kindynos-mark.svg';
import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import styles from './ReportFooter.module.css';

/** The end of a report: how it was made and what it is for, and the credit of the MIT taxonomies */
export function ReportFooter({ year }: { year: number }) {
  const { t } = useI18n<CommonMessages>();
  return (
    <footer className={styles.footer}>
      <img src={mark} alt="" width="512" height="512" className={styles.mark} />
      <div className={styles.text}>
        <p className={styles.disclaimer}>{t('common.report_footer.disclaimer')}</p>
        <p className={styles.attribution}>{t('common.report_footer.attribution', { year })}</p>
      </div>
    </footer>
  );
}
