import { LANGUAGES, type Language } from './translate';

const STORAGE_KEY = 'kindynos:language';

function isLanguage(value: unknown): value is Language {
  return LANGUAGES.includes(value as Language);
}

/** The language chosen on an earlier visit, else the first of the browser's that Kindynos speaks. */
export function detectLanguage(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isLanguage(stored)) return stored;
  } catch {
    // Storage blocked (private browsing, policies): ask the browser
  }
  const preferred = navigator.languages.map((tag) => tag.slice(0, 2).toLowerCase());
  return preferred.find(isLanguage) ?? LANGUAGES[0];
}

export function storeLanguage(lang: Language): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Not kept for the next visit: the choice still holds for this one
  }
}
