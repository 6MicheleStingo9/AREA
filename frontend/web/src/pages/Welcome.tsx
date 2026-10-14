import {
  Badge,
  Button,
  ButtonLink,
  Card,
  Choice,
  ChoiceGroup,
  Eyebrow,
  Field,
  LANGUAGES,
  TextInput,
} from '@kindynos/ui';
import { ArrowRight, FileDown, Library, ListChecks, ShieldCheck } from 'lucide-react';
import { useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import owl from '../../../../files/img/brand/kindynos-owl.png';
import { useTaxonomy, useWebI18n } from '../messages';
import { PageHeading } from '../PageHeading';
import { useDocumentTitle } from '../pageTitle';
import { useAssessment } from '../questionnaire/context';
import { isComplete } from '../questionnaire/logic';
import { useQuestions } from '../questionnaire/questions';
import page from './Page.module.css';
import styles from './Welcome.module.css';

const HOW_IT_WORKS = 'https://github.com/6MicheleStingo9/kindynos/blob/main/docs/how-it-works.md';

/** The first page: what Kindynos does, the name of the system and the language, and the start */
export function Welcome() {
  const { t, lang, setLang } = useWebI18n();
  const taxonomy = useTaxonomy();
  const questions = useQuestions();
  const { draft, setSystemName, reset } = useAssessment();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);
  const start = useRef<HTMLButtonElement>(null);
  useDocumentTitle(t('app.welcome.page_title'));

  const started = Object.keys(draft.answers).length > 0;
  const answered = questions.filter((q) => isComplete(q, draft.answers[q.id])).length;
  const next = questions.find((q) => !isComplete(q, draft.answers[q.id]));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void navigate(next ? `/questions/${next.id}` : '/review');
  };
  const startOver = () => {
    reset();
    setConfirming(false);
    start.current?.focus();
  };

  const features = [
    {
      icon: <ListChecks />,
      title: t('app.welcome.questions_title'),
      text: t('app.welcome.questions_text'),
    },
    {
      icon: <Library />,
      title: t('app.welcome.taxonomy_title'),
      text: t('app.welcome.taxonomy_text'),
    },
    {
      icon: <FileDown />,
      title: t('app.welcome.report_title'),
      text: t('app.welcome.report_text'),
    },
  ];

  return (
    <div className={`${page.page} ${styles.welcome}`}>
      <section className={styles.main}>
        <div className={page.intro}>
          <Eyebrow>{t('app.welcome.eyebrow')}</Eyebrow>
          <PageHeading size="hero">{t('app.welcome.title')}</PageHeading>
          <p className={page.lead}>{t('app.welcome.lead')}</p>
        </div>

        <ul aria-label={t('app.welcome.features_label')} className={styles.features}>
          {features.map((feature) => (
            <li key={feature.title} className={styles.feature}>
              <span aria-hidden="true" className={styles.featureIcon}>
                {feature.icon}
              </span>
              <span className={styles.featureText}>
                <strong>{feature.title}</strong>
                <span>{feature.text}</span>
              </span>
            </li>
          ))}
        </ul>

        <form className={styles.form} onSubmit={submit}>
          <div className={styles.name}>
            <Field label={t('app.welcome.name_label')} hint={t('app.welcome.name_hint')} optional>
              <TextInput
                value={draft.systemName}
                onChange={(event) => setSystemName(event.target.value)}
                placeholder={t('app.welcome.name_placeholder')}
                maxLength={120}
                autoComplete="off"
              />
            </Field>
          </div>
          <ChoiceGroup legend={t('app.welcome.language_legend')} direction="row">
            {LANGUAGES.map((language) => (
              <Choice
                key={language}
                shape="pill"
                name="language"
                value={language}
                checked={lang === language}
                onChange={() => setLang(language)}
                label={t(`common.language.${language}`)}
                lang={language}
              />
            ))}
          </ChoiceGroup>
          {started && (
            <p className={page.note}>
              {t('app.welcome.draft', { count: answered, total: questions.length })}
            </p>
          )}
          <div className={page.actions}>
            <Button ref={start} type="submit" size="lg" iconEnd={<ArrowRight />}>
              {started ? t('app.welcome.continue') : t('app.welcome.start')}
            </Button>
            <ButtonLink variant="link" size="lg" href={HOW_IT_WORKS}>
              {t('app.welcome.how_it_works')}
            </ButtonLink>
          </div>
          {started &&
            (confirming ? (
              <div role="group" aria-label={t('app.welcome.start_over')} className={styles.confirm}>
                <p>{t('app.welcome.start_over_question')}</p>
                <div className={page.actions}>
                  <Button variant="secondary" onClick={startOver}>
                    {t('app.welcome.start_over_confirm')}
                  </Button>
                  <Button variant="link" onClick={() => setConfirming(false)}>
                    {t('app.welcome.start_over_cancel')}
                  </Button>
                </div>
              </div>
            ) : (
              <div className={page.actions}>
                <Button variant="link" onClick={() => setConfirming(true)}>
                  {t('app.welcome.start_over')}
                </Button>
              </div>
            ))}
          {draft.lastRun && (
            <p>
              <Link to={`/analysis/${draft.lastRun}`} className={page.textLink}>
                {t('app.welcome.last_analysis')}
              </Link>
            </p>
          )}
        </form>

        <Card tone="muted" className={styles.privacy}>
          <ShieldCheck aria-hidden="true" className={styles.privacyIcon} />
          <p>
            <strong>{t('app.welcome.privacy_title')}</strong> {t('app.welcome.privacy_text')}
          </p>
        </Card>
      </section>

      <aside aria-label={t('app.welcome.example_label')} className={styles.aside}>
        <img
          src={owl}
          alt={t('app.welcome.owl_alt')}
          width="512"
          height="512"
          className={styles.owl}
        />
        <Card className={styles.example}>
          <Eyebrow>{t('app.welcome.example_eyebrow')}</Eyebrow>
          <p className={styles.exampleTitle}>
            <strong>{t('app.welcome.example_title')}</strong>
            <span>3.1 {taxonomy.subdomains['3.1']?.name}</span>
          </p>
          <p className={styles.badges}>
            <Badge tone="high">{t('common.severity.high')}</Badge>
            <Badge tone="ai">{t('common.entity.ai')}</Badge>
            <Badge>{t('common.intent.unintentional')}</Badge>
            <Badge>{t('common.timing.post_deployment')}</Badge>
          </p>
        </Card>
      </aside>
    </div>
  );
}
