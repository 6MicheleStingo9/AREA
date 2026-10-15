import { Meter } from '@kindynos/ui';
import { AXES, type Answer, type Axis, type Cause, type ReportData, type Risk } from '../data';
import { causeKey, classes, percent } from '../format';
import { useReportI18n, type ReportKey } from '../messages';
import section from '../sections/Section.module.css';
import styles from './RiskDetails.module.css';

/** What the report knows of a risk: the answer it comes from, why it is a risk, and its causes */
export function RiskDetails({ risk, data }: { risk: Risk; data: ReportData }) {
  const { t } = useReportI18n();
  const answer = data.answers[risk.subdomain];
  const model = data.causality_model;
  const texts = [
    { title: t('report.explorer.why'), text: risk.explanation },
    { title: t('report.explorer.severity_why'), text: risk.severity_rationale },
    { title: t('report.explorer.mitigation'), text: risk.mitigation },
  ].filter((entry): entry is { title: string; text: string } => Boolean(entry.text));

  return (
    <div className={styles.details}>
      {answer && (
        <div className={styles.answer}>
          <p className={styles.eyebrow}>
            {t('report.explorer.from_answers', { id: risk.subdomain })}
          </p>
          {answer.question && <p className={styles.question}>{answer.question}</p>}
          <AnswerText answer={answer.answer} />
          {answer.followups.map((followup, i) => (
            <p key={i} className={styles.followup}>
              <strong>{followup.question}</strong> {followup.answer}
            </p>
          ))}
        </div>
      )}
      {texts.length > 0 && (
        <div className={styles.texts}>
          {texts.map((entry) => (
            <div key={entry.title} className={styles.text}>
              <h6>{entry.title}</h6>
              <p>{entry.text}</p>
            </div>
          ))}
        </div>
      )}
      <div className={styles.causes}>
        <div className={styles.causesHead}>
          <h6>{t('report.explorer.causes')}</h6>
          {model && (
            <p className={section.note}>
              {model.backend === 'laya'
                ? t('report.explorer.by_laya')
                : t('report.explorer.by_llm', { model: model.model })}
            </p>
          )}
        </div>
        <div className={styles.cards}>
          {AXES.map((axis) => (
            <CauseCard key={axis} axis={axis} cause={risk.causes[axis]} />
          ))}
        </div>
      </div>
    </div>
  );
}

/** The answer as it was given: its text, or the options chosen */
function AnswerText({ answer }: { answer: Answer }) {
  const { t } = useReportI18n();
  if (answer === null) return <p className={styles.missing}>{t('report.explorer.no_answer')}</p>;
  if (typeof answer === 'string') return <p>{answer}</p>;
  return (
    <ul className={styles.chips}>
      {answer.selected.map((option) => (
        <li key={option}>{option}</li>
      ))}
      {answer.other && <li>{t('report.explorer.other', { text: answer.other })}</li>}
    </ul>
  );
}

/**
 * One causal label: its value and the MIT definition of it; how sure Laya was and its next guess,
 * or why the LLM chose it
 */
function CauseCard({ axis, cause }: { axis: Axis; cause: Cause }) {
  const { t } = useReportI18n();
  const label = (value: string) => t(causeKey(axis, value) as ReportKey);
  const definition = t(`report.definitions.${axis}.${cause.value}` as ReportKey);
  const next = Object.entries(cause.probabilities ?? {})
    .filter(([value]) => value !== cause.value)
    .sort((a, b) => b[1] - a[1])[0];
  const confidence = cause.confidence === null ? null : percent(cause.confidence * 100);

  return (
    <div className={styles.card}>
      <p className={styles.axis}>{t(`report.axes.${axis}`)}</p>
      <p className={styles.value}>
        {axis === 'entity' && (
          <span
            aria-hidden="true"
            className={classes(section.swatch, section.dot, section[cause.value])}
          />
        )}
        {label(cause.value)}
      </p>
      {definition !== `report.definitions.${axis}.${cause.value}` && (
        <p className={styles.definition}>{definition}</p>
      )}
      {confidence !== null ? (
        <div className={styles.confidence}>
          <p className={styles.confidenceLine}>
            <span>{t('report.explorer.confidence')}</span>
            <strong>{confidence}%</strong>
          </p>
          <Meter
            value={confidence}
            size="sm"
            label={t('report.explorer.confidence_label', { axis: t(`report.axes.${axis}`) })}
            valueText={`${confidence}%`}
          />
          {next && (
            <p className={styles.next}>
              {t('report.explorer.next', { label: label(next[0]), value: percent(next[1] * 100) })}
            </p>
          )}
        </div>
      ) : (
        cause.rationale && (
          <div className={styles.confidence}>
            <p className={styles.rationaleTitle}>{t('report.explorer.rationale')}</p>
            <p className={styles.rationale}>{cause.rationale}</p>
          </div>
        )
      )}
    </div>
  );
}
