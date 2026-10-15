import { describe, expect, it } from 'vitest';
import { readReportData } from './data';
import { longDate, percent, servedBy, yearOf } from './format';

const at = (href: string) => new URL(href) as unknown as Location;

describe('where the report is', () => {
  it('knows the archive of its run on the Kindynos server that serves it', () => {
    expect(servedBy('abcd1234', at('http://localhost:8000/report/abcd1234'))).toEqual({
      home: '/',
      archive: '/api/assessments/abcd1234/archive',
    });
    // Behind a path, as a proxy may serve it
    expect(servedBy('abcd1234', at('https://example.org/kindynos/report/abcd1234/'))).toEqual({
      home: '/kindynos/',
      archive: '/kindynos/api/assessments/abcd1234/archive',
    });
  });

  it('opened from a file, or found anywhere else, has no server to ask', () => {
    expect(servedBy('abcd1234', at('file:///home/me/report/abcd1234'))).toBeNull();
    expect(servedBy('abcd1234', at('http://localhost:8000/report/other999'))).toBeNull();
    expect(servedBy('abcd1234', at('https://example.org/reports/kindynos.html'))).toBeNull();
  });
});

describe('the numbers and the dates', () => {
  it('show percentages as whole numbers', () => {
    expect([percent(61.47), percent(91.18), percent(0), percent(null)]).toEqual([61, 91, 0, 0]);
  });

  it('write the date of the report in its language', () => {
    expect(longDate('2025-12-27T16:06:56', 'en')).toBe('27 December 2025');
    expect(longDate('2025-12-27T16:06:56', 'it')).toBe('27 dicembre 2025');
    expect(longDate('not a date', 'en')).toBe('not a date');
    expect(yearOf('2025-12-27T16:06:56')).toBe(2025);
  });
});

describe('the data in the page', () => {
  it('are read only when Python wrote them', () => {
    expect(readReportData('__KINDYNOS_REPORT_DATA__')).toBeNull();
    expect(readReportData('{"version": 2, "risks": []}')).toBeNull();
    expect(readReportData('{"version": 1, "risks": []}')).toEqual({ version: 1, risks: [] });
    expect(readReportData(null)).toBeNull();
  });
});
