import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import { renderInApp } from '../../test/render';
import { LanguageSwitch } from '../LanguageSwitch/LanguageSwitch';
import { SegmentedControl } from './SegmentedControl';

function Filter() {
  const [value, setValue] = useState('all');
  return (
    <SegmentedControl
      legend="Severity"
      variant="chips"
      value={value}
      onChange={setValue}
      options={[
        { value: 'all', label: 'All' },
        { value: 'high', label: 'High' },
      ]}
    />
  );
}

describe('SegmentedControl', () => {
  it('is a group of radio buttons named by its legend', async () => {
    renderInApp(<Filter />);
    const group = screen.getByRole('group', { name: 'Severity' });
    expect(group).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'All' })).toBeChecked();
    await userEvent.click(screen.getByText('High'));
    expect(screen.getByRole('radio', { name: 'High' })).toBeChecked();
  });
});

describe('LanguageSwitch', () => {
  it('reads each language by its name, and switches the interface', async () => {
    renderInApp(<LanguageSwitch />);
    expect(screen.getByRole('group', { name: 'Language' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('radio', { name: 'Italiano' }));
    expect(screen.getByRole('group', { name: 'Lingua' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Italiano' })).toBeChecked();
    expect(document.documentElement.lang).toBe('it');
  });
});
