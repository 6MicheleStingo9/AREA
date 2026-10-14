import { Fragment, type ReactNode } from 'react';

const PLACEHOLDER = /\{(\w+)\}/;

/**
 * A translated string with elements in its placeholders, for the strings that hold a link or some
 * code: richText(t('key'), { path: <code>files/reports/</code> }). t() leaves the placeholders it
 * has no value for, so that they reach this function.
 */
export function richText(text: string, nodes: Record<string, ReactNode>): ReactNode[] {
  // With a capturing group, split() puts the placeholder names at the odd indices
  return text
    .split(PLACEHOLDER)
    .map((part, i) =>
      i % 2 ? <Fragment key={i}>{part in nodes ? nodes[part] : `{${part}}`}</Fragment> : part,
    );
}
