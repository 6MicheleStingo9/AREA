import { describe, expect, it } from 'vitest';
import { EXAMPLE } from '../test/report';
import { grouped, isFiltered, matching, NO_FILTERS } from './filter';

describe('the filters of the risks', () => {
  it('keep every risk without a filter', () => {
    expect(matching(EXAMPLE.risks, NO_FILTERS)).toHaveLength(34);
    expect(isFiltered(NO_FILTERS)).toBe(false);
  });

  it('combine the severity and the causes', () => {
    const filters = {
      ...NO_FILTERS,
      severity: 'high' as const,
      causes: { ...NO_FILTERS.causes, intent: 'intentional', timing: 'other' },
    };
    expect(isFiltered(filters)).toBe(true);
    expect(matching(EXAMPLE.risks, filters).map((risk) => risk.id)).toEqual(['2.2-1']);
  });

  it('search every word, in any case and without accents', () => {
    const search = (query: string) => matching(EXAMPLE.risks, { ...NO_FILTERS, query });
    expect(search('PHISHING').map((risk) => risk.id)).toContain('4.3-1');
    expect(search('fraud scams').map((risk) => risk.id)).toEqual(['4.3-1']);
    expect(search('Phìshing')).toEqual(search('phishing'));
    expect(search('   ')).toHaveLength(34);
  });

  it('group the risks by domain and subdomain, in order', () => {
    const domains = grouped(EXAMPLE.risks);
    expect([...domains.keys()]).toEqual(['1', '2', '3', '4', '5', '6', '7']);
    expect([...(domains.get('1')?.keys() ?? [])]).toEqual(['1.1', '1.2', '1.3']);
    expect(
      domains
        .get('1')
        ?.get('1.2')
        ?.map((risk) => risk.id),
    ).toEqual(['1.2-1', '1.2-2']);
  });
});
