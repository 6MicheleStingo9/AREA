import {
  Badge,
  Button,
  ButtonLink,
  Card,
  Choice,
  Eyebrow,
  Field,
  FieldError,
  Meter,
  TextArea,
  TextInput,
} from '@kindynos/ui';
import { ArrowLeft, ArrowRight, Check, CornerDownRight } from 'lucide-react';
import { useId, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { flushSync } from 'react-dom';
import { Link, useNavigate, useParams } from 'react-router';
import { useTaxonomy, useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import { useAssessment } from '../questionnaire/context';
import { useErrorText } from '../questionnaire/errorText';
import { answerErrors, visibleFollowups } from '../questionnaire/logic';
import { useQuestions } from '../questionnaire/questions';
import type { Answer, AnswerError, Question } from '../questionnaire/types';
import { NotFound } from './NotFound';
import page from './Page.module.css';
import { ProgressNav } from './ProgressNav';
import styles from './QuestionPage.module.css';

/** One question at a time: /questions/1.3 */
export function QuestionPage() {
  const { id } = useParams();
  const questions = useQuestions();
  const index = questions.findIndex((question) => question.id === id);
  if (index < 0) return <NotFound />;
  // A new question, a new screen: the errors shown belong to the question left behind
  return <QuestionScreen key={id} questions={questions} index={index} />;
}

function QuestionScreen({ questions, index }: { questions: Question[]; index: number }) {
  const question = questions[index] as Question;
  const { t } = useWebI18n();
  const taxonomy = useTaxonomy();
  const errorText = useErrorText();
  const { draft, setAnswer } = useAssessment();
  const navigate = useNavigate();
  const form = useRef<HTMLFormElement>(null);
  const [checked, setChecked] = useState(false);
  const total = questions.length;
  useDocumentTitle(
    t('app.page_title', { page: t('app.question.page_title', { number: index + 1, total }) }),
  );

  const answer = draft.answers[question.id] ?? {};
  // The errors appear once the user tries to go on, and then follow the answer as it changes
  const errors = checked ? answerErrors(question, answer) : [];
  const previous = questions[index - 1];
  const next = questions[index + 1];
  const domain = question.id.split('.')[0] ?? '';

  const update = (change: Partial<Answer>) => setAnswer(question.id, { ...answer, ...change });

  const goOn = (event: FormEvent) => {
    event.preventDefault();
    if (answerErrors(question, answer).length) {
      flushSync(() => setChecked(true));
      form.current
        ?.querySelector<HTMLElement>('[aria-invalid="true"], [data-invalid] input')
        ?.focus();
      return;
    }
    void navigate(next ? `/questions/${next.id}` : '/review');
  };

  return (
    <div className={`${page.page} ${styles.layout}`}>
      <form ref={form} className={styles.card} onSubmit={goOn} noValidate>
        <div className={styles.head}>
          <div className={styles.headRow}>
            <Eyebrow>
              {t('app.question.domain', { number: domain, name: taxonomy.domains[domain] ?? '' })}
            </Eyebrow>
            <p className={styles.counter}>
              {t('app.question.counter', { number: index + 1, total })}
            </p>
          </div>
          {/* The counter above says it: the bar only draws it */}
          <Meter value={((index + 1) / total) * 100} tone="human" size="sm" />
          <p>
            <Badge>
              {question.id} {taxonomy.subdomains[question.id]?.name}
            </Badge>
          </p>
        </div>

        <AnswerInput
          question={question}
          answer={answer}
          error={errors.find(
            (error) => error.code !== 'followup_required' && error.code !== 'other_required',
          )}
          otherError={errors.find((error) => error.code === 'other_required')}
          errorText={errorText}
          onChange={update}
        />

        {visibleFollowups(question, answer).map((i) => {
          const followup = question.follow_ups[i];
          if (!followup) return null;
          const error = errors.find((e) => e.code === 'followup_required' && e.followup === i);
          return (
            <Card key={i} tone="muted" className={styles.followup}>
              <CornerDownRight aria-hidden="true" className={styles.followupIcon} />
              <div className={styles.followupField}>
                <Field
                  label={followup.text}
                  optional={!followup.required}
                  error={error && errorText(error)}
                >
                  <TextArea
                    value={answer.followups?.[String(i)] ?? ''}
                    onChange={(event) =>
                      update({
                        followups: { ...answer.followups, [String(i)]: event.target.value },
                      })
                    }
                  />
                </Field>
              </div>
            </Card>
          );
        })}

        <div className={styles.footer}>
          <p className={styles.saved}>
            <Check aria-hidden="true" />
            {t('app.question.saved')}
          </p>
          <div className={page.actions}>
            <ButtonLink
              as={Link}
              to={previous ? `/questions/${previous.id}` : '/'}
              variant="secondary"
              icon={<ArrowLeft />}
            >
              {t('app.question.back')}
            </ButtonLink>
            <Button type="submit" iconEnd={<ArrowRight />}>
              {next ? t('app.question.next') : t('app.question.review')}
            </Button>
          </div>
        </div>
      </form>

      <ProgressNav questions={questions} current={question} />
    </div>
  );
}

interface AnswerInputProps {
  question: Question;
  answer: Answer;
  /** The error of the answer itself, if shown */
  error?: AnswerError;
  /** The error of the text of "Other", if shown */
  otherError?: AnswerError;
  errorText: ReturnType<typeof useErrorText>;
  onChange: (change: Partial<Answer>) => void;
}

/** The question as the title of the page, and the control that answers it */
function AnswerInput({
  question,
  answer,
  error,
  otherError,
  errorText,
  onChange,
}: AnswerInputProps) {
  const { t } = useWebI18n();
  const id = useId();
  const helpId = question.help_text ? `${id}-help` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, helpId].filter(Boolean).join(' ') || undefined;
  const help = question.help_text && (
    <p id={helpId} className={styles.help}>
      {question.help_text}
    </p>
  );
  const errorMessage = error && <FieldError id={errorId}>{errorText(error)}</FieldError>;

  if (question.type === 'free_text') {
    return (
      <div className={styles.answer}>
        <PageHeading size="title" className={styles.question}>
          <label htmlFor={`${id}-text`}>{question.question}</label>
        </PageHeading>
        {help}
        <TextArea
          id={`${id}-text`}
          rows={question.multiline === false ? 1 : 5}
          value={answer.text ?? ''}
          onChange={(event) => onChange({ text: event.target.value })}
          placeholder={question.placeholder}
          aria-describedby={describedBy}
          aria-invalid={error ? true : undefined}
        />
        {errorMessage}
      </div>
    );
  }

  const options = question.options ?? [];
  const choices = answer.choices ?? [];
  const ticked = answer.other !== undefined;
  let controls: ReactNode;
  if (question.type === 'multiple_choice') {
    controls = options.map((option, i) => (
      <Choice
        key={option}
        name={`${id}-choice`}
        value={String(i)}
        checked={answer.choice === i}
        onChange={() => onChange({ choice: i })}
        label={option}
      />
    ));
  } else {
    const toggle = (i: number) =>
      onChange({ choices: choices.includes(i) ? choices.filter((c) => c !== i) : [...choices, i] });
    controls = (
      <>
        {options.map((option, i) => (
          <Choice
            key={option}
            type="checkbox"
            value={String(i)}
            checked={choices.includes(i)}
            onChange={() => toggle(i)}
            label={option}
          />
        ))}
        {question.allow_other && (
          <Choice
            type="checkbox"
            value="other"
            checked={ticked}
            onChange={() => onChange({ other: ticked ? undefined : '' })}
            label={question.other_label ?? t('app.question.other')}
          />
        )}
        {question.allow_other && ticked && (
          <div className={styles.other}>
            <Field
              label={t('app.question.other_label')}
              error={otherError && errorText(otherError)}
            >
              <TextInput
                value={answer.other ?? ''}
                onChange={(event) => onChange({ other: event.target.value })}
              />
            </Field>
          </div>
        )}
      </>
    );
  }
  return (
    <fieldset
      className={styles.answer}
      aria-describedby={describedBy}
      data-invalid={error ? true : undefined}
    >
      <legend className={styles.legend}>
        <PageHeading size="title" className={styles.question}>
          {question.question}
        </PageHeading>
      </legend>
      {help}
      <div className={styles.options}>{controls}</div>
      {errorMessage}
    </fieldset>
  );
}
