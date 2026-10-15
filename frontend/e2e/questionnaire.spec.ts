import { expect, test } from '@playwright/test';
import { DONE, fakeApi, questions, RUNNING } from './api';

test('a whole assessment, from the welcome page to the results', async ({ page }) => {
  // 24 questions: more than the default 30 seconds when the other tests run beside it
  test.slow();
  const sent = await fakeApi(page, [RUNNING, DONE]);
  await page.goto('/');
  await page.getByRole('textbox', { name: /Name of the AI system/ }).fill('Developer assistant');
  await page.getByRole('button', { name: 'Start the assessment' }).click();

  for (const question of questions('en')) {
    await expect(page).toHaveURL(`/questions/${question.id}`);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(question.question);
    if (question.type === 'multiple_choice') {
      await page.getByRole('radio', { name: question.options?.[0], exact: true }).check();
    } else if (question.type === 'checkbox') {
      await page.getByRole('checkbox', { name: question.options?.[0], exact: true }).check();
    }
    // The written answer and the follow-ups that the first option opens
    for (const box of await page.locator('textarea').all())
      await box.fill('An answer long enough.');
    await page.getByRole('button', { name: /Next question|Review your answers/ }).click();
  }

  await expect(page).toHaveURL('/review');
  await expect(page.getByRole('heading', { name: 'Ready for the analysis' })).toBeVisible();
  await page.getByRole('button', { name: 'Run the analysis' }).click();
  await expect(page).toHaveURL('/analysis/run12345');
  await expect(page.getByText('12 of 34 risks')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Your report is ready' })).toBeVisible();
  await expect(page.getByText('Active threats')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open the report' })).toHaveAttribute(
    'href',
    '/report/run12345',
  );

  const body = sent[0] as { lang: string; system_name: string; answers: Record<string, unknown> };
  expect(body.lang).toBe('en');
  expect(body.system_name).toBe('Developer assistant');
  expect(Object.keys(body.answers)).toHaveLength(24);
  expect(body.answers['1.3']).toEqual({ choice: 0, followups: { '0': 'An answer long enough.' } });
});

test('the answers survive a reload of the page', async ({ page }) => {
  await fakeApi(page);
  await page.goto('/questions/1.1');
  const answer = page.getByRole('textbox', { name: questions('en')[0]?.question });
  await answer.fill('Logs of the queries and their timing.');
  await page.reload();
  await expect(answer).toHaveValue('Logs of the queries and their timing.');
  await page.goto('/');
  await expect(page.getByText('1 of 24 questions answered, kept in this browser.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continue the assessment' })).toBeVisible();
});

test('the keyboard reaches the content and chooses an option', async ({ page, isMobile }) => {
  test.skip(isMobile, 'a phone has no keyboard');
  await fakeApi(page);
  await page.goto('/questions/1.3');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to the content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await page.keyboard.press('Tab');
  const [first, second] = questions('en')[2]?.options ?? [];
  await expect(page.getByRole('radio', { name: first, exact: true })).toBeFocused();
  await page.keyboard.press('ArrowDown');
  await expect(page.getByRole('radio', { name: second, exact: true })).toBeChecked();
});

test('a missing answer is said, and the focus goes to it', async ({ page }) => {
  await fakeApi(page);
  await page.goto('/questions/1.1');
  await page.getByRole('button', { name: 'Next question' }).click();
  const answer = page.getByRole('textbox', { name: questions('en')[0]?.question });
  await expect(answer).toBeFocused();
  await expect(page.getByText('This question needs an answer.')).toBeVisible();
  await expect(page).toHaveURL('/questions/1.1');
});
