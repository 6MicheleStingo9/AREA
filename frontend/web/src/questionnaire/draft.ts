import type { Answer } from './types';

/** What the questionnaire keeps in this browser until the user starts again */
export interface Draft {
  systemName: string;
  answers: Record<string, Answer>;
  /** The last analysis started from these answers */
  lastRun?: string;
}

const STORAGE_KEY = 'kindynos:assessment';
const VERSION = 1;

export const EMPTY_DRAFT: Draft = { systemName: '', answers: {} };

export function readDraft(): Draft {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null') as {
      version?: number;
      draft?: Draft;
    } | null;
    if (stored?.version === VERSION && stored.draft) return { ...EMPTY_DRAFT, ...stored.draft };
  } catch {
    // Storage blocked, or a value not written by this version: start empty
  }
  return EMPTY_DRAFT;
}

export function writeDraft(draft: Draft): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: VERSION, draft }));
  } catch {
    // Not kept: the answers still hold until the page closes
  }
}
