import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  CircleAlert,
  CornerDownRight,
  Download,
  FileDown,
  Library,
  ListChecks,
  LoaderCircle,
  Moon,
  Search,
  ShieldCheck,
  Sun,
} from 'lucide-react';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

/** The icons of the mockups, by their Lucide names */
const ICONS = {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  CircleAlert,
  CornerDownRight,
  Download,
  FileDown,
  Library,
  ListChecks,
  LoaderCircle,
  Moon,
  Search,
  ShieldCheck,
  Sun,
};

export function Icons() {
  const { t } = useWebI18n();
  return (
    <Section id="icons" title={t('gallery.icons.title')} intro={t('gallery.icons.intro')}>
      <ul className={styles.icons}>
        {Object.entries(ICONS).map(([name, Icon]) => (
          <li key={name} className={styles.icon}>
            <Icon aria-hidden="true" />
            <code className={styles.token}>{name}</code>
          </li>
        ))}
      </ul>
    </Section>
  );
}
