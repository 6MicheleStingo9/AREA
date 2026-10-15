import * as Primitive from '@radix-ui/react-accordion';
import { ChevronDown } from 'lucide-react';
import styles from './Accordion.module.css';

type AccordionProps = (Primitive.AccordionSingleProps | Primitive.AccordionMultipleProps) & {
  /**
   * boxed: the sections in one frame; cards: each section in its own; plain: no frame, for the
   * sections inside another one
   */
  variant?: 'boxed' | 'cards' | 'plain';
};

/**
 * Sections that open one at a time (type="single") or together (type="multiple"), on Radix: the
 * keyboard (arrows, Home, End) and the ARIA attributes come from there.
 */
export function Accordion({ variant = 'boxed', className, ...rest }: AccordionProps) {
  return (
    <Primitive.Root className={[styles[variant], className].filter(Boolean).join(' ')} {...rest} />
  );
}

export function AccordionItem({ className, ...rest }: Primitive.AccordionItemProps) {
  return (
    <Primitive.Item className={[styles.item, className].filter(Boolean).join(' ')} {...rest} />
  );
}

interface AccordionTriggerProps extends Primitive.AccordionTriggerProps {
  /** The level of the heading around the button, in the outline of the page */
  level?: 2 | 3 | 4 | 5 | 6;
}

export function AccordionTrigger({
  level = 3,
  className,
  children,
  ...rest
}: AccordionTriggerProps) {
  const Heading = `h${level}` as const;
  return (
    <Primitive.Header asChild>
      <Heading className={styles.header}>
        <Primitive.Trigger
          className={[styles.trigger, className].filter(Boolean).join(' ')}
          {...rest}
        >
          <span className={styles.label}>{children}</span>
          <ChevronDown aria-hidden="true" className={styles.chevron} />
        </Primitive.Trigger>
      </Heading>
    </Primitive.Header>
  );
}

export function AccordionContent({
  className,
  children,
  ...rest
}: Primitive.AccordionContentProps) {
  return (
    <Primitive.Content className={[styles.content, className].filter(Boolean).join(' ')} {...rest}>
      <div className={styles.body}>{children}</div>
    </Primitive.Content>
  );
}
