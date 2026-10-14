import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

// Read from the disk: Vitest empties the CSS files that the tests import
const tokens = readFileSync(new URL('./tokens.css', import.meta.url), 'utf-8');

type Palette = Record<string, string>;

/** The colour tokens of tokens.css, one palette per theme */
function palettes(): { light: Palette; dark: Palette } {
  const light: Palette = {};
  const dark: Palette = {};
  for (const [, name = '', value = ''] of tokens.matchAll(/--color-([\w-]+):\s*([^;]+);/g)) {
    const pair = /^light-dark\((#\w+),\s*(#\w+)\)$/.exec(value);
    light[name] = pair?.[1] ?? value;
    dark[name] = pair?.[2] ?? value;
  }
  return { light, dark };
}

/** The relative luminance of a #rrggbb colour, as WCAG defines it */
function luminance(hex: string): number {
  const [r = 0, g = 0, b = 0] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a = '', b = ''): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (light + 0.05) / (dark + 0.05);
}

const TEXT = ['ink', 'ink-muted', 'ink-subtle'];
const SURFACES = ['ground', 'surface', 'surface-muted'];

describe.each(['light', 'dark'] as const)('the %s theme', (theme) => {
  const colors = palettes()[theme];

  it('gives every text 4.5:1 on every surface (WCAG 1.4.3)', () => {
    for (const text of TEXT) {
      for (const surface of SURFACES) {
        expect(
          contrast(colors[text], colors[surface]),
          `${text} on ${surface}`,
        ).toBeGreaterThanOrEqual(4.5);
      }
    }
    expect(contrast(colors['on-primary'], colors.primary)).toBeGreaterThanOrEqual(4.5);
    // The error messages of the fields
    expect(contrast(colors['severity-high'], colors.surface)).toBeGreaterThanOrEqual(4.5);
  });

  it('gives the edge of the fields and the focus ring 3:1 on every surface (WCAG 1.4.11)', () => {
    for (const surface of SURFACES) {
      expect(
        contrast(colors['line-strong'], colors[surface]),
        `edge on ${surface}`,
      ).toBeGreaterThanOrEqual(3);
      expect(contrast(colors.focus, colors[surface]), `focus on ${surface}`).toBeGreaterThanOrEqual(
        3,
      );
    }
  });
});
