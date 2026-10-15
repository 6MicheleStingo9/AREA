import { Heading } from '@kindynos/ui';
import type { Alert, ReportData } from '../data';
import { classes, percent } from '../format';
import { useReportI18n, useTaxonomy, type ReportKey } from '../messages';
import section from './Section.module.css';
import styles from './KeyFindings.module.css';

/**
 * A string by a key built from the data (a concern, an alert), or null when the report has none for
 * it: a value that the rules may add later then reads as it comes.
 */
function useOptional() {
  const { t } = useReportI18n();
  return (key: string, params?: Record<string, string | number>): string | null => {
    const text = t(key as ReportKey, params);
    return text === key ? null : text;
  };
}

/** The verdict of the expert rules: the score, the concern, the action, the domains and the alerts */
export function KeyFindings({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const optional = useOptional();
  const taxonomy = useTaxonomy();
  const { score, level, concern, action, critical_domains: critical } = data.results;
  const value = percent(score);

  return (
    <section aria-labelledby="findings" className={section.section}>
      <Heading level={2} id="findings">
        {t('report.findings.title')}
      </Heading>
      <div className={styles.grid}>
        <div className={styles.score}>
          <h3 className={styles.label}>{t('report.findings.score')}</h3>
          <p className={styles.scoreLine}>
            <span className={styles.scoreValue}>{value}</span>
            <span className={styles.scale}>{t('report.findings.score_scale')}</span>
          </p>
          <span aria-hidden="true" className={styles.track}>
            <span
              className={styles.fill}
              style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
            />
          </span>
          {level && <p className={styles.level}>{optional(`common.level.${level}`) ?? level}</p>}
        </div>
        <Finding
          label={t('report.findings.concern')}
          value={concern && (optional(`common.concern.${concern}`) ?? concern)}
          text={concern && optional(`report.findings.concerns.${concern}`)}
        />
        <Finding
          label={t('report.findings.action')}
          value={action && (optional(`common.action.${action}`) ?? action)}
          text={action && optional(`report.findings.actions.${action}`)}
        />
        <div className={styles.card}>
          <h3 className={styles.label}>{t('report.findings.critical_domains')}</h3>
          {critical.length > 0 ? (
            <ol className={styles.domains}>
              {critical.map((domain) => (
                <li key={domain.id}>
                  <span className={styles.domain}>
                    {domain.id} · {taxonomy.domains[domain.id] ?? domain.id}
                  </span>
                  <span className={styles.high}>
                    {t('report.findings.high', { count: domain.high })}
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className={styles.text}>{t('report.findings.no_critical_domains')}</p>
          )}
        </div>
      </div>
      <div className={classes(styles.card, styles.alerts)}>
        <h3 className={styles.alertsTitle}>{t('report.findings.alerts')}</h3>
        {data.alerts.length > 0 ? (
          <ul className={styles.alertList}>
            {data.alerts.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </ul>
        ) : (
          <p className={styles.text}>{t('report.findings.no_alerts')}</p>
        )}
      </div>
    </section>
  );
}

function Finding({
  label,
  value,
  text,
}: {
  label: string;
  value: string | null;
  text: string | null;
}) {
  return (
    <div className={styles.card}>
      <h3 className={styles.label}>{label}</h3>
      <p className={styles.value}>{value ?? '—'}</p>
      {text && <p className={styles.text}>{text}</p>}
    </div>
  );
}

/** An alert of the rules, with what it measured: a count, or a share of the risks */
function AlertItem({ alert }: { alert: Alert }) {
  const optional = useOptional();
  const key = `report.alerts.${alert.id}`;
  const value = alert.value ?? 0;
  const text =
    alert.id === 'intentional_threats'
      ? optional(`${key}.text`, { count: value })
      : alert.id === 'low_preventable_ratio' && percent(value) === 0
        ? optional(`${key}.none`)
        : alert.id === 'high_risk_fragmentation'
          ? value >= 7
            ? optional(`${key}.all`)
            : optional(`${key}.text`, { count: value })
          : optional(`${key}.text`, { value: percent(value) });
  return (
    <li className={styles.alert}>
      <span aria-hidden="true" className={styles.alertDot} />
      <span className={styles.alertText}>
        <strong>{optional(`${key}.name`) ?? alert.id.replaceAll('_', ' ')}</strong>
        <span>{text ?? String(alert.value ?? '')}</span>
      </span>
    </li>
  );
}
