import { readFileSync } from 'node:fs';
import type { Page } from '@playwright/test';

/** A question of files/questions_<language>.json, as far as the tests need it */
export interface Question {
  id: string;
  question: string;
  type: 'free_text' | 'multiple_choice' | 'checkbox';
  options?: string[];
}

export function questions(lang: 'en' | 'it'): Question[] {
  const file = new URL(`../../files/questions_${lang}.json`, import.meta.url);
  return (JSON.parse(readFileSync(file, 'utf-8')) as { questions: Question[] }).questions;
}

export const RUNNING = {
  id: 'run12345',
  status: 'running',
  step: 'causes',
  risks: 34,
  labelled: 12,
};

export const DONE = {
  id: 'run12345',
  status: 'done',
  system_name: 'Developer assistant',
  result: {
    score: 61.47,
    level: 'high',
    concern: 'active_threats',
    action: 'immediate_mitigation',
    critical_domain: { id: '4', high: 4 },
    risks: 34,
    domains: 7,
    severity: { high: 11, medium: 19, low: 4 },
  },
  report_url: '/report/run12345',
  archive_url: '/api/assessments/run12345/archive',
};

/**
 * The API of FastAPI, answered in the page: the real questionnaires, an assessment started as
 * run12345, and its states, one per request (the last one repeats). Returns what the page sent.
 */
export async function fakeApi(page: Page, statuses: object[] = [DONE]): Promise<unknown[]> {
  const sent: unknown[] = [];
  const queue = [...statuses];
  await page.route('**/api/questionnaire?*', (route) => {
    const lang = new URL(route.request().url()).searchParams.get('lang') === 'it' ? 'it' : 'en';
    return route.fulfill({ json: { lang, questions: questions(lang) } });
  });
  await page.route('**/api/assessments', (route) => {
    sent.push(route.request().postDataJSON());
    return route.fulfill({ status: 201, json: { id: 'run12345' } });
  });
  await page.route('**/api/assessments/run12345', (route) =>
    route.fulfill({ json: queue.length > 1 ? queue.shift() : queue[0] }),
  );
  return sent;
}
