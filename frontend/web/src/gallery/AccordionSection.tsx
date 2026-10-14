import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@kindynos/ui';
import { useWebI18n } from '../messages';
import { Section } from './Section';

const QUESTIONS = ['data', 'time', 'answers'] as const;

export function AccordionSection() {
  const { t } = useWebI18n();
  return (
    <Section id="accordion" title={t('gallery.accordion.title')}>
      <Accordion type="single" collapsible defaultValue="data">
        {QUESTIONS.map((question) => (
          <AccordionItem key={question} value={question}>
            <AccordionTrigger>{t(`gallery.accordion.${question}_question`)}</AccordionTrigger>
            <AccordionContent>
              <p>{t(`gallery.accordion.${question}_answer`)}</p>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </Section>
  );
}
