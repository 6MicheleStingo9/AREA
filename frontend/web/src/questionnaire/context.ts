import { createContext, use } from 'react';
import type { Draft } from './draft';
import type { Answer } from './types';

export interface Assessment {
  draft: Draft;
  setAnswer: (questionId: string, answer: Answer) => void;
  setSystemName: (name: string) => void;
  setLastRun: (runId: string) => void;
  /** Forget the answers, to start a new assessment */
  reset: () => void;
}

export const AssessmentContext = createContext<Assessment | null>(null);

export function useAssessment(): Assessment {
  const assessment = use(AssessmentContext);
  if (!assessment) throw new Error('useAssessment() needs an <AssessmentProvider>');
  return assessment;
}
