import { Button } from '@kindynos/ui';
import { ArrowLeft, ArrowRight, Download, LoaderCircle } from 'lucide-react';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

export function Buttons() {
  const { t } = useWebI18n();
  return (
    <Section id="buttons" title={t('gallery.buttons.title')}>
      <div className={styles.row}>
        <Button size="lg" iconEnd={<ArrowRight />}>
          {t('gallery.buttons.primary')}
        </Button>
        <Button size="lg" variant="secondary" icon={<Download />}>
          {t('gallery.buttons.secondary')}
        </Button>
        <Button size="lg" variant="link">
          {t('gallery.buttons.link')}
        </Button>
      </div>
      <div className={styles.row}>
        <Button variant="secondary" icon={<ArrowLeft />}>
          {t('gallery.buttons.back')}
        </Button>
        <Button disabled icon={<LoaderCircle />}>
          {t('gallery.buttons.disabled')}
        </Button>
      </div>
    </Section>
  );
}
