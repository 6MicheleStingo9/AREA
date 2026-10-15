/** A follow-up: a question that an answer opens, by its condition */
export interface FollowUp {
  text: string;
  required?: boolean;
  multiline?: boolean;
  condition: { type: string; value?: number | number[] };
}

/** A question, as GET /api/questionnaire sends it (files/questions_<language>.json) */
export interface Question {
  /** The MIT subdomain that the question explores: "1.3" */
  id: string;
  question: string;
  help_text?: string;
  type: 'free_text' | 'multiple_choice' | 'checkbox';
  required?: boolean;
  multiline?: boolean;
  placeholder?: string;
  validation?: { min_length?: number; max_length?: number };
  options?: string[];
  allow_other?: boolean;
  other_label?: string;
  min_selections?: number;
  follow_ups: FollowUp[];
}

/**
 * An answer, as POST /api/assessments takes it: the options by index, so that an answer survives a
 * change of language.
 */
export interface Answer {
  text?: string;
  choice?: number;
  choices?: number[];
  /** The text of "Other", while it is ticked */
  other?: string;
  /** The answers to the follow-ups, by their index */
  followups?: Record<string, string>;
}

export type ErrorCode =
  | 'required'
  | 'min_length'
  | 'max_length'
  | 'unknown_option'
  | 'other_required'
  | 'min_selections'
  | 'followup_required';

/** What is wrong with an answer: the same codes as quiz/logic.py */
export interface AnswerError {
  code: ErrorCode;
  min?: number;
  max?: number;
  followup?: number;
}
