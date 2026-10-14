import { Badge, Button, Card, Heading, Meter } from '@kindynos/ui';
import { ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { startAssessment } from '../api';
import { useTaxonomy, useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import { useAssessment } from '../questionnaire/context';
import { byDomain } from '../questionnaire/domains';
import { isComplete, visibleFollowups } from '../questionnaire/logic';
import { useQuestions } from '../questionnaire/questions';
import type { Answer, AnswerError, Question } from '../questionnaire/types';
import page from './Page.module.css';
import styles from './Review.module.css';

/** Every answer before the analysis, with a link to change it; then the start of the analysis */
export function Review() {
  const { t, lang } = useWebI18n();
  const taxonomy = useTaxonomy();
  const questions = useQuestions();
  const { draft, setLastRun } = useAssessment();
  const navigate = useNavigate();
  const [state, setState] = useState<'idle' | 'starting' | 'failed' | 'rejected'>('idle');
  const [refused, setRefused] = useState<Record<string, AnswerError[]>>({});
  useDocumentTitle(t('app.page_title', { page: t('app.review.page_title') }));

  const complete = (question: Question) =>
    isComplete(question, draft.answers[question.id]) && !refused[question.id];
  const incomplete = questions.filter((question) => !complete(question));
  const ready = incomplete.length === 0;

  const run = async () => {
    setState('starting');
    try {
      const answers = Object.fromEntries(
        questions.flatMap((q) => (draft.answers[q.id] ? [[q.id, draft.answers[q.id]]] : [])),
      ) as Record<string, Answer>;
      const outcome = await startAssessment({
        lang,
        system_name: draft.systemName.trim() || undefined,
        answers,
      });
      if (outcome.ok) {
        setLastRun(outcome.id);
        void navigate(`/analysis/${outcome.id}`);
      } else {
        setRefused(outcome.errors);
        setState('rejected');
      }
    } catch {
      setState('failed');
    }
  };

  return (
    <div className={page.page}>
      <div className={page.intro}>
        <PageHeading>{t('app.review.title')}</PageHeading>
        <p className={page.lead}>{t('app.review.lead')}</p>
      </div>

      <div className={styles.layout}>
        <div className={styles.answers}>
          {byDomain(questions).map(({ domain, questions: list }) => (
            <section key={domain} aria-labelledby={`domain-${domain}`} className={styles.domain}>
              <div className={styles.domainHead}>
                <Heading
                  level={2}
                  size="title"
                  id={`domain-${domain}`}
                  className={styles.domainTitle}
                >
                  {taxonomy.domains[domain]}
                </Heading>
                <p className={styles.domainCount}>
                  {t('app.review.domain_answered', {
                    answered: list.filter(complete).length,
                    total: list.length,
                  })}
                </p>
              </div>
              <ol className={styles.questions}>
                {list.map((question) => (
                  <li key={question.id} className={styles.item}>
                    <div className={styles.itemHead}>
                      <span className={styles.id}>{question.id}</span>
                      <p className={styles.text}>{question.question}</p>
                      <Link
                        to={`/questions/${question.id}`}
                        aria-label={t('app.review.edit_label', { id: question.id })}
                        className={styles.edit}
                      >
                        {t('app.review.edit')}
                      </Link>
                    </div>
                    {complete(question) ? (
                      <AnswerView question={question} answer={draft.answers[question.id] ?? {}} />
                    ) : (
                      <p>
                        <Badge tone="high">
                          {draft.answers[question.id]
                            ? t('app.review.incomplete')
                            : t('app.review.missing')}
                        </Badge>
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>

        <aside aria-label={t('app.review.panel_label')} className={styles.aside}>
          <Card className={styles.panel}>
            <Heading level={2} size="title">
              {ready ? t('app.review.ready_title') : t('app.review.not_ready_title')}
            </Heading>
            <div className={styles.progress}>
              <Meter
                value={((questions.length - incomplete.length) / questions.length) * 100}
                tone="human"
                size="sm"
              />
              <p className={page.note}>
                {t('app.review.answered', {
                  count: questions.length - incomplete.length,
                  total: questions.length,
                })}
              </p>
            </div>
            {!ready && (
              <div className={styles.todo}>
                <p>{t('app.review.to_complete')}</p>
                <ul className={styles.todoList}>
                  {incomplete.map((question) => (
                    <li key={question.id}>
                      <Link to={`/questions/${question.id}`} className={page.textLink}>
                        {question.id} {taxonomy.subdomains[question.id]?.short}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className={styles.next}>
              <Heading level={3} size="title" className={styles.nextTitle}>
                {t('app.review.next_title')}
              </Heading>
              <ol className={styles.steps}>
                <li>{t('app.review.next_domain')}</li>
                <li>{t('app.review.next_causes')}</li>
                <li>{t('app.review.next_rules')}</li>
                <li>{t('app.review.next_report')}</li>
              </ol>
            </div>
            {ready && (
              <Button
                size="lg"
                iconEnd={<ArrowRight />}
                onClick={() => void run()}
                disabled={state === 'starting'}
              >
                {state === 'starting' ? t('app.review.starting') : t('app.review.run')}
              </Button>
            )}
            <p className={page.note}>{t('app.review.run_note')}</p>
            {state === 'failed' && (
              <p role="alert" className={page.alert}>
                {t('app.review.run_error')}
              </p>
            )}
            {state === 'rejected' && (
              <p role="alert" className={page.alert}>
                {t('app.review.run_rejected')}
              </p>
            )}
          </Card>
        </aside>
      </div>
    </div>
  );
}

/** An answer as the user gave it: the text, or the options in words, then the follow-ups */
function AnswerView({ question, answer }: { question: Question; answer: Answer }) {
  const { t } = useWebI18n();
  const options = question.options ?? [];
  const followups = visibleFollowups(question, answer).flatMap((i) => {
    const text = answer.followups?.[String(i)]?.trim();
    return text ? [{ i, text }] : [];
  });
  return (
    <div className={styles.answer}>
      {question.type === 'free_text' && <p className={styles.written}>{answer.text?.trim()}</p>}
      {question.type === 'multiple_choice' && answer.choice !== undefined && (
        <p className={styles.chosen}>{options[answer.choice]}</p>
      )}
      {question.type === 'checkbox' && (
        <ul className={styles.chips}>
          {[...new Set(answer.choices ?? [])]
            .sort((a, b) => a - b)
            .map((i) => (
              <li key={i}>{options[i]}</li>
            ))}
          {answer.other?.trim() && <li>{t('app.review.other', { text: answer.other.trim() })}</li>}
        </ul>
      )}
      {followups.map(({ i, text }) => (
        <p key={i} className={styles.followup}>
          <span className={styles.followupLabel}>{t('app.review.followup')}:</span> {text}
        </p>
      ))}
    </div>
  );
}
