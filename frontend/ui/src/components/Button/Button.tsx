import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'link';

interface ButtonLook {
  /** primary: the main action of a page; secondary: the others; link: an action that reads as a link */
  variant?: ButtonVariant;
  size?: 'md' | 'lg';
  /** Icons before and after the text: decorative, since the text names the action */
  icon?: ReactNode;
  iconEnd?: ReactNode;
}

function className({ variant = 'primary', size = 'md' }: ButtonLook, extra?: string): string {
  return [styles.button, styles[variant], styles[size], extra].filter(Boolean).join(' ');
}

function Icon({ children }: { children: ReactNode }) {
  return (
    <span aria-hidden="true" className={styles.icon}>
      {children}
    </span>
  );
}

export function Button({
  variant,
  size,
  icon,
  iconEnd,
  className: extra,
  type = 'button',
  children,
  ...rest
}: ButtonLook & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button type={type} className={className({ variant, size }, extra)} {...rest}>
      {icon && <Icon>{icon}</Icon>}
      {children}
      {iconEnd && <Icon>{iconEnd}</Icon>}
    </button>
  );
}

/** A link with the look of a button: for an action that goes to another page */
export function ButtonLink({
  variant,
  size,
  icon,
  iconEnd,
  className: extra,
  children,
  ...rest
}: ButtonLook & AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) {
  return (
    <a className={className({ variant, size }, extra)} {...rest}>
      {icon && <Icon>{icon}</Icon>}
      {children}
      {iconEnd && <Icon>{iconEnd}</Icon>}
    </a>
  );
}
