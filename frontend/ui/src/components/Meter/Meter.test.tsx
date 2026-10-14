import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Meter } from './Meter';

describe('Meter', () => {
  it('is a meter with its value when it has a label', () => {
    render(<Meter value={94} label="Confidence" valueText="94%" />);
    const meter = screen.getByRole('meter', { name: 'Confidence' });
    expect(meter).toHaveAttribute('aria-valuenow', '94');
    expect(meter).toHaveAttribute('aria-valuetext', '94%');
  });

  it('is hidden from screen readers without a label', () => {
    const { container } = render(<Meter value={61} />);
    expect(screen.queryByRole('meter')).toBeNull();
    expect(container.firstElementChild).toHaveAttribute('aria-hidden', 'true');
  });

  it('keeps the value between 0 and 100', () => {
    render(<Meter value={140} label="Score" />);
    expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '100');
  });
});
