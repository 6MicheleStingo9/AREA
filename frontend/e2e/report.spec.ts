/// <reference lib="dom" />
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { EXAMPLE, exampleReport } from './report';

const REPORT = `/report/${EXAMPLE.run_id}`;

/** The report as the Kindynos server serves it, at /report/<run id>, with what went wrong in it */
async function served(page: Page, html = exampleReport()): Promise<string[]> {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()));
  await page.route(`**${REPORT}`, (route) =>
    route.fulfill({ body: html, contentType: 'text/html' }),
  );
  await page.goto(REPORT);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  return errors;
}

test('the report shows the run, from the verdict of the rules to every risk', async ({ page }) => {
  const errors = await served(
    page,
    exampleReport((data) => (data.system_name = 'Developer assistant')),
  );
  await expect(page).toHaveTitle('Developer assistant · Kindynos report');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Developer assistant');
  for (const name of [
    'Key findings',
    'Summary',
    'Risks by domain',
    'How the risks come about',
    'Alert & safety profile',
    'Risk patterns',
    'All the risks',
  ]) {
    await expect(page.getByRole('region', { name })).toBeVisible();
  }
  await expect(page.getByRole('region', { name: 'Key findings' })).toContainText('61');
  // The fonts and the logo are in the file
  const fraunces = await page.evaluate(async () => {
    await document.fonts.ready;
    return document.fonts.check('600 16px Fraunces');
  });
  expect(fraunces).toBe(true);
  const logo = page.getByRole('banner').locator('img').first();
  await expect
    .poll(() => logo.evaluate((img: HTMLImageElement) => img.naturalWidth))
    .toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

test('the archive of the run comes from the server, and the data open in a tab', async ({
  page,
}) => {
  await served(page);
  // A download leaves the page before page.route() can answer it: the link is enough
  const archive = page.getByRole('link', { name: 'Download (ZIP)' });
  await expect(archive).toHaveAttribute('href', `/api/assessments/${EXAMPLE.run_id}/archive`);
  await expect(archive).toHaveAttribute('download', '');

  // A tab without an opener: the context sees it, not the page
  const [tab] = await Promise.all([
    page.context().waitForEvent('page'),
    page.getByRole('button', { name: 'View data' }).click(),
  ]);
  await tab.waitForLoadState();
  expect(tab.url()).toMatch(/^blob:/);
  expect(JSON.parse((await tab.locator('pre').textContent()) ?? '{}')).toMatchObject({
    run_id: EXAMPLE.run_id,
  });
});

test('opened from a file, the report works offline, without the archive', async ({ page }) => {
  const file = join(mkdtempSync(join(tmpdir(), 'kindynos-report-')), 'report.html');
  writeFileSync(file, exampleReport());
  const errors: string[] = [];
  page.on('console', (message) => message.type() === 'error' && errors.push(message.text()));
  // Nothing outside the file: every request to the network fails
  await page.route(/^https?:/, (route) => route.abort());
  await page.goto(pathToFileURL(file).href);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('AI risk report');
  await expect(page.getByRole('link', { name: 'Download (ZIP)' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'View data' })).toBeVisible();
  await page.getByRole('button', { name: 'Switch to the dark theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  expect(errors).toEqual([]);
});

test('the risks open and filter from the keyboard', async ({ page, isMobile }) => {
  test.skip(isMobile, 'a phone has no keyboard');
  await served(page);
  const risks = page.getByRole('region', { name: 'All the risks' });
  // The filters: the arrows move between the options of a group
  await risks.getByRole('radio', { name: 'All' }).first().focus();
  await page.keyboard.press('ArrowRight');
  await expect(risks.getByRole('radio', { name: 'High' })).toBeChecked();
  await expect(risks.getByText('11 of 34 risks')).toBeVisible();
  // The domains: open, and the arrows go from one to the next
  await risks.getByRole('button', { name: /Discrimination & Toxicity/ }).focus();
  await page.keyboard.press('ArrowDown');
  await expect(risks.getByRole('button', { name: /Privacy & Security/ })).toBeFocused();
  // In a domain, a risk opens with Enter
  await page.keyboard.press('Tab');
  const risk = risks.getByRole('button', { name: /Vulnerability to adversarial attacks/ });
  await expect(risk).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(risk).toHaveAttribute('aria-expanded', 'true');
  await expect(
    page.getByRole('region', { name: /Vulnerability to adversarial attacks/ }),
  ).toContainText('Why it is a risk');
});

test('a band of the causal flow shows its risks under the pointer', async ({ page, isMobile }) => {
  test.skip(isMobile, 'a phone has no pointer to hover with');
  await served(page);
  const flow = page.getByRole('region', { name: 'How the risks come about' });
  const band = flow.locator('path').nth(1);
  await band.hover();
  await expect(flow.getByText('AI → Unintentional')).toBeVisible();
  await expect(flow.getByText('18 risks')).toBeVisible();
});

for (const scheme of ['light', 'dark'] as const) {
  test(`report, ${scheme}: no accessibility violation, and no sideways scroll`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await served(page);
    await page.getByRole('button', { name: /Bias in output tailoring/ }).click();
    await page.getByRole('button', { name: 'What each pattern counts' }).click();
    const { violations } = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(
      violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`),
    ).toEqual([]);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
}
