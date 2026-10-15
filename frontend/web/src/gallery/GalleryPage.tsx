import { Eyebrow, ReportFooter } from '@kindynos/ui';
import { useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import { AccordionSection } from './AccordionSection';
import { Badges } from './Badges';
import { Buttons } from './Buttons';
import { Colors } from './Colors';
import { Form } from './Form';
import styles from './GalleryPage.module.css';
import { Icons } from './Icons';
import { Section } from './Section';
import { Type } from './Type';

/** The components of the interface, in both themes and languages: the page at /ui */
export function GalleryPage() {
  const { t } = useWebI18n();
  useDocumentTitle(t('gallery.page_title'));
  return (
    <div className={styles.main}>
      <div className={styles.intro}>
        <Eyebrow>{t('gallery.eyebrow')}</Eyebrow>
        <PageHeading>{t('gallery.title')}</PageHeading>
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
    </div>
  );
}
