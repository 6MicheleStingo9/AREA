import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Badge,
  Button,
  Heading,
  SegmentedControl,
  VisuallyHidden,
  type BadgeTone,
} from '@kindynos/ui';
import { Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AXES, CAUSES, SEVERITIES, type Axis, type ReportData, type Risk } from '../data';
import { causeKey } from '../format';
import { useReportI18n, useTaxonomy, type ReportKey } from '../messages';
import section from '../sections/Section.module.css';
import styles from './Explorer.module.css';
import { ALL, grouped, isFiltered, matching, NO_FILTERS, type Filters } from './filter';
import { RiskDetails } from './RiskDetails';

/**
 * Every risk, by domain and subdomain, with a search and a filter for the severity and each cause.
 * The domains and the risks open as sections: the arrow keys move between them, Enter opens one.
 */
export function Explorer({ data }: { data: ReportData }) {
  const { t } = useReportI18n();
  const taxonomy = useTaxonomy();
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const shown = useMemo(() => matching(data.risks, filters), [data.risks, filters]);
  const groups = useMemo(() => grouped(shown), [shown]);
  // The first domain open, as an example of what the others hold
  const [open, setOpen] = useState<string[]>(() => [...grouped(data.risks).keys()].slice(0, 1));
  const filtered = isFiltered(filters);

  const update = (change: Partial<Filters>) => {
    const next = { ...filters, ...change };
    setFilters(next);
    // A search, or a filter, opens every domain where it finds something
    if (isFiltered(next)) setOpen([...grouped(matching(data.risks, next)).keys()]);
  };

  const options = (axis: Axis): { value: string; label: string }[] => [
    { value: ALL, label: t('report.explorer.all') },
    ...(CAUSES[axis] as readonly string[]).map((value) => ({
      value,
      label: t(causeKey(axis, value) as ReportKey),
    })),
  ];
  const total = t('report.explorer.count', { count: data.risks.length });

  return (
    <section aria-labelledby="risks" className={section.section}>
      <div className={styles.head}>
        <Heading level={2} id="risks">
          {t('report.explorer.title')}
        </Heading>
        <p aria-live="polite" className={styles.count}>
          {filtered ? t('report.explorer.shown', { shown: shown.length, total }) : total}
        </p>
      </div>

      <form
        role="search"
        aria-label={t('report.explorer.filters')}
        className={styles.filters}
        onSubmit={(event) => event.preventDefault()}
      >
        <label className={styles.search}>
          <Search aria-hidden="true" className={styles.searchIcon} />
          <VisuallyHidden>{t('report.explorer.search')}</VisuallyHidden>
          <input
            type="search"
            value={filters.query}
            placeholder={t('report.explorer.search')}
            onChange={(event) => update({ query: event.target.value })}
            className={styles.input}
          />
        </label>
        <div className={styles.groups}>
          <SegmentedControl
            variant="chips"
            legend={t('report.explorer.severity')}
            options={[
              { value: ALL, label: t('report.explorer.all') },
              ...SEVERITIES.map((s) => ({ value: s, label: t(`common.severity.${s}`) })),
            ]}
            value={filters.severity}
            onChange={(severity) => update({ severity })}
          />
          {AXES.map((axis) => (
            <SegmentedControl
              key={axis}
              variant="chips"
              legend={t(`report.axes.${axis}`)}
              options={options(axis)}
              value={filters.causes[axis]}
              onChange={(value) => update({ causes: { ...filters.causes, [axis]: value } })}
            />
          ))}
        </div>
      </form>

      {shown.length === 0 ? (
        <div className={styles.empty}>
          <p>{t('report.explorer.none')}</p>
          <Button variant="secondary" onClick={() => setFilters(NO_FILTERS)}>
            {t('report.explorer.clear')}
          </Button>
        </div>
      ) : (
        <>
          {filtered && (
            <Button variant="link" className={styles.clear} onClick={() => setFilters(NO_FILTERS)}>
              {t('report.explorer.clear')}
            </Button>
          )}
          <Accordion type="multiple" variant="cards" value={open} onValueChange={setOpen}>
            {[...groups].map(([domain, subdomains]) => (
              <AccordionItem key={domain} value={domain}>
                <AccordionTrigger level={3} className={styles.domainTrigger}>
                  <span className={styles.domainHead}>
                    <span className={styles.domainId}>{domain}</span>
                    <span className={styles.domainName}>{taxonomy.domains[domain] ?? domain}</span>
                    <span className={styles.domainCount}>
                      {t('report.explorer.count', {
                        count: [...subdomains.values()].reduce((n, risks) => n + risks.length, 0),
                      })}
                    </span>
                  </span>
                </AccordionTrigger>
                <AccordionContent className={styles.domainContent}>
                  <Accordion type="multiple" variant="plain">
                    {[...subdomains].flatMap(([code, risks]) => [
                      <h4 key={`subdomain-${code}`} className={styles.subdomain}>
                        <span className={styles.code}>{code}</span>{' '}
                        {taxonomy.subdomains[code]?.name ?? code}
                      </h4>,
                      ...risks.map((risk) => <RiskItem key={risk.id} risk={risk} data={data} />),
                    ])}
                  </Accordion>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </>
      )}
    </section>
  );
}

const SEVERITY_TONE: Record<string, BadgeTone> = { high: 'high', medium: 'medium', low: 'low' };
const ENTITY_TONE: Record<string, BadgeTone> = { ai: 'ai', human: 'human', other: 'other' };

/** A risk: its title and its labels, and its details when open */
function RiskItem({ risk, data }: { risk: Risk; data: ReportData }) {
  const { t } = useReportI18n();
  const label = (axis: Axis) => t(causeKey(axis, risk.causes[axis].value) as ReportKey);
  return (
    <AccordionItem value={risk.id}>
      <AccordionTrigger level={5}>
        <span className={styles.riskRow}>
          <span className={styles.riskTitle}>{risk.title}</span>
          <span className={styles.badges}>
            <Badge tone={SEVERITY_TONE[risk.severity] ?? 'neutral'}>
              {t(`common.severity.${risk.severity}`)}
            </Badge>
            <Badge tone={ENTITY_TONE[risk.causes.entity.value] ?? 'other'}>{label('entity')}</Badge>
            <Badge>{label('intent')}</Badge>
            <Badge>{label('timing')}</Badge>
          </span>
        </span>
      </AccordionTrigger>
      <AccordionContent>
        <RiskDetails risk={risk} data={data} />
      </AccordionContent>
    </AccordionItem>
  );
}
