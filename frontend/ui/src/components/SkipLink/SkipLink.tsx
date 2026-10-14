import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import styles from './SkipLink.module.css';

/** The first link of the page, visible when focused: it jumps over the header to the content */
export function SkipLink({ href = '#content' }: { href?: string }) {
  const { t } = useI18n<CommonMessages>();
  return (
    <a href={href} className={styles.link}>
      {t('common.skip_to_content')}
    </a>
  );
}
