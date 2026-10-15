/** The languages of the interface, as the folders of locales/: the first is the fallback. */
export const LANGUAGES = ['en', 'it'] as const;
export type Language = (typeof LANGUAGES)[number];

/** A string that depends on a number: one form per plural category of English and Italian. */
export interface PluralForms {
  one: string;
  other: string;
}

/** Strings in nested groups, as in a file of locales/<language>/. */
export interface Messages {
  [key: string]: string | PluralForms | Messages;
}

/** The dotted paths to the strings of a catalog, like "common.theme.to_dark"; any for Messages. */
export type MessageKey<M> = string extends keyof M
  ? string
  : {
      [K in keyof M & string]: M[K] extends string | PluralForms ? K : `${K}.${MessageKey<M[K]>}`;
    }[keyof M & string];

export type Params = Record<string, string | number>;

const PLACEHOLDER = /\{(\w+)\}/g;

function isPlural(entry: unknown): entry is PluralForms {
  if (typeof entry !== 'object' || entry === null) return false;
  const keys = Object.keys(entry);
  return keys.length === 2 && keys.includes('one') && keys.includes('other');
}

function lookup(messages: Messages | undefined, key: string): string | PluralForms | undefined {
  let node: Messages[string] | undefined = messages;
  for (const part of key.split('.')) {
    if (typeof node !== 'object' || isPlural(node)) return undefined;
    node = node[part];
  }
  return typeof node === 'string' || isPlural(node) ? node : undefined;
}

/** The text with its placeholders replaced; a placeholder without a value stays as it is. */
export function fill(text: string, params: Params = {}): string {
  return text.replace(PLACEHOLDER, (placeholder, name: string) =>
    name in params ? String(params[name]) : placeholder,
  );
}

/**
 * The string at a dotted key in a language, with its placeholders filled. A key missing in the
 * language falls back to English, then to the key itself.
 */
export function translate(
  catalogs: Partial<Record<Language, Messages>>,
  lang: Language,
  key: string,
  params: Params = {},
): string {
  for (const language of new Set<Language>([lang, LANGUAGES[0]])) {
    const entry = lookup(catalogs[language], key);
    if (entry === undefined) continue;
    if (typeof entry === 'string') return fill(entry, params);
    const category = new Intl.PluralRules(language).select(Number(params.count));
    return fill(category === 'one' ? entry.one : entry.other, params);
  }
  return key;
}
