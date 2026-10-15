import { Eyebrow, VisuallyHidden } from '@kindynos/ui';
import { Check } from 'lucide-react';
import { Link } from 'react-router';
import { useTaxonomy, useWebI18n } from '../messages';
import { useAssessment } from '../questionnaire/context';
import { byDomain } from '../questionnaire/domains';
import { isComplete } from '../questionnaire/logic';
import type { Question } from '../questionnaire/types';
import styles from './ProgressNav.module.css';

/** The answers given, by domain, with a link to every question: the current domain is open */
export function ProgressNav({ questions, current }: { questions: Question[]; current: Question }) {
  const { t } = useWebI18n();
  const taxonomy = useTaxonomy();
  const { draft } = useAssessment();
  const done = (question: Question) => isComplete(question, draft.answers[question.id]);
  const answered = questions.filter(done).length;
  const currentDomain = current.id.split('.')[0];

  return (
    <nav aria-label={t('app.question.nav_label')} className={styles.nav}>
      <div className={styles.head}>
        <Eyebrow>{t('app.question.nav_title')}</Eyebrow>
        <p className={styles.count}>
          {t('app.question.nav_answered', { count: answered, total: questions.length })}
        </p>
      </div>
      <ol className={styles.domains}>
        {byDomain(questions).map(({ domain, questions: list }) => {
          const count = list.filter(done).length;
          const name = (
            <>
              <span aria-hidden="true" className={styles.number}>
                {domain}
              </span>
              <span className={styles.name}>{taxonomy.domains[domain]}</span>
              <span className={styles.domainCount}>
                <span aria-hidden="true">
                  {count}/{list.length}
                </span>
                <VisuallyHidden>
                  {t('app.question.nav_domain', { answered: count, total: list.length })}
                </VisuallyHidden>
              </span>
            </>
          );
          if (domain !== currentDomain) {
            const target = list.find((question) => !done(question)) ?? list[0];
            return (
              <li key={domain}>
                <Link to={`/questions/${target?.id ?? ''}`} className={styles.domain}>
                  {name}
                </Link>
              </li>
            );
          }
          return (
            <li key={domain} className={styles.current}>
              <p className={`${styles.domain} ${styles.currentDomain}`}>{name}</p>
              <ol className={styles.questions}>
                {list.map((question) => {
                  const here = question.id === current.id;
                  return (
                    <li key={question.id}>
                      <Link
                        to={`/questions/${question.id}`}
                        aria-current={here ? 'step' : undefined}
                        className={styles.question}
                      >
                        <span aria-hidden="true" className={styles.mark}>
                          {here ? <span className={styles.dot} /> : done(question) && <Check />}
                        </span>
                        <span>
                          {question.id} {taxonomy.subdomains[question.id]?.short}
                        </span>
                        {!here && done(question) && (
                          <VisuallyHidden>, {t('app.question.nav_done')}</VisuallyHidden>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ol>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
