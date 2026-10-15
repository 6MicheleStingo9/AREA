import type { Language } from '@kindynos/ui';

/**
 * The data of a report, as agents/report_generator/report_data.py prepares them and
 * html_generator.py writes them into the page, in <script id="report-data">.
 */
export interface ReportData {
  version: 1;
  run_id: string;
  language: Language;
  /** The name of the AI system, the title of the report: it stays on the computer */
  system_name: string | null;
  /** When the report was made, in ISO 8601 */
  created: string;
  questions: { answered: number | null; total: number | null };
  /** The executive summary that Gemini wrote, in paragraphs separated by blank lines */
  summary: string | null;
  /** What labelled the causes: the local Laya model, or the LLM */
  causality_model: { backend: 'laya' | 'llm'; model: string } | null;
  results: Results;
  alerts: Alert[];
  counts: Counts;
  domains: DomainRow[];
  profile: ProfileAxis[];
  flow: { entity_intent: FlowLink[]; intent_timing: FlowLink[] };
  patterns: Pattern[];
  risks: Risk[];
  /** The answers behind the risks, by question id: the id of the subdomain */
  answers: Record<string, AnswerEntry>;
  /** The output of the expert rules, as they wrote it */
  heuristic: unknown;
}

export type Severity = 'high' | 'medium' | 'low';
export type Entity = 'ai' | 'human' | 'other';
export type Intent = 'intentional' | 'unintentional' | 'other';
export type Timing = 'pre-deployment' | 'post-deployment' | 'other';
export type Axis = 'entity' | 'intent' | 'timing';

export const SEVERITIES: readonly Severity[] = ['high', 'medium', 'low'];
/** The values of each causal axis, in the order of the MIT Causal Taxonomy */
export const CAUSES = {
  entity: ['ai', 'human', 'other'],
  intent: ['intentional', 'unintentional', 'other'],
  timing: ['pre-deployment', 'post-deployment', 'other'],
} as const satisfies Record<Axis, readonly string[]>;
export const AXES: readonly Axis[] = ['entity', 'intent', 'timing'];

export interface Results {
  score: number | null;
  /** critical, high, medium or low */
  level: string | null;
  concern: string | null;
  action: string | null;
  /** The domains with the most high-severity risks, at most three */
  critical_domains: { id: string; high: number }[];
}

export interface Alert {
  id: string;
  /** A count or a percentage, as the rule computes it */
  value: number | null;
}

export interface Counts {
  risks: number;
  domains: number;
  subdomains: number;
  severity: Record<Severity, number>;
  entity: Record<Entity, number>;
  intent: Record<Intent, number>;
  timing: Record<Timing, number>;
}

export interface DomainRow {
  id: string;
  high: number;
  medium: number;
  low: number;
}

export type ProfileAxisName = 'severity' | 'exposure' | 'prevention' | 'intent' | 'entity';

/** One axis of the alert and safety profile: its criticality and its safety index, in % */
export interface ProfileAxis {
  axis: ProfileAxisName;
  criticality: number | null;
  safety: number | null;
}

export interface FlowLink {
  from: string;
  to: string;
  count: number;
}

export type PatternCategory = 'critical' | 'moderate' | 'prevention' | 'low';
export type PatternCause = 'ai' | 'human' | 'any';

export interface Pattern {
  id: string;
  category: PatternCategory;
  cause: PatternCause;
  count: number;
}

export interface Cause {
  value: string;
  /** Why, in the words of the LLM that labelled it */
  rationale: string | null;
  /** The probability of the value, for a label of Laya */
  confidence: number | null;
  /** The probability of every value, for a label of Laya */
  probabilities: Record<string, number> | null;
}

export interface Risk {
  /** The subdomain and the position of the risk in it: 1.2-1 */
  id: string;
  subdomain: string;
  title: string;
  explanation: string | null;
  severity: Severity;
  severity_rationale: string | null;
  mitigation: string | null;
  causes: Record<Axis, Cause>;
}

export type Answer = string | { selected: string[]; other: string | null } | null;

export interface AnswerEntry {
  question: string | null;
  answer: Answer;
  followups: { question: string; answer: string }[];
}

/** The data in the page, or null when there are none: the app built but not filled by Python */
export function readReportData(text: string | null | undefined): ReportData | null {
  if (!text) return null;
  try {
    const data = JSON.parse(text) as Partial<ReportData> | null;
    return data?.version === 1 && Array.isArray(data.risks) ? (data as ReportData) : null;
  } catch {
    return null;
  }
}
