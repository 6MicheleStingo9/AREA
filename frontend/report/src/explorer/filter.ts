import { AXES, type Axis, type Risk, type Severity } from '../data';
import { searchable } from '../format';

export const ALL = 'all';

/** The search and the filters of the list: a value for each filter, or "all" */
export interface Filters {
  query: string;
  severity: Severity | typeof ALL;
  causes: Record<Axis, string>;
}

export const NO_FILTERS: Filters = {
  query: '',
  severity: ALL,
  causes: { entity: ALL, intent: ALL, timing: ALL },
};

export function isFiltered(filters: Filters): boolean {
  return (
    filters.query.trim() !== '' ||
    filters.severity !== ALL ||
    AXES.some((axis) => filters.causes[axis] !== ALL)
  );
}

/** What the search reads of a risk: its title and its texts, without accents */
function text(risk: Risk): string {
  return searchable(
    [risk.title, risk.explanation, risk.severity_rationale, risk.mitigation]
      .filter(Boolean)
      .join(' '),
  );
}

/** The risks that match every filter and every word of the search */
export function matching(risks: Risk[], filters: Filters): Risk[] {
  const words = searchable(filters.query).split(/\s+/).filter(Boolean);
  return risks.filter(
    (risk) =>
      (filters.severity === ALL || risk.severity === filters.severity) &&
      AXES.every(
        (axis) => filters.causes[axis] === ALL || risk.causes[axis].value === filters.causes[axis],
      ) &&
      (words.length === 0 || words.every((word) => text(risk).includes(word))),
  );
}

/** The risks by domain and by subdomain, in the order of the taxonomy */
export function grouped(risks: Risk[]): Map<string, Map<string, Risk[]>> {
  const domains = new Map<string, Map<string, Risk[]>>();
  for (const risk of risks) {
    const domain = risk.subdomain.split('.')[0] ?? risk.subdomain;
    const subdomains = domains.get(domain) ?? new Map<string, Risk[]>();
    subdomains.set(risk.subdomain, [...(subdomains.get(risk.subdomain) ?? []), risk]);
    domains.set(domain, subdomains);
  }
  return domains;
}
