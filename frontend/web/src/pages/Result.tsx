import { Badge, Button, ButtonLink, Eyebrow, Meter, richText } from '@kindynos/ui';
import { ArrowRight, Check, Download } from 'lucide-react';
import { useNavigate } from 'react-router';
import type { AssessmentStatus, Results } from '../api';
import { useTaxonomy, useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import { useAssessment } from '../questionnaire/context';
import page from './Page.module.css';
import styles from './Result.module.css';

type Severity = 'high' | 'medium' | 'low';
const TONE: Record<string, Severity> = {
  critical: 'high',
  high: 'high',
  medium: 'medium',
  low: 'low',
};

/** A finished analysis: its main results, the report, the archive, and a new assessment */
export function Result({ status }: { status: AssessmentStatus }) {
  const { t } = useWebI18n();
  const { reset } = useAssessment();
  const navigate = useNavigate();
  useDocumentTitle(t('app.page_title', { page: t('app.result.page_title') }));

  const startNew = () => {
    reset();
    void navigate('/');
  };

  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <Eyebrow icon={<Check />}>{t('app.result.eyebrow')}</Eyebrow>
        <PageHeading>{t('app.result.title')}</PageHeading>
        {status.system_name && <p className={page.lead}>{status.system_name}</p>}
      </div>
      {status.result ? (
        <Summary results={status.result} />
      ) : (
        <p className={page.note}>{t('app.result.no_results')}</p>
      )}
      <div className={page.actions}>
        <ButtonLink
          href={status.report_url ?? `/report/${status.id}`}
          size="lg"
          iconEnd={<ArrowRight />}
        >
          {t('app.result.open_report')}
        </ButtonLink>
        <ButtonLink
          href={status.archive_url ?? `/api/assessments/${status.id}/archive`}
          download
          size="lg"
          variant="secondary"
          icon={<Download />}
        >
          {t('app.result.archive')}
        </ButtonLink>
        <Button size="lg" variant="link" onClick={startNew}>
          {t('app.result.new')}
        </Button>
      </div>
      <p className={page.note}>
        {richText(t('app.result.saved_in'), { path: <code>files/reports/</code> })}
      </p>
    </div>
  );
}

/** The score, the level, the concern, the action and the critical domain, as the expert rules found them */
function Summary({ results }: { results: Results }) {
  const { t } = useWebI18n();
  const taxonomy = useTaxonomy();
  const score = Math.round(results.score ?? 0);
  const tone: Severity | undefined = TONE[results.level ?? ''];
  // A value the rules may add later reads as it comes, until it has a translation
  const label = (key: string, value: string | null) => {
    const text = value ? t(key as Parameters<typeof t>[0]) : '';
    return text === key ? (value ?? '') : text;
  };
  const severity = (['high', 'medium', 'low'] as const).filter(
    (s) => results.severity[s] !== undefined,
  );

  return (
    <section aria-label={t('app.result.summary_label')} className={styles.summary}>
      <div className={styles.score}>
        <p className={styles.label}>{t('app.result.score')}</p>
        <p className={styles.scoreLine}>
          <span className={styles.scoreValue}>{score}</span>
          <span className={styles.scale}>{t('app.result.score_scale')}</span>
        </p>
        <Meter value={score} tone={tone ?? 'neutral'} />
        {results.level && (
          <p>
            <Badge tone={tone ?? 'neutral'} on="muted">
              {label(`common.level.${results.level}`, results.level)}
            </Badge>
          </p>
        )}
      </div>
      <div className={styles.facts}>
        <dl className={styles.list}>
          <div className={styles.fact}>
            <dt>{t('app.result.concern')}</dt>
            <dd>{label(`common.concern.${results.concern}`, results.concern)}</dd>
          </div>
          <div className={styles.fact}>
            <dt>{t('app.result.action')}</dt>
            <dd>{label(`common.action.${results.action}`, results.action)}</dd>
          </div>
          <div className={styles.fact}>
            <dt>{t('app.result.critical_domain')}</dt>
            <dd>
              {results.critical_domain ? (
                <>
                  {taxonomy.domains[results.critical_domain.id] ?? results.critical_domain.id}{' '}
                  <span className={styles.aside}>
                    · {t('app.result.high_risks', { count: results.critical_domain.high })}
                  </span>
                </>
              ) : (
                t('app.result.no_critical_domain')
              )}
            </dd>
          </div>
        </dl>
        <div className={styles.counts}>
          <p>
            {t('app.result.counts', {
              risks: t('app.result.risks', { count: results.risks }),
              domains: t('app.result.domains', { count: results.domains }),
            })}
          </p>
          <ul aria-label={t('app.result.by_severity')} className={styles.severity}>
            {severity.map((s) => (
              <li key={s}>
                <Badge tone={s}>
                  {t(`common.severity.${s}`)} · {results.severity[s]}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
