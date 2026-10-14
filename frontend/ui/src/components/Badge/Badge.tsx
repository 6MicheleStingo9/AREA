import type { ReactNode } from 'react';
import styles from './Badge.module.css';

/** A severity, a causal entity, or neutral (no dot) */
export type BadgeTone = 'neutral' | 'high' | 'medium' | 'low' | 'ai' | 'human' | 'other';

interface BadgeProps {
  tone?: BadgeTone;
  /** What the badge sits on, to stand out from it */
  on?: 'surface' | 'muted';
  children: ReactNode;
}

/** A label in a pill. The dot repeats the tone in colour: the text always says it too. */
export function Badge({ tone = 'neutral', on = 'surface', children }: BadgeProps) {
  return (
    <span className={[styles.badge, styles[`on-${on}`], styles[tone]].join(' ')}>
      {tone !== 'neutral' && <span aria-hidden="true" className={styles.dot} />}
      {children}
    </span>
  );
}
