import type { HTMLAttributes } from 'react';
import styles from './Card.module.css';

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: 'div' | 'section' | 'article' | 'aside';
  /** surface: a card on the ground; muted: a panel inside a card */
  tone?: 'surface' | 'muted';
}

export function Card({ as: Element = 'div', tone = 'surface', className, ...rest }: CardProps) {
  return (
    <Element
      className={[styles.card, styles[tone], className].filter(Boolean).join(' ')}
      {...rest}
    />
  );
}
