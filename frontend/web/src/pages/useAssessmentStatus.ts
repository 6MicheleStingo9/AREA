import { useEffect, useState } from 'react';
import { fetchAssessment, type AssessmentStatus } from '../api';

const WAIT = 1500;
const RETRY = 3000;

/** The state of an assessment, asked again until the analysis ends; offline while the server is away */
export function useAssessmentStatus(id: string): {
  status: AssessmentStatus | null;
  offline: boolean;
} {
  const [status, setStatus] = useState<AssessmentStatus | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let timer: number | undefined;
    const ask = async () => {
      try {
        const next = await fetchAssessment(id, controller.signal);
        setStatus(next);
        setOffline(false);
        if (next.status === 'pending' || next.status === 'running')
          timer = window.setTimeout(() => void ask(), WAIT);
      } catch {
        if (controller.signal.aborted) return;
        setOffline(true);
        timer = window.setTimeout(() => void ask(), RETRY);
      }
    };
    void ask();
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [id]);

  return { status, offline };
}
