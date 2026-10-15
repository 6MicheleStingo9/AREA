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
  /**
   * A control after the others that stays beside the logo on a narrow screen, where the others go to
   * a row of their own: the theme, when there are more controls than fit beside the logo
   */
  end?: ReactNode;
}

export function AppHeader({ homeHref = '/', renderHome, children, end }: AppHeaderProps) {
  const { t } = useI18n<CommonMessages>();
  const home: HomeLinkProps = {
    className: styles.home ?? '',
    'aria-label': t('common.brand.home'),
    children: <Brand />,
  };
  return (
    <header className={[styles.header, end && styles.withEnd].filter(Boolean).join(' ')}>
      {renderHome ? (
        renderHome(home)
      ) : (
        <a href={homeHref} className={home.className} aria-label={home['aria-label']}>
          {home.children}
        </a>
      )}
      {children && <div className={styles.actions}>{children}</div>}
      {end && <div className={styles.end}>{end}</div>}
    </header>
  );
}
