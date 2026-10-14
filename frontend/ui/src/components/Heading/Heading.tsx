import type { HTMLAttributes, Ref } from 'react';
import styles from './Heading.module.css';

type Level = 1 | 2 | 3 | 4;
type Size = 'hero' | 'page' | 'section' | 'title';

const SIZE_OF_LEVEL: Record<Level, Size> = { 1: 'page', 2: 'section', 3: 'title', 4: 'title' };

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  /** The level in the outline of the page */
  level: Level;
  /** The look, by default the one of the level: hero is the title of the welcome page */
  size?: Size;
  ref?: Ref<HTMLHeadingElement>;
}

export function Heading({ level, size = SIZE_OF_LEVEL[level], className, ...rest }: HeadingProps) {
  const Tag = `h${level}` as const;
  return (
    <Tag
      className={[styles.heading, styles[size], className].filter(Boolean).join(' ')}
      {...rest}
    />
  );
}
