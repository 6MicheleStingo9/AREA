import { CircleAlert } from 'lucide-react';
import {
  useId,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from 'react';
import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import { FieldContext, useFieldControl } from './context';
import styles from './Field.module.css';

interface FieldProps {
  label: ReactNode;
  /** A help text under the control */
  hint?: ReactNode;
  /** What is wrong with the value: it marks the control invalid and comes before the hint */
  error?: ReactNode;
  /** Shows "(optional)" after the label */
  optional?: boolean;
  /** One TextInput or TextArea */
  children: ReactNode;
}

/** A label, a control, and its help and error texts, tied together for screen readers */
export function Field({ label, hint, error, optional, children }: FieldProps) {
  const { t } = useI18n<CommonMessages>();
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [error && errorId, hint && hintId].filter(Boolean).join(' ') || undefined;
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
        {/* The space outside the span: an accessible name joins the text of each element, trimmed */}
        {optional && (
          <>
            {' '}
            <span className={styles.optional}>{t('common.optional')}</span>
          </>
        )}
      </label>
      <FieldContext
        value={{ id, 'aria-describedby': describedBy, 'aria-invalid': error ? true : undefined }}
      >
        {children}
      </FieldContext>
      {error && (
        <p id={errorId} className={styles.error}>
          <CircleAlert aria-hidden="true" className={styles.errorIcon} />
          {error}
        </p>
      )}
      {hint && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
    </div>
  );
}

export function TextInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  const control = useFieldControl();
  return (
    <input
      type="text"
      {...control}
      className={[styles.control, className].filter(Boolean).join(' ')}
      {...rest}
    />
  );
}

export function TextArea({
  className,
  rows = 3,
  ...rest
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const control = useFieldControl();
  return (
    <textarea
      rows={rows}
      {...control}
      className={[styles.control, styles.textarea, className].filter(Boolean).join(' ')}
      {...rest}
    />
  );
}
