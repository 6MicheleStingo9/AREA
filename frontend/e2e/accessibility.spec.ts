/// <reference lib="dom" />
import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { DONE, fakeApi, RUNNING } from './api';

/** Every screen, in the state that shows the most: an open follow-up and its error, a running step */
const PAGES: {
  name: string;
  path: string;
  statuses?: object[];
  prepare?: (page: Page) => Promise<void>;
}[] = [
  { name: 'welcome', path: '/' },
  {
    name: 'question',
    path: '/questions/1.3',
    prepare: async (page) => {
      // The first option opens a required follow-up; Next then shows its error
      await page.getByRole('main').getByRole('radio').first().check();
      await page.getByRole('button', { name: 'Next question' }).click();
      await expect(page.getByText('This question needs an answer too.')).toBeVisible();
    },
  },
  { name: 'review', path: '/review' },
  { name: 'progress', path: '/analysis/run12345', statuses: [RUNNING] },
  { name: 'result', path: '/analysis/run12345', statuses: [DONE] },
  { name: 'not found', path: '/nothing' },
  { name: 'components', path: '/ui' },
];

for (const scheme of ['light', 'dark'] as const) {
  for (const { name, path, statuses, prepare } of PAGES) {
    test(`${name}, ${scheme}: no accessibility violation, and no sideways scroll`, async ({
      page,
    }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await fakeApi(page, statuses);
      await page.goto(path);
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await prepare?.(page);
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
}
