import { act, render } from '@testing-library/react';
import type { Cause, ReportData } from '../data';
import { ReportApp } from '../Report';
import example from './example.json';

/** The example run as Python prepares it: tests/test_report_data.py keeps the file up to date */
export const EXAMPLE = example as unknown as ReportData;

/** A copy of the example, to change */
export function exampleCopy(): ReportData {
  return JSON.parse(JSON.stringify(EXAMPLE)) as ReportData;
}

const laya = (value: string, probabilities: Record<string, number>): Cause => ({
  value,
  rationale: 'A definition. Label assigned by the local Laya model with 94% confidence.',
  confidence: probabilities[value] ?? 0,
  probabilities,
});

/** The example with its first risk labelled by Laya, which gives a confidence and the probabilities */
export function labelledByLaya(): ReportData {
  const data = exampleCopy();
  data.causality_model = { backend: 'laya', model: 'laya-causal-v4' };
  const [first] = data.risks;
  if (first) {
    first.causes = {
      entity: laya('ai', { ai: 0.94, human: 0.03, other: 0.03 }),
      intent: laya('unintentional', { intentional: 0.12, unintentional: 0.7, other: 0.18 }),
      timing: laya('post-deployment', {
        'pre-deployment': 0.04,
        'post-deployment': 0.93,
        other: 0.03,
      }),
    };
  }
  return data;
}

/** The report of the data, awaited: React renders it in a transition */
export async function renderReport(data: ReportData = EXAMPLE) {
  await act(() => {
    render(<ReportApp data={data} />);
    return Promise.resolve();
  });
}
