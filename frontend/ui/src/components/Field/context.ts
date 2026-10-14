import { createContext, use } from 'react';

/** What a field gives its control: the id of its label, its description, whether it is invalid */
export interface FieldControl {
  id: string;
  'aria-describedby'?: string;
  'aria-invalid'?: true;
}

export const FieldContext = createContext<FieldControl | null>(null);

/** The attributes that tie a control to the Field around it, or none outside a Field */
export function useFieldControl(): FieldControl | Record<string, never> {
  return use(FieldContext) ?? {};
}
