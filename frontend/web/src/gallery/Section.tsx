import { Heading } from '@kindynos/ui';
import type { ReactNode } from 'react';
import styles from './Gallery.module.css';

interface SectionProps {
  id: string;
  title: string;
  intro?: string;
  children: ReactNode;
}

export function Section({ id, title, intro, children }: SectionProps) {
  return (
    <section aria-labelledby={id} className={styles.section}>
      <div className={styles.head}>
        <Heading level={2} id={id}>
          {title}
        </Heading>
        {intro && <p className={styles.intro}>{intro}</p>}
      </div>
      {children}
    </section>
  );
}
