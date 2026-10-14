import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { renderInApp } from '../../test/render';
import { Field, TextArea, TextInput } from './Field';

describe('Field', () => {
  it('names its control and describes it with the hint', () => {
    renderInApp(
      <Field label="Name of the AI system" hint="It becomes the title of the report." optional>
        <TextInput />
      </Field>,
    );
    const input = screen.getByRole('textbox', { name: 'Name of the AI system (optional)' });
    expect(input).toHaveAccessibleDescription('It becomes the title of the report.');
    expect(input).not.toBeInvalid();
  });

  it('marks the control invalid and reads the error first', () => {
    renderInApp(
      <Field label="Details" hint="A sentence or two." error="Write at least 10 characters.">
        <TextArea />
      </Field>,
    );
    const area = screen.getByRole('textbox', { name: 'Details' });
    expect(area).toBeInvalid();
    expect(area).toHaveAccessibleDescription('Write at least 10 characters. A sentence or two.');
  });

  it('says "optional" in the language of the interface', () => {
    renderInApp(
      <Field label="Nome" optional>
        <TextInput />
      </Field>,
      'it',
    );
    expect(screen.getByRole('textbox', { name: 'Nome (facoltativo)' })).toBeInTheDocument();
  });
});
