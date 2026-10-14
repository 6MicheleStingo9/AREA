import styles from './Meter.module.css';

interface MeterProps {
  /** From 0 to 100 */
  value: number;
  /**
   * What the meter measures, for screen readers. Without it the meter is decorative: give it none
   * only when the page shows its value in text next to it.
   */
  label?: string;
  /** The value as it should be read, if not the number: "61 out of 100" */
  valueText?: string;
  tone?: 'neutral' | 'high' | 'medium' | 'low' | 'human';
  size?: 'sm' | 'md';
}

/** A bar that fills to a value: a score, a confidence, the progress of the questionnaire */
export function Meter({ value, label, valueText, tone = 'neutral', size = 'md' }: MeterProps) {
  const percent = Math.min(100, Math.max(0, value));
  const track = [styles.track, styles[size], styles[tone]].join(' ');
  const fill = <span className={styles.fill} style={{ width: `${percent}%` }} />;
  if (!label) {
    return (
      <span aria-hidden="true" className={track}>
        {fill}
      </span>
    );
  }
  return (
    <span
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      aria-valuetext={valueText}
      className={track}
    >
      {fill}
    </span>
  );
}
