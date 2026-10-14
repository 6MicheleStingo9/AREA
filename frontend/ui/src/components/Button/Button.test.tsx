import { render, screen } from '@testing-library/react';
import { ArrowRight } from 'lucide-react';
import { describe, expect, it } from 'vitest';
import { Button, ButtonLink } from './Button';

describe('Button', () => {
  it('is a button, not a submit, unless asked', () => {
    render(<Button iconEnd={<ArrowRight />}>Next question</Button>);
    const button = screen.getByRole('button', { name: 'Next question' });
    expect(button).toHaveAttribute('type', 'button');
  });

  it('has a link twin for the actions that go to another page', () => {
    render(<ButtonLink href="/report/abc">Open the report</ButtonLink>);
    expect(screen.getByRole('link', { name: 'Open the report' })).toHaveAttribute(
      'href',
      '/report/abc',
    );
  });
});
