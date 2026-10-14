import { I18nProvider, ThemeProvider } from '@kindynos/ui';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { describe, expect, it } from 'vitest';
import { App } from './App';
import { messages } from './messages';

function renderApp() {
  return render(
    <ThemeProvider>
      <I18nProvider messages={messages}>
        <App />
      </I18nProvider>
    </ThemeProvider>,
  );
}

describe('The components page', () => {
  it('switches language from the header', async () => {
    renderApp();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('The Kindynos interface');
    expect(document.title).toBe('Kindynos · Interface');
    const banner = within(screen.getByRole('banner'));
    await userEvent.click(banner.getByRole('radio', { name: 'Italiano' }));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      "L'interfaccia di Kindynos",
    );
    expect(document.title).toBe('Kindynos · Interfaccia');
    expect(document.documentElement.lang).toBe('it');
  });

  it('switches theme from the header', async () => {
    renderApp();
    const banner = within(screen.getByRole('banner'));
    await userEvent.click(banner.getByRole('button', { name: 'Switch to the dark theme' }));
    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(banner.getByRole('button', { name: 'Switch to the light theme' })).toBeInTheDocument();
  });

  it('has no accessibility violations that axe can find without a layout', async () => {
    const { container } = renderApp();
    // jsdom computes no colours: the contrast is checked on the tokens (ui/src/styles/tokens.node.test.ts)
    const results = await axe.run(container, { rules: { 'color-contrast': { enabled: false } } });
    expect(
      results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(' | ')}`),
    ).toEqual([]);
  });
});
