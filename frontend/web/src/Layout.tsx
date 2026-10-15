import { AppHeader, LanguageSwitch, SkipLink, ThemeToggle } from '@kindynos/ui';
import { Suspense } from 'react';
import { Link, Outlet, ScrollRestoration } from 'react-router';
import styles from './Layout.module.css';
import { useWebI18n } from './messages';

/** Every page: the header with the language and the theme, and the page in <main> */
export function Layout() {
  const { t } = useWebI18n();
  return (
    <>
      <SkipLink />
      <AppHeader renderHome={(home) => <Link to="/" {...home} />}>
        <LanguageSwitch />
        <ThemeToggle />
      </AppHeader>
      <main id="content" tabIndex={-1} className={styles.main}>
        <Suspense fallback={<p className={styles.loading}>{t('app.loading')}</p>}>
          <Outlet />
        </Suspense>
      </main>
      <ScrollRestoration />
    </>
  );
}
