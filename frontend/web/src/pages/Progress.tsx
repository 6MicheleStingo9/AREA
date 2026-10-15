import { Eyebrow, VisuallyHidden } from '@kindynos/ui';
import { Check, LoaderCircle } from 'lucide-react';
import { STEPS, type AssessmentStatus, type Step } from '../api';
import { useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import page from './Page.module.css';
import styles from './Progress.module.css';

type StepState = 'done' | 'running' | 'waiting';

/** The steps of a running analysis: what is done, what runs (with its count), what waits */
export function Progress({ status, offline }: { status: AssessmentStatus; offline: boolean }) {
  const { t } = useWebI18n();
  useDocumentTitle(t('app.page_title', { page: t('app.analysis.page_title') }));
  const current = Math.max(0, STEPS.indexOf(status.step ?? 'domain'));

  const detail = (step: Step, state: StepState) => {
    if (state === 'waiting') return t('app.analysis.waiting');
    if (state === 'done') {
      return step === 'domain' && typeof status.risks === 'number'
        ? t('app.analysis.done_risks', { count: status.risks })
        : t('app.analysis.done');
    }
    if (step === 'causes' && typeof status.labelled === 'number' && status.risks) {
      return t('app.analysis.labelled', { labelled: status.labelled, risks: status.risks });
    }
    return t('app.analysis.in_progress');
  };

  return (
    <div className={`${page.page} ${page.narrow}`}>
      <div className={page.intro}>
        <Eyebrow>{t('app.analysis.eyebrow')}</Eyebrow>
        <PageHeading>{t('app.analysis.title')}</PageHeading>
        <p className={page.lead}>{t('app.analysis.lead')}</p>
      </div>
      <ol aria-label={t('app.analysis.steps_label')} className={styles.steps}>
        {STEPS.map((step, i) => {
          const state: StepState = i < current ? 'done' : i === current ? 'running' : 'waiting';
          return (
            <li
              key={step}
              className={`${styles.step} ${styles[state]}`}
              aria-current={state === 'running' ? 'step' : undefined}
            >
              <span aria-hidden="true" className={styles.icon}>
                {state === 'done' && <Check />}
                {state === 'running' && <LoaderCircle className={styles.spinner} />}
              </span>
              <div className={styles.text}>
                <p className={styles.title}>{t(`app.analysis.${step}_title`)}</p>
                <p className={styles.description}>{t(`app.analysis.${step}_text`)}</p>
              </div>
              <p className={styles.state}>{detail(step, state)}</p>
            </li>
          );
        })}
      </ol>
      {/* The step in course, read when it changes; the counts change too often to be read */}
      <p aria-live="polite">
        <VisuallyHidden>{t(`app.analysis.${STEPS[current] ?? 'domain'}_title`)}</VisuallyHidden>
      </p>
      {offline && (
        <p role="alert" className={page.alert}>
          {t('app.analysis.offline')}
        </p>
      )}
    </div>
  );
}
