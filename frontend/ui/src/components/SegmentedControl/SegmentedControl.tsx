import { useId, type ReactNode } from 'react';
import styles from './SegmentedControl.module.css';

export interface SegmentedOption<V extends string> {
  value: V;
  label: ReactNode;
  /** The name to read, when the label is short ("IT" for "Italiano"): it must contain the label */
  ariaLabel?: string;
  /** The language of the option, if not the page's */
  lang?: string;
}

interface SegmentedControlProps<V extends string> {
  legend: string;
  /** Hide the legend when the options speak for themselves: screen readers still read it */
  hideLegend?: boolean;
  options: readonly SegmentedOption<V>[];
  value: V;
  /** NoInfer: the options and the value say what V is, not the handler */
  onChange: (value: NoInfer<V>) => void;
  /** segmented: options in a track, as a switch; chips: separate pills, as filters */
  variant?: 'segmented' | 'chips';
}

/** One option out of a few, always visible: radio buttons, so the arrow keys move between them */
export function SegmentedControl<V extends string>({
  legend,
  hideLegend,
  options,
  value,
  onChange,
  variant = 'segmented',
}: SegmentedControlProps<V>) {
  const name = useId();
  return (
    <fieldset className={[styles.group, styles[variant]].join(' ')}>
      <legend className={hideLegend ? styles.hiddenLegend : styles.legend}>{legend}</legend>
      <div className={styles.options}>
        {options.map((option) => (
          <label key={option.value} className={styles.option} lang={option.lang}>
            <input
              type="radio"
              className={styles.input}
              name={name}
              value={option.value}
              checked={option.value === value}
              onChange={() => onChange(option.value)}
              aria-label={option.ariaLabel}
            />
            <span aria-hidden={option.ariaLabel ? true : undefined}>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
