import type { ReportData } from './data';

/** The data of the report in a new tab, as JSON: they are in the page, so this works offline too */
export function openData(data: ReportData): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank', 'noopener');
  // The tab has its copy by then
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
