import type { Language } from '@kindynos/ui';
import type { Axis } from './data';

/** The class names that apply, in one attribute */
export function classes(...names: (string | false | null | undefined)[]): string {
  return names.filter(Boolean).join(' ');
}

/** A percentage of the data (61.47) as the report shows it: a whole number */
export function percent(value: number | null | undefined): number {
  return Math.round(value ?? 0);
}

/** The date of the report in its language: 27 December 2025, 27 dicembre 2025 */
export function longDate(iso: string, lang: Language): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const locale = lang === 'it' ? 'it-IT' : 'en-GB';
  return new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'long', year: 'numeric' }).format(
    date,
  );
}

/** The year of the report, for the credit of the taxonomies */
export function yearOf(iso: string): number {
  const year = new Date(iso).getFullYear();
  return Number.isNaN(year) ? new Date().getFullYear() : year;
}

/** The key of a causal value in common.json: timing.pre_deployment for pre-deployment */
export function causeKey(axis: Axis, value: string): string {
  return `common.${axis}.${value.replaceAll('-', '_')}`;
}

/** The text without accents and in lower case, to search it */
export function searchable(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

/** The first letter in capital: an index of the profile, as the title of its line */
export function capitalized(text: string): string {
  return text.charAt(0).toLocaleUpperCase() + text.slice(1);
}

/**
 * Where the report is, when the Kindynos server that made it serves it (/report/<run id>): the root
 * of the app and the archive of the run. Null for a report opened from a file, or found elsewhere.
 */
export function servedBy(runId: string, location: Location = window.location) {
  if (!/^https?:$/.test(location.protocol) || !runId) return null;
  const match = /^(.*\/)report\/([^/]+)\/?$/.exec(location.pathname);
  if (match?.[2] !== runId) return null;
  const root = match[1] ?? '/';
  return { home: root, archive: `${root}api/assessments/${encodeURIComponent(runId)}/archive` };
}
