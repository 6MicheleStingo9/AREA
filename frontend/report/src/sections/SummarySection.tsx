import { Heading } from '@kindynos/ui';
import { CAUSES, SEVERITIES, type ReportData } from '../data';
import { classes } from '../format';
import { useReportI18n } from '../messages';
import section from './Section.module.css';
import styles from './SummarySection.module.css';

/** The summary that Gemini wrote, and the risks at a glance */
export function SummarySection({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const paragraphs = (data.summary ?? '')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
  const { counts } = data;

  return (
    <div className={styles.layout}>
      <section aria-labelledby="summary" className={classes(section.section, styles.summary)}>
        <div className={section.titles}>
          <Heading level={2} id="summary">
            {t('report.summary.title')}
          </Heading>
          <p className={section.note}>
            {paragraphs.length > 0 ? t('report.summary.by') : t('report.summary.missing')}
          </p>
        </div>
        {paragraphs.length > 0 && (
          <div className={styles.text}>
            {paragraphs.map((paragraph, i) => (
              <p key={i}>{paragraph}</p>
            ))}
          </div>
        )}
      </section>

      <aside aria-labelledby="glance" className={classes(section.card, styles.glance)}>
        <h2 id="glance" className={styles.glanceTitle}>
          {t('report.glance.title')}
        </h2>
        <p className={styles.total}>
          <span className={styles.totalValue}>
            {t('report.glance.risks', { count: counts.risks })}
          </span>
          <span>
            {t('report.glance.where', {
              domains: t('report.glance.domains', { count: counts.domains }),
              subdomains: t('report.glance.subdomains', { count: counts.subdomains }),
            })}
          </span>
        </p>
        <Split
          label={t('report.glance.severity')}
          parts={SEVERITIES.map((s) => ({
            key: s,
            label: t(`common.severity.${s}`),
            count: counts.severity[s],
          }))}
        />
        <Split
          label={t('report.glance.entity')}
          round
          parts={CAUSES.entity.map((e) => ({
            key: e,
            label: t(`common.entity.${e}`),
            count: counts.entity[e],
          }))}
        />
      </aside>
    </div>
  );
}

interface Part {
  key: string;
  label: string;
  count: number;
}

/** How the risks split: a bar in parts, and the parts in words */
function Split({ label, parts, round }: { label: string; parts: Part[]; round?: boolean }) {
  return (
    <div className={styles.split}>
      <p className={styles.splitLabel}>{label}</p>
      <div aria-hidden="true" className={styles.bar}>
        {parts
          .filter((part) => part.count > 0)
          .map((part) => (
            <span
              key={part.key}
              className={classes(styles.part, section[part.key])}
              style={{ flexGrow: part.count }}
            />
          ))}
      </div>
      <ul className={section.legend}>
        {parts.map((part) => (
          <li key={part.key}>
            <span
              aria-hidden="true"
              className={classes(section.swatch, section[part.key], round && section.dot)}
            />
            {part.label} <strong className={styles.count}>{part.count}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
