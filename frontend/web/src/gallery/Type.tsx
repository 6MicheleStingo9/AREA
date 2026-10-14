import { Card, Eyebrow, Heading, richText } from '@kindynos/ui';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

export function Type() {
  const { t } = useWebI18n();
  return (
    <Section id="type" title={t('gallery.type.title')} intro={t('gallery.type.intro')}>
      <Card className={styles.stack}>
        <Eyebrow>{t('gallery.type.eyebrow')}</Eyebrow>
        <Heading level={3} size="hero">
          {t('gallery.type.display')}
        </Heading>
        <p className={styles.spec}>Fraunces 600 · SOFT 50 · 36–54 px</p>
        <Heading level={3} size="section">
          {t('gallery.type.heading')}
        </Heading>
        <p className={styles.spec}>Fraunces 600 · 28 px</p>
        <p className={styles.lead}>{t('gallery.type.lead')}</p>
        <p className={styles.spec}>Inter 400 · 18 px</p>
        <p className={styles.text}>{t('gallery.type.body')}</p>
        <p className={styles.spec}>Inter 400 · 16 px</p>
        <p className={styles.note}>
          {richText(t('gallery.type.code'), { path: <code>files/reports/</code> })}
        </p>
        <p className={styles.spec}>Inter 400 · 14 px</p>
      </Card>
    </Section>
  );
}
