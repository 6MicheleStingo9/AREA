import type { HTMLAttributes, ReactNode } from 'react';
import styles from './Eyebrow.module.css';

interface EyebrowProps extends HTMLAttributes<HTMLElement> {
  as?: 'p' | 'span' | 'h2' | 'h3';
  /** A decorative icon before the text */
  icon?: ReactNode;
}

/** The small capitals above a title, that say what the page or the section is about */
export function Eyebrow({ as: Element = 'p', icon, className, children, ...rest }: EyebrowProps) {
  return (
    <Element className={[styles.eyebrow, className].filter(Boolean).join(' ')} {...rest}>
      {icon && (
        <span aria-hidden="true" className={styles.icon}>
          {icon}
        </span>
      )}
      {children}
    </Element>
  );
}
