import type { ReactNode } from 'react';
import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import { Brand } from '../Brand/Brand';
import styles from './AppHeader.module.css';

interface AppHeaderProps {
  /** Where the logo leads */
  homeHref?: string;
  /** The controls on the right: language, theme */
  children?: ReactNode;
}

export function AppHeader({ homeHref = '/', children }: AppHeaderProps) {
  const { t } = useI18n<CommonMessages>();
  return (
    <header className={styles.header}>
      <a href={homeHref} className={styles.home} aria-label={t('common.brand.home')}>
        <Brand />
      </a>
      {children && <div className={styles.actions}>{children}</div>}
    </header>
  );
}
