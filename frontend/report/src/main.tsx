import '@kindynos/ui/styles.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import mark from '../../../files/img/brand/kindynos-mark.svg';
import { readReportData, type ReportData } from './data';
import { NoData, ReportApp } from './Report';

// The icon of the tab: the mark, as a data: URL in the code, like the logo of the header
const icon = document.createElement('link');
icon.rel = 'icon';
icon.type = 'image/svg+xml';
icon.href = mark;
document.head.append(icon);

/** The data that Python wrote in the page; in `npm run dev`, the example run */
async function load(): Promise<ReportData | null> {
  const data = readReportData(document.getElementById('report-data')?.textContent);
  if (data || !import.meta.env.DEV) return data;
  const example = await import('./test/example.json');
  return example.default as unknown as ReportData;
}

const root = document.getElementById('root');
if (!root) throw new Error('index.html has no #root');
const data = await load();

createRoot(root).render(<StrictMode>{data ? <ReportApp data={data} /> : <NoData />}</StrictMode>);
