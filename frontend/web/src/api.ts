import type { Language } from '@kindynos/ui';
import type { Answer, AnswerError, Question } from './questionnaire/types';

/* The JSON API of FastAPI (api/assessments.py): the questionnaire, and the assessments. */

export type Step = 'domain' | 'causes' | 'rules' | 'report';
export const STEPS: readonly Step[] = ['domain', 'causes', 'rules', 'report'];

/** The main results of a finished assessment: the summary of the report */
export interface Results {
  score: number | null;
  level: 'critical' | 'high' | 'medium' | 'low' | null;
  concern: string | null;
  action: string | null;
  critical_domain: { id: string; high: number } | null;
  risks: number;
  domains: number;
  severity: { high?: number; medium?: number; low?: number };
}

export interface AssessmentStatus {
  id: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'interrupted' | 'not_found';
  step?: Step | null;
  risks?: number | null;
  labelled?: number | null;
  lang?: Language | null;
  system_name?: string | null;
  error?: string | null;
  error_code?: 'quota' | 'failed' | null;
  result?: Results | null;
  report_url?: string;
  archive_url?: string;
}

export interface NewAssessment {
  lang: Language;
  system_name?: string;
  answers: Record<string, Answer>;
}

export type StartOutcome =
  { ok: true; id: string } | { ok: false; errors: Record<string, AnswerError[]> };

async function json<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

export async function fetchQuestionnaire(lang: Language): Promise<Question[]> {
  const response = await fetch(`/api/questionnaire?lang=${lang}`);
  if (!response.ok) throw new Error(`GET /api/questionnaire: ${response.status}`);
  return (await json<{ questions: Question[] }>(response)).questions;
}

/** Start the analysis, or get back the errors of each question that the server refused */
export async function startAssessment(assessment: NewAssessment): Promise<StartOutcome> {
  const response = await fetch('/api/assessments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(assessment),
  });
  if (response.status === 422) {
    const body = await json<{ errors?: Record<string, AnswerError[]> }>(response);
    return { ok: false, errors: body.errors ?? {} };
  }
  if (!response.ok) throw new Error(`POST /api/assessments: ${response.status}`);
  return { ok: true, id: (await json<{ id: string }>(response)).id };
}

export async function fetchAssessment(id: string, signal?: AbortSignal): Promise<AssessmentStatus> {
  const response = await fetch(`/api/assessments/${encodeURIComponent(id)}`, { signal });
  if (response.status === 404) return { id, status: 'not_found' };
  if (!response.ok) throw new Error(`GET /api/assessments/${id}: ${response.status}`);
  return json<AssessmentStatus>(response);
}
