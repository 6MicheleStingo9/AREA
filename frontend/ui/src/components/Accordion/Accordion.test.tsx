import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './Accordion';

describe('Accordion', () => {
  it('opens a section from its heading button', async () => {
    render(
      <Accordion type="single" collapsible>
        <AccordionItem value="time">
          <AccordionTrigger level={2}>How long does the analysis take?</AccordionTrigger>
          <AccordionContent>Usually from one to three minutes.</AccordionContent>
        </AccordionItem>
      </Accordion>,
    );
    const button = screen.getByRole('button', { name: 'How long does the analysis take?' });
    expect(button.closest('h2')).not.toBeNull();
    expect(button).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(
      screen.getByRole('region', { name: 'How long does the analysis take?' }),
    ).toHaveTextContent('Usually from one to three minutes.');
  });
});
