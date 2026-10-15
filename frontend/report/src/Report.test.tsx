import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { describe, expect, it, vi } from 'vitest';
import { EXAMPLE, exampleCopy, labelledByLaya, renderReport } from './test/report';

const section = (name: string) => screen.getByRole('region', { name });

describe('the head of the report', () => {
  it('is titled with the name of the system, in the language of the run', async () => {
    const data = exampleCopy();
    data.system_name = 'Assistente per sviluppatori';
    data.language = 'it';
    await renderReport(data);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Assistente per sviluppatori',
    );
    expect(document.title).toBe('Assistente per sviluppatori · Report di Kindynos');
    expect(document.documentElement.lang).toBe('it');
    const about = screen.getByRole('list', { name: 'Informazioni sul report' });
    expect(within(about).getByText('27 dicembre 2025')).toBeInTheDocument();
    expect(within(about).getByText('24 domande su 24 con risposta')).toBeInTheDocument();
  });

  it('has a title without a name, and the data a click away', async () => {
    const open = vi.fn<typeof window.open>(() => null);
    vi.stubGlobal('open', open);
    URL.createObjectURL = vi.fn(() => 'blob:report-data');
    URL.revokeObjectURL = vi.fn();
    await renderReport();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('AI risk report');
    await userEvent.click(screen.getByRole('button', { name: 'View data' }));
    expect(open).toHaveBeenCalledWith('blob:report-data', '_blank', 'noopener');
  });

  it('offers the archive of the run only where the Kindynos server serves the report', async () => {
    await renderReport();
    expect(screen.queryByRole('link', { name: 'Download (ZIP)' })).toBeNull();
    // The logo is no link: a report opened from a file has no app to go back to
    expect(screen.queryByRole('link', { name: /Kindynos/ })).toBeNull();
  });

  it('served by Kindynos, links its archive and the app', async () => {
    window.history.pushState({}, '', `/report/${EXAMPLE.run_id}`);
    try {
      await renderReport();
      expect(screen.getByRole('link', { name: 'Download (ZIP)' })).toHaveAttribute(
        'href',
        `/api/assessments/${EXAMPLE.run_id}/archive`,
      );
      expect(screen.getByRole('link', { name: 'Kindynos, home page' })).toHaveAttribute(
        'href',
        '/',
      );
    } finally {
      window.history.pushState({}, '', '/');
    }
  });
});

describe('the key findings', () => {
  it('give the verdict of the expert rules, and what each part of it means', async () => {
    await renderReport();
    const findings = section('Key findings');
    expect(within(findings).getByText('61')).toBeInTheDocument();
    expect(within(findings).getByText('High risk level')).toBeInTheDocument();
    expect(within(findings).getByText('Active threats')).toBeInTheDocument();
    expect(
      within(findings).getByText('More than three risks are intentional.'),
    ).toBeInTheDocument();
    expect(within(findings).getByText('Immediate mitigation')).toBeInTheDocument();
    const domains = within(findings).getAllByRole('listitem').slice(0, 3);
    expect(domains.map((li) => li.textContent)).toEqual([
      '4 · Malicious Actors & Misuse4 high',
      '7 · AI System Safety, Failures, & Limitations2 high',
      '6 · Socioeconomic & Environmental1 high',
    ]);
  });

  it('say what each alert found, in words', async () => {
    await renderReport();
    const findings = section('Key findings');
    for (const text of [
      '11 risks are intentional.',
      '91% of the risks occur after deployment.',
      'None of the risks occurs before deployment, when it could still be prevented.',
      '56% of the risks are of medium severity.',
      'High-severity risks appear in all seven domains.',
    ]) {
      expect(within(findings).getByText(text)).toBeInTheDocument();
    }
  });

  it('name a critical level as such', async () => {
    const data = exampleCopy();
    data.results.level = 'critical';
    data.alerts = [];
    await renderReport(data);
    expect(screen.getByText('Critical risk level')).toBeInTheDocument();
    expect(screen.getByText('The expert rules raised no alert.')).toBeInTheDocument();
  });
});

describe('the summary', () => {
  it('is in paragraphs, by Gemini, beside the risks at a glance', async () => {
    await renderReport();
    const summary = section('Summary');
    expect(within(summary).getByText(/Written by Gemini/)).toBeInTheDocument();
    expect(summary.querySelectorAll('p')).toHaveLength(3);
    const glance = screen.getByRole('complementary', { name: 'At a glance' });
    expect(within(glance).getByText('34 risks')).toBeInTheDocument();
    expect(within(glance).getByText('in 7 domains and 21 subdomains')).toBeInTheDocument();
  });

  it('says when it is missing', async () => {
    const data = exampleCopy();
    data.summary = null;
    await renderReport(data);
    expect(
      within(section('Summary')).getByText('The summary is not available for this report.'),
    ).toBeInTheDocument();
  });
});

describe('the charts', () => {
  it('read the risks of each domain, by severity', async () => {
    await renderReport();
    // The legend of the colours is hidden from screen readers: the rows say the severities in words
    const rows = within(section('Risks by domain')).getAllByRole('listitem');
    expect(rows).toHaveLength(7);
    expect(rows[3]).toHaveTextContent('Malicious Actors & Misuse');
    expect(rows[3]).toHaveTextContent('6 risks: 4 high, 2 medium, 0 low');
  });

  it('give the causal flows in a table, and the values that no risk has', async () => {
    await renderReport();
    const flow = section('How the risks come about');
    const table = within(flow).getByRole('table');
    expect(within(table).getAllByRole('row')).toHaveLength(1 + 9);
    expect(
      within(table).getByRole('row', { name: 'Entity: AI Intent: Unintentional 18' }),
    ).toBeInTheDocument();
    expect(
      within(flow).getByText('No risks: Other (intent), Pre-deployment (timing).'),
    ).toBeInTheDocument();
  });

  it('list the eight indices of the profile with their values', async () => {
    await renderReport();
    const profile = section('Alert & safety profile');
    const values = within(profile)
      .getAllByRole('definition')
      .map((dd) => dd.textContent?.split(' The share')[0]);
    expect(values).toEqual([
      'Risk concentration 32',
      'Impact control 68',
      'Operational exposure 91',
      'Prevention deficit 100',
      'Preventability 0',
      'Threat intensity 32',
      'Safety culture 68',
      'Human-caused share 41',
    ]);
  });

  it('put the patterns in a table of groups by cause', async () => {
    await renderReport();
    const table = within(section('Risk patterns')).getByRole('table');
    const critical = within(table).getByRole('row', { name: /^Critical/ });
    const [ai, human, any] = within(critical).getAllByRole('cell');
    expect(ai).toHaveTextContent('Unintended AI failures18');
    expect(human).toHaveTextContent('Malicious human risks10');
    expect(any).toHaveTextContent('Low-priority preventable0');
    const low = within(table).getByRole('row', { name: /^Low/ });
    expect(
      within(low)
        .getAllByRole('cell')
        .map((cell) => cell.textContent),
    ).toEqual(['', '', 'Low operational risks4']);
  });
});

describe('all the risks', () => {
  it('filter by severity and by cause, and search their text', async () => {
    await renderReport();
    const risks = section('All the risks');
    expect(within(risks).getByText('34 risks')).toBeInTheDocument();
    const filters = within(risks).getByRole('search', { name: 'Filter the risks' });
    await userEvent.click(
      within(within(filters).getByRole('group', { name: 'Severity' })).getByRole('radio', {
        name: 'High',
      }),
    );
    expect(within(risks).getByText('11 of 34 risks')).toBeInTheDocument();
    await userEvent.click(
      within(within(filters).getByRole('group', { name: 'Entity' })).getByRole('radio', {
        name: 'Human',
      }),
    );
    expect(within(risks).getByText('7 of 34 risks')).toBeInTheDocument();
    await userEvent.type(within(filters).getByRole('searchbox'), 'phishing');
    expect(within(risks).getByText('1 of 34 risks')).toBeInTheDocument();
    expect(
      within(risks).getByRole('button', {
        name: /Facilitation of fraud, scams, or phishing attacks/,
      }),
    ).toBeInTheDocument();
  });

  it('say when nothing matches, and show them all again', async () => {
    await renderReport();
    const risks = section('All the risks');
    await userEvent.type(within(risks).getByRole('searchbox'), 'quantum entanglement');
    expect(
      within(risks).getByText('No risk matches the search and the filters.'),
    ).toBeInTheDocument();
    await userEvent.click(within(risks).getByRole('button', { name: 'Show all the risks' }));
    expect(within(risks).getByText('34 risks')).toBeInTheDocument();
    expect(within(risks).getByRole('searchbox')).toHaveValue('');
  });

  it('move between the filters with the arrow keys', async () => {
    await renderReport();
    const severity = within(section('All the risks')).getByRole('group', { name: 'Severity' });
    await userEvent.click(within(severity).getByRole('radio', { name: 'All' }));
    await userEvent.keyboard('{ArrowRight}');
    expect(within(severity).getByRole('radio', { name: 'High' })).toBeChecked();
  });

  it('open a risk on what the report knows of it: the answer, the reasons, the causes', async () => {
    await renderReport();
    const risk = screen.getByRole('button', { name: /Bias in output tailoring/ });
    expect(risk).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(risk);
    expect(risk).toHaveAttribute('aria-expanded', 'true');
    const details = screen.getByRole('region', { name: /Bias in output tailoring/ });
    expect(within(details).getByText('From your answers · question 1.1')).toBeInTheDocument();
    expect(
      within(details).getByText(/^What user data or attributes are collected/),
    ).toBeInTheDocument();
    for (const heading of ['Why it is a risk', 'Why this severity', 'Mitigation', 'Causes']) {
      expect(within(details).getByRole('heading', { name: heading })).toBeInTheDocument();
    }
    // Labelled by Gemini: its reasons, and no confidence
    expect(within(details).getAllByText('Why this label')).toHaveLength(3);
    expect(within(details).queryByRole('meter')).toBeNull();
  });

  it('show how sure Laya was of each label, in the same tone for every one', async () => {
    await renderReport(labelledByLaya());
    await userEvent.click(screen.getByRole('button', { name: /Bias in output tailoring/ }));
    const details = screen.getByRole('region', { name: /Bias in output tailoring/ });
    expect(
      within(details).getByText('Labelled by the Laya model, on this computer'),
    ).toBeInTheDocument();
    const entity = within(details).getByRole('meter', { name: 'Confidence of the label: Entity' });
    expect(entity).toHaveAttribute('aria-valuenow', '94');
    expect(within(details).getByText('Next most likely: Human, 3%')).toBeInTheDocument();
    expect(within(details).getByText('Next most likely: Other, 18%')).toBeInTheDocument();
    expect(
      within(details).getByText(
        'The risk occurs due to an unexpected outcome from pursuing a goal.',
      ),
    ).toBeInTheDocument();
    // No warning sign, and none of the texts of the old review threshold
    expect(details).not.toHaveTextContent('⚠');
    expect(details).not.toHaveTextContent(/To review|Label assigned/);
  });

  it('leave out a reason that the analysis did not give', async () => {
    const data = exampleCopy();
    for (const risk of data.risks) risk.severity_rationale = null;
    await renderReport(data);
    await userEvent.click(screen.getByRole('button', { name: /Bias in output tailoring/ }));
    const details = screen.getByRole('region', { name: /Bias in output tailoring/ });
    expect(within(details).queryByRole('heading', { name: 'Why this severity' })).toBeNull();
  });
});

describe('the whole report', () => {
  it('passes the checks of axe', async () => {
    await renderReport(labelledByLaya());
    await userEvent.click(screen.getByRole('button', { name: /Bias in output tailoring/ }));
    // Colours need a real browser: the end-to-end tests check them
    const results = await axe.run(document.body, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(
      results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(' | ')}`),
    ).toEqual([]);
  });

  it('ends with what it is for, and the credit of the MIT taxonomies', async () => {
    await renderReport();
    const footer = screen.getByRole('contentinfo');
    expect(footer).toHaveTextContent(
      'It supports, but does not replace, a risk assessment by qualified people.',
    );
    expect(footer).toHaveTextContent(
      '© 2025 · Taxonomies: MIT AI Risk Repository (Slattery et al., 2024), CC BY 4.0',
    );
  });
});
