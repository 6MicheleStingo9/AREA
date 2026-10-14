import { useId, type InputHTMLAttributes, type ReactNode } from 'react';
import styles from './Choice.module.css';

interface ChoiceGroupProps {
  /** The question, or the name of the choice */
  legend: ReactNode;
  /** question: the big title of a questionnaire page; label: the size of a field label */
  legendStyle?: 'question' | 'label';
  hint?: ReactNode;
  /** row: side by side, as pills; column: one under the other, as cards */
  direction?: 'column' | 'row';
  children: ReactNode;
}

/** A set of Choices with its question */
export function ChoiceGroup({
  legend,
  legendStyle = 'label',
  hint,
  direction = 'column',
  children,
}: ChoiceGroupProps) {
  const hintId = useId();
  return (
    <fieldset className={styles.group} aria-describedby={hint ? hintId : undefined}>
      <legend className={styles[legendStyle]}>{legend}</legend>
      {hint && (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      <div className={[styles.options, styles[direction]].join(' ')}>{children}</div>
    </fieldset>
  );
}

interface ChoiceProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  type?: 'radio' | 'checkbox';
  /** card: a whole row to click; pill: a short option */
  shape?: 'card' | 'pill';
  label: ReactNode;
}

/** A radio button or a checkbox inside its label, which marks it when chosen */
export function Choice({ type = 'radio', shape = 'card', label, className, ...rest }: ChoiceProps) {
  return (
    <label className={[styles.choice, styles[shape], className].filter(Boolean).join(' ')}>
      <input type={type} className={styles.input} {...rest} />
      <span>{label}</span>
    </label>
  );
}
