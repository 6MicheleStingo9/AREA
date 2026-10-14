import { act, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { describe, expect, it } from 'vitest';
import type { AssessmentStatus } from '../api';
import { completeAnswers, fakeServer, keepDraft, QUESTIONS, renderApp } from '../test/app';

const draft = () =>
  JSON.parse(localStorage.getItem('kindynos:assessment') ?? 'null') as {
    draft: { systemName: string; answers: Record<string, unknown>; lastRun?: string };
  };

const DONE: AssessmentStatus = {
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

describe('the welcome page', () => {
  it('keeps the name of the system and starts from the first question', async () => {
    fakeServer();
    const router = await renderApp('/');
    await userEvent.type(
      await screen.findByRole('textbox', { name: /Name of the AI system/ }),
      'Developer assistant',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Start the assessment' }));
    expect(router.state.location.pathname).toBe('/questions/1.1');
    expect(draft().draft.systemName).toBe('Developer assistant');
  });

  it('continues where the answers stopped, or deletes them after a confirmation', async () => {
    fakeServer();
    keepDraft({ '1.1': { text: 'Logs of the queries.' } });
    await renderApp('/');
    expect(
      await screen.findByText('1 of 24 questions answered, kept in this browser.'),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Start again' }));
    await userEvent.click(screen.getByRole('button', { name: 'Delete the answers' }));
    expect(screen.getByRole('button', { name: 'Start the assessment' })).toHaveFocus();
    expect(draft().draft.answers).toEqual({});
  });
});

describe('a question', () => {
  it('shows what is missing and keeps the user there, focused on it', async () => {
    fakeServer();
    const router = await renderApp('/questions/1.1');
    await userEvent.click(await screen.findByRole('button', { name: 'Next question' }));
    const answer = screen.getByRole('textbox', { name: QUESTIONS.en[0]?.question });
    expect(answer).toBeInvalid();
    expect(answer).toHaveFocus();
    expect(answer).toHaveAccessibleDescription(/This question needs an answer/);
    expect(router.state.location.pathname).toBe('/questions/1.1');
    await userEvent.type(answer, 'Logs of the queries and their timing.');
    expect(answer).not.toBeInvalid();
  });

  it('opens the follow-up of a choice, which then needs its answer', async () => {
    fakeServer();
    const router = await renderApp('/questions/1.3');
    const question = QUESTIONS.en[2];
    expect(await screen.findByRole('group', { name: question?.question })).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).toBeNull();
    await userEvent.click(screen.getByRole('radio', { name: question?.options?.[0] }));
    const followup = screen.getByRole('textbox', { name: question?.follow_ups[0]?.text });
    await userEvent.click(screen.getByRole('button', { name: 'Next question' }));
    expect(followup).toHaveFocus();
    expect(followup).toHaveAccessibleDescription('This question needs an answer too.');
    await userEvent.type(followup, 'Users of niche languages.');
    await userEvent.click(screen.getByRole('button', { name: 'Next question' }));
    expect(router.state.location.pathname).toBe('/questions/2.1');
    expect(draft().draft.answers['1.3']).toEqual({
      choice: 0,
      followups: { '0': 'Users of niche languages.' },
    });
  });

  it('keeps a choice across a change of language, since it keeps the option by its index', async () => {
    fakeServer();
    keepDraft({ '1.3': { choice: 1 } });
    await renderApp('/questions/1.3');
    expect(await screen.findByRole('radio', { name: QUESTIONS.en[2]?.options?.[1] })).toBeChecked();
    // The switch waits for the Italian questions in a transition: act must wait with it
    const italian = within(screen.getByRole('banner')).getByRole('radio', { name: 'Italiano' });
    await act(() => Promise.resolve(italian.click()));
    expect(await screen.findByRole('radio', { name: QUESTIONS.it[2]?.options?.[1] })).toBeChecked();
    expect(document.documentElement.lang).toBe('it');
  });

  it('takes the text of "Other", once ticked', async () => {
    fakeServer();
    await renderApp('/questions/1.2');
    await userEvent.click(await screen.findByRole('checkbox', { name: 'Other' }));
    await userEvent.click(screen.getByRole('button', { name: 'Next question' }));
    const other = screen.getByRole('textbox', { name: 'What else' });
    expect(other).toHaveFocus();
    expect(other).toHaveAccessibleDescription('Write what “Other” is, or untick it.');
  });

  it('does not exist outside the questionnaire', async () => {
    fakeServer();
    await renderApp('/questions/9.9');
    expect(
      await screen.findByRole('heading', { name: 'This page does not exist' }),
    ).toBeInTheDocument();
  });
});

describe('the review', () => {
  it('lists the questions to complete, and has no start until then', async () => {
    fakeServer();
    keepDraft({ '1.1': { text: 'Logs of the queries.' } });
    await renderApp('/review');
    expect(
      await screen.findByRole('heading', { name: 'Some answers are missing' }),
    ).toBeInTheDocument();
    expect(screen.getByText('1 of 24 questions answered')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '1.2 Toxic content' })).toHaveAttribute(
      'href',
      '/questions/1.2',
    );
    expect(screen.queryByRole('button', { name: 'Run the analysis' })).toBeNull();
  });

  it('starts the analysis with the options by index and the name of the system, then shows its results', async () => {
    const calls = fakeServer({
      statuses: [
        { id: 'run12345', status: 'running', step: 'causes', risks: 34, labelled: 12 },
        DONE,
      ],
    });
    keepDraft(completeAnswers(), 'Developer assistant');
    const router = await renderApp('/review');
    await userEvent.click(await screen.findByRole('button', { name: 'Run the analysis' }));
    const sent = calls.find((call) => call.method === 'POST')?.body as Record<string, unknown>;
    expect(sent).toMatchObject({ lang: 'en', system_name: 'Developer assistant' });
    expect((sent.answers as Record<string, unknown>)['1.3']).toEqual({
      choice: 0,
      followups: { '0': 'Some detail.' },
    });

    expect(router.state.location.pathname).toBe('/analysis/run12345');
    expect(await screen.findByText('12 of 34 risks')).toBeInTheDocument();
    expect(screen.getByText('Done · 34 risks')).toBeInTheDocument();
    expect(
      await screen.findByRole('heading', { name: 'Your report is ready' }, { timeout: 4000 }),
    ).toBeInTheDocument();
    expect(screen.getByText('61')).toBeInTheDocument();
    expect(screen.getByText('Active threats')).toBeInTheDocument();
    expect(screen.getByText('Malicious Actors & Misuse')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open the report' })).toHaveAttribute(
      'href',
      '/report/run12345',
    );
    expect(draft().draft.lastRun).toBe('run12345');
  });

  it('marks the answers that the server refused', async () => {
    fakeServer({
      start: () =>
        new Response(JSON.stringify({ errors: { '1.1': [{ code: 'min_length', min: 10 }] } }), {
          status: 422,
        }),
    });
    keepDraft(completeAnswers());
    await renderApp('/review');
    await userEvent.click(await screen.findByRole('button', { name: 'Run the analysis' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Some answers were not accepted');
    expect(screen.getByRole('link', { name: '1.1 Unfair discrimination' })).toBeInTheDocument();
  });
});

describe('an analysis', () => {
  it('stopped by the quota of Gemini says so, and leads back to the answers', async () => {
    fakeServer({
      statuses: [
        { id: 'run12345', status: 'error', error_code: 'quota', error: '429 RESOURCE_EXHAUSTED' },
      ],
    });
    await renderApp('/analysis/run12345');
    expect(
      await screen.findByRole('heading', { name: 'The analysis stopped' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/the free quota of the day may be used up/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to your answers' })).toHaveAttribute(
      'href',
      '/review',
    );
  });

  it('that does not exist', async () => {
    fakeServer();
    await renderApp('/analysis/nothing');
    expect(
      await screen.findByRole('heading', { name: 'This analysis does not exist' }),
    ).toBeInTheDocument();
  });
});

describe('every page', () => {
  it.each([
    ['/', 'Know the risks of your AI system, and where they come from.'],
    ['/questions/1.3', QUESTIONS.en[2]?.question ?? ''],
    ['/review', 'Review your answers'],
    ['/analysis/run12345', 'Your report is ready'],
    ['/nothing', 'This page does not exist'],
  ])('%s has no accessibility violation that axe finds without a layout', async (path, title) => {
    fakeServer({ statuses: [DONE] });
    keepDraft({ '1.3': { choice: 0 } });
    await renderApp(path);
    await screen.findByRole('heading', { level: 1, name: title });
    // jsdom computes no colours: the contrast is checked on the tokens (ui/src/styles/tokens.node.test.ts)
    const results = await axe.run(document.body, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(
      results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(' | ')}`),
    ).toEqual([]);
  });

  it('switches theme from the header', async () => {
    fakeServer();
    await renderApp('/');
    const banner = within(await screen.findByRole('banner'));
    await userEvent.click(banner.getByRole('button', { name: 'Switch to the dark theme' }));
    await waitFor(() => expect(document.documentElement.dataset.theme).toBe('dark'));
  });
});
