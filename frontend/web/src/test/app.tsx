import { I18nProvider, ThemeProvider, type Language } from '@kindynos/ui';
import { act, render } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { vi } from 'vitest';
import questionsEn from '../../../../files/questions_en.json';
import questionsIt from '../../../../files/questions_it.json';
import type { AssessmentStatus } from '../api';
import { messages } from '../messages';
import { AssessmentProvider } from '../questionnaire/AssessmentProvider';
import { visibleFollowups } from '../questionnaire/logic';
import type { Answer, Question } from '../questionnaire/types';
import { routes } from '../router';

export const QUESTIONS = {
  en: questionsEn.questions,
  it: questionsIt.questions,
} as unknown as Record<Language, Question[]>;

export interface Call {
  method: string;
  url: string;
  body?: unknown;
}

const reply = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

/**
 * A fake FastAPI behind fetch: the real questionnaires, an assessment started as run12345, and the
 * states of that assessment, one per request (the last one repeats).
 */
export function fakeServer({
  statuses = [],
  start = () => reply({ id: 'run12345' }, 201),
}: { statuses?: AssessmentStatus[]; start?: () => Response } = {}): Call[] {
  const calls: Call[] = [];
  const queue = [...statuses];
  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => {
    const url = input instanceof Request ? input.url : input.toString();
    const method = init?.method ?? 'GET';
    const body: unknown = typeof init?.body === 'string' ? JSON.parse(init.body) : undefined;
    calls.push({ method, url, body });
    if (url.startsWith('/api/questionnaire')) {
      const lang = new URLSearchParams(url.split('?')[1]).get('lang') as Language;
      return Promise.resolve(reply({ lang, questions: QUESTIONS[lang] }));
    }
    if (url === '/api/assessments' && method === 'POST') return Promise.resolve(start());
    if (url.startsWith('/api/assessments/')) {
      const status = (queue.length > 1 ? queue.shift() : queue[0]) ?? { status: 'not_found' };
      return Promise.resolve(reply(status, status.status === 'not_found' ? 404 : 200));
    }
    return Promise.resolve(reply({ detail: 'Not Found' }, 404));
  });
  return calls;
}

/** An answer to every question, follow-ups included where they open */
export function completeAnswers(lang: Language = 'en'): Record<string, Answer> {
  return Object.fromEntries(
    QUESTIONS[lang].map((question) => {
      const answer: Answer =
        question.type === 'free_text'
          ? { text: 'An answer long enough.' }
          : question.type === 'multiple_choice'
            ? { choice: 0 }
            : { choices: [0] };
      answer.followups = Object.fromEntries(
        visibleFollowups(question, answer).map((i) => [String(i), 'Some detail.']),
      );
      return [question.id, answer];
    }),
  );
}

/** Answers kept in the browser by an earlier visit */
export function keepDraft(answers: Record<string, Answer>, systemName = ''): void {
  localStorage.setItem(
    'kindynos:assessment',
    JSON.stringify({ version: 1, draft: { systemName, answers } }),
  );
}

/** The whole app at a path, in a language: awaited, since the pages wait for the questionnaire */
export async function renderApp(path = '/', language: Language = 'en') {
  localStorage.setItem('kindynos:language', language);
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  await act(() => {
    render(
      <ThemeProvider>
        <I18nProvider messages={messages}>
          <AssessmentProvider>
            <RouterProvider router={router} />
          </AssessmentProvider>
        </I18nProvider>
      </ThemeProvider>,
    );
    return Promise.resolve();
  });
  return router;
}
