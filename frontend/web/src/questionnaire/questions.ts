import type { Language } from '@kindynos/ui';
import { use } from 'react';
import { fetchQuestionnaire } from '../api';
import { useWebI18n } from '../messages';
import type { Question } from './types';

const cache = new Map<Language, Promise<Question[]>>();

/** The questions in a language, fetched once; after a failure, the next call fetches them again */
export function questionsIn(lang: Language): Promise<Question[]> {
  let questions = cache.get(lang);
  if (!questions) {
    questions = fetchQuestionnaire(lang);
    cache.set(lang, questions);
    questions.catch(() => cache.delete(lang));
  }
  return questions;
}

/** The questions in the language of the interface: the page waits for them (Suspense) */
export function useQuestions(): Question[] {
  const { lang } = useWebI18n();
  return use(questionsIn(lang));
}
