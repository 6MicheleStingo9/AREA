import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Heading,
} from '@kindynos/ui';
import { heat } from '../charts/heat';
import { useWidth } from '../charts/useWidth';
import type { Pattern, PatternCategory, PatternCause, ReportData } from '../data';
import { classes } from '../format';
import { useReportI18n, type ReportKey } from '../messages';
import section from './Section.module.css';
import styles from './Patterns.module.css';

const CATEGORIES: readonly PatternCategory[] = ['critical', 'moderate', 'prevention', 'low'];
const CAUSES: readonly PatternCause[] = ['ai', 'human', 'any'];
// The width of the table in CSS pixels (46rem in Patterns.module.css), under which it scrolls
const TABLE_WIDTH = 736;

/**
 * The patterns of the expert rules (option D of the redesign): a table of their groups by the cause
 * that their rule names, each pattern with the risks it matches.
 */
export function Patterns({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const [ref, measured] = useWidth<HTMLDivElement>(1000);
  const scrolls = measured < TABLE_WIDTH;
  const most = Math.max(0, ...data.patterns.map((pattern) => pattern.count));
  const name = (pattern: Pattern) => {
    const key = `report.patterns.names.${pattern.id}`;
    const text = t(key as ReportKey);
    return text === key ? pattern.id.replaceAll('_', ' ') : text;
  };
  const known = data.patterns.filter((pattern) => {
    const key = `report.patterns.definitions.${pattern.id}`;
    return t(key as ReportKey) !== key;
  });

  return (
    <section aria-labelledby="patterns" className={classes(section.section, section.card)}>
      <div className={section.titles}>
        <Heading level={2} id="patterns">
          {t('report.patterns.title')}
        </Heading>
        <p className={section.lead}>{t('report.patterns.lead')}</p>
      </div>
      <div
        ref={ref}
        className={section.scroll}
        // Narrower than the table, the card scrolls it: the table takes the focus, for the arrow keys
        tabIndex={scrolls ? 0 : undefined}
        role={scrolls ? 'group' : undefined}
        aria-label={scrolls ? t('report.patterns.title') : undefined}
      >
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col" className={styles.corner}>
                {t('report.patterns.group')}
              </th>
              {CAUSES.map((cause) => (
                <th key={cause} scope="col" className={styles.cause}>
                  <span
                    aria-hidden="true"
                    className={classes(section.swatch, section.dot, section[cause])}
                  />
                  {t(`report.patterns.causes.${cause}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map((category) => (
              <tr key={category}>
                <th scope="row" className={styles.category}>
                  {t(`report.patterns.categories.${category}`)}
                </th>
                {CAUSES.map((cause) => {
                  const cell = data.patterns.filter(
                    (pattern) => pattern.category === category && pattern.cause === cause,
                  );
                  return (
                    <td key={cause} className={styles.cell}>
                      {cell.length > 0 && (
                        <ul className={styles.chips}>
                          {cell.map((pattern) => (
                            <li
                              key={pattern.id}
                              className={classes(
                                styles.chip,
                                styles[`heat${heat(pattern.count, most)}`],
                              )}
                            >
                              <span className={styles.name}>{name(pattern)}</span>
                              <strong className={styles.count}>{pattern.count}</strong>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={section.note}>{t('report.patterns.empty')}</p>
      <Accordion type="single" collapsible className={styles.guide}>
        <AccordionItem value="guide">
          <AccordionTrigger level={3}>{t('report.patterns.guide')}</AccordionTrigger>
          <AccordionContent>
            <dl className={styles.definitions}>
              {known.map((pattern) => (
                <div key={pattern.id}>
                  <dt>{name(pattern)}</dt>
                  <dd>{t(`report.patterns.definitions.${pattern.id}` as ReportKey)}</dd>
                </div>
              ))}
            </dl>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </section>
  );
}
