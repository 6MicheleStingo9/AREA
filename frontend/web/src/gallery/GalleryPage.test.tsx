import { screen } from '@testing-library/react';
import axe from 'axe-core';
import { describe, expect, it } from 'vitest';
import { fakeServer, renderApp } from '../test/app';

describe('the page of the components', () => {
  it('shows them, in the language of the interface, with no violation that axe finds without a layout', async () => {
    fakeServer();
    await renderApp('/ui', 'it');
    expect(
      await screen.findByRole('heading', { level: 1, name: "L'interfaccia di Kindynos" }),
    ).toBeInTheDocument();
    expect(document.title).toBe('Kindynos · Interfaccia');
    const results = await axe.run(document.body, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(
      results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(' | ')}`),
    ).toEqual([]);
  });
});
