import type { ReactNode } from 'react';
import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import { Brand } from '../Brand/Brand';
import styles from './AppHeader.module.css';

interface HomeLinkProps {
  className: string;
  'aria-label': string;
  children: ReactNode;
}

interface AppHeaderProps {
  /** Where the logo leads */
  homeHref?: string;
  /** The link of the logo, for an app with a router: by default an <a> to homeHref */
  renderHome?: (props: HomeLinkProps) => ReactNode;
  /** The controls on the right: language, theme */
  children?: ReactNode;
}

export function AppHeader({ homeHref = '/', renderHome, children }: AppHeaderProps) {
  const { t } = useI18n<CommonMessages>();
  const home: HomeLinkProps = {
    className: styles.home ?? '',
    'aria-label': t('common.brand.home'),
    children: <Brand />,
  };
  return (
    <header className={styles.header}>
      {renderHome ? (
        renderHome(home)
      ) : (
        <a href={homeHref} className={home.className} aria-label={home['aria-label']}>
          {home.children}
        </a>
      )}
      {children && <div className={styles.actions}>{children}</div>}
    </header>
  );
}
