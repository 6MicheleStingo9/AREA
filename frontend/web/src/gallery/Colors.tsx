import tokens from '@kindynos/ui/tokens.css?raw';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

const GROUPS = [
  {
    name: 'surfaces',
    tokens: ['ground', 'surface', 'surface-muted', 'line', 'line-strong', 'track'],
  },
  { name: 'text', tokens: ['ink', 'ink-muted', 'ink-subtle'] },
  { name: 'actions', tokens: ['primary', 'on-primary', 'focus', 'ai', 'human', 'other'] },
  { name: 'severity', tokens: ['severity-high', 'severity-medium', 'severity-low'] },
] as const;

/** The values of each colour token as tokens.css writes them: light · dark, or one for both */
const VALUES = new Map(
  [...tokens.matchAll(/--color-([\w-]+):\s*([^;]+);/g)].map(([, name = '', value = '']) => {
    const pair = /^light-dark\(([^,]+),\s*(.+)\)$/.exec(value);
    return [name, pair ? `${pair[1]} · ${pair[2]}` : value] as const;
  }),
);

export function Colors() {
  const { t } = useWebI18n();
  return (
    <Section id="colors" title={t('gallery.colors.title')} intro={t('gallery.colors.intro')}>
      {GROUPS.map((group) => (
        <div key={group.name} className={styles.group}>
          <h3 className={styles.groupTitle}>{t(`gallery.colors.${group.name}`)}</h3>
          <ul className={styles.swatches}>
            {group.tokens.map((token) => (
              <li key={token} className={styles.swatch}>
                <span className={styles.chip} style={{ background: `var(--color-${token})` }} />
                <code className={styles.token}>--color-{token}</code>
                <span className={styles.value}>{VALUES.get(token)}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </Section>
  );
}
