import {
  AppHeader,
  Eyebrow,
  Heading,
  LanguageSwitch,
  ReportFooter,
  SkipLink,
  ThemeToggle,
} from '@kindynos/ui';
import { useEffect } from 'react';
import styles from './App.module.css';
import { AccordionSection } from './gallery/AccordionSection';
import { Badges } from './gallery/Badges';
import { Buttons } from './gallery/Buttons';
import { Colors } from './gallery/Colors';
import { Form } from './gallery/Form';
import { Icons } from './gallery/Icons';
import { Section } from './gallery/Section';
import { Type } from './gallery/Type';
import { useWebI18n } from './messages';

/** The components of the interface, in both themes and languages: the page at /ui */
export function App() {
  const { t } = useWebI18n();

  useEffect(() => {
    document.title = t('gallery.page_title');
  }, [t]);

  return (
    <>
      <SkipLink />
      <AppHeader>
        <LanguageSwitch />
        <ThemeToggle />
      </AppHeader>
      <main id="content" tabIndex={-1} className={styles.main}>
        <div className={styles.intro}>
          <Eyebrow>{t('gallery.eyebrow')}</Eyebrow>
          <Heading level={1}>{t('gallery.title')}</Heading>
          <p className={styles.lead}>{t('gallery.lead')}</p>
        </div>
        <Colors />
        <Type />
        <Buttons />
        <Badges />
        <Form />
        <AccordionSection />
        <Icons />
        <Section id="footer" title={t('gallery.footer.title')}>
          <ReportFooter year={new Date().getFullYear()} />
        </Section>
      </main>
    </>
  );
}
