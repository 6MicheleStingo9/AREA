import { Heading, VisuallyHidden } from '@kindynos/ui';
import { SEVERITIES, type ReportData } from '../data';
import { classes } from '../format';
import { useReportI18n, useTaxonomy } from '../messages';
import section from './Section.module.css';
import styles from './DomainChart.module.css';

/** The risks of the seven domains, by severity: one bar each, to the scale of the longest */
export function DomainChart({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const taxonomy = useTaxonomy();
  const longest = Math.max(1, ...data.domains.map((d) => d.high + d.medium + d.low));

  return (
    <section aria-labelledby="by-domain" className={classes(section.section, section.card)}>
      <div className={section.head}>
        <div className={section.titles}>
          <Heading level={2} id="by-domain">
            {t('report.domains.title')}
          </Heading>
          <p className={section.lead}>{t('report.domains.lead')}</p>
        </div>
        <ul aria-hidden="true" className={section.legend}>
          {SEVERITIES.map((s) => (
            <li key={s}>
              <span className={classes(section.swatch, section[s])} />
              {t(`common.severity.${s}`)}
            </li>
          ))}
        </ul>
      </div>
      <ol className={styles.rows}>
        {data.domains.map((domain) => {
          const total = domain.high + domain.medium + domain.low;
          return (
            <li key={domain.id} className={styles.row}>
              <span className={styles.name}>
                <span className={styles.id}>{domain.id}</span>
                <span>{taxonomy.domains[domain.id] ?? domain.id}</span>
              </span>
              <span className={styles.chart}>
                <span aria-hidden="true" className={styles.track}>
                  <span className={styles.bar} style={{ width: `${(total / longest) * 100}%` }}>
                    {SEVERITIES.filter((s) => domain[s] > 0).map((s) => (
                      <span
                        key={s}
                        className={classes(styles.part, section[s])}
                        style={{ flexGrow: domain[s] }}
                      />
                    ))}
                  </span>
                </span>
                <span aria-hidden="true" className={styles.total}>
                  {total}
                </span>
                <VisuallyHidden>
                  {t('report.domains.row', {
                    risks: t('report.glance.risks', { count: total }),
                    high: domain.high,
                    medium: domain.medium,
                    low: domain.low,
                  })}
                </VisuallyHidden>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
