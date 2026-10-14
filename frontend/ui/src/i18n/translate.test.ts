import { describe, expect, it } from 'vitest';
import { fill, translate } from './translate';

const catalogs = {
  en: {
    quiz: { next: 'Next', only_english: 'English only' },
    report: { risks: { one: '{count} risk', other: '{count} risks' } },
    common: { entity: { ai: 'AI', human: 'Human', other: 'Other' } },
  },
  it: {
    quiz: { next: 'Avanti' },
    report: { risks: { one: '{count} rischio', other: '{count} rischi' } },
  },
};

describe('translate', () => {
  it('reads a dotted key in the language', () => {
    expect(translate(catalogs, 'it', 'quiz.next')).toBe('Avanti');
    expect(translate(catalogs, 'en', 'common.entity.other')).toBe('Other');
  });

  it('falls back to English, then to the key', () => {
    expect(translate(catalogs, 'it', 'quiz.only_english')).toBe('English only');
    expect(translate(catalogs, 'it', 'quiz.missing')).toBe('quiz.missing');
    expect(translate(catalogs, 'en', 'nothing')).toBe('nothing');
  });

  it('never returns a group of strings', () => {
    expect(translate(catalogs, 'en', 'common.entity')).toBe('common.entity');
    expect(translate(catalogs, 'en', 'quiz.next.deeper')).toBe('quiz.next.deeper');
  });

  it('picks the plural form from count, with the rules of the language', () => {
    expect(translate(catalogs, 'en', 'report.risks', { count: 1 })).toBe('1 risk');
    expect(translate(catalogs, 'en', 'report.risks', { count: 0 })).toBe('0 risks');
    expect(translate(catalogs, 'it', 'report.risks', { count: 1 })).toBe('1 rischio');
    expect(translate(catalogs, 'it', 'report.risks', { count: 34 })).toBe('34 rischi');
  });
});

describe('fill', () => {
  it('replaces the placeholders it has a value for, and leaves the others', () => {
    expect(fill('{count} of {total}', { count: 3 })).toBe('3 of {total}');
    expect(fill('© {year}', { year: 2026 })).toBe('© 2026');
    expect(fill('a {b c}', { b: 1 })).toBe('a {b c}');
  });
});
