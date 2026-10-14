import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './IconButton.module.css';

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label'> {
  /** What the button does: its accessible name and its tooltip */
  label: string;
  children: ReactNode;
}

/** A round button with only an icon */
export function IconButton({ label, className, children, ...rest }: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={[styles.button, className].filter(Boolean).join(' ')}
      {...rest}
    >
      <span aria-hidden="true" className={styles.icon}>
        {children}
      </span>
    </button>
  );
}
