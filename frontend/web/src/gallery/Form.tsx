import {
  Card,
  Choice,
  ChoiceGroup,
  Field,
  LANGUAGES,
  SegmentedControl,
  TextArea,
  TextInput,
} from '@kindynos/ui';
import { useState } from 'react';
import { useWebI18n } from '../messages';
import styles from './Gallery.module.css';
import { Section } from './Section';

const ANSWERS = ['yes', 'no', 'unknown'] as const;
const DATA = ['personal', 'public', 'synthetic'] as const;
const SEVERITIES = ['all', 'high', 'medium', 'low'] as const;

export function Form() {
  const { t } = useWebI18n();
  const [name, setName] = useState('');
  const [language, setLanguage] = useState<string>('en');
  const [answer, setAnswer] = useState<(typeof ANSWERS)[number]>('yes');
  const [details, setDetails] = useState('');
  const [data, setData] = useState<string[]>(['public']);
  const [severity, setSeverity] = useState<(typeof SEVERITIES)[number]>('all');

  const toggle = (value: string) =>
    setData((current) =>
      current.includes(value) ? current.filter((v) => v !== value) : [...current, value],
    );

  return (
    <Section id="form" title={t('gallery.form.title')}>
      <div className={styles.form}>
        <Field label={t('gallery.form.name_label')} hint={t('gallery.form.name_hint')} optional>
          <TextInput
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={t('gallery.form.name_placeholder')}
          />
        </Field>
        <ChoiceGroup legend={t('common.language.label')} direction="row">
          {LANGUAGES.map((value) => (
            <Choice
              key={value}
              shape="pill"
              name="gallery-language"
              value={value}
              checked={language === value}
              onChange={() => setLanguage(value)}
              label={t(`common.language.${value}`)}
              lang={value}
            />
          ))}
        </ChoiceGroup>
        <Card className={styles.stack}>
          <ChoiceGroup
            legend={t('gallery.form.question')}
            legendStyle="question"
            hint={t('gallery.form.question_hint')}
          >
            {ANSWERS.map((value) => (
              <Choice
                key={value}
                name="gallery-answer"
                value={value}
                checked={answer === value}
                onChange={() => setAnswer(value)}
                label={t(`gallery.form.option_${value}`)}
              />
            ))}
          </ChoiceGroup>
          {answer === 'yes' && (
            <Card tone="muted">
              <Field
                label={t('gallery.form.followup')}
                error={details.trim().length < 10 ? t('gallery.form.followup_error') : undefined}
              >
                <TextArea value={details} onChange={(event) => setDetails(event.target.value)} />
              </Field>
            </Card>
          )}
        </Card>
        <ChoiceGroup legend={t('gallery.form.data_legend')}>
          {DATA.map((value) => (
            <Choice
              key={value}
              type="checkbox"
              name="gallery-data"
              value={value}
              checked={data.includes(value)}
              onChange={() => toggle(value)}
              label={t(`gallery.form.data_${value}`)}
            />
          ))}
        </ChoiceGroup>
        <SegmentedControl
          variant="chips"
          legend={t('gallery.form.filter_legend')}
          value={severity}
          onChange={setSeverity}
          options={SEVERITIES.map((value) => ({
            value,
            label: value === 'all' ? t('gallery.form.filter_all') : t(`common.severity.${value}`),
          }))}
        />
      </div>
    </Section>
  );
}
