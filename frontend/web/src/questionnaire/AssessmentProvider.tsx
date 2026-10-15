import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AssessmentContext, type Assessment } from './context';
import { EMPTY_DRAFT, readDraft, writeDraft, type Draft } from './draft';

/** The answers being given, kept in this browser at every change */
export function AssessmentProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<Draft>(readDraft);

  useEffect(() => {
    writeDraft(draft);
  }, [draft]);

  const assessment = useMemo<Assessment>(
    () => ({
      draft,
      setAnswer: (questionId, answer) =>
        setDraft((current) => ({
          ...current,
          answers: { ...current.answers, [questionId]: answer },
        })),
      setSystemName: (systemName) => setDraft((current) => ({ ...current, systemName })),
      setLastRun: (lastRun) => setDraft((current) => ({ ...current, lastRun })),
      // The last analysis stays reachable from the welcome page
      reset: () => setDraft((current) => ({ ...EMPTY_DRAFT, lastRun: current.lastRun })),
    }),
    [draft],
  );

  return <AssessmentContext value={assessment}>{children}</AssessmentContext>;
}
