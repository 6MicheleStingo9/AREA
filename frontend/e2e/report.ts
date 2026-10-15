import { readFileSync } from 'node:fs';

/** The data of the example run, as Python prepares them (report/src/test/example.json) */
export interface ExampleData {
  run_id: string;
  system_name: string | null;
  [key: string]: unknown;
}

export const EXAMPLE = JSON.parse(
  readFileSync(new URL('../report/src/test/example.json', import.meta.url), 'utf-8'),
) as ExampleData;

/**
 * The built report app with the data of the example run in it, written as Python writes them
 * (agents/report_generator/html_generator.py): build first, with npm run build.
 */
export function exampleReport(change?: (data: ExampleData) => void): string {
  const template = readFileSync(new URL('../report/dist/index.html', import.meta.url), 'utf-8');
  const data = structuredClone(EXAMPLE);
  change?.(data);
  const json = JSON.stringify(data)
    .replaceAll('<', '\\u003c')
    .replaceAll('>', '\\u003e')
    .replaceAll('&', '\\u0026');
  return template.replace('__KINDYNOS_REPORT_DATA__', () => json);
}
